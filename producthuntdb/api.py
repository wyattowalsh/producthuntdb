"""GraphQL API client for Product Hunt.

This module provides an async HTTP/2 client with:
- Connection pooling and HTTP/2 multiplexing
- Retry logic with exponential backoff
- Rate limiting awareness and adaptive delays
- Structured error handling
- OpenTelemetry distributed tracing integration

Reference:
    - docs/source/refactoring-enhancements.md lines 243-308
    - Extracted from io.py lines 241-513

Example:
    >>> from producthuntdb.api import AsyncGraphQLClient
    >>> from producthuntdb.config import PostsOrder
    >>> 
    >>> async with AsyncGraphQLClient() as client:
    ...     posts = await client.fetch_posts_page(
    ...         after_cursor=None,
    ...         first=50,
    ...         order=PostsOrder.NEWEST
    ...     )
    ...     print(f"Fetched {len(posts['nodes'])} posts")
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import httpx
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

from producthuntdb.config import PostsOrder, settings
from producthuntdb.logging import logger
from producthuntdb.utils import format_iso

# OpenTelemetry imports (optional - graceful degradation if not installed)
try:
    from producthuntdb.telemetry import (
        add_span_attributes,
        get_tracer,
        record_exception_in_span,
        set_span_error,
    )
    
    TELEMETRY_AVAILABLE = True
    tracer = get_tracer(__name__)
except ImportError:
    TELEMETRY_AVAILABLE = False
    tracer = None

# Prometheus metrics (optional - graceful degradation if not installed)
try:
    from producthuntdb.metrics import (
        errors_total,
        graphql_queries_total,
        graphql_request_duration_seconds,
    )
    
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

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
    """Retryable network/HTTP layer failures.
    
    Raised for errors that should trigger retry logic:
    - Network timeouts
    - Connection errors
    - HTTP 429 (rate limit)
    - HTTP 5xx (server errors)
    """

    pass


# =============================================================================
# Async GraphQL Client
# =============================================================================


class AsyncGraphQLClient:
    """Async HTTP/2 client for Product Hunt GraphQL API.

    Features:
    - HTTP/2 multiplexing for concurrent requests
    - Connection pooling to reuse TCP connections
    - Keepalive connections for reduced latency
    - Retry logic with exponential backoff
    - Rate limiting awareness with adaptive delays
    - Structured error handling

    Args:
        token: Product Hunt API authentication token
        max_concurrency: Maximum concurrent requests
        pool_limits: Custom httpx connection pool limits
        timeout: Custom httpx timeout configuration

    Example:
        >>> async with AsyncGraphQLClient() as client:
        ...     viewer = await client.fetch_viewer()
        ...     print(f"Authenticated as {viewer['user']['username']}")
    """

    def __init__(
        self,
        token: str | None = None,
        max_concurrency: int | None = None,
        pool_limits: httpx.Limits | None = None,
        timeout: httpx.Timeout | None = None,
    ) -> None:
        """Initialize async GraphQL client.

        Args:
            token: API token (defaults to settings.producthunt_token)
            max_concurrency: Max concurrent requests (defaults to settings.max_concurrency)
            pool_limits: Connection pool configuration (defaults to production settings)
            timeout: Timeout configuration (defaults to 30s overall)
        """
        self._token = token or settings.producthunt_token
        self._max_concurrency = max_concurrency or settings.max_concurrency
        self._sem = asyncio.Semaphore(self._max_concurrency)

        # Rate limit tracking
        self._rate_limit_limit: str | None = None
        self._rate_limit_remaining: str | None = None
        self._rate_limit_reset: str | None = None

        # Production-grade connection pooling
        self._limits = pool_limits or httpx.Limits(
            max_connections=100,  # Max total connections
            max_keepalive_connections=20,  # Keep 20 alive for reuse
            keepalive_expiry=30.0,  # Close idle connections after 30s
        )

        # Timeout configuration
        self._timeout = timeout or httpx.Timeout(
            timeout=30.0,  # Overall timeout
            connect=10.0,  # TCP connection timeout
            read=20.0,  # Reading response timeout
            write=10.0,  # Writing request timeout
            pool=5.0,  # Getting connection from pool timeout
        )

        # Initialize HTTP client (created on first use)
        self._client: httpx.AsyncClient | None = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        """Lazy initialization of HTTP client.
        
        Returns:
            Configured httpx.AsyncClient instance
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                limits=self._limits,
                timeout=self._timeout,
                http2=True,  # Enable HTTP/2 multiplexing
                follow_redirects=True,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def __aenter__(self) -> "AsyncGraphQLClient":
        """Context manager entry for resource management."""
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - ensure cleanup."""
        await self.close()

    async def close(self) -> None:
        """Close all connections and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    @property
    def rate_limit_remaining(self) -> int | None:
        """Get remaining rate limit from last API call.
        
        Returns:
            Number of requests remaining, or None if unknown
        """
        if self._rate_limit_remaining:
            try:
                return int(self._rate_limit_remaining)
            except (ValueError, TypeError):
                return None
        return None

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
        client = await self._ensure_client()

        try:
            resp = await client.post(
                settings.graphql_endpoint,
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
                f" (resets at {self._rate_limit_reset})"
                if resp.status_code == 429
                else ""
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

    async def fetch_posts_page(
        self,
        after_cursor: str | None = None,
        posted_after_dt: datetime | str | None = None,
        first: int | None = None,
        order: PostsOrder | None = None,
    ) -> dict[str, Any]:
        """Fetch a page of posts with OpenTelemetry tracing and Prometheus metrics.

        Args:
            after_cursor: Pagination cursor from previous page
            posted_after_dt: Filter posts created after this datetime (datetime or ISO string)
            first: Page size (defaults to settings.page_size)
            order: Post ordering (defaults to NEWEST)

        Returns:
            Posts object with nodes and pageInfo

        Example:
            >>> posts = await client.fetch_posts_page(first=10, order=PostsOrder.RANKING)
            >>> for post in posts['nodes']:
            ...     print(f"{post['name']}: {post['votesCount']} votes")
        """
        first = first or settings.page_size
        order = order or PostsOrder.NEWEST

        # Start tracing span if telemetry is available
        span_context = None
        if TELEMETRY_AVAILABLE and tracer:
            span_context = tracer.start_as_current_span("graphql.fetch_posts_page")
            span = span_context.__enter__()
            add_span_attributes(span, {
                "query_type": "posts",
                "page_size": first,
                "order": order.value,
                "has_cursor": after_cursor is not None,
                "has_date_filter": posted_after_dt is not None,
            })

        # Start timing for metrics
        start_time = time.time() if METRICS_AVAILABLE else None

        try:
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
            result = data.get("posts", {})

            # Record success metrics
            if METRICS_AVAILABLE:
                graphql_queries_total.labels(query_type="posts", status="success").inc()
                if start_time:
                    duration = time.time() - start_time
                    graphql_request_duration_seconds.labels(
                        query_type="posts", status="success"
                    ).observe(duration)

            # Add result attributes to span
            if TELEMETRY_AVAILABLE and span_context:
                nodes_count = len(result.get("nodes", []))
                add_span_attributes(span, {
                    "result.nodes_count": nodes_count,
                    "result.has_next_page": result.get("pageInfo", {}).get("hasNextPage", False),
                })

            return result

        except Exception as exc:
            # Record error metrics
            if METRICS_AVAILABLE:
                graphql_queries_total.labels(query_type="posts", status="error").inc()
                errors_total.labels(error_type=type(exc).__name__, component="api").inc()
                if start_time:
                    duration = time.time() - start_time
                    graphql_request_duration_seconds.labels(
                        query_type="posts", status="error"
                    ).observe(duration)

            # Record exception in span
            if TELEMETRY_AVAILABLE and span_context:
                record_exception_in_span(span, exc)

            raise

        finally:
            # Close span
            if TELEMETRY_AVAILABLE and span_context:
                span_context.__exit__(None, None, None)

    async def fetch_viewer(self) -> dict[str, Any]:
        """Fetch authenticated viewer information.

        Returns:
            Viewer object with user data

        Example:
            >>> viewer = await client.fetch_viewer()
            >>> print(f"Logged in as: {viewer['user']['username']}")
        """
        data = await self._post_with_retry(QUERY_VIEWER, {})
        return data.get("viewer", {})

    async def fetch_topics_page(
        self,
        after_cursor: str | None = None,
        first: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a page of topics.

        Args:
            after_cursor: Pagination cursor from previous page
            first: Page size (defaults to settings.page_size)

        Returns:
            Topics object with nodes and pageInfo

        Example:
            >>> topics = await client.fetch_topics_page(first=20)
            >>> for topic in topics['nodes']:
            ...     print(f"{topic['name']}: {topic['followersCount']} followers")
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
        after_cursor: str | None = None,
        first: int | None = None,
    ) -> dict[str, Any]:
        """Fetch a page of collections.

        Args:
            after_cursor: Pagination cursor from previous page
            first: Page size (defaults to settings.page_size)

        Returns:
            Collections object with nodes and pageInfo

        Example:
            >>> collections = await client.fetch_collections_page(first=10)
            >>> for col in collections['nodes']:
            ...     print(f"{col['name']}: {col['followersCount']} followers")
        """
        first = first or settings.page_size

        variables = {
            "first": first,
            "after": after_cursor,
        }

        data = await self._post_with_retry(QUERY_COLLECTIONS_PAGE, variables)
        return data.get("collections", {})


# =============================================================================
# Export Public API
# =============================================================================

__all__ = [
    "AsyncGraphQLClient",
    "TransientGraphQLError",
    "QUERY_POSTS_PAGE",
    "QUERY_VIEWER",
    "QUERY_TOPICS_PAGE",
    "QUERY_COLLECTIONS_PAGE",
]
