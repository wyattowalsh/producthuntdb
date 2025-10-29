"""Data pipeline orchestration for ProductHuntDB.

This module orchestrates the ETL pipeline:
1. Extract: Fetch data from Product Hunt GraphQL API
2. Transform: Parse and validate with Pydantic models
3. Load: Store in SQLite database with SQLModel

Features:
- Incremental updates with safety margins
- Progress tracking and logging
- Error handling and retry logic
- Database transaction management
"""

from datetime import datetime
from typing import Any, Optional

from loguru import logger
from pydantic import ValidationError
from tqdm.asyncio import tqdm  # type: ignore[import-untyped]

from producthuntdb.config import PostsOrder, settings
from producthuntdb.io import AsyncGraphQLClient, DatabaseManager
from producthuntdb.models import Collection, Post, Topic
from producthuntdb.utils import format_iso, parse_datetime


class DataPipeline:
    """Orchestrates data extraction, transformation, and loading.

    The pipeline supports:
    - Full historical harvests
    - Incremental updates
    - Progress tracking
    - Error recovery

    Example:
        >>> pipeline = DataPipeline()
        >>> await pipeline.initialize()
        >>> await pipeline.sync_posts()
        >>> pipeline.close()
    """

    def __init__(
        self,
        client: Optional[AsyncGraphQLClient] = None,
        db: Optional[DatabaseManager] = None,
    ):
        """Initialize data pipeline.

        Args:
            client: GraphQL client (creates new if None)
            db: Database manager (creates new if None)
        """
        self.client = client or AsyncGraphQLClient()
        self.db     = db or DatabaseManager()

    async def initialize(self) -> None:
        """Initialize pipeline components."""
        self.db.initialize()
        logger.info("✅ Pipeline initialized")

    def close(self) -> None:
        """Close pipeline resources."""
        self.db.close()
        logger.info("✅ Pipeline closed")

    def _get_safety_cutoff(self, timestamp: Optional[str]) -> Optional[datetime]:
        """Calculate safety cutoff timestamp for incremental updates.

        Args:
            timestamp: Last crawl timestamp string

        Returns:
            Datetime with safety margin applied, or None
        """
        if not timestamp:
            return None

        dt = parse_datetime(timestamp)
        if not dt:
            return None

        return dt - settings.safety_timedelta

    async def verify_authentication(self) -> dict[str, Any]:
        """Verify API authentication and return viewer info.

        Returns:
            Viewer data with user information

        Raises:
            RuntimeError: If authentication fails
        """
        try:
            viewer_data = await self.client.fetch_viewer()

            if not viewer_data or "user" not in viewer_data:
                raise RuntimeError("Failed to authenticate with Product Hunt API")

            user_data = viewer_data["user"]
            logger.info(
                f"✅ Authenticated as: {user_data.get('username')} "
                f"({user_data.get('name')})"
            )

            return viewer_data

        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")
            raise

    async def sync_posts(
        self,
        full_refresh: bool = False,
        max_pages: Optional[int] = None,
    ) -> dict[str, int]:
        """Synchronize posts from Product Hunt API.

        Args:
            full_refresh: If True, fetch all posts; if False, incremental update
            max_pages: Maximum pages to fetch (None for unlimited)

        Returns:
            Statistics dictionary with counts

        Example:
            >>> stats = await pipeline.sync_posts(full_refresh=False)
            >>> print(f"Synced {stats['posts']} posts")
        """
        logger.info("🚀 Starting posts synchronization")

        stats = {
            "posts":    0,
            "users":    0,
            "topics":   0,
            "pages":    0,
            "skipped":  0,
        }

        # Determine starting point for incremental updates
        posted_after = None
        if not full_refresh:
            last_timestamp = self.db.get_crawl_state("posts")
            if last_timestamp:
                posted_after = self._get_safety_cutoff(last_timestamp)
                logger.info(
                    f"📅 Incremental update from {format_iso(posted_after)} "
                    f"(safety margin: {settings.safety_minutes} minutes)"
                )

        # Pagination loop
        cursor          = None
        has_next_page   = True
        latest_timestamp = None

        with tqdm(desc="Fetching posts", unit=" pages") as pbar:
            while has_next_page:
                # Check max pages limit
                if max_pages and stats["pages"] >= max_pages:
                    logger.info(f"⏹️ Reached max pages limit: {max_pages}")
                    break

                try:
                    # Fetch page
                    posts_response = await self.client.fetch_posts_page(
                        after_cursor=cursor,
                        posted_after_dt=posted_after,
                        first=settings.page_size,
                        order=PostsOrder.NEWEST,
                    )

                    nodes    = posts_response.get("nodes", [])
                    page_info = posts_response.get("pageInfo", {})

                    if not nodes:
                        logger.info("✅ No more posts to fetch")
                        break

                    # Process each post
                    for post_data in nodes:
                        try:
                            # Parse and validate with Pydantic
                            post = Post(**post_data)

                            # Track latest timestamp
                            if post.createdAt:
                                if (
                                    not latest_timestamp
                                    or post.createdAt > latest_timestamp
                                ):
                                    latest_timestamp = post.createdAt

                            # Store user (submitter)
                            if post.user:
                                self.db.upsert_user(post.user.model_dump())
                                stats["users"] += 1

                            # Store makers
                            for maker in post.makers:
                                self.db.upsert_user(maker.model_dump())
                                stats["users"] += 1

                            # Store topics
                            topic_ids = []
                            if post.topics:
                                for topic_dict in post.topics:
                                    # topic_dict is already a Topic object from Pydantic parsing
                                    if isinstance(topic_dict, Topic):
                                        topic = topic_dict
                                    else:
                                        topic = Topic(**topic_dict)  # type: ignore[arg-type]
                                    self.db.upsert_topic(topic.model_dump())
                                    topic_ids.append(topic.id)
                                    stats["topics"] += 1

                            # Store post
                            self.db.upsert_post(post.model_dump())

                            # Create relationships
                            if topic_ids:
                                self.db.link_post_topics(post.id, topic_ids)

                            maker_ids = [m.id for m in post.makers]
                            if maker_ids:
                                self.db.link_post_makers(post.id, maker_ids)

                            stats["posts"] += 1

                        except ValidationError as e:
                            logger.warning(
                                f"⚠️ Validation error for post "
                                f"{post_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                        except Exception as e:
                            logger.error(
                                f"❌ Error processing post "
                                f"{post_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                    # Update pagination
                    cursor        = page_info.get("endCursor")
                    has_next_page = page_info.get("hasNextPage", False)
                    stats["pages"] += 1

                    pbar.update(1)
                    pbar.set_postfix(
                        posts=stats["posts"],
                        users=stats["users"],
                        topics=stats["topics"],
                    )

                except Exception as e:
                    logger.error(f"❌ Error fetching posts page: {e}")
                    break

        # Update crawl state
        if latest_timestamp:
            timestamp_str = format_iso(latest_timestamp)
            if timestamp_str:
                self.db.update_crawl_state("posts", timestamp_str)
                logger.info(f"📝 Updated crawl state: {timestamp_str}")

        logger.info(f"✅ Posts sync complete: {stats}")
        return stats

    async def sync_topics(
        self,
        max_pages: Optional[int] = None,
    ) -> dict[str, int]:
        """Synchronize topics from Product Hunt API.

        Args:
            max_pages: Maximum pages to fetch (None for unlimited)

        Returns:
            Statistics dictionary

        Example:
            >>> stats = await pipeline.sync_topics()
            >>> print(f"Synced {stats['topics']} topics")
        """
        logger.info("🚀 Starting topics synchronization")

        stats = {
            "topics": 0,
            "pages":  0,
            "skipped": 0,
        }

        cursor        = None
        has_next_page = True

        with tqdm(desc="Fetching topics", unit=" pages") as pbar:
            while has_next_page:
                if max_pages and stats["pages"] >= max_pages:
                    logger.info(f"⏹️ Reached max pages limit: {max_pages}")
                    break

                try:
                    topics_response = await self.client.fetch_topics_page(
                        after_cursor=cursor,
                        first=settings.page_size,
                    )

                    nodes     = topics_response.get("nodes", [])
                    page_info = topics_response.get("pageInfo", {})

                    if not nodes:
                        logger.info("✅ No more topics to fetch")
                        break

                    for topic_data in nodes:
                        try:
                            topic = Topic(**topic_data)
                            self.db.upsert_topic(topic.model_dump())
                            stats["topics"] += 1

                        except ValidationError as e:
                            logger.warning(
                                f"⚠️ Validation error for topic "
                                f"{topic_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                        except Exception as e:
                            logger.error(
                                f"❌ Error processing topic "
                                f"{topic_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                    cursor        = page_info.get("endCursor")
                    has_next_page = page_info.get("hasNextPage", False)
                    stats["pages"] += 1

                    pbar.update(1)
                    pbar.set_postfix(topics=stats["topics"])

                except Exception as e:
                    logger.error(f"❌ Error fetching topics page: {e}")
                    break

        logger.info(f"✅ Topics sync complete: {stats}")
        return stats

    async def sync_collections(
        self,
        max_pages: Optional[int] = None,
    ) -> dict[str, int]:
        """Synchronize collections from Product Hunt API.

        Args:
            max_pages: Maximum pages to fetch (None for unlimited)

        Returns:
            Statistics dictionary

        Example:
            >>> stats = await pipeline.sync_collections()
            >>> print(f"Synced {stats['collections']} collections")
        """
        logger.info("🚀 Starting collections synchronization")

        stats = {
            "collections": 0,
            "users":       0,
            "pages":       0,
            "skipped":     0,
        }

        cursor        = None
        has_next_page = True

        with tqdm(desc="Fetching collections", unit=" pages") as pbar:
            while has_next_page:
                if max_pages and stats["pages"] >= max_pages:
                    logger.info(f"⏹️ Reached max pages limit: {max_pages}")
                    break

                try:
                    collections_response = await self.client.fetch_collections_page(
                        after_cursor=cursor,
                        first=settings.page_size,
                    )

                    nodes     = collections_response.get("nodes", [])
                    page_info = collections_response.get("pageInfo", {})

                    if not nodes:
                        logger.info("✅ No more collections to fetch")
                        break

                    for collection_data in nodes:
                        try:
                            collection = Collection(**collection_data)

                            # Store curator user
                            if collection.user:
                                self.db.upsert_user(collection.user.model_dump())
                                stats["users"] += 1

                            # Store collection
                            from producthuntdb.models import CollectionRow

                            if self.db.session is None:
                                raise RuntimeError("Database not initialized")

                            collection_row = CollectionRow.from_pydantic(collection)
                            existing_collection = self.db.session.get(
                                CollectionRow, collection.id
                            )

                            if existing_collection:
                                # Update existing
                                for key, value in collection_row.model_dump().items():
                                    setattr(existing_collection, key, value)
                            else:
                                self.db.session.add(collection_row)

                            self.db.session.commit()
                            stats["collections"] += 1

                        except ValidationError as e:
                            logger.warning(
                                f"⚠️ Validation error for collection "
                                f"{collection_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                        except Exception as e:
                            logger.error(
                                f"❌ Error processing collection "
                                f"{collection_data.get('id')}: {e}"
                            )
                            stats["skipped"] += 1
                            continue

                    cursor        = page_info.get("endCursor")
                    has_next_page = page_info.get("hasNextPage", False)
                    stats["pages"] += 1

                    pbar.update(1)
                    pbar.set_postfix(collections=stats["collections"])

                except Exception as e:
                    logger.error(f"❌ Error fetching collections page: {e}")
                    break

        logger.info(f"✅ Collections sync complete: {stats}")
        return stats

    async def sync_all(
        self,
        full_refresh: bool = False,
        max_pages: Optional[int] = None,
    ) -> dict[str, Any]:
        """Synchronize all entities from Product Hunt API.

        Args:
            full_refresh: If True, fetch all data; if False, incremental
            max_pages: Maximum pages per entity (None for unlimited)

        Returns:
            Combined statistics dictionary

        Example:
            >>> stats = await pipeline.sync_all()
            >>> print(f"Total posts: {stats['posts']['posts']}")
        """
        logger.info("🚀 Starting full synchronization")

        # Verify authentication first
        await self.verify_authentication()

        # Sync all entities
        posts_stats       = await self.sync_posts(full_refresh, max_pages)
        topics_stats      = await self.sync_topics(max_pages)
        collections_stats = await self.sync_collections(max_pages)

        combined_stats = {
            "posts":       posts_stats,
            "topics":      topics_stats,
            "collections": collections_stats,
            "total_entities": (
                posts_stats["posts"]
                + topics_stats["topics"]
                + collections_stats["collections"]
            ),
        }

        logger.info(f"✅ Full synchronization complete: {combined_stats}")
        return combined_stats

    def get_statistics(self) -> dict[str, int]:
        """Get current database statistics.

        Returns:
            Dictionary with entity counts

        Example:
            >>> stats = pipeline.get_statistics()
            >>> print(f"Total posts: {stats['posts']}")
        """
        from sqlmodel import func, select

        from producthuntdb.models import (
            CollectionRow,
            CommentRow,
            PostRow,
            TopicRow,
            UserRow,
            VoteRow,
        )

        if self.db.session is None:
            raise RuntimeError("Database not initialized")

        stats = {
            "posts":       self.db.session.exec(
                select(func.count(PostRow.id))  # type: ignore[arg-type]
            ).one(),
            "users":       self.db.session.exec(
                select(func.count(UserRow.id))  # type: ignore[arg-type]
            ).one(),
            "topics":      self.db.session.exec(
                select(func.count(TopicRow.id))  # type: ignore[arg-type]
            ).one(),
            "collections": self.db.session.exec(
                select(func.count(CollectionRow.id))  # type: ignore[arg-type]
            ).one(),
            "comments":    self.db.session.exec(
                select(func.count(CommentRow.id))  # type: ignore[arg-type]
            ).one(),
            "votes":       self.db.session.exec(
                select(func.count(VoteRow.id))  # type: ignore[arg-type]
            ).one(),
        }

        return stats

