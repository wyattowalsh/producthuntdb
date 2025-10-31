"""Tests for repository pattern implementation.

This module tests the Repository[T] generic class and RepositoryFactory for type-safe
database operations.

Coverage Target: 0% → 85% (+47 lines)
Priority: High - Core data access layer
"""

import pytest
from sqlmodel import Field, Session, SQLModel, create_engine

from producthuntdb.repository import Repository, RepositoryFactory


# =============================================================================
# Test Models
# =============================================================================


class TestEntity(SQLModel, table=True):
    """Test entity for repository tests."""

    __tablename__ = "test_entities"  # type: ignore[assignment]

    id: str = Field(primary_key=True)
    name: str
    value: int = 0
    is_active: bool = True


class AnotherEntity(SQLModel, table=True):
    """Another test entity for factory tests."""

    __tablename__ = "another_entities"  # type: ignore[assignment]

    id: str = Field(primary_key=True)
    title: str
    count: int = 0


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def test_engine():
    """Create in-memory SQLite engine for testing."""
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create a test session."""
    with Session(test_engine) as session:
        yield session
        session.rollback()


@pytest.fixture
def test_repo(test_session):
    """Create a repository for TestEntity."""
    return Repository[TestEntity](test_session, TestEntity)


@pytest.fixture
def sample_entity():
    """Create a sample test entity."""
    return TestEntity(id="test-1", name="Test Item", value=42, is_active=True)


# =============================================================================
# Repository Core Tests
# =============================================================================


def test_repository_initialization(test_session):
    """Test repository can be initialized with session and model."""
    repo = Repository[TestEntity](test_session, TestEntity)
    assert repo.session == test_session
    assert repo.model == TestEntity


def test_repository_get_returns_none_when_not_found(test_repo):
    """Test get() returns None for non-existent entity."""
    result = test_repo.get("nonexistent-id")
    assert result is None


def test_repository_get_returns_entity_when_found(test_repo, sample_entity):
    """Test get() returns entity when it exists."""
    # Create entity first
    created = test_repo.create(sample_entity)

    # Retrieve it
    result = test_repo.get(created.id)
    assert result is not None
    assert result.id == "test-1"
    assert result.name == "Test Item"
    assert result.value == 42


def test_repository_get_all_empty_database(test_repo):
    """Test get_all() returns empty list for empty database."""
    results = test_repo.get_all()
    assert len(results) == 0


def test_repository_get_all_returns_all_entities(test_repo):
    """Test get_all() returns all entities."""
    # Create multiple entities
    entities = [
        TestEntity(id=f"test-{i}", name=f"Item {i}", value=i * 10)
        for i in range(5)
    ]
    for entity in entities:
        test_repo.create(entity)

    # Retrieve all
    results = test_repo.get_all()
    assert len(results) == 5
    assert all(isinstance(r, TestEntity) for r in results)


def test_repository_get_all_with_limit(test_repo):
    """Test get_all() respects limit parameter."""
    # Create 10 entities
    for i in range(10):
        test_repo.create(TestEntity(id=f"test-{i}", name=f"Item {i}", value=i))

    # Get only 3
    results = test_repo.get_all(limit=3)
    assert len(results) == 3


def test_repository_get_all_with_offset(test_repo):
    """Test get_all() respects offset parameter."""
    # Create entities with predictable IDs
    for i in range(5):
        test_repo.create(TestEntity(id=f"test-{i:02d}", name=f"Item {i}", value=i))

    # Get second page (skip first 2)
    results = test_repo.get_all(limit=2, offset=2)
    assert len(results) == 2


def test_repository_get_all_with_limit_and_offset(test_repo):
    """Test get_all() with both limit and offset."""
    # Create 20 entities
    for i in range(20):
        test_repo.create(TestEntity(id=f"test-{i:03d}", name=f"Item {i}", value=i))

    # Get page 3 (items 10-14)
    results = test_repo.get_all(limit=5, offset=10)
    assert len(results) == 5


# =============================================================================
# Create/Update/Delete Tests
# =============================================================================


def test_repository_create_saves_entity(test_repo, sample_entity):
    """Test create() saves entity to database."""
    created = test_repo.create(sample_entity)

    # Verify returned entity
    assert created.id == "test-1"
    assert created.name == "Test Item"
    assert created.value == 42

    # Verify persisted to database
    retrieved = test_repo.get("test-1")
    assert retrieved is not None
    assert retrieved.id == created.id


def test_repository_create_returns_refreshed_entity(test_repo):
    """Test create() returns entity with database-generated values."""
    entity = TestEntity(id="test-1", name="Test", value=100)
    created = test_repo.create(entity)

    # Entity should be refreshed from database
    assert created.id == "test-1"
    assert created.name == "Test"


def test_repository_update_modifies_entity(test_repo, sample_entity):
    """Test update() modifies existing entity."""
    # Create entity
    created = test_repo.create(sample_entity)

    # Modify and update
    created.name = "Modified Name"
    created.value = 999
    updated = test_repo.update(created)

    # Verify changes
    assert updated.name == "Modified Name"
    assert updated.value == 999

    # Verify persisted
    retrieved = test_repo.get("test-1")
    assert retrieved.name == "Modified Name"
    assert retrieved.value == 999


def test_repository_delete_removes_entity(test_repo, sample_entity):
    """Test delete() removes entity from database."""
    # Create entity
    created = test_repo.create(sample_entity)
    assert test_repo.get(created.id) is not None

    # Delete
    deleted = test_repo.delete(created.id)
    assert deleted is True

    # Verify removed
    assert test_repo.get(created.id) is None


def test_repository_delete_returns_false_when_not_found(test_repo):
    """Test delete() returns False for non-existent entity."""
    deleted = test_repo.delete("nonexistent-id")
    assert deleted is False


# =============================================================================
# Query Helper Tests
# =============================================================================


def test_repository_find_by_single_attribute(test_repo):
    """Test find_by() with single attribute filter."""
    # Create entities with different values
    test_repo.create(TestEntity(id="test-1", name="Alice", value=10))
    test_repo.create(TestEntity(id="test-2", name="Bob", value=20))
    test_repo.create(TestEntity(id="test-3", name="Alice", value=30))

    # Find by name
    results = test_repo.find_by(name="Alice")
    assert len(results) == 2
    assert all(r.name == "Alice" for r in results)


def test_repository_find_by_multiple_attributes(test_repo):
    """Test find_by() with multiple attribute filters."""
    # Create entities
    test_repo.create(TestEntity(id="test-1", name="Alice", value=10, is_active=True))
    test_repo.create(TestEntity(id="test-2", name="Alice", value=10, is_active=False))
    test_repo.create(TestEntity(id="test-3", name="Bob", value=10, is_active=True))

    # Find by multiple attributes
    results = test_repo.find_by(name="Alice", is_active=True)
    assert len(results) == 1
    assert results[0].id == "test-1"


def test_repository_find_by_returns_empty_when_no_match(test_repo):
    """Test find_by() returns empty list when no entities match."""
    test_repo.create(TestEntity(id="test-1", name="Alice", value=10))

    results = test_repo.find_by(name="NonExistent")
    assert len(results) == 0


def test_repository_find_by_ignores_unknown_attributes(test_repo):
    """Test find_by() ignores attributes that don't exist on model."""
    test_repo.create(TestEntity(id="test-1", name="Alice", value=10))

    # This should not raise an error
    results = test_repo.find_by(name="Alice", unknown_field="value")
    assert len(results) == 1


def test_repository_count_empty_database(test_repo):
    """Test count() returns 0 for empty database."""
    count = test_repo.count()
    assert count == 0


def test_repository_count_returns_total(test_repo):
    """Test count() returns total number of entities."""
    # Create 7 entities
    for i in range(7):
        test_repo.create(TestEntity(id=f"test-{i}", name=f"Item {i}", value=i))

    count = test_repo.count()
    assert count == 7


def test_repository_exists_returns_false_when_not_found(test_repo):
    """Test exists() returns False for non-existent entity."""
    assert test_repo.exists("nonexistent-id") is False


def test_repository_exists_returns_true_when_found(test_repo, sample_entity):
    """Test exists() returns True for existing entity."""
    created = test_repo.create(sample_entity)
    assert test_repo.exists(created.id) is True


# =============================================================================
# Get-or-Create Tests
# =============================================================================


def test_repository_get_or_create_creates_when_not_found(test_repo):
    """Test get_or_create() creates entity when it doesn't exist."""
    entity, created = test_repo.get_or_create(
        "test-1",
        defaults={"id": "test-1", "name": "New Item", "value": 50},
    )

    assert created is True
    assert entity.id == "test-1"
    assert entity.name == "New Item"
    assert entity.value == 50


def test_repository_get_or_create_returns_existing_when_found(test_repo, sample_entity):
    """Test get_or_create() returns existing entity without creating."""
    # Create entity first
    existing = test_repo.create(sample_entity)

    # Try to get_or_create
    entity, created = test_repo.get_or_create(
        "test-1",
        defaults={"id": "test-1", "name": "Different Name", "value": 999},
    )

    assert created is False
    assert entity.id == existing.id
    assert entity.name == existing.name  # Original name, not defaults
    assert entity.value == existing.value  # Original value, not defaults


def test_repository_get_or_create_with_all_defaults(test_repo):
    """Test get_or_create() uses all default values when creating."""
    entity, created = test_repo.get_or_create(
        "test-1",
        defaults={
            "id": "test-1",
            "name": "Default Name",
            "value": 100,
            "is_active": False,
        },
    )

    assert created is True
    assert entity.name == "Default Name"
    assert entity.value == 100
    assert entity.is_active is False


# =============================================================================
# RepositoryFactory Tests
# =============================================================================


def test_repository_factory_initialization(test_session):
    """Test RepositoryFactory can be initialized with session."""
    factory = RepositoryFactory(test_session)
    assert factory.session == test_session


def test_repository_factory_creates_repository_for_entity(test_session):
    """Test factory creates repository for specified entity type."""
    factory = RepositoryFactory(test_session)
    repo = factory.for_entity(TestEntity)

    assert isinstance(repo, Repository)
    assert repo.session == test_session
    assert repo.model == TestEntity


def test_repository_factory_creates_different_repositories(test_session):
    """Test factory can create repositories for different entity types."""
    factory = RepositoryFactory(test_session)

    repo1 = factory.for_entity(TestEntity)
    repo2 = factory.for_entity(AnotherEntity)

    assert repo1.model == TestEntity
    assert repo2.model == AnotherEntity
    assert repo1.session == repo2.session  # Share same session


def test_repository_factory_repositories_are_independent(test_session):
    """Test repositories created by factory operate independently."""
    # Setup tables
    SQLModel.metadata.create_all(test_session.get_bind())

    factory = RepositoryFactory(test_session)

    # Create repositories
    entity_repo = factory.for_entity(TestEntity)
    another_repo = factory.for_entity(AnotherEntity)

    # Add data to each
    entity_repo.create(TestEntity(id="test-1", name="Test", value=10))
    another_repo.create(AnotherEntity(id="another-1", title="Another", count=5))

    # Verify independence
    assert entity_repo.count() == 1
    assert another_repo.count() == 1

    # Cross-repository queries should not interfere
    assert entity_repo.get("another-1") is None
    assert another_repo.get("test-1") is None


# =============================================================================
# Type Safety Tests
# =============================================================================


def test_repository_preserves_type_information(test_repo, sample_entity):
    """Test repository operations preserve type information."""
    # Create
    created = test_repo.create(sample_entity)
    assert isinstance(created, TestEntity)

    # Get
    retrieved = test_repo.get(created.id)
    assert isinstance(retrieved, TestEntity)

    # Get all
    all_entities = test_repo.get_all()
    assert all(isinstance(e, TestEntity) for e in all_entities)

    # Update
    updated = test_repo.update(created)
    assert isinstance(updated, TestEntity)


def test_repository_handles_multiple_entity_types(test_session):
    """Test multiple repositories can coexist with different types."""
    # Setup tables
    SQLModel.metadata.create_all(test_session.get_bind())

    # Create repositories for different types
    test_repo = Repository[TestEntity](test_session, TestEntity)
    another_repo = Repository[AnotherEntity](test_session, AnotherEntity)

    # Add data
    test_entity = test_repo.create(TestEntity(id="t1", name="Test", value=10))
    another_entity = another_repo.create(
        AnotherEntity(id="a1", title="Another", count=5)
    )

    # Verify types are preserved
    assert isinstance(test_entity, TestEntity)
    assert isinstance(another_entity, AnotherEntity)

    # Verify retrieval maintains types
    retrieved_test = test_repo.get("t1")
    retrieved_another = another_repo.get("a1")

    assert isinstance(retrieved_test, TestEntity)
    assert isinstance(retrieved_another, AnotherEntity)


# =============================================================================
# Edge Cases
# =============================================================================


def test_repository_handles_empty_defaults_in_get_or_create(test_repo):
    """Test get_or_create() with minimal defaults."""
    entity, created = test_repo.get_or_create(
        "test-1",
        defaults={"id": "test-1", "name": "Minimal"},
    )

    assert created is True
    assert entity.id == "test-1"
    assert entity.name == "Minimal"
    assert entity.value == 0  # Default from model


def test_repository_update_persists_all_changes(test_repo, sample_entity):
    """Test update() persists multiple field changes."""
    created = test_repo.create(sample_entity)

    # Change multiple fields
    created.name = "New Name"
    created.value = 999
    created.is_active = False

    updated = test_repo.update(created)

    # Verify all changes persisted
    retrieved = test_repo.get(created.id)
    assert retrieved.name == "New Name"
    assert retrieved.value == 999
    assert retrieved.is_active is False


def test_repository_find_by_with_boolean_false(test_repo):
    """Test find_by() correctly handles boolean False values."""
    test_repo.create(TestEntity(id="test-1", name="Active", is_active=True))
    test_repo.create(TestEntity(id="test-2", name="Inactive", is_active=False))

    # Find inactive entities
    results = test_repo.find_by(is_active=False)
    assert len(results) == 1
    assert results[0].id == "test-2"


def test_repository_find_by_with_zero_value(test_repo):
    """Test find_by() correctly handles zero values."""
    test_repo.create(TestEntity(id="test-1", name="Zero", value=0))
    test_repo.create(TestEntity(id="test-2", name="Ten", value=10))

    # Find entities with value=0
    results = test_repo.find_by(value=0)
    assert len(results) == 1
    assert results[0].id == "test-1"
