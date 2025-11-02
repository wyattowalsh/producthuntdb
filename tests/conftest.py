"""Pytest configuration and shared fixtures for ProductHuntDB tests."""

import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator
from unittest.mock import MagicMock

import pytest
from hypothesis import HealthCheck, Phase, Verbosity, settings
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from producthuntdb.config import Settings
from producthuntdb.io import AsyncGraphQLClient, DatabaseManager
from producthuntdb.models import (
    CollectionRow,
    CommentRow,
    PostRow,
    TopicRow,
    UserRow,
    VoteRow,
)


# =============================================================================
# Hypothesis Configuration
# =============================================================================

# Configure Hypothesis settings with tiered example counts
settings.register_profile(
    "default",
    max_examples=100,  # Standard complexity
    deadline=5000,  # 5 second timeout per example
    suppress_health_check=[HealthCheck.too_slow],
)

settings.register_profile(
    "simple",
    max_examples=50,  # Simple functions
    deadline=2000,
)

settings.register_profile(
    "complex",
    max_examples=200,  # Complex transformations
    deadline=10000,
)

settings.register_profile(
    "critical",
    max_examples=500,  # Critical security/data integrity
    deadline=15000,
)

# Use default profile
settings.load_profile("default")


# =============================================================================
# Test Configuration
# =============================================================================


@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure loguru for tests to avoid I/O errors."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level="ERROR",  # Only log errors during tests
        format="{time} {level} {message}",
        catch=True,  # Prevent exceptions in logging
        enqueue=True,  # Thread-safe logging
    )
    yield
    logger.remove()  # Clean up after all tests


@pytest.fixture(scope="function", autouse=True)
def reset_loguru():
    """Reset loguru handlers before each test to prevent I/O errors."""
    # Remove all handlers
    logger.remove()
    # Add a safe handler that won't fail
    logger.add(
        sys.stderr,
        level="ERROR",
        format="{time} {level} {message}",
        catch=True,
        enqueue=True,
    )
    yield
    # Clean up after test
    logger.remove()


@pytest.fixture(scope="function", autouse=True)
def ensure_prometheus_metrics():
    """Ensure Prometheus metrics are registered before each test.
    
    The metrics are registered at module import time, but we verify they
    remain registered throughout the test. We don't clear values to avoid
    breaking the Prometheus client's internal state.
    """
    # Import metrics module to ensure collectors are registered
    from producthuntdb import metrics
    
    # Verify key metrics are registered (they should be registered at import time)
    # This is a no-op but ensures the module is loaded
    assert metrics.registry is not None
    
    yield
    
    # No cleanup - metrics are stateful and shared across tests
    # This matches real-world usage where metrics accumulate


@pytest.fixture(scope="session")
def test_settings(tmp_path_factory: pytest.TempPathFactory) -> Settings:
    """Create test settings with temporary data directory."""
    # Create a temporary data directory for tests
    test_data_dir = tmp_path_factory.mktemp("test_data")
    
    os.environ["PRODUCTHUNT_TOKEN"] = "test_token_12345678"
    os.environ["KAGGLE_USERNAME"] = "test_user"
    os.environ["KAGGLE_KEY"] = "test_key"
    os.environ["DATA_DIR"] = str(test_data_dir)

    return Settings()  # type: ignore[call-arg]


@pytest.fixture
def temp_db_path() -> Generator[Path, None, None]:
    """Create temporary database file with unique name."""
    import uuid
    # Create a unique temp file for each test
    temp_dir = Path(tempfile.gettempdir())
    db_path = temp_dir / f"test_producthunt_{uuid.uuid4().hex[:8]}.db"
    
    # Ensure it doesn't exist before starting
    if db_path.exists():
        db_path.unlink()

    yield db_path

    # Cleanup - force remove with retries
    if db_path.exists():
        try:
            db_path.unlink()
        except (PermissionError, OSError):
            # File might be locked, try again after a brief delay
            import time
            time.sleep(0.1)
            try:
                db_path.unlink()
            except Exception:
                pass  # Best effort cleanup


@pytest.fixture
def test_db_manager(temp_db_path: Path) -> Generator[DatabaseManager, None, None]:
    """Create test database manager with temporary database."""
    db = DatabaseManager(database_path=temp_db_path)
    db.initialize()

    yield db

    # Cleanup - close all connections and remove file
    try:
        if db.session:
            db.session.rollback()  # Rollback any pending transactions
            db.session.close()
        if db.engine:
            db.engine.dispose()  # Close all connections
    except Exception:
        pass
    
    # Ensure file is deleted
    if temp_db_path.exists():
        try:
            temp_db_path.unlink()
        except Exception:
            pass


@pytest.fixture
def test_session(temp_db_path: Path) -> Generator[Session, None, None]:
    """Create test database session."""
    engine = create_engine(f"sqlite:///{temp_db_path}", echo=False)
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


# =============================================================================
# Mock Data Fixtures
# =============================================================================


@pytest.fixture
def mock_user_data() -> dict[str, Any]:
    """Mock user data from API."""
    return {
        "id": "user123",
        "username": "testuser",
        "name": "Test User",
        "headline": "Building awesome things",
        "twitterUsername": "testuser",
        "websiteUrl": "https://test.com",
        "url": "https://producthunt.com/@testuser",
        "createdAt": "2024-01-01T00:00:00Z",
        "profileImage": "https://example.com/avatar.jpg",
        "coverImage": "https://example.com/cover.jpg",
        "isMaker": True,
        "isFollowing": False,
        "isViewer": False,
    }


@pytest.fixture
def mock_topic_data() -> dict[str, Any]:
    """Mock topic data from API."""
    return {
        "id": "topic123",
        "name": "Productivity",
        "slug": "productivity",
        "description": "Tools to get things done",
        "url": "https://producthunt.com/topics/productivity",
        "createdAt": "2024-01-01T00:00:00Z",
        "followersCount": 5000,
        "postsCount": 1000,
        "isFollowing": False,
        "image": "https://example.com/topic.jpg",
    }


@pytest.fixture
def mock_post_data(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Mock post data from API."""
    return {
        "id": "post123",
        "userId": "user123",
        "name": "Awesome Product",
        "tagline": "The best thing ever",
        "description": "This is an amazing product that does amazing things.",
        "slug": "awesome-product",
        "url": "https://producthunt.com/posts/awesome-product",
        "website": "https://awesome.com",
        "createdAt": "2024-01-15T10:00:00Z",
        "featuredAt": "2024-01-15T10:00:00Z",
        "commentsCount": 42,
        "votesCount": 123,
        "reviewsRating": 4.5,
        "reviewsCount": 10,
        "isCollected": False,
        "isVoted": False,
        "user": mock_user_data,
        "makers": [mock_user_data],
        "topics": [],
        "thumbnail": {"type": "image", "url": "https://example.com/thumb.jpg"},
        "media": [{"type": "image", "url": "https://example.com/screenshot.jpg"}],
        "productLinks": [{"type": "website", "url": "https://awesome.com"}],
    }


@pytest.fixture
def mock_collection_data(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Mock collection data from API."""
    return {
        "id": "collection123",
        "name": "Best Products 2024",
        "tagline": "Top picks of the year",
        "description": "A curated list of the best products",
        "url": "https://producthunt.com/collections/best-products-2024",
        "coverImage": "https://example.com/collection-cover.jpg",
        "createdAt": "2024-01-01T00:00:00Z",
        "featuredAt": "2024-01-10T00:00:00Z",
        "followersCount": 250,
        "isFollowing": False,
        "userId": "user123",
        "user": mock_user_data,
        "posts": [],
        "topics": [],
    }


@pytest.fixture
def mock_comment_data(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Mock comment data from API."""
    return {
        "id": "comment123",
        "body": "Great product! Really love it.",
        "url": "https://producthunt.com/posts/awesome-product/comments/comment123",
        "createdAt": "2024-01-15T12:00:00Z",
        "isVoted": False,
        "votesCount": 5,
        "user": mock_user_data,
        "parentId": None,
        "parent": None,
        "replies": [],
        "votes": [],
    }


@pytest.fixture
def mock_vote_data(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Mock vote data from API."""
    return {
        "id": "vote123",
        "createdAt": "2024-01-15T11:00:00Z",
        "user": mock_user_data,
        "userId": "user123",
    }


# =============================================================================
# Mock API Response Fixtures
# =============================================================================


@pytest.fixture
def mock_posts_response(mock_post_data: dict[str, Any]) -> dict[str, Any]:
    """Mock GraphQL posts query response."""
    return {
        "posts": {
            "nodes": [mock_post_data],
            "pageInfo": {
                "endCursor": "cursor123",
                "hasNextPage": False,
                "startCursor": "cursor123",
                "hasPreviousPage": False,
            },
        }
    }


@pytest.fixture
def mock_viewer_response(mock_user_data: dict[str, Any]) -> dict[str, Any]:
    """Mock GraphQL viewer query response."""
    return {"viewer": {"user": {**mock_user_data, "isViewer": True}}}


@pytest.fixture
def mock_topics_response(mock_topic_data: dict[str, Any]) -> dict[str, Any]:
    """Mock GraphQL topics query response."""
    return {
        "topics": {
            "nodes": [mock_topic_data],
            "pageInfo": {
                "endCursor": "cursor123",
                "hasNextPage": False,
                "startCursor": "cursor123",
                "hasPreviousPage": False,
            },
        }
    }


# =============================================================================
# Mock Client Fixtures
# =============================================================================


@pytest.fixture
def mock_graphql_client(mocker) -> AsyncGraphQLClient:
    """Create mocked GraphQL client."""
    client = AsyncGraphQLClient(token="test_token")

    # Mock HTTP requests
    mocker.patch.object(
        client,
        "_do_http_post",
        return_value={"data": {}},
    )

    return client


@pytest.fixture
def mock_httpx_response(mocker):
    """Create mock httpx Response."""
    mock_response = mocker.MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        "X-RateLimit-Limit": "100",
        "X-RateLimit-Remaining": "50",
        "X-RateLimit-Reset": "2024-01-15T12:00:00Z",
    }
    mock_response.json.return_value = {"data": {}}
    return mock_response


# =============================================================================
# Database Fixtures with Sample Data
# =============================================================================


@pytest.fixture
def populated_db() -> Generator[DatabaseManager, None, None]:
    """Database manager with sample data - uses its own independent database."""
    import uuid
    # Create a unique temp file for this fixture
    temp_dir = Path(tempfile.gettempdir())
    pop_db_path = temp_dir / f"test_populated_{uuid.uuid4().hex[:8]}.db"
    
    db = DatabaseManager(database_path=pop_db_path)
    db.initialize()
    
    if db.session is None:
        raise RuntimeError("Database not initialized")

    # Add sample user
    user = UserRow(
        id="user123",
        username="testuser",
        name="Test User",
        headline="Building things",
        url="https://producthunt.com/@testuser",
    )
    db.session.add(user)

    # Add sample topic
    topic = TopicRow(
        id="topic123",
        name="Productivity",
        slug="productivity",
        followersCount=5000,
    )
    db.session.add(topic)

    # Add sample post
    post = PostRow(
        id="post123",
        userId="user123",
        name="Test Product",
        tagline="Amazing product",
        url="https://producthunt.com/posts/test",
        commentsCount=10,
        votesCount=50,
        reviewsRating=4.5,
        reviewsCount=5,
        isCollected=False,
        isVoted=False,
    )
    db.session.add(post)

    db.session.commit()

    yield db

    # Cleanup
    try:
        if db.session:
            db.session.rollback()
            db.session.close()
        if db.engine:
            db.engine.dispose()
    except Exception:
        pass
    
    if pop_db_path.exists():
        try:
            pop_db_path.unlink()
        except Exception:
            pass


# =============================================================================
# Utility Fixtures
# =============================================================================


@pytest.fixture
def freeze_time(mocker):
    """Freeze time to a specific datetime."""
    frozen_time = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
    mocker.patch("producthuntdb.utils.utc_now", return_value=frozen_time)
    return frozen_time


@pytest.fixture
def mock_kaggle_api(mocker):
    """Mock Kaggle API."""
    mock_api = MagicMock()
    mock_api.dataset_status.return_value = {"status": "ok"}
    mocker.patch("kaggle.api", mock_api)
    return mock_api


# =============================================================================
# Hypothesis Custom Strategies
# =============================================================================

from hypothesis import strategies as st

# Valid IDs (non-empty strings with reasonable length)
valid_ids = st.text(min_size=1, max_size=50, alphabet=st.characters(blacklist_categories=("Cs",)))

# Valid usernames (alphanumeric with underscores)
valid_usernames = st.text(
    min_size=1,
    max_size=30,
    alphabet=st.characters(whitelist_categories=("L", "N"), whitelist_characters="_-"),
)

# Valid URLs
valid_urls = st.just("https://producthunt.com/") + valid_ids

# Valid datetimes as ISO 8601 strings
valid_datetime_strings = st.datetimes(
    min_value=datetime(2013, 1, 1, tzinfo=timezone.utc),
    max_value=datetime(2030, 12, 31, tzinfo=timezone.utc),
).map(lambda dt: dt.isoformat())

# Valid user data strategy
@st.composite
def user_data_strategy(draw):
    """Generate valid user API response data."""
    user_id = draw(valid_ids)
    return {
        "id": user_id,
        "username": draw(valid_usernames),
        "name": draw(st.text(min_size=1, max_size=100)),
        "headline": draw(st.text(max_size=200) | st.none()),
        "url": draw(valid_urls),
        "createdAt": draw(valid_datetime_strings | st.none()),
    }


# Valid topic data strategy
@st.composite
def topic_data_strategy(draw):
    """Generate valid topic API response data."""
    return {
        "id": draw(valid_ids),
        "name": draw(st.text(min_size=1, max_size=100)),
        "slug": draw(valid_usernames),
        "followersCount": draw(st.integers(min_value=0, max_value=1000000)),
        "url": draw(valid_urls | st.none()),
    }

