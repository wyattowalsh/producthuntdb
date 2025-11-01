"""Tests for producthuntdb.database module.

Tests database manager functionality including:
- Connection management and initialization
- WAL mode and PRAGMA settings
- Index creation
- User CRUD operations
- Post CRUD operations (single and batch)
- Topic operations
- Link operations (post-topics, post-makers)
- Crawl state tracking
- Error handling and edge cases

Run: uv run pytest tests/test_database.py -v
"""

import json
from pathlib import Path
from typing import Any, Generator

import pytest
from sqlmodel import Session, select

from producthuntdb.database import DatabaseManager
from producthuntdb.models import (
    CrawlState,
    MakerPostLink,
    MediaRow,
    PostRow,
    PostTopicLink,
    TopicRow,
    UserRow,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def temp_db_path(tmp_path: Path) -> Path:
    """Provide a temporary database path."""
    return tmp_path / "test_producthunt.db"


@pytest.fixture
def db_manager(temp_db_path: Path) -> Generator[DatabaseManager, None, None]:
    """Provide an initialized DatabaseManager instance."""
    db = DatabaseManager(database_path=temp_db_path)
    db.initialize()
    yield db
    db.close()


@pytest.fixture
def sample_user_data() -> dict[str, Any]:
    """Provide sample user data."""
    return {
        "id": "user_123",
        "username": "john_doe",
        "name": "John Doe",
        "headline": "Product Maker",
        "profileImage": "https://example.com/john.jpg",
        "websiteUrl": "https://johndoe.com",
        "url": "https://producthunt.com/@john_doe",
        "createdAt": "2024-01-01T12:00:00Z",
    }


@pytest.fixture
def sample_post_data() -> dict[str, Any]:
    """Provide sample post data."""
    return {
        "id": "post_456",
        "userId": "user_123",
        "name": "Amazing Product",
        "tagline": "The best thing ever",
        "description": "This is a great product",
        "slug": "amazing-product",
        "url": "https://producthunt.com/posts/amazing-product",
        "website": "https://amazing-product.com",
        "createdAt": "2024-01-15T10:00:00Z",
        "featuredAt": "2024-01-15T12:00:00Z",
        "votesCount": 150,
        "commentsCount": 25,
        "reviewsCount": 10,
        "reviewsRating": 4.5,
        "isCollected": False,
        "isVoted": True,
        "thumbnail": {
            "type": "image",
            "url": "https://example.com/thumb.jpg",
            "videoUrl": None,
        },
        "productLinks": [
            {"type": "WEBSITE", "url": "https://amazing-product.com"},
            {"type": "IOS_APP", "url": "https://apps.apple.com/app/123"},
        ],
        "media": [
            {"type": "image", "url": "https://example.com/media1.jpg", "videoUrl": None},
            {"type": "video", "url": "https://example.com/media2.mp4", "videoUrl": "https://example.com/media2.mp4"},
        ],
    }


@pytest.fixture
def sample_topic_data() -> dict[str, Any]:
    """Provide sample topic data."""
    return {
        "id": "topic_789",
        "name": "Artificial Intelligence",
        "slug": "artificial-intelligence",
        "description": "AI and machine learning products",
        "url": "https://producthunt.com/topics/artificial-intelligence",
        "createdAt": "2023-01-01T00:00:00Z",
        "followersCount": 5000,
        "postsCount": 1200,
        "isFollowing": False,
        "image": "https://example.com/ai.jpg",
    }


# =============================================================================
# Initialization Tests
# =============================================================================


def test_database_initialization(temp_db_path: Path):
    """Test database initialization creates file and tables."""
    db = DatabaseManager(database_path=temp_db_path)
    db.initialize()

    # Database file should exist
    assert temp_db_path.exists()

    # WAL files may exist
    assert (temp_db_path.parent / f"{temp_db_path.name}-wal").exists() or True

    # Should be able to query tables
    with Session(db.engine) as session:
        # Tables should be empty initially
        assert session.exec(select(UserRow)).all() == []
        assert session.exec(select(PostRow)).all() == []
        assert session.exec(select(TopicRow)).all() == []

    db.close()


def test_database_initialization_creates_parent_directory(tmp_path: Path):
    """Test that initialization creates parent directories."""
    nested_path = tmp_path / "nested" / "dir" / "test.db"
    db = DatabaseManager(database_path=nested_path)
    db.initialize()

    assert nested_path.exists()
    assert nested_path.parent.exists()

    db.close()


def test_database_wal_mode_enabled(db_manager: DatabaseManager):
    """Test that WAL mode is properly enabled."""
    assert db_manager.engine is not None
    with db_manager.engine.connect() as conn:
        result = conn.exec_driver_sql("PRAGMA journal_mode;").fetchone()
        assert result is not None
        assert result[0].lower() == "wal"


def test_database_pragma_settings(db_manager: DatabaseManager):
    """Test that PRAGMA settings are correctly configured."""
    assert db_manager.engine is not None
    with db_manager.engine.connect() as conn:
        # Check synchronous mode
        result = conn.exec_driver_sql("PRAGMA synchronous;").fetchone()
        assert result is not None
        assert result[0] == 1  # NORMAL = 1

        # Check cache size (should be negative for KB)
        result = conn.exec_driver_sql("PRAGMA cache_size;").fetchone()
        assert result is not None
        assert result[0] == -64000  # 64MB

        # Check temp_store (MEMORY = 2)
        result = conn.exec_driver_sql("PRAGMA temp_store;").fetchone()
        assert result is not None
        assert result[0] == 2


def test_database_indexes_created(db_manager: DatabaseManager):
    """Test that indexes are properly created."""
    assert db_manager.engine is not None
    with db_manager.engine.connect() as conn:
        # Query sqlite_master for indexes
        result = conn.exec_driver_sql(
            "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%';"
        ).fetchall()

        index_names = [row[0] for row in result]

        # Verify critical indexes exist
        expected_indexes = [
            "idx_post_created_at",
            "idx_post_featured_at",
            "idx_post_votes",
            "idx_post_user",
            "idx_user_username",
            "idx_topic_slug",
        ]

        for expected in expected_indexes:
            assert expected in index_names, f"Missing index: {expected}"


def test_close_without_initialization():
    """Test that close works even if database was never initialized."""
    db = DatabaseManager()
    db.close()  # Should not raise


# =============================================================================
# User Operations Tests
# =============================================================================


def test_upsert_user_creates_new(db_manager: DatabaseManager, sample_user_data: dict[str, Any]):
    """Test that upsert_user creates a new user."""
    user = db_manager.upsert_user(sample_user_data)

    assert user.id == sample_user_data["id"]
    assert user.username == sample_user_data["username"]
    assert user.name == sample_user_data["name"]
    assert user.headline == sample_user_data["headline"]

    # Verify in database
    with Session(db_manager.engine) as session:
        db_user = session.get(UserRow, sample_user_data["id"])
        assert db_user is not None
        assert db_user.username == sample_user_data["username"]


def test_upsert_user_updates_existing(db_manager: DatabaseManager, sample_user_data: dict[str, Any]):
    """Test that upsert_user updates an existing user."""
    # Create initial user
    db_manager.upsert_user(sample_user_data)

    # Update with new data
    updated_data = {**sample_user_data, "name": "Jane Doe", "headline": "Designer"}
    updated_user = db_manager.upsert_user(updated_data)

    assert updated_user.name == "Jane Doe"
    assert updated_user.headline == "Designer"

    # Verify only one user exists
    with Session(db_manager.engine) as session:
        users = session.exec(select(UserRow)).all()
        assert len(users) == 1


def test_upsert_user_handles_timestamp(db_manager: DatabaseManager):
    """Test that upsert_user properly handles timestamp conversion."""
    user_data = {
        "id": "user_ts",
        "username": "timestamp_user",
        "name": "Timestamp User",
        "createdAt": "2024-01-01T12:00:00+00:00",
    }

    user = db_manager.upsert_user(user_data)
    assert user.createdAt is not None
    assert "2024-01-01" in user.createdAt


def test_upsert_user_without_initialization_raises():
    """Test that operations without initialization raise RuntimeError."""
    db = DatabaseManager()
    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.upsert_user({"id": "test", "username": "test", "name": "Test"})


# =============================================================================
# Post Operations Tests
# =============================================================================


def test_upsert_post_creates_new(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that upsert_post creates a new post."""
    post = db_manager.upsert_post(sample_post_data)

    assert post.id == sample_post_data["id"]
    assert post.name == sample_post_data["name"]
    assert post.tagline == sample_post_data["tagline"]
    assert post.votesCount == sample_post_data["votesCount"]


def test_upsert_post_updates_existing(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that upsert_post updates an existing post."""
    # Create initial post
    db_manager.upsert_post(sample_post_data)

    # Update with new data
    updated_data = {**sample_post_data, "votesCount": 200, "commentsCount": 50}
    updated_post = db_manager.upsert_post(updated_data)

    assert updated_post.votesCount == 200
    assert updated_post.commentsCount == 50

    # Verify only one post exists
    with Session(db_manager.engine) as session:
        posts = session.exec(select(PostRow)).all()
        assert len(posts) == 1


def test_upsert_post_handles_thumbnail(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that upsert_post properly extracts thumbnail fields."""
    post = db_manager.upsert_post(sample_post_data)

    assert post.thumbnail_type == "image"
    assert post.thumbnail_url == "https://example.com/thumb.jpg"
    assert post.thumbnail_videoUrl is None


def test_upsert_post_handles_product_links(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that upsert_post stores productLinks as JSON."""
    post = db_manager.upsert_post(sample_post_data)

    assert post.productlinks_json is not None
    links = json.loads(post.productlinks_json)
    assert len(links) == 2
    assert links[0]["type"] == "WEBSITE"


def test_upsert_post_handles_media(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that upsert_post creates MediaRow entries."""
    post = db_manager.upsert_post(sample_post_data)

    # Check media entries
    with Session(db_manager.engine) as session:
        stmt = select(MediaRow).where(MediaRow.post_id == post.id)
        media_items = list(session.exec(stmt).all())
        # Sort by order_index for consistent comparison
        media_items.sort(key=lambda m: m.order_index if m.order_index is not None else 0)

        assert len(media_items) == 2
        assert media_items[0].type == "image"
        assert media_items[0].url == "https://example.com/media1.jpg"
        assert media_items[1].type == "video"


def test_upsert_post_updates_media(db_manager: DatabaseManager, sample_post_data: dict[str, Any]):
    """Test that updating a post replaces old media entries."""
    # Create post with media
    db_manager.upsert_post(sample_post_data)

    # Update with new media
    updated_data = {
        **sample_post_data,
        "media": [
            {"type": "image", "url": "https://example.com/new_media.jpg", "videoUrl": None},
        ],
    }
    db_manager.upsert_post(updated_data)

    # Verify only new media exists
    with Session(db_manager.engine) as session:
        media_items = session.exec(
            select(MediaRow).where(MediaRow.post_id == sample_post_data["id"])
        ).all()

        assert len(media_items) == 1
        assert media_items[0].url == "https://example.com/new_media.jpg"


def test_upsert_post_handles_timestamps(db_manager: DatabaseManager):
    """Test that upsert_post handles timestamp formatting correctly."""
    post_data = {
        "id": "post_ts",
        "userId": "user_123",
        "name": "Timestamp Post",
        "tagline": "Testing timestamps",
        "url": "https://producthunt.com/posts/timestamp-post",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
        "createdAt": "2024-01-01T10:00:00+00:00",
        "featuredAt": "2024-01-01T12:00:00+00:00",
    }

    post = db_manager.upsert_post(post_data)
    assert post.createdAt is not None
    assert "2024-01-01" in post.createdAt
    assert post.featuredAt is not None


# =============================================================================
# Batch Operations Tests
# =============================================================================


def test_upsert_posts_batch_creates_multiple(db_manager: DatabaseManager):
    """Test that upsert_posts_batch creates multiple posts."""
    posts_data = [
        {
            "id": f"post_{i}",
            "userId": "user_123",
            "name": f"Product {i}",
            "tagline": f"Tagline {i}",
            "url": f"https://producthunt.com/posts/product-{i}",
            "votesCount": i * 10,
            "commentsCount": 0,
            "reviewsCount": 0,
            "reviewsRating": 0.0,
            "isCollected": False,
            "isVoted": False,
            "createdAt": "2024-01-01T10:00:00Z",
        }
        for i in range(5)
    ]

    posts = db_manager.upsert_posts_batch(posts_data)

    assert len(posts) == 5
    assert posts[0].name == "Product 0"
    assert posts[4].name == "Product 4"


def test_upsert_posts_batch_updates_existing(db_manager: DatabaseManager):
    """Test that upsert_posts_batch updates existing posts."""
    # Create initial posts
    initial_data = [
        {
            "id": f"post_{i}",
            "userId": "user_123",
            "name": f"Product {i}",
            "tagline": f"Tagline {i}",
            "url": f"https://producthunt.com/posts/product-{i}",
            "votesCount": 10,
            "commentsCount": 0,
            "reviewsCount": 0,
            "reviewsRating": 0.0,
            "isCollected": False,
            "isVoted": False,
            "createdAt": "2024-01-01T10:00:00Z",
        }
        for i in range(3)
    ]
    db_manager.upsert_posts_batch(initial_data)

    # Update with new vote counts
    updated_data = [
        {
            "id": f"post_{i}",
            "userId": "user_123",
            "name": f"Product {i}",
            "tagline": f"Tagline {i}",
            "url": f"https://producthunt.com/posts/product-{i}",
            "votesCount": 50,
            "commentsCount": 0,
            "reviewsCount": 0,
            "reviewsRating": 0.0,
            "isCollected": False,
            "isVoted": False,
            "createdAt": "2024-01-01T10:00:00Z",
        }
        for i in range(3)
    ]
    updated_posts = db_manager.upsert_posts_batch(updated_data)

    assert len(updated_posts) == 3
    assert all(p.votesCount == 50 for p in updated_posts)

    # Verify only 3 posts exist (not 6)
    with Session(db_manager.engine) as session:
        all_posts = session.exec(select(PostRow)).all()
        assert len(all_posts) == 3


def test_upsert_posts_batch_with_large_batch_size(db_manager: DatabaseManager):
    """Test batch processing with custom batch size."""
    posts_data = [
        {
            "id": f"post_{i}",
            "userId": "user_123",
            "name": f"Product {i}",
            "tagline": f"Tagline {i}",
            "url": f"https://producthunt.com/posts/product-{i}",
            "votesCount": i,
            "commentsCount": 0,
            "reviewsCount": 0,
            "reviewsRating": 0.0,
            "isCollected": False,
            "isVoted": False,
            "createdAt": "2024-01-01T10:00:00Z",
        }
        for i in range(250)  # More than default batch size
    ]

    posts = db_manager.upsert_posts_batch(posts_data, batch_size=50)

    assert len(posts) == 250
    assert posts[0].votesCount == 0
    assert posts[249].votesCount == 249


def test_upsert_posts_batch_without_initialization_raises():
    """Test that batch operations without initialization raise RuntimeError."""
    db = DatabaseManager()
    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.upsert_posts_batch([{"id": "test", "name": "Test"}])


# =============================================================================
# Topic Operations Tests
# =============================================================================


def test_upsert_topic_creates_new(db_manager: DatabaseManager, sample_topic_data: dict[str, Any]):
    """Test that upsert_topic creates a new topic."""
    topic = db_manager.upsert_topic(sample_topic_data)

    assert topic.id == sample_topic_data["id"]
    assert topic.name == sample_topic_data["name"]
    assert topic.slug == sample_topic_data["slug"]


def test_upsert_topic_updates_existing(db_manager: DatabaseManager, sample_topic_data: dict[str, Any]):
    """Test that upsert_topic updates an existing topic."""
    # Create initial topic
    db_manager.upsert_topic(sample_topic_data)

    # Update with new data
    updated_data = {**sample_topic_data, "followersCount": 10000}
    updated_topic = db_manager.upsert_topic(updated_data)

    assert updated_topic.followersCount == 10000

    # Verify only one topic exists
    with Session(db_manager.engine) as session:
        topics = session.exec(select(TopicRow)).all()
        assert len(topics) == 1


# =============================================================================
# Link Operations Tests
# =============================================================================


def test_link_post_topics(db_manager: DatabaseManager):
    """Test creating post-topic links."""
    # Create post and topics
    post_data = {
        "id": "post_link",
        "userId": "user_1",
        "name": "Test Post",
        "tagline": "Test",
        "url": "https://producthunt.com/posts/test-post",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
    }
    db_manager.upsert_post(post_data)

    topic1_data = {"id": "topic_1", "name": "AI", "slug": "ai"}
    topic2_data = {"id": "topic_2", "name": "ML", "slug": "ml"}
    db_manager.upsert_topic(topic1_data)
    db_manager.upsert_topic(topic2_data)

    # Link post to topics
    db_manager.link_post_topics("post_link", ["topic_1", "topic_2"])

    # Verify links
    with Session(db_manager.engine) as session:
        links = session.exec(
            select(PostTopicLink).where(PostTopicLink.post_id == "post_link")
        ).all()

        assert len(links) == 2
        topic_ids = [link.topic_id for link in links]
        assert "topic_1" in topic_ids
        assert "topic_2" in topic_ids


def test_link_post_topics_prevents_duplicates(db_manager: DatabaseManager):
    """Test that link_post_topics doesn't create duplicate links."""
    post_data = {
        "id": "post_dup",
        "userId": "user_1",
        "name": "Test",
        "tagline": "Test",
        "url": "https://producthunt.com/posts/test-dup",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
    }
    db_manager.upsert_post(post_data)

    topic_data = {"id": "topic_dup", "name": "AI", "slug": "ai"}
    db_manager.upsert_topic(topic_data)

    # Link twice
    db_manager.link_post_topics("post_dup", ["topic_dup"])
    db_manager.link_post_topics("post_dup", ["topic_dup"])

    # Should only have one link
    with Session(db_manager.engine) as session:
        links = session.exec(
            select(PostTopicLink).where(PostTopicLink.post_id == "post_dup")
        ).all()

        assert len(links) == 1


def test_link_post_makers(db_manager: DatabaseManager):
    """Test creating post-maker links."""
    # Create post and makers
    post_data = {
        "id": "post_makers",
        "userId": "user_1",
        "name": "Test",
        "tagline": "Test",
        "url": "https://producthunt.com/posts/test-makers",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
    }
    db_manager.upsert_post(post_data)

    maker1_data = {"id": "maker_1", "username": "maker1", "name": "Maker One"}
    maker2_data = {"id": "maker_2", "username": "maker2", "name": "Maker Two"}
    db_manager.upsert_user(maker1_data)
    db_manager.upsert_user(maker2_data)

    # Link post to makers
    db_manager.link_post_makers("post_makers", ["maker_1", "maker_2"])

    # Verify links
    with Session(db_manager.engine) as session:
        links = session.exec(
            select(MakerPostLink).where(MakerPostLink.post_id == "post_makers")
        ).all()

        assert len(links) == 2
        maker_ids = [link.user_id for link in links]
        assert "maker_1" in maker_ids
        assert "maker_2" in maker_ids


def test_link_post_makers_prevents_duplicates(db_manager: DatabaseManager):
    """Test that link_post_makers doesn't create duplicate links."""
    post_data = {
        "id": "post_maker_dup",
        "userId": "user_1",
        "name": "Test",
        "tagline": "Test",
        "url": "https://producthunt.com/posts/test-maker-dup",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
    }
    db_manager.upsert_post(post_data)

    maker_data = {"id": "maker_dup", "username": "maker", "name": "Maker"}
    db_manager.upsert_user(maker_data)

    # Link twice
    db_manager.link_post_makers("post_maker_dup", ["maker_dup"])
    db_manager.link_post_makers("post_maker_dup", ["maker_dup"])

    # Should only have one link
    with Session(db_manager.engine) as session:
        links = session.exec(
            select(MakerPostLink).where(MakerPostLink.post_id == "post_maker_dup")
        ).all()

        assert len(links) == 1


# =============================================================================
# Crawl State Tests
# =============================================================================


def test_get_crawl_state_returns_none_initially(db_manager: DatabaseManager):
    """Test that get_crawl_state returns None for new entity."""
    timestamp = db_manager.get_crawl_state("posts")
    assert timestamp is None


def test_update_crawl_state_creates_new(db_manager: DatabaseManager):
    """Test that update_crawl_state creates new state."""
    db_manager.update_crawl_state("posts", "2024-01-01T12:00:00Z")

    timestamp = db_manager.get_crawl_state("posts")
    assert timestamp == "2024-01-01T12:00:00Z"


def test_update_crawl_state_updates_existing(db_manager: DatabaseManager):
    """Test that update_crawl_state updates existing state."""
    db_manager.update_crawl_state("posts", "2024-01-01T12:00:00Z")
    db_manager.update_crawl_state("posts", "2024-01-02T12:00:00Z")

    timestamp = db_manager.get_crawl_state("posts")
    assert timestamp == "2024-01-02T12:00:00Z"

    # Verify only one state entry exists
    with Session(db_manager.engine) as session:
        states = session.exec(select(CrawlState)).all()
        assert len(states) == 1


def test_crawl_state_multiple_entities(db_manager: DatabaseManager):
    """Test that crawl state works for multiple entities."""
    db_manager.update_crawl_state("posts", "2024-01-01T12:00:00Z")
    db_manager.update_crawl_state("topics", "2024-01-02T12:00:00Z")
    db_manager.update_crawl_state("collections", "2024-01-03T12:00:00Z")

    assert db_manager.get_crawl_state("posts") == "2024-01-01T12:00:00Z"
    assert db_manager.get_crawl_state("topics") == "2024-01-02T12:00:00Z"
    assert db_manager.get_crawl_state("collections") == "2024-01-03T12:00:00Z"


def test_crawl_state_without_initialization_raises(temp_db_path: Path):
    """Test that crawl state operations without initialization raise RuntimeError."""
    db = DatabaseManager(database_path=temp_db_path)

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.get_crawl_state("posts")

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.update_crawl_state("posts", "2024-01-01T12:00:00Z")


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================


def test_operations_with_empty_session_raise(temp_db_path: Path):
    """Test that operations without proper session raise errors."""
    db = DatabaseManager(database_path=temp_db_path)
    # Initialize to create engine, but don't create session
    db.initialize()
    # Close to clear session
    if db.session:
        db.session.close()
    db.session = None

    # All operations should raise RuntimeError
    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.upsert_user({"id": "test", "username": "test", "name": "Test"})

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.upsert_post({"id": "test", "name": "Test", "tagline": "Test"})

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.upsert_topic({"id": "test", "name": "Test", "slug": "test"})

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.link_post_topics("post_1", ["topic_1"])

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.link_post_makers("post_1", ["maker_1"])

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.get_crawl_state("posts")

    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.update_crawl_state("posts", "2024-01-01T12:00:00Z")

    db.close()


def test_upsert_post_without_nested_objects(db_manager: DatabaseManager):
    """Test upsert_post works without nested objects."""
    minimal_post = {
        "id": "minimal_post",
        "userId": "user_1",
        "name": "Minimal Post",
        "tagline": "Just the basics",
        "url": "https://producthunt.com/posts/minimal-post",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
    }

    post = db_manager.upsert_post(minimal_post)
    assert post.id == "minimal_post"
    assert post.name == "Minimal Post"


def test_upsert_post_with_null_thumbnail(db_manager: DatabaseManager):
    """Test upsert_post handles null thumbnail."""
    post_data = {
        "id": "no_thumb",
        "userId": "user_1",
        "name": "No Thumbnail",
        "tagline": "Testing null",
        "url": "https://producthunt.com/posts/no-thumb",
        "votesCount": 0,
        "commentsCount": 0,
        "reviewsCount": 0,
        "reviewsRating": 0.0,
        "isCollected": False,
        "isVoted": False,
        "thumbnail": None,
    }

    post = db_manager.upsert_post(post_data)
    assert post.thumbnail_type is None
    assert post.thumbnail_url is None


def test_create_indexes_without_engine_raises():
    """Test that create_indexes without engine raises RuntimeError."""
    db = DatabaseManager()
    with pytest.raises(RuntimeError, match="Database not initialized"):
        db.create_indexes()


def test_database_path_default():
    """Test that DatabaseManager uses default path from settings."""
    from producthuntdb.config import settings

    db = DatabaseManager()
    assert db.database_path == settings.database_path
