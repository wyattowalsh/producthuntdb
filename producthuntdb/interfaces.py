"""Protocol interfaces for dependency injection.

This module defines Protocol interfaces that enable loose coupling and
dependency injection throughout the codebase. Using @runtime_checkable
Protocol allows for structural subtyping without requiring inheritance.

Key benefits:
- Easy testing with mock implementations
- Supports alternative implementations (e.g., PostgreSQL, different APIs)
- Clear contracts for all major components
- No inheritance required - duck typing with type safety

Example:
    >>> from producthuntdb.interfaces import IGraphQLClient
    >>> class MockClient:
    ...     async def fetch_posts_page(self, after, posted_after, first, order):
    ...         return {'nodes': [], 'pageInfo': {'hasNextPage': False}}
    >>> mock = MockClient()
    >>> isinstance(mock, IGraphQLClient)  # True, structural typing!

References:
    - ArjanCodes: Python Dependency Injection Best Practices
      https://arjancodes.com/blog/python-dependency-injection-best-practices/
    - Python typing.Protocol documentation
      https://docs.python.org/3/library/typing.html#typing.Protocol
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

from producthuntdb.config import PostsOrder
from producthuntdb.models import (
    CrawlState,
    MakerPostLink,
    MediaRow,
    PostRow,
    PostTopicLink,
    TopicRow,
    UserRow,
)


@runtime_checkable
class IGraphQLClient(Protocol):
    """GraphQL API client interface.

    Defines the contract for interacting with the Product Hunt GraphQL API
    (or any compatible GraphQL endpoint). Implementations should handle:
    - Authentication
    - Rate limiting
    - Retry logic
    - Connection pooling

    The @runtime_checkable decorator enables isinstance() checks based on
    method signatures rather than inheritance.
    """

    async def fetch_posts_page(
        self,
        after_cursor: str | None,
        posted_after_dt: datetime | None,
        first: int,
        order: PostsOrder,
    ) -> dict[str, Any]:
        """Fetch a page of posts from the API.

        Args:
            after_cursor: Pagination cursor (None for first page)
            posted_after_dt: Filter posts created after this datetime
            first: Number of posts to fetch
            order: Sorting order (e.g., NEWEST, MOST_VOTED)

        Returns:
            Dictionary containing 'nodes' (list of posts) and 'pageInfo'

        Raises:
            TransientGraphQLError: For retryable failures (network, rate limit)
            RuntimeError: For permanent failures (auth, validation)
        """
        ...

    async def fetch_topics_page(
        self,
        after_cursor: str | None,
        first: int,
    ) -> dict[str, Any]:
        """Fetch a page of topics from the API.

        Args:
            after_cursor: Pagination cursor (None for first page)
            first: Number of topics to fetch

        Returns:
            Dictionary containing 'nodes' (list of topics) and 'pageInfo'
        """
        ...

    async def fetch_viewer(self) -> dict[str, Any]:
        """Fetch authenticated viewer (current user) information.

        Useful for verifying authentication and checking API access.

        Returns:
            Dictionary with viewer details (id, username, etc.)

        Raises:
            RuntimeError: If authentication fails
        """
        ...

    async def close(self) -> None:
        """Close all connections and cleanup resources.

        Should be called when the client is no longer needed,
        typically in a finally block or context manager __aexit__.
        """
        ...

    @property
    def rate_limit_remaining(self) -> int | None:
        """Get remaining API calls in current rate limit window.

        Returns None if rate limit information is not available.
        """
        ...

    @property
    def rate_limit_reset(self) -> str | None:
        """Get timestamp when rate limit resets.

        Returns None if rate limit information is not available.
        """
        ...


@runtime_checkable
class IDatabaseManager(Protocol):
    """Database operations interface.

    Defines the contract for database interactions. Implementations should
    support CRUD operations for all entity types and manage connections,
    transactions, and migrations.

    This interface is database-agnostic - implementations could use SQLite,
    PostgreSQL, MySQL, or any other database system.
    """

    database_path: Path
    """Path to database file (for file-based databases like SQLite)."""

    def initialize(self) -> None:
        """Initialize database connection and create tables if needed.

        Should be called once at startup to set up the database schema.
        """
        ...

    def close(self) -> None:
        """Close all database connections and cleanup resources."""
        ...

    # -------------------------------------------------------------------------
    # Post operations
    # -------------------------------------------------------------------------

    def upsert_post(self, post_data: dict[str, Any]) -> PostRow:
        """Insert or update a post.

        Args:
            post_data: Dictionary with post fields (id, name, tagline, etc.)

        Returns:
            The inserted or updated PostRow object
        """
        ...

    def upsert_posts_batch(self, posts_data: list[dict[str, Any]]) -> list[PostRow]:
        """Bulk insert or update posts.

        Much faster than individual upserts for large datasets.

        Args:
            posts_data: List of post dictionaries

        Returns:
            List of inserted/updated PostRow objects
        """
        ...

    def get_post(self, post_id: str) -> PostRow | None:
        """Get a post by ID.

        Args:
            post_id: Post identifier

        Returns:
            PostRow if found, None otherwise
        """
        ...

    # -------------------------------------------------------------------------
    # User operations
    # -------------------------------------------------------------------------

    def upsert_user(self, user_data: dict[str, Any]) -> UserRow:
        """Insert or update a user.

        Args:
            user_data: Dictionary with user fields (id, username, name, etc.)

        Returns:
            The inserted or updated UserRow object
        """
        ...

    def get_user(self, user_id: str) -> UserRow | None:
        """Get a user by ID."""
        ...

    # -------------------------------------------------------------------------
    # Topic operations
    # -------------------------------------------------------------------------

    def upsert_topic(self, topic_data: dict[str, Any]) -> TopicRow:
        """Insert or update a topic."""
        ...

    def get_topic(self, topic_id: str) -> TopicRow | None:
        """Get a topic by ID."""
        ...

    # -------------------------------------------------------------------------
    # Media operations
    # -------------------------------------------------------------------------

    def upsert_media(self, media_data: dict[str, Any]) -> MediaRow:
        """Insert or update a media item."""
        ...

    def delete_media_for_post(self, post_id: str) -> int:
        """Delete all media items for a post.

        Args:
            post_id: Post identifier

        Returns:
            Number of media items deleted
        """
        ...

    # -------------------------------------------------------------------------
    # Link table operations
    # -------------------------------------------------------------------------

    def upsert_post_topic_link(self, post_id: str, topic_id: str) -> PostTopicLink:
        """Create or update a post-topic relationship."""
        ...

    def upsert_maker_post_link(self, user_id: str, post_id: str) -> MakerPostLink:
        """Create or update a maker-post relationship."""
        ...

    def delete_post_topic_links(self, post_id: str) -> int:
        """Delete all topic links for a post.

        Returns:
            Number of links deleted
        """
        ...

    def delete_maker_post_links(self, post_id: str) -> int:
        """Delete all maker links for a post.

        Returns:
            Number of links deleted
        """
        ...

    # -------------------------------------------------------------------------
    # Crawl state operations
    # -------------------------------------------------------------------------

    def get_crawl_state(self, entity: str) -> CrawlState | None:
        """Get crawl state for an entity type.

        Args:
            entity: Entity type ('posts', 'users', 'topics', etc.)

        Returns:
            CrawlState if exists, None otherwise
        """
        ...

    def upsert_crawl_state(
        self,
        entity: str,
        last_cursor: str | None,
        last_synced_at: str,
    ) -> CrawlState:
        """Update crawl state for an entity.

        Args:
            entity: Entity type
            last_cursor: Last pagination cursor processed
            last_synced_at: ISO 8601 timestamp of sync

        Returns:
            Updated CrawlState object
        """
        ...

    # -------------------------------------------------------------------------
    # Statistics operations
    # -------------------------------------------------------------------------

    def get_entity_counts(self) -> dict[str, int]:
        """Get row counts for all tables.

        Returns:
            Dictionary mapping table names to row counts
        """
        ...


@runtime_checkable
class ILogger(Protocol):
    """Logging interface.

    Defines the contract for logging operations. Implementations could use
    the standard library logging, Loguru, structlog, or any other logging
    framework.

    This interface supports structured logging with arbitrary key-value pairs.
    """

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional context.

        Args:
            message: Log message (may contain {} placeholders)
            **kwargs: Key-value pairs for structured logging
        """
        ...

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional context."""
        ...

    def success(self, message: str, **kwargs: Any) -> None:
        """Log success message with optional context.

        Not all logging frameworks support this level. Implementations
        should fall back to info() if success is not available.
        """
        ...

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional context."""
        ...

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with optional context."""
        ...

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log error with full exception traceback.

        Should be called from within an except block to capture
        the current exception information.
        """
        ...

    def bind(self, **kwargs: Any) -> "ILogger":
        """Create a logger with bound context.

        Returns a new logger that automatically includes the given
        key-value pairs in all log messages.

        Args:
            **kwargs: Context to bind (e.g., request_id=123)

        Returns:
            New logger instance with bound context

        Example:
            >>> base_logger = get_logger()
            >>> request_logger = base_logger.bind(request_id="abc-123")
            >>> request_logger.info("Processing request")  # Includes request_id
        """
        ...


@runtime_checkable
class IKaggleManager(Protocol):
    """Kaggle dataset management interface.

    Defines the contract for publishing and managing datasets on Kaggle.
    Implementations should handle authentication, metadata management,
    and dataset versioning.
    """

    def publish_dataset(self, dataset_dir: Path) -> None:
        """Publish or update a Kaggle dataset.

        Args:
            dataset_dir: Directory containing CSV files and metadata

        Raises:
            RuntimeError: If Kaggle credentials are not configured
            ValueError: If dataset metadata is invalid
        """
        ...

    def has_credentials(self) -> bool:
        """Check if Kaggle credentials are configured.

        Returns:
            True if KAGGLE_USERNAME and KAGGLE_KEY are set
        """
        ...


# =============================================================================
# Type Aliases
# =============================================================================

# These type aliases improve readability when used in function signatures
GraphQLResponse = dict[str, Any]
"""Type alias for GraphQL API responses."""

EntityData = dict[str, Any]
"""Type alias for entity data dictionaries (before model conversion)."""

PaginationCursor = str | None
"""Type alias for pagination cursors (None for first page)."""


# =============================================================================
# Notes on Protocol Usage
# =============================================================================
"""
Protocol-based interfaces enable:

1. **Dependency Injection**: Pass different implementations at runtime
   >>> def process_posts(client: IGraphQLClient, db: IDatabaseManager):
   ...     posts = await client.fetch_posts_page(...)
   ...     db.upsert_posts_batch(posts)

2. **Testing with Mocks**: No need for complex mocking frameworks
   >>> class MockClient:
   ...     async def fetch_posts_page(self, ...):
   ...         return test_data
   >>> 
   >>> process_posts(MockClient(), MockDatabase())  # Just works!

3. **Alternative Implementations**: Easy to swap backends
   >>> # Use PostgreSQL instead of SQLite
   >>> db = PostgreSQLManager()  # Just implements IDatabaseManager
   >>> pipeline = DataPipeline(db=db)

4. **Structural Typing**: No inheritance required
   >>> # As long as it has the right methods, it's valid
   >>> assert isinstance(my_client, IGraphQLClient)  # True!

See Also:
    - docs/source/refactoring-enhancements.md - Complete implementation guide
    - Python PEP 544: Protocols - https://peps.python.org/pep-0544/
"""
