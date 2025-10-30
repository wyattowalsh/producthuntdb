"""Generic repository pattern for type-safe database operations.

This module provides a Generic Repository[T] implementation for SQLModel entities,
enabling type-safe CRUD operations with IDE autocomplete and type checking.

Reference:
    - docs/source/refactoring-enhancements.md lines 752-820
    - Repository Pattern: https://martinfowler.com/eaaCatalog/repository.html

Example:
    >>> from producthuntdb.repository import Repository
    >>> from producthuntdb.models import PostRow, UserRow
    >>> from sqlmodel import Session
    >>> 
    >>> # Create type-safe repositories
    >>> post_repo = Repository[PostRow](session, PostRow)
    >>> user_repo = Repository[UserRow](session, UserRow)
    >>> 
    >>> # Type checker knows these return PostRow | None
    >>> post = post_repo.get("post-123")
    >>> if post:
    ...     print(f"{post.name}: {post.votesCount} votes")
    >>> 
    >>> # Type checker knows this returns Sequence[PostRow]
    >>> posts = post_repo.get_all(limit=50)
    >>> for post in posts:
    ...     print(post.name)  # IDE autocomplete works!
"""

from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlmodel import Session, SQLModel, select

# =============================================================================
# Type Variables
# =============================================================================

T = TypeVar("T", bound=SQLModel)


# =============================================================================
# Generic Repository
# =============================================================================


class Repository(Generic[T]):
    """Generic repository implementation for SQLModel entities.

    Provides type-safe CRUD operations for any SQLModel entity with:
    - Full type inference (IDE autocomplete, type checking)
    - Consistent interface across all entities
    - Testable with mock repositories
    - Query optimization opportunities

    Type Parameter:
        T: SQLModel entity type (PostRow, UserRow, TopicRow, etc.)

    Args:
        session: SQLModel Session instance
        model: SQLModel class (e.g., PostRow, UserRow)

    Example:
        >>> # Create repository for PostRow
        >>> post_repo = Repository[PostRow](session, PostRow)
        >>> 
        >>> # Get single post (returns PostRow | None)
        >>> post = post_repo.get("123")
        >>> assert isinstance(post, PostRow) or post is None
        >>> 
        >>> # Get all posts (returns Sequence[PostRow])
        >>> posts = post_repo.get_all(limit=10)
        >>> for post in posts:
        ...     print(f"{post.name}: {post.votesCount}")
        >>> 
        >>> # Create new post
        >>> new_post = PostRow(id="456", name="New Product", ...)
        >>> saved_post = post_repo.create(new_post)
        >>> 
        >>> # Update existing post
        >>> post.votesCount += 1
        >>> updated_post = post_repo.update(post)
        >>> 
        >>> # Delete post
        >>> deleted = post_repo.delete("456")
        >>> assert deleted is True
        >>> 
        >>> # Find by attributes
        >>> featured = post_repo.find_by(featuredAt__ne=None)
        >>> popular = post_repo.find_by(votesCount__gt=100)
    """

    def __init__(self, session: Session, model: type[T]):
        """Initialize repository.

        Args:
            session: SQLModel Session for database operations
            model: SQLModel class (e.g., PostRow, UserRow, TopicRow)
        """
        self.session = session
        self.model = model

    def get(self, entity_id: str) -> T | None:
        """Get entity by ID.

        Args:
            entity_id: Primary key value

        Returns:
            Entity instance or None if not found

        Example:
            >>> post = post_repo.get("post-123")
            >>> if post:
            ...     print(f"Found: {post.name}")
            ... else:
            ...     print("Not found")
        """
        return self.session.get(self.model, entity_id)

    def get_all(self, limit: int = 100, offset: int = 0) -> Sequence[T]:
        """Get all entities with pagination.

        Args:
            limit: Maximum number of results (default 100)
            offset: Number of results to skip (default 0)

        Returns:
            Sequence of entity instances

        Example:
            >>> # Get first page
            >>> page1 = post_repo.get_all(limit=50, offset=0)
            >>> 
            >>> # Get second page
            >>> page2 = post_repo.get_all(limit=50, offset=50)
        """
        stmt = select(self.model).limit(limit).offset(offset)
        return self.session.exec(stmt).all()

    def create(self, entity: T) -> T:
        """Create new entity.

        Args:
            entity: Entity instance to create

        Returns:
            Created entity with refreshed state from database

        Example:
            >>> new_post = PostRow(
            ...     id="123",
            ...     name="My Product",
            ...     tagline="Amazing",
            ...     votesCount=0
            ... )
            >>> saved_post = post_repo.create(new_post)
            >>> print(f"Created: {saved_post.id}")
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def update(self, entity: T) -> T:
        """Update existing entity.

        Args:
            entity: Entity instance to update (must exist in database)

        Returns:
            Updated entity with refreshed state from database

        Example:
            >>> post = post_repo.get("123")
            >>> post.votesCount += 1
            >>> updated_post = post_repo.update(post)
            >>> print(f"New vote count: {updated_post.votesCount}")
        """
        self.session.add(entity)
        self.session.commit()
        self.session.refresh(entity)
        return entity

    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Primary key value

        Returns:
            True if deleted, False if not found

        Example:
            >>> deleted = post_repo.delete("123")
            >>> if deleted:
            ...     print("Successfully deleted")
            ... else:
            ...     print("Not found")
        """
        entity = self.get(entity_id)
        if entity:
            self.session.delete(entity)
            self.session.commit()
            return True
        return False

    def find_by(self, **filters: Any) -> Sequence[T]:
        """Find entities matching filters.

        Supports simple equality filters on entity attributes.

        Args:
            **filters: Keyword arguments for filtering (attribute=value)

        Returns:
            Sequence of matching entities

        Example:
            >>> # Find posts by user
            >>> user_posts = post_repo.find_by(userId="user-123")
            >>> 
            >>> # Find featured posts (note: requires manual query for None checks)
            >>> stmt = select(PostRow).where(PostRow.featuredAt != None)
            >>> featured = session.exec(stmt).all()
        """
        stmt = select(self.model)
        for key, value in filters.items():
            if hasattr(self.model, key):
                stmt = stmt.where(getattr(self.model, key) == value)
        return self.session.exec(stmt).all()

    def count(self) -> int:
        """Count total number of entities.

        Returns:
            Total count of entities

        Example:
            >>> total_posts = post_repo.count()
            >>> print(f"Total posts: {total_posts}")
        """
        from sqlalchemy import func

        stmt = select(func.count()).select_from(self.model)
        return self.session.exec(stmt).one()

    def exists(self, entity_id: str) -> bool:
        """Check if entity exists by ID.

        Args:
            entity_id: Primary key value

        Returns:
            True if exists, False otherwise

        Example:
            >>> if post_repo.exists("123"):
            ...     print("Post exists")
            ... else:
            ...     print("Post not found")
        """
        return self.get(entity_id) is not None

    def get_or_create(self, entity_id: str, defaults: dict[str, Any]) -> tuple[T, bool]:
        """Get existing entity or create if not found.

        Args:
            entity_id: Primary key value
            defaults: Default values for creation (must include 'id')

        Returns:
            Tuple of (entity, created) where created is True if new entity was created

        Example:
            >>> user, created = user_repo.get_or_create(
            ...     "user-123",
            ...     defaults={"id": "user-123", "username": "john", "name": "John"}
            ... )
            >>> if created:
            ...     print("Created new user")
            ... else:
            ...     print("User already existed")
        """
        entity = self.get(entity_id)
        if entity:
            return entity, False

        # Create new entity
        new_entity = self.model(**defaults)
        created_entity = self.create(new_entity)
        return created_entity, True


# =============================================================================
# Repository Factory Helper
# =============================================================================


class RepositoryFactory:
    """Factory for creating type-safe repositories.

    Provides convenience methods for creating repositories for common entities.

    Example:
        >>> from producthuntdb.repository import RepositoryFactory
        >>> from producthuntdb.models import PostRow, UserRow, TopicRow
        >>> 
        >>> factory = RepositoryFactory(session)
        >>> 
        >>> post_repo = factory.for_entity(PostRow)
        >>> user_repo = factory.for_entity(UserRow)
        >>> topic_repo = factory.for_entity(TopicRow)
    """

    def __init__(self, session: Session):
        """Initialize repository factory.

        Args:
            session: SQLModel Session for database operations
        """
        self.session = session

    def for_entity(self, model: type[T]) -> Repository[T]:
        """Create repository for specific entity type.

        Args:
            model: SQLModel class (e.g., PostRow, UserRow)

        Returns:
            Type-safe Repository[T] instance

        Example:
            >>> from producthuntdb.models import PostRow
            >>> post_repo = factory.for_entity(PostRow)
            >>> post = post_repo.get("123")  # Returns PostRow | None
        """
        return Repository[T](self.session, model)


# =============================================================================
# Export Public API
# =============================================================================

__all__ = ["Repository", "RepositoryFactory"]
