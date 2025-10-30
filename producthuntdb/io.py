"""I/O operations for ProductHuntDB.

This module handles:
1. Async GraphQL API client with retry logic
2. Database operations (SQLite with SQLModel)
3. Kaggle dataset management and publishing

Example:
    >>> from producthuntdb.io import AsyncGraphQLClient
    >>> client = AsyncGraphQLClient(token="...")
    >>> posts = await client.fetch_posts_page(None, None, 50, PostsOrder.NEWEST)
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import httpx
from loguru import logger
from sqlmodel import Session, create_engine, select
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from producthuntdb.config import PostsOrder, settings
from producthuntdb.models import (
    CrawlState,
    MakerPostLink,
    MediaRow,
    PostRow,
    PostTopicLink,
    TopicRow,
    UserRow,
)
from producthuntdb.utils import format_iso, parse_datetime, utc_now_iso

# =============================================================================
# GraphQL Query Definitions
# =============================================================================

QUERY_POSTS_PAGE = """
query PostsPage($first: Int!, $after: String, $order: PostsOrder, $postedAfter: DateTime) {
  posts(
    first: $first,
    after: $after,
    order: $order,
    postedAfter: $postedAfter
  ) {
    nodes {
      id
      userId
      name
      tagline
      description
      slug
      url
      website
      createdAt
      featuredAt
      commentsCount
      votesCount
      reviewsCount
      reviewsRating
      isCollected
      isVoted
      user {
        id
        username
        name
        headline
        profileImage
        websiteUrl
        url
      }
      makers {
        id
        username
        name
        headline
        profileImage
      }
      topics(first: 10) {
        nodes {
          id
          name
          slug
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
      productLinks {
        type
        url
      }
      thumbnail {
        type
        url
        videoUrl
      }
      media {
        type
        url
        videoUrl
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""

QUERY_VIEWER = """
query Viewer {
  viewer {
    user {
      id
      username
      name
      headline
      isViewer
      profileImage
      websiteUrl
      url
    }
  }
}
"""

QUERY_TOPICS_PAGE = """
query TopicsPage($first: Int!, $after: String) {
  topics(first: $first, after: $after, order: FOLLOWERS_COUNT) {
    nodes {
      id
      name
      slug
      description
      url
      createdAt
      followersCount
      postsCount
      isFollowing
      image(height: 128, width: 128)
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""

QUERY_COLLECTIONS_PAGE = """
query CollectionsPage($first: Int!, $after: String) {
  collections(first: $first, after: $after, order: FEATURED_AT) {
    nodes {
      id
      name
      tagline
      description
      url
      coverImage
      createdAt
      featuredAt
      followersCount
      isFollowing
      userId
      user {
        id
        username
        name
        headline
        profileImage
        websiteUrl
        url
        isViewer
      }
      posts(first: 10) {
        nodes {
          id
          name
          votesCount
          commentsCount
          url
          createdAt
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
      topics(first: 10) {
        nodes {
          id
          name
          slug
          followersCount
          postsCount
        }
        pageInfo {
          endCursor
          hasNextPage
        }
      }
    }
    pageInfo {
      endCursor
      hasNextPage
    }
  }
}
"""

# =============================================================================
# Custom Exceptions
# =============================================================================


class TransientGraphQLError(Exception):
    """Retryable network/HTTP layer failures."""

    pass


# =============================================================================
# Async GraphQL Client
# =============================================================================


class AsyncGraphQLClient:
    """Async HTTP/2 client for Product Hunt GraphQL API.

    Features:
    - Retry logic with exponential backoff
    - Rate limiting awareness
    - Connection pooling
    - Error handling for transient and permanent failures

    Args:
        token: Product Hunt API authentication token
        max_concurrency: Maximum concurrent requests

    Example:
        >>> client = AsyncGraphQLClient(token="...")
        >>> posts = await client.fetch_posts_page(None, None, 50, PostsOrder.NEWEST)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        max_concurrency: Optional[int] = None,
    ) -> None:
        """Initialize async GraphQL client.

        Args:
            token: API token (defaults to settings.producthunt_token)
            max_concurrency: Max concurrent requests (defaults to settings.max_concurrency)
        """
        self._token = token or settings.producthunt_token
        self._max_concurrency = max_concurrency or settings.max_concurrency
        self._sem = asyncio.Semaphore(self._max_concurrency)
        self._rate_limit_limit = None
        self._rate_limit_remaining = None
        self._rate_limit_reset = None

    async def _do_http_post(
        self,
        query: str,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """Perform raw HTTP POST with error handling.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Parsed JSON data field from response

        Raises:
            TransientGraphQLError: For retryable failures
            RuntimeError: For permanent GraphQL errors
        """
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(http2=True, timeout=30.0) as client:
            try:
                resp = await client.post(
                    settings.graphql_endpoint,
                    headers=headers,
                    json={"query": query, "variables": variables},
                )
            except (httpx.TimeoutException, httpx.NetworkError) as exc:
                raise TransientGraphQLError(f"Network/timeout error: {exc}") from exc

            # Extract rate limit information
            self._rate_limit_limit = resp.headers.get("X-RateLimit-Limit")
            self._rate_limit_remaining = resp.headers.get("X-RateLimit-Remaining")
            self._rate_limit_reset = resp.headers.get("X-RateLimit-Reset")

            # Log rate limit status
            if self._rate_limit_remaining:
                try:
                    remaining = int(self._rate_limit_remaining)
                    limit = int(self._rate_limit_limit) if self._rate_limit_limit else "?"

                    if remaining < 10:
                        logger.warning(
                            f"⚠️ Rate limit low: {remaining}/{limit} remaining "
                            f"(resets at {self._rate_limit_reset or 'unknown'})"
                        )
                except (ValueError, TypeError):
                    pass

            # Handle non-200 status codes
            if resp.status_code != 200 and (
                resp.status_code == 429 or 500 <= resp.status_code < 600
            ):
                reset_info = (
                    f" (resets at {self._rate_limit_reset})" if resp.status_code == 429 else ""
                )
                raise TransientGraphQLError(f"HTTP {resp.status_code}{reset_info}")

            if resp.status_code != 200:
                logger.error(f"Non-retryable HTTP {resp.status_code}: {resp.text[:200]}")
                raise RuntimeError(f"HTTP {resp.status_code}")

            # Parse response
            try:
                body = resp.json()
            except Exception as exc:
                raise TransientGraphQLError(f"Invalid JSON: {exc}") from exc

            # Check for GraphQL errors
            if "errors" in body and body["errors"]:
                logger.error(f"GraphQL errors: {body['errors']}")
                raise RuntimeError(f"GraphQL errors: {body['errors']}")

            return body.get("data", {})

    async def _post_with_retry(
        self,
        query: str,
        variables: dict[str, Any],
    ) -> dict[str, Any]:
        """POST with semaphore and retry logic.

        Args:
            query: GraphQL query string
            variables: Query variables

        Returns:
            Parsed data from response
        """

        # Create logging bridge for tenacity
        logging_logger = logging.getLogger(__name__)

        @retry(
            reraise=True,
            stop=stop_after_attempt(20),
            wait=wait_exponential(multiplier=3, min=5, max=120) + wait_random(0, 5),
            retry=retry_if_exception_type(TransientGraphQLError),
            before_sleep=before_sleep_log(logging_logger, logging.WARNING),
        )
        async def _runner() -> dict[str, Any]:
            async with self._sem:
                # Adaptive delay based on rate limit
                if self._rate_limit_remaining:
                    try:
                        remaining = int(self._rate_limit_remaining)
                        if remaining < 5:
                            await asyncio.sleep(5.0)
                        elif remaining < 20:
                            await asyncio.sleep(3.0)
                        else:
                            await asyncio.sleep(2.0)
                    except (ValueError, TypeError):
                        await asyncio.sleep(2.0)
                else:
                    await asyncio.sleep(2.0)

                return await self._do_http_post(query, variables)

        return await _runner()

    def get_rate_limit_status(self) -> dict[str, Any]:
        """Get current rate limit status from last API call.

        Returns:
            Dictionary with limit, remaining, and reset keys
        """
        return {
            "limit": self._rate_limit_limit,
            "remaining": self._rate_limit_remaining,
            "reset": self._rate_limit_reset,
        }

    async def fetch_posts_page(
        self,
        after_cursor: Optional[str] = None,
        posted_after_dt: Optional[datetime | str] = None,
        first: Optional[int] = None,
        order: Optional[PostsOrder] = None,
    ) -> dict[str, Any]:
        """Fetch a page of posts.

        Args:
            after_cursor: Pagination cursor
            posted_after_dt: Filter posts created after this datetime (datetime object or ISO string)
            first: Page size (defaults to settings.page_size)
            order: Post ordering (defaults to NEWEST)

        Returns:
            Posts object with nodes and pageInfo
        """
        first = first or settings.page_size
        order = order or PostsOrder.NEWEST

        # Handle both string and datetime inputs for posted_after_dt
        posted_after_str = None
        if posted_after_dt:
            if isinstance(posted_after_dt, str):
                posted_after_str = posted_after_dt
            else:
                posted_after_str = format_iso(posted_after_dt)

        variables = {
            "first": first,
            "after": after_cursor,
            "order": order.value,
            "postedAfter": posted_after_str,
        }

        data = await self._post_with_retry(QUERY_POSTS_PAGE, variables)
        return data.get("posts", {})

    async def fetch_viewer(self) -> dict[str, Any]:
        """Fetch authenticated viewer information.

        Returns:
            Viewer object with user data
        """
        data = await self._post_with_retry(QUERY_VIEWER, {})
        return data.get("viewer", {})

    async def fetch_topics_page(
        self,
        after_cursor: Optional[str] = None,
        first: Optional[int] = None,
    ) -> dict[str, Any]:
        """Fetch a page of topics.

        Args:
            after_cursor: Pagination cursor
            first: Page size (defaults to settings.page_size)

        Returns:
            Topics object with nodes and pageInfo
        """
        first = first or settings.page_size

        variables = {
            "first": first,
            "after": after_cursor,
        }

        data = await self._post_with_retry(QUERY_TOPICS_PAGE, variables)
        return data.get("topics", {})

    async def fetch_collections_page(
        self,
        after_cursor: Optional[str] = None,
        first: Optional[int] = None,
    ) -> dict[str, Any]:
        """Fetch a page of collections.

        Args:
            after_cursor: Pagination cursor
            first: Page size (defaults to settings.page_size)

        Returns:
            Collections object with nodes and pageInfo
        """
        first = first or settings.page_size

        variables = {
            "first": first,
            "after": after_cursor,
        }

        data = await self._post_with_retry(QUERY_COLLECTIONS_PAGE, variables)
        return data.get("collections", {})


# =============================================================================
# Database Operations
# =============================================================================


class DatabaseManager:
    """Manages SQLite database operations.

    Features:
    - Connection management with WAL mode
    - CRUD operations for all entity types
    - Crawl state tracking
    - Bulk inserts and updates

    Example:
        >>> db = DatabaseManager()
        >>> db.initialize()
        >>> user = db.upsert_user(user_data)
    """

    def __init__(self, database_path: Optional[Path] = None):
        """Initialize database manager.

        Args:
            database_path: Path to SQLite database (defaults to settings.database_path)
        """
        self.database_path = database_path or settings.database_path
        self.engine = None
        self.session = None

    def initialize(self) -> None:
        """Initialize database engine and create tables."""
        from producthuntdb.models import SQLModel

        # Use the instance's database_path to construct the URL
        db_url = f"sqlite:///{self.database_path}"

        self.engine = create_engine(
            db_url,
            echo=False,
            connect_args={"check_same_thread": False},
        )

        # Create all tables
        SQLModel.metadata.create_all(self.engine)

        # Enable WAL mode for better concurrency
        with self.engine.connect() as conn:
            conn.exec_driver_sql("PRAGMA journal_mode = WAL;")
            conn.exec_driver_sql("PRAGMA synchronous = NORMAL;")
            conn.commit()

        self.session = Session(self.engine)
        logger.info(f"✅ Database initialized at {self.database_path}")

    def close(self) -> None:
        """Close database connection."""
        if self.session is not None:
            self.session.close()
        if self.engine is not None:
            self.engine.dispose()

    def upsert_user(self, user_data: dict[str, Any]) -> UserRow:
        """Insert or update user record.

        Args:
            user_data: User data dictionary

        Returns:
            Inserted or updated UserRow
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        user_id = user_data["id"]
        existing = self.session.get(UserRow, user_id)

        if existing:
            # Update existing
            for key, value in user_data.items():
                if key == "createdAt" and value:
                    value = format_iso(parse_datetime(value))
                setattr(existing, key, value)
            user_row = existing
        else:
            # Create new
            if "createdAt" in user_data and user_data["createdAt"]:
                user_data["createdAt"] = format_iso(parse_datetime(user_data["createdAt"]))
            user_row = UserRow(**user_data)
            self.session.add(user_row)

        self.session.commit()
        return user_row

    def upsert_post(self, post_data: dict[str, Any]) -> PostRow:
        """Insert or update post record.

        Args:
            post_data: Post data dictionary

        Returns:
            Inserted or updated PostRow
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        post_id = post_data["id"]
        existing = self.session.get(PostRow, post_id)

        # Prepare data
        processed = {**post_data}

        # Convert timestamps
        for ts_field in ["createdAt", "featuredAt"]:
            if ts_field in processed and processed[ts_field]:
                processed[ts_field] = format_iso(parse_datetime(processed[ts_field]))

        # Convert JSON fields
        if "thumbnail" in processed and processed["thumbnail"]:
            thumb = processed["thumbnail"]
            if isinstance(thumb, dict):
                processed["thumbnail_type"] = thumb.get("type")
                processed["thumbnail_url"] = thumb.get("url")
                processed["thumbnail_videoUrl"] = thumb.get("videoUrl")
            del processed["thumbnail"]

        # Handle media separately - will be saved to MediaRow table
        media_items = None
        if "media" in processed:
            media_items = processed.pop("media", None)

        if "productLinks" in processed and processed["productLinks"]:
            processed["productlinks_json"] = json.dumps(processed["productLinks"])
            del processed["productLinks"]

        # Remove fields not in PostRow
        for key in ["user", "makers", "topics"]:
            processed.pop(key, None)

        if existing:
            # Update existing
            for key, value in processed.items():
                setattr(existing, key, value)
            post_row = existing
        else:
            # Create new
            post_row = PostRow(**processed)
            self.session.add(post_row)

        self.session.commit()

        # Handle media items - save to MediaRow table
        if media_items and isinstance(media_items, list):
            # Delete existing media for this post
            self.session.query(MediaRow).filter(MediaRow.post_id == post_id).delete()

            # Add new media entries
            for idx, media_dict in enumerate(media_items):
                if isinstance(media_dict, dict):
                    media_row = MediaRow(
                        post_id=post_id,
                        type=media_dict.get("type", ""),
                        url=media_dict.get("url", ""),
                        videoUrl=media_dict.get("videoUrl"),
                        order_index=idx,
                    )
                    self.session.add(media_row)

            self.session.commit()

        return post_row

    def upsert_topic(self, topic_data: dict[str, Any]) -> TopicRow:
        """Insert or update topic record.

        Args:
            topic_data: Topic data dictionary

        Returns:
            Inserted or updated TopicRow
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        topic_id = topic_data["id"]
        existing = self.session.get(TopicRow, topic_id)

        # Process timestamps
        if "createdAt" in topic_data and topic_data["createdAt"]:
            topic_data["createdAt"] = format_iso(parse_datetime(topic_data["createdAt"]))

        if existing:
            for key, value in topic_data.items():
                setattr(existing, key, value)
            topic_row = existing
        else:
            topic_row = TopicRow(**topic_data)
            self.session.add(topic_row)

        self.session.commit()
        return topic_row

    def link_post_topics(self, post_id: str, topic_ids: list[str]) -> None:
        """Create post-topic links.

        Args:
            post_id: Post ID
            topic_ids: List of topic IDs to link
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        for topic_id in topic_ids:
            # Check if link exists
            stmt = select(PostTopicLink).where(
                PostTopicLink.post_id == post_id,
                PostTopicLink.topic_id == topic_id,
            )
            existing = self.session.exec(stmt).first()

            if not existing:
                link = PostTopicLink(post_id=post_id, topic_id=topic_id)
                self.session.add(link)

        self.session.commit()

    def link_post_makers(self, post_id: str, maker_ids: list[str]) -> None:
        """Create post-maker links.

        Args:
            post_id: Post ID
            maker_ids: List of maker user IDs to link
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        for maker_id in maker_ids:
            stmt = select(MakerPostLink).where(
                MakerPostLink.post_id == post_id,
                MakerPostLink.user_id == maker_id,
            )
            existing = self.session.exec(stmt).first()

            if not existing:
                link = MakerPostLink(post_id=post_id, user_id=maker_id)
                self.session.add(link)

        self.session.commit()

    def get_crawl_state(self, entity: str) -> Optional[str]:
        """Get last crawl timestamp for entity.

        Args:
            entity: Entity name (e.g., "posts")

        Returns:
            Last timestamp string or None
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        state = self.session.get(CrawlState, entity)
        return state.last_timestamp if state else None

    def update_crawl_state(self, entity: str, timestamp: str) -> None:
        """Update crawl state for entity.

        Args:
            entity: Entity name
            timestamp: ISO8601 timestamp string
        """
        if self.session is None:
            raise RuntimeError("Database not initialized")

        state = self.session.get(CrawlState, entity)

        if state:
            state.last_timestamp = timestamp
            state.updated_at = utc_now_iso()
        else:
            state = CrawlState(
                entity=entity,
                last_timestamp=timestamp,
                updated_at=utc_now_iso(),
            )
            self.session.add(state)

        self.session.commit()


# =============================================================================
# Kaggle Dataset Management
# =============================================================================


class KaggleManager:
    """Manages Kaggle dataset operations.

    Features:
    - Dataset creation and updates
    - File preparation and compression
    - Metadata management

    Example:
        >>> km = KaggleManager()
        >>> km.export_database_to_csv("/path/to/db")
        >>> km.publish_dataset()
    """

    def __init__(self):
        """Initialize Kaggle manager."""
        self.dataset_slug = settings.kaggle_dataset_slug
        self.has_kaggle = settings.kaggle_username and settings.kaggle_key

        if self.has_kaggle:
            # Import kaggle API only if credentials are available
            try:
                from kaggle import api  # type: ignore[import-untyped]

                self.api = api
                logger.info("✅ Kaggle API initialized")
            except Exception as exc:
                logger.warning(f"⚠️ Kaggle API import failed: {exc}")
                self.has_kaggle = False

    def export_database_to_csv(self, output_dir: Optional[Path] = None) -> None:
        """Export database tables to CSV files and copy database file.

        Args:
            output_dir: Directory to write CSV files (defaults to settings.export_dir)
        """
        import shutil

        import pandas as pd  # type: ignore[import-untyped]
        from sqlalchemy import create_engine as sa_create_engine

        # Use settings.export_dir if output_dir not provided
        output_dir = output_dir or settings.export_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy the SQLite database file
        db_path = Path(str(settings.database_path))
        if db_path.exists():
            dest_db = output_dir / "producthunt.db"
            shutil.copy2(db_path, dest_db)
            logger.info(f"✅ Copied database to {dest_db}")

            # Also copy WAL and SHM files if they exist (for WAL mode)
            for ext in ["-wal", "-shm"]:
                wal_path = Path(str(db_path) + ext)
                if wal_path.exists():
                    shutil.copy2(wal_path, output_dir / f"producthunt.db{ext}")

        # Export tables to CSV
        engine = sa_create_engine(settings.database_url)

        tables = [
            "userrow",
            "postrow",
            "topicrow",
            "collectionrow",
            "commentrow",
            "voterow",
            "posttopiclink",
            "makerpostlink",
            "collectionpostlink",
            "crawlstate",
        ]

        for table in tables:
            try:
                df = pd.read_sql_table(table, engine)
                csv_path = output_dir / f"{table}.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"✅ Exported {table} ({len(df)} rows) to {csv_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to export {table}: {e}")

    def publish_dataset(
        self,
        data_dir: Optional[Path] = None,
        title: str = "ProductHuntDB - Complete Product Hunt Data Archive",
        subtitle: str = "Daily-updated GraphQL API data: products, users, topics, collections, votes & more",
        description: str = """# ProductHunt GraphQL API Data Sink

A comprehensive, production-grade dataset containing Product Hunt data extracted via the official GraphQL API. This dataset provides normalized, relational data about products, users, topics, collections, comments, votes, and engagement metrics.

## 📊 Dataset Contents

### Core Tables
- **Posts** (`postrow.csv`): Product launches with detailed metadata, descriptions, taglines, URLs, and timestamps (~50K-100K rows, ~20-50MB)
- **Topics** (`topicrow.csv`): Product categories, tags, and topic hierarchies (~1K-2K rows, ~200KB-500KB)
- **Collections** (`collectionrow.csv`): Curated product collections with metadata (~5K-10K rows, ~1-3MB)
- **Users** (`userrow.csv`): User profiles including makers, hunters, and community members (~100K-200K rows, ~30-80MB)
- **Comments** (`commentrow.csv`): Community discussions, feedback threads, and engagement (~200K-500K rows, ~100-300MB)
- **Votes** (`voterow.csv`): Product upvotes, voting timestamps, and engagement patterns (~1M-5M rows, ~50-200MB)

### Junction Tables (Many-to-Many Relationships)
- **Post-Topic Links** (`posttopiclink.csv`): Maps products to their categories/tags (~150K-300K rows, ~5-10MB)
- **Maker-Post Links** (`makerpostlink.csv`): Links makers to the products they created (~100K-200K rows, ~3-8MB)
- **Collection-Post Links** (`collectionpostlink.csv`): Maps products to curated collections (~50K-150K rows, ~2-5MB)

### System Tables
- **Crawl State** (`crawlstate.csv`): Metadata tracking last sync timestamps and cursor positions (~10-20 rows, <1KB)

### Database Files
- **SQLite Database** (`producthunt.db`): Complete relational database with all tables, indexes, and foreign keys (~500MB-2GB)

**Total Dataset Size**: ~600MB-2.5GB compressed  
**Data Coverage**: Products from 2013-present (updated daily)  
**Encoding**: UTF-8 throughout  
**Compression**: Kaggle auto-compresses for download

## 🔄 Update Schedule

**Daily Updates**: This dataset is refreshed daily via automated Kaggle notebook execution, ensuring fresh data with minimal lag. The incremental sync process tracks changes and only fetches new/modified records.

**Update Time**: ~02:00 UTC daily  
**Sync Duration**: 5-15 minutes (incremental)  
**Data Lag**: <24 hours from Product Hunt

## 📚 Data Structure & Schema

All CSV files follow a consistent, normalized schema with:
- **Primary Keys**: Unique identifiers for each record
- **Foreign Keys**: Relationships between tables
- **Timestamps**: ISO 8601 formatted datetime fields
- **Nullable Fields**: Clearly documented optional data

The SQLite database provides:
- Full relational integrity with foreign key constraints
- Optimized indexes for common query patterns
- Efficient storage with proper data types
- ACID compliance for data consistency

## 🎯 Use Cases

- **Product Analytics**: Track product launches, trends, and success patterns
- **User Behavior Analysis**: Study voting patterns, comment engagement, and community dynamics
- **Time Series Analysis**: Analyze temporal patterns in product launches and user activity
- **Network Analysis**: Explore maker networks, collection curation, and topic relationships
- **Machine Learning**: Train models for product success prediction, recommendation systems, or sentiment analysis
- **Market Research**: Identify trending topics, popular products, and startup ecosystem insights

## 🛠️ Data Collection Methodology

- **Source**: Official Product Hunt GraphQL API (v2)
- **Authentication**: OAuth2 API token
- **Rate Limiting**: Adaptive retry with exponential backoff
- **Sync Strategy**: Incremental updates with cursor-based pagination
- **Data Validation**: Pydantic v2 schemas with strict type checking
- **Error Handling**: Comprehensive logging and graceful failure recovery

## 📦 File Formats

- **CSV Files**: UTF-8 encoded, comma-delimited, with headers
- **SQLite Database**: SQLite 3.x compatible, optimized for read queries
- **Schema Documentation**: Embedded field descriptions in metadata

## ⚠️ Known Limitations

- **API Coverage**: Dataset completeness depends on Product Hunt API availability and rate limits
- **Historical Data**: May not include pre-2015 products due to API limitations
- **Deleted Content**: Removed posts/comments may persist in historical snapshots
- **Real-time Updates**: Daily refresh means up to 24-hour lag for latest data

## 📖 Documentation & Code

- **GitHub Repository**: [producthuntdb](https://github.com/wyattowalsh/producthuntdb)
- **CLI Tool**: `producthuntdb` Python package for data sync and export
- **Documentation**: Full API docs and usage guides at repository
- **License**: CC0-1.0 (Public Domain) - free for any use

## 📝 Citation

If you use this dataset in research or publications, please cite:

```bibtex
@dataset{producthuntdb_2024,
  title={ProductHuntDB: Complete Product Hunt Data Archive},
  author={Walsh, Wyatt},
  year={2024},
  publisher={Kaggle},
  howpublished={\\url{https://www.kaggle.com/datasets/wyattowalsh/producthunt-graphql-api-data-sink}},
  note={Daily-updated dataset via Product Hunt GraphQL API}
}
```

## 💡 Example Notebooks & Queries

### Sample SQL Queries

```sql
-- Top 10 products by votes
SELECT name, tagline, votesCount 
FROM postrow 
ORDER BY votesCount DESC 
LIMIT 10;

-- Most active topics
SELECT t.name, COUNT(ptl.post_id) as product_count
FROM topicrow t
JOIN posttopiclink ptl ON t.id = ptl.topic_id
GROUP BY t.id
ORDER BY product_count DESC;

-- Maker collaboration network
SELECT u.name, COUNT(DISTINCT mpl.post_id) as products_made
FROM userrow u
JOIN makerpostlink mpl ON u.id = mpl.user_id
GROUP BY u.id
HAVING products_made > 1;
```

### Getting Started

1. **Load SQLite**: `import sqlite3; conn = sqlite3.connect('producthunt.db')`
2. **Load CSV with Pandas**: `import pandas as pd; df = pd.read_csv('postrow.csv')`
3. **Explore Schema**: Check metadata.json or use `.schema` in SQLite

### Related Resources

- [Product Hunt Official Site](https://www.producthunt.com)
- [Product Hunt API Docs](https://api.producthunt.com/v2/docs)
- [Example Analysis Notebook](#) _(coming soon)_

## 🔄 Version History

### v1.0.0 (2024-10-30)
- Initial release with complete dataset
- 11 tables with full schema documentation
- Enhanced metadata following Kaggle best practices
- Daily automated updates configured

### Schema Evolution
- **v1.0**: Initial normalized schema with 8 core tables + 3 junction tables
- **Future**: Planned additions for media assets, reviews, and goal tracking

## 🏷️ Data Quality

- **Completeness**: 95%+ coverage of public Product Hunt data
- **Accuracy**: Validated against API responses with strict schemas
- **Consistency**: Normalized schema with referential integrity
- **Timeliness**: Daily automated updates via scheduled Kaggle notebook
- **Usability**: Full field-level documentation with data types
""",
    ) -> None:
        """Publish or update Kaggle dataset with enhanced metadata.

        Args:
            data_dir: Directory containing database and CSV files (defaults to settings.export_dir)
            title: Dataset title (6-50 characters)
            subtitle: Dataset subtitle (20-80 characters)
            description: Dataset description (markdown supported)
        """
        if not self.has_kaggle:
            logger.warning("⚠️ Kaggle credentials not configured")
            return

        if not self.dataset_slug:
            logger.warning("⚠️ Kaggle dataset slug not configured")
            return

        # Use settings.export_dir if data_dir not provided
        data_dir = data_dir or settings.export_dir

        # Ensure data directory exists
        if not data_dir.exists():
            raise ValueError(f"Data directory does not exist: {data_dir}")

        # Create/update metadata file with comprehensive information following Kaggle Data Package spec
        metadata = {
            "title": title,
            "id": self.dataset_slug,
            "subtitle": subtitle,
            "description": description,
            "isPrivate": False,
            "licenses": [{"name": "CC0-1.0"}],
            "keywords": [
                "product-hunt",
                "graphql-api",
                "data-pipeline",
                "time-series",
                "products",
                "startups",
                "technology",
                "user-generated-content",
                "social-media",
                "api-data",
                "sqlite",
                "csv",
                "normalized-data",
                "relational-database",
                "business",
                "beginner",
                "intermediate",
                "advanced",
                "analytics",
                "machine-learning",
                "makers",
                "entrepreneurs",
                "innovation",
                "saas",
                "tech-products",
            ],
            "collaborators": [
                {
                    "name": "Wyatt Walsh",
                    "role": "owner",
                    "username": "wyattowalsh",
                }
            ],
            "data": [],
            "resources": [
                {
                    "path": "producthunt.db",
                    "description": "Complete SQLite database (v3.x) containing all normalized tables with foreign key constraints, indexes, and relationships. Ideal for complex queries, joins, and analytical workflows. Use with pandas.read_sql, SQLAlchemy, or any SQLite-compatible tool.",
                    "schema": {
                        "fields": [
                            {
                                "name": "database_file",
                                "type": "string",
                                "description": "Self-contained SQLite database with 11 tables: userrow, postrow, topicrow, collectionrow, commentrow, voterow, posttopiclink, makerpostlink, collectionpostlink, crawlstate, plus alembic_version for schema versioning",
                            }
                        ]
                    },
                },
                {
                    "path": "userrow.csv",
                    "description": "Product Hunt user profiles including makers, hunters, voters, and commenters. Contains display names, profile images, social links, and account metadata. Foreign key target for posts, comments, and votes tables.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique user identifier (UUID or numeric string)",
                            },
                            {
                                "name": "username",
                                "type": "string",
                                "description": "User handle/username on Product Hunt (unique, lowercase)",
                            },
                            {"name": "name", "type": "string", "description": "Full display name"},
                            {
                                "name": "headline",
                                "type": "string",
                                "description": "User bio/headline (max ~140 chars)",
                            },
                            {
                                "name": "profileImage",
                                "type": "url",
                                "description": "Avatar image URL (typically 400x400px JPEG/PNG)",
                            },
                            {
                                "name": "websiteUrl",
                                "type": "url",
                                "description": "Personal or company website URL",
                            },
                            {
                                "name": "url",
                                "type": "url",
                                "description": "Product Hunt profile page URL",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Account creation timestamp (ISO 8601 UTC)",
                            },
                        ]
                    },
                },
                {
                    "path": "postrow.csv",
                    "description": "Product launches, updates, and community posts with comprehensive metadata. Core analytical table containing vote counts, comment counts, review ratings, media assets, and temporal data. Each row represents a unique product launch or significant update.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique post identifier (UUID or numeric string, primary key)",
                            },
                            {
                                "name": "userId",
                                "type": "id",
                                "description": "Foreign key to userrow.id (hunter/creator)",
                            },
                            {
                                "name": "name",
                                "type": "string",
                                "description": "Product name (2-60 chars typically)",
                            },
                            {
                                "name": "tagline",
                                "type": "string",
                                "description": "One-line product description (max ~60-80 chars)",
                            },
                            {
                                "name": "description",
                                "type": "string",
                                "description": "Full markdown-formatted product description (HTML may be present)",
                            },
                            {
                                "name": "url",
                                "type": "url",
                                "description": "Canonical Product Hunt post URL",
                            },
                            {
                                "name": "website",
                                "type": "url",
                                "description": "External product website/landing page URL",
                            },
                            {
                                "name": "votesCount",
                                "type": "integer",
                                "description": "Total lifetime upvotes (snapshot at crawl time)",
                            },
                            {
                                "name": "commentsCount",
                                "type": "integer",
                                "description": "Total comment count (snapshot at crawl time)",
                            },
                            {
                                "name": "reviewsCount",
                                "type": "integer",
                                "description": "Total review submissions",
                            },
                            {
                                "name": "reviewsRating",
                                "type": "number",
                                "description": "Average user rating (0.0-5.0 scale, nullable)",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Post creation timestamp (ISO 8601 UTC)",
                            },
                            {
                                "name": "featuredAt",
                                "type": "datetime",
                                "description": "Featured on homepage timestamp (ISO 8601 UTC, nullable)",
                            },
                        ]
                    },
                },
                {
                    "path": "topicrow.csv",
                    "description": "Product categories, tags, and topic hierarchies used for classification and discovery. Topics enable categorical analysis and trending topic identification. Each topic tracks follower engagement and associated post counts for popularity metrics.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique topic identifier (UUID or numeric string, primary key)",
                            },
                            {
                                "name": "name",
                                "type": "string",
                                "description": "Topic display name (e.g., 'AI', 'Productivity', 'Developer Tools')",
                            },
                            {
                                "name": "slug",
                                "type": "string",
                                "description": "URL-safe topic slug (lowercase, hyphenated)",
                            },
                            {
                                "name": "followersCount",
                                "type": "integer",
                                "description": "Number of users following this topic (snapshot at crawl time)",
                            },
                            {
                                "name": "postsCount",
                                "type": "integer",
                                "description": "Total products tagged with this topic (snapshot at crawl time)",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Topic creation timestamp (ISO 8601 UTC)",
                            },
                        ]
                    },
                },
                {
                    "path": "collectionrow.csv",
                    "description": "User-curated collections grouping related products by theme, category, or curation criteria. Collections enable thematic analysis, trend identification, and curated product discovery. Popular collections can influence product visibility and success.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique collection identifier (UUID or numeric string, primary key)",
                            },
                            {
                                "name": "userId",
                                "type": "id",
                                "description": "Foreign key to userrow.id (collection curator)",
                            },
                            {
                                "name": "name",
                                "type": "string",
                                "description": "Collection title (e.g., 'Best AI Tools 2024')",
                            },
                            {
                                "name": "tagline",
                                "type": "string",
                                "description": "Short collection description/subtitle (nullable)",
                            },
                            {
                                "name": "followersCount",
                                "type": "integer",
                                "description": "Number of followers tracking this collection",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Collection creation timestamp (ISO 8601 UTC)",
                            },
                            {
                                "name": "featuredAt",
                                "type": "datetime",
                                "description": "Featured on homepage timestamp (ISO 8601 UTC, nullable)",
                            },
                        ]
                    },
                },
                {
                    "path": "commentrow.csv",
                    "description": "User comments, discussions, questions, and feedback on product posts. Contains threaded conversations with voting support. Useful for sentiment analysis, community engagement metrics, and qualitative product feedback analysis.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique comment identifier (UUID or numeric string, primary key)",
                            },
                            {
                                "name": "postId",
                                "type": "id",
                                "description": "Foreign key to postrow.id (parent post)",
                            },
                            {
                                "name": "userId",
                                "type": "id",
                                "description": "Foreign key to userrow.id (comment author)",
                            },
                            {
                                "name": "body",
                                "type": "string",
                                "description": "Comment text content (markdown supported, may contain HTML)",
                            },
                            {
                                "name": "votesCount",
                                "type": "integer",
                                "description": "Comment upvotes (snapshot at crawl time)",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Comment creation timestamp (ISO 8601 UTC)",
                            },
                        ]
                    },
                },
                {
                    "path": "voterow.csv",
                    "description": "Individual upvote records for posts and comments. Enables temporal voting analysis, user engagement patterns, and product momentum tracking. Each row represents a single upvote action by a user.",
                    "schema": {
                        "fields": [
                            {
                                "name": "id",
                                "type": "id",
                                "description": "Unique vote identifier (UUID or numeric string, primary key)",
                            },
                            {
                                "name": "userId",
                                "type": "id",
                                "description": "Foreign key to userrow.id (voter)",
                            },
                            {
                                "name": "postId",
                                "type": "id",
                                "description": "Foreign key to postrow.id (voted post, nullable if voting on comment)",
                            },
                            {
                                "name": "commentId",
                                "type": "id",
                                "description": "Foreign key to commentrow.id (voted comment, nullable if voting on post)",
                            },
                            {
                                "name": "createdAt",
                                "type": "datetime",
                                "description": "Vote timestamp (ISO 8601 UTC, enables time-series vote analysis)",
                            },
                        ]
                    },
                },
                {
                    "path": "posttopiclink.csv",
                    "description": "Junction table implementing many-to-many relationship between posts and topics. Each row links a product to a category/tag, enabling multi-category classification and cross-topic product discovery.",
                    "schema": {
                        "fields": [
                            {
                                "name": "post_id",
                                "type": "id",
                                "description": "Foreign key to postrow.id",
                            },
                            {
                                "name": "topic_id",
                                "type": "id",
                                "description": "Foreign key to topicrow.id",
                            },
                        ]
                    },
                },
                {
                    "path": "makerpostlink.csv",
                    "description": "Junction table implementing many-to-many relationship between makers (product creators) and their products. Enables multi-maker product analysis, co-creation network analysis, and maker collaboration patterns. One product can have multiple makers.",
                    "schema": {
                        "fields": [
                            {
                                "name": "user_id",
                                "type": "id",
                                "description": "Foreign key to userrow.id (maker)",
                            },
                            {
                                "name": "post_id",
                                "type": "id",
                                "description": "Foreign key to postrow.id (product)",
                            },
                        ]
                    },
                },
                {
                    "path": "collectionpostlink.csv",
                    "description": "Junction table implementing many-to-many relationship between collections and products. Each row represents a product's inclusion in a curated collection. Enables collection analysis, curation patterns, and cross-collection product discovery.",
                    "schema": {
                        "fields": [
                            {
                                "name": "collection_id",
                                "type": "id",
                                "description": "Foreign key to collectionrow.id",
                            },
                            {
                                "name": "post_id",
                                "type": "id",
                                "description": "Foreign key to postrow.id",
                            },
                        ]
                    },
                },
                {
                    "path": "crawlstate.csv",
                    "description": "System metadata table tracking incremental sync state for each entity type. Records cursor positions and last successful sync timestamps to enable efficient delta updates. Critical for maintaining data freshness without full re-crawls.",
                    "schema": {
                        "fields": [
                            {
                                "name": "entity",
                                "type": "string",
                                "description": "Entity type being tracked (e.g., 'posts', 'topics', 'users', 'comments')",
                            },
                            {
                                "name": "last_timestamp",
                                "type": "datetime",
                                "description": "Last successful sync completion timestamp (ISO 8601 UTC)",
                            },
                            {
                                "name": "cursor",
                                "type": "string",
                                "description": "GraphQL pagination cursor for next sync (nullable)",
                            },
                            {
                                "name": "updated_at",
                                "type": "datetime",
                                "description": "State record last update timestamp (ISO 8601 UTC)",
                            },
                        ]
                    },
                },
            ],
        }

        metadata_path = data_dir / "dataset-metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✅ Created metadata file: {metadata_path}")

        try:
            # Check if dataset exists
            try:
                self.api.dataset_status(self.dataset_slug)
                # Dataset exists, create new version
                logger.info(f"📤 Updating Kaggle dataset: {self.dataset_slug}")
                self.api.dataset_create_version(
                    str(data_dir),
                    version_notes="Automated update from ProductHuntDB pipeline",
                    dir_mode="zip",
                )
                logger.info("✅ Kaggle dataset updated successfully")
            except Exception:
                # Dataset doesn't exist, create it
                logger.info(f"📤 Creating new Kaggle dataset: {self.dataset_slug}")

                self.api.dataset_create_new(str(data_dir), public=True, quiet=False, dir_mode="zip")
                logger.info("✅ Kaggle dataset created successfully")

        except Exception as e:
            logger.error(f"❌ Failed to publish Kaggle dataset: {e}")
            raise
