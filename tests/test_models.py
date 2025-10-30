"""Unit tests for data models (Pydantic and SQLModel)."""

from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from producthuntdb.models import (
    Collection,
    CollectionRow,
    Comment,
    Error,
    PageInfo,
    Post,
    PostRow,
    Topic,
    TopicRow,
    User,
    UserRow,
    Viewer,
    Vote,
    VoteRow,
)


class TestPageInfo:
    """Tests for PageInfo model."""

    def test_pageinfo_required_fields(self):
        """Test PageInfo with required fields only."""
        page_info = PageInfo(hasNextPage=True)

        assert page_info.hasNextPage is True
        assert page_info.startCursor is None
        assert page_info.endCursor is None
        assert page_info.hasPreviousPage is None

    def test_pageinfo_all_fields(self):
        """Test PageInfo with all fields."""
        page_info = PageInfo(
            startCursor="start123",
            endCursor="end123",
            hasNextPage=True,
            hasPreviousPage=False,
        )

        assert page_info.startCursor == "start123"
        assert page_info.endCursor == "end123"
        assert page_info.hasNextPage is True
        assert page_info.hasPreviousPage is False


class TestError:
    """Tests for Error model."""

    def test_error_empty(self):
        """Test Error with no fields."""
        error = Error()

        assert error.code is None
        assert error.message is None

    def test_error_with_fields(self):
        """Test Error with fields."""
        error = Error(code="AUTH_ERROR", message="Invalid token")

        assert error.code == "AUTH_ERROR"
        assert error.message == "Invalid token"


class TestUserModel:
    """Tests for User Pydantic model."""

    def test_user_minimal_fields(self):
        """Test User with minimal required fields."""
        user = User(
            id="user123",
            username="testuser",
            name="Test User",
        )

        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.name == "Test User"
        assert user.createdAt is None

    def test_user_timestamp_parsing(self):
        """Test User timestamp parsing."""
        user = User(
            id="user123",
            username="testuser",
            name="Test User",
            createdAt="2024-01-15T10:00:00Z",
        )

        assert isinstance(user.createdAt, datetime)
        assert user.createdAt.tzinfo == timezone.utc
        assert user.createdAt.year == 2024

    def test_user_all_fields(self, mock_user_data):
        """Test User with all fields."""
        user = User(**mock_user_data)

        assert user.id == "user123"
        assert user.username == "testuser"
        assert user.isMaker is True
        assert user.isFollowing is False


class TestTopicModel:
    """Tests for Topic Pydantic model."""

    def test_topic_minimal_fields(self):
        """Test Topic with minimal fields."""
        topic = Topic(
            id="topic123",
            name="Productivity",
            slug="productivity",
        )

        assert topic.id == "topic123"
        assert topic.name == "Productivity"
        assert topic.slug == "productivity"

    def test_topic_timestamp_parsing(self, mock_topic_data):
        """Test Topic timestamp parsing."""
        topic = Topic(**mock_topic_data)

        assert isinstance(topic.createdAt, datetime)
        assert topic.createdAt.tzinfo == timezone.utc

    def test_topic_all_fields(self, mock_topic_data):
        """Test Topic with all fields."""
        topic = Topic(**mock_topic_data)

        assert topic.followersCount == 5000
        assert topic.postsCount == 1000
        assert topic.isFollowing is False


class TestPostModel:
    """Tests for Post Pydantic model."""

    def test_post_minimal_fields(self):
        """Test Post with minimal required fields."""
        user = User(id="user123", username="test", name="Test")

        post = Post(
            id="post123",
            userId="user123",
            name="Test Product",
            tagline="Amazing",
            url="https://test.com",
            commentsCount=0,
            votesCount=0,
            reviewsRating=0.0,
            reviewsCount=0,
            isCollected=False,
            isVoted=False,
            user=user,
            makers=[],
        )

        assert post.id == "post123"
        assert post.name == "Test Product"

    def test_post_timestamp_parsing(self, mock_post_data):
        """Test Post timestamp parsing."""
        post = Post(**mock_post_data)

        assert isinstance(post.createdAt, datetime)
        assert isinstance(post.featuredAt, datetime)
        assert post.createdAt.tzinfo == timezone.utc

    def test_post_topics_extraction(self):
        """Test Post topics extraction from GraphQL connection."""
        user = User(id="user123", username="test", name="Test")
        topic = Topic(id="topic123", name="Test", slug="test")

        # Test with nodes wrapper (GraphQL connection format)
        post_data = {
            "id": "post123",
            "userId": "user123",
            "name": "Test",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": user.model_dump(),
            "makers": [],
            "topics": {"nodes": [topic.model_dump()]},
        }

        post = Post(**post_data)
        assert len(post.topics) == 1
        assert post.topics[0].id == "topic123"

    def test_post_all_fields(self, mock_post_data):
        """Test Post with all fields."""
        post = Post(**mock_post_data)

        assert post.votesCount == 123
        assert post.reviewsRating == 4.5
        assert len(post.makers) == 1
        assert post.thumbnail is not None
        assert post.media is not None


class TestModelsAdditionalCoverage:
    """Additional tests for full coverage."""

    def test_collection_model(self):
        """Test Collection model creation and serialization."""
        data = {
            "id": "col1",
            "name": "Test Collection",
            "tagline": "A test",
            "url": "https://test.com",
            "followersCount": 10,
            "isFollowing": False,
            "userId": "user1",
        }
        collection = Collection(**data)
        assert collection.id == "col1"
        assert collection.name == "Test Collection"
        assert collection.followersCount == 10

    def test_vote_row_from_pydantic_with_post(self):
        """Test VoteRow.from_pydantic with post_id."""
        vote_data = {
            "id": "vote1",
            "userId": "user1",
            "createdAt": "2024-01-01T00:00:00Z",
        }
        vote = Vote(**vote_data)
        vote_row = VoteRow.from_pydantic(vote, post_id="post1")
        
        assert vote_row.id == "vote1"
        assert vote_row.userId == "user1"
        assert vote_row.post_id == "post1"
        assert vote_row.comment_id is None

    def test_vote_row_from_pydantic_with_comment(self):
        """Test VoteRow.from_pydantic with comment_id."""
        vote_data = {
            "id": "vote2",
            "userId": "user2",
            "createdAt": "2024-01-01T00:00:00Z",
        }
        vote = Vote(**vote_data)
        vote_row = VoteRow.from_pydantic(vote, comment_id="comment1")
        
        assert vote_row.id == "vote2"
        assert vote_row.userId == "user2"
        assert vote_row.post_id is None
        assert vote_row.comment_id == "comment1"


class TestCommentModel:
    """Tests for Comment Pydantic model."""

    def test_comment_minimal_fields(self):
        """Test Comment with minimal fields."""
        user = User(id="user123", username="test", name="Test")

        comment = Comment(
            id="comment123",
            body="Great product!",
            url="https://test.com",
            isVoted=False,
            votesCount=5,
            user=user,
        )

        assert comment.id == "comment123"
        assert comment.body == "Great product!"
        assert comment.votesCount == 5

    def test_comment_timestamp_parsing(self, mock_comment_data):
        """Test Comment timestamp parsing."""
        comment = Comment(**mock_comment_data)

        assert isinstance(comment.createdAt, datetime)


class TestVoteModel:
    """Tests for Vote Pydantic model."""

    def test_vote_minimal_fields(self):
        """Test Vote with minimal fields."""
        vote = Vote(id="vote123", userId="user123")

        assert vote.id == "vote123"
        assert vote.userId == "user123"

    def test_vote_timestamp_parsing(self, mock_vote_data):
        """Test Vote timestamp parsing."""
        vote = Vote(**mock_vote_data)

        assert isinstance(vote.createdAt, datetime)


class TestViewerModel:
    """Tests for Viewer model."""

    def test_viewer(self):
        """Test Viewer model."""
        user = User(id="user123", username="test", name="Test", isViewer=True)
        viewer = Viewer(user=user)

        assert viewer.user.isViewer is True


# =============================================================================
# SQLModel Tests
# =============================================================================


class TestUserRow:
    """Tests for UserRow SQLModel."""

    def test_user_row_creation(self, test_session):
        """Test creating UserRow."""
        user_row = UserRow(
            id="user123",
            username="testuser",
            name="Test User",
        )

        test_session.add(user_row)
        test_session.commit()

        retrieved = test_session.get(UserRow, "user123")
        assert retrieved is not None
        assert retrieved.username == "testuser"

    def test_user_row_from_pydantic(self, mock_user_data):
        """Test creating UserRow from Pydantic User."""
        user = User(**mock_user_data)
        user_row = UserRow.from_pydantic(user)

        assert user_row.id == user.id
        assert user_row.username == user.username
        assert user_row.createdAt is not None


class TestTopicRow:
    """Tests for TopicRow SQLModel."""

    def test_topic_row_creation(self, test_session):
        """Test creating TopicRow."""
        topic_row = TopicRow(
            id="topic123",
            name="Productivity",
            slug="productivity",
        )

        test_session.add(topic_row)
        test_session.commit()

        retrieved = test_session.get(TopicRow, "topic123")
        assert retrieved is not None
        assert retrieved.name == "Productivity"

    def test_topic_row_from_pydantic(self, mock_topic_data):
        """Test creating TopicRow from Pydantic Topic."""
        topic = Topic(**mock_topic_data)
        topic_row = TopicRow.from_pydantic(topic)

        assert topic_row.id == topic.id
        assert topic_row.slug == topic.slug


class TestPostRow:
    """Tests for PostRow SQLModel."""

    def test_post_row_creation(self, test_session):
        """Test creating PostRow."""
        # First create user
        user = UserRow(id="user123", username="test", name="Test")
        test_session.add(user)
        test_session.commit()

        post_row = PostRow(
            id="post123",
            userId="user123",
            name="Test Product",
            tagline="Amazing",
            url="https://test.com",
            commentsCount=10,
            votesCount=50,
            reviewsRating=4.5,
            reviewsCount=5,
            isCollected=False,
            isVoted=False,
        )

        test_session.add(post_row)
        test_session.commit()

        retrieved = test_session.get(PostRow, "post123")
        assert retrieved is not None
        assert retrieved.name == "Test Product"
        assert retrieved.votesCount == 50

    def test_post_row_from_pydantic(self, mock_post_data):
        """Test creating PostRow from Pydantic Post."""
        post = Post(**mock_post_data)
        post_row = PostRow.from_pydantic(post)

        assert post_row.id == post.id
        assert post_row.name == post.name
        assert post_row.votesCount == post.votesCount


class TestCollectionRow:
    """Tests for CollectionRow SQLModel."""

    def test_collection_row_creation(self, test_session):
        """Test creating CollectionRow."""
        # First create user
        user = UserRow(id="user123", username="test", name="Test")
        test_session.add(user)
        test_session.commit()

        collection_row = CollectionRow(
            id="coll123",
            name="Best Products",
            tagline="Top picks",
            url="https://test.com",
            followersCount=100,
            isFollowing=False,
            userId="user123",
        )

        test_session.add(collection_row)
        test_session.commit()

        retrieved = test_session.get(CollectionRow, "coll123")
        assert retrieved is not None
        assert retrieved.followersCount == 100

    def test_collection_row_from_pydantic(self, mock_collection_data):
        """Test creating CollectionRow from Pydantic Collection."""
        collection = Collection(**mock_collection_data)
        collection_row = CollectionRow.from_pydantic(collection)

        assert collection_row.id == collection.id
        assert collection_row.followersCount == collection.followersCount


class TestVoteRow:
    """Tests for VoteRow SQLModel."""

    def test_vote_row_creation(self, test_session):
        """Test creating VoteRow."""
        # Create dependencies
        user = UserRow(id="user123", username="test", name="Test")
        test_session.add(user)
        test_session.commit()

        vote_row = VoteRow(
            id="vote123",
            userId="user123",
            post_id="post123",
        )

        test_session.add(vote_row)
        test_session.commit()

        retrieved = test_session.get(VoteRow, "vote123")
        assert retrieved is not None
        assert retrieved.userId == "user123"


# =============================================================================
# Model Validation Tests
# =============================================================================


class TestModelValidation:
    """Tests for model validation."""

    def test_user_missing_required_fields(self):
        """Test User validation with missing fields."""
        with pytest.raises(ValidationError):
            User(id="user123")  # Missing username and name

    def test_post_missing_required_fields(self):
        """Test Post validation with missing fields."""
        with pytest.raises(ValidationError):
            Post(id="post123")  # Missing many required fields

    def test_invalid_timestamp_format(self):
        """Test invalid timestamp raises error."""
        with pytest.raises(ValidationError):
            User(
                id="user123",
                username="test",
                name="Test",
                createdAt="not-a-date",
            )

    def test_extra_fields_ignored(self):
        """Test that extra fields are ignored."""
        user = User(
            id="user123",
            username="test",
            name="Test",
            extra_field="should_be_ignored",  # type: ignore[call-arg]
        )

        assert user.id == "user123"
        assert not hasattr(user, "extra_field")


# =============================================================================
# Model Serialization Tests
# =============================================================================


class TestModelSerialization:
    """Tests for model serialization."""

    def test_user_model_dump(self, mock_user_data):
        """Test User model_dump."""
        user = User(**mock_user_data)
        dumped = user.model_dump()

        assert isinstance(dumped, dict)
        assert dumped["id"] == "user123"
        assert dumped["username"] == "testuser"

    def test_post_model_dump(self, mock_post_data):
        """Test Post model_dump."""
        post = Post(**mock_post_data)
        dumped = post.model_dump()

        assert isinstance(dumped, dict)
        assert dumped["id"] == "post123"
        assert "user" in dumped
        assert "makers" in dumped

    def test_model_json_serialization(self, mock_user_data):
        """Test model JSON serialization."""
        user = User(**mock_user_data)
        json_str = user.model_dump_json()

        assert isinstance(json_str, str)
        assert "user123" in json_str
        assert "testuser" in json_str


class TestModelsCoverage:
    """Tests to improve models coverage."""

    def test_collection_model(self, mock_collection_data):
        """Test Collection model."""
        collection = Collection(**mock_collection_data)

        assert collection.id == "collection123"
        assert collection.followersCount == 250

    def test_post_topics_extraction_dict(self):
        """Test Post _extract_topics_nodes with dict."""
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "topics": {"nodes": [{"id": "topic1", "name": "Tech", "slug": "tech"}]},
        }
        post = Post(**post_data)
        assert post.topics is not None
        assert len(post.topics) == 1
        assert post.topics[0].name == "Tech"

    def test_post_topics_extraction_list(self):
        """Test Post _extract_topics_nodes with list."""
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "topics": [{"id": "topic1", "name": "Tech", "slug": "tech"}],
        }
        post = Post(**post_data)
        assert post.topics is not None
        assert len(post.topics) == 1

    def test_post_thumbnail_media_object(self):
        """Test Post _coerce_thumbnail with Media object."""
        from producthuntdb.models import Media

        media = Media(type="image", url="https://test.com/img.jpg")
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "thumbnail": media,
        }
        post = Post(**post_data)
        assert post.thumbnail is not None
        assert post.thumbnail.url == "https://test.com/img.jpg"

    def test_post_thumbnail_dict(self):
        """Test Post _coerce_thumbnail with dict."""
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "thumbnail": {"type": "image", "url": "https://test.com/img.jpg"},
        }
        post = Post(**post_data)
        assert post.thumbnail is not None
        assert post.thumbnail.url == "https://test.com/img.jpg"

    def test_post_media_list_coercion(self):
        """Test Post _coerce_media with list of dicts."""
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "media": [
                {"type": "image", "url": "https://test.com/img1.jpg"},
                {"type": "image", "url": "https://test.com/img2.jpg"},
            ],
        }
        post = Post(**post_data)
        assert post.media is not None
        assert len(post.media) == 2
        assert post.media[0].url == "https://test.com/img1.jpg"

    def test_post_media_none(self):
        """Test Post _coerce_media with None."""
        post_data = {
            "id": "post1",
            "userId": "user1",
            "name": "Test Post",
            "tagline": "Test",
            "url": "https://test.com",
            "commentsCount": 0,
            "votesCount": 0,
            "reviewsRating": 0.0,
            "reviewsCount": 0,
            "isCollected": False,
            "isVoted": False,
            "user": {"id": "user1", "username": "testuser", "name": "Test User"},
            "makers": [],
            "media": None,
        }
        post = Post(**post_data)
        assert post.media is None

