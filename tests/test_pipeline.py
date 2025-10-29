"""Unit tests for data pipeline orchestration."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from producthuntdb.pipeline import DataPipeline


class TestDataPipeline:
    """Tests for DataPipeline."""

    def test_pipeline_initialization(self):
        """Test pipeline initialization."""
        pipeline = DataPipeline()

        assert pipeline.client is not None
        assert pipeline.db is not None

    @pytest.mark.asyncio
    async def test_pipeline_initialize(self, temp_db_path):
        """Test pipeline initialization with database."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        assert pipeline.db.engine is not None
        assert pipeline.db.session is not None

        pipeline.close()

    def test_pipeline_close(self):
        """Test pipeline cleanup."""
        pipeline = DataPipeline()
        pipeline.close()

        # Should not raise error

    def test_get_safety_cutoff_with_timestamp(self):
        """Test safety cutoff calculation."""
        pipeline = DataPipeline()

        timestamp = "2024-01-15T10:00:00Z"
        cutoff = pipeline._get_safety_cutoff(timestamp)

        assert cutoff is not None
        assert cutoff < datetime(2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc)

    def test_get_safety_cutoff_none(self):
        """Test safety cutoff with None."""
        pipeline = DataPipeline()

        cutoff = pipeline._get_safety_cutoff(None)
        assert cutoff is None

    @pytest.mark.asyncio
    async def test_verify_authentication_success(self, mocker, mock_viewer_response):
        """Test successful authentication verification."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_viewer",
            AsyncMock(return_value=mock_viewer_response["viewer"]),
        )

        result = await pipeline.verify_authentication()

        assert result["user"]["username"] == "testuser"

        pipeline.close()

    @pytest.mark.asyncio
    async def test_verify_authentication_failure(self, mocker):
        """Test authentication verification failure."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_viewer",
            AsyncMock(return_value={}),
        )

        with pytest.raises(RuntimeError) as exc_info:
            await pipeline.verify_authentication()

        assert "authenticate" in str(exc_info.value).lower()

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_no_posts(self, mocker):
        """Test syncing posts when none available."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(return_value={"nodes": [], "pageInfo": {"hasNextPage": False}}),
        )

        stats = await pipeline.sync_posts(max_pages=1)

        assert stats["posts"] == 0
        assert stats["pages"] == 0

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_with_data(self, mocker, mock_posts_response, mock_post_data):
        """Test syncing posts with data."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(return_value=mock_posts_response["posts"]),
        )

        stats = await pipeline.sync_posts(max_pages=1)

        assert stats["posts"] == 1
        assert stats["users"] >= 1
        assert stats["pages"] == 1

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_max_pages_limit(self, mocker, mock_posts_response):
        """Test sync_posts respects max_pages limit."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        # Mock infinite pages
        infinite_response = {**mock_posts_response["posts"], "pageInfo": {"hasNextPage": True, "endCursor": "cursor"}}
        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(return_value=infinite_response),
        )

        stats = await pipeline.sync_posts(max_pages=2)

        assert stats["pages"] == 2

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_topics(self, mocker, mock_topics_response):
        """Test syncing topics."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_topics_page",
            AsyncMock(return_value=mock_topics_response["topics"]),
        )

        stats = await pipeline.sync_topics(max_pages=1)

        assert stats["topics"] == 1
        assert stats["pages"] == 1

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_all(self, mocker, mock_viewer_response, mock_posts_response, mock_topics_response):
        """Test syncing all entities."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_viewer",
            AsyncMock(return_value=mock_viewer_response["viewer"]),
        )
        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(return_value=mock_posts_response["posts"]),
        )
        mocker.patch.object(
            pipeline.client,
            "fetch_topics_page",
            AsyncMock(return_value=mock_topics_response["topics"]),
        )
        mocker.patch.object(
            pipeline.client,
            "fetch_collections_page",
            AsyncMock(return_value={"nodes": [], "pageInfo": {"hasNextPage": False}}),
        )

        stats = await pipeline.sync_all(max_pages=1)

        assert "posts" in stats
        assert "topics" in stats
        assert "collections" in stats
        assert stats["total_entities"] >= 0

        pipeline.close()

    def test_get_statistics(self, populated_db):
        """Test getting database statistics."""
        pipeline = DataPipeline(db=populated_db)

        stats = pipeline.get_statistics()

        assert "posts" in stats
        assert "users" in stats
        assert "topics" in stats
        assert stats["posts"] == 1
        assert stats["users"] == 1


class TestPipelineErrorHandling:
    """Tests for pipeline error handling."""

    @pytest.mark.asyncio
    async def test_sync_posts_handles_validation_error(self, mocker):
        """Test that sync_posts handles validation errors gracefully."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        # Mock response with invalid data
        bad_response = {
            "nodes": [{"id": "post123"}],  # Missing required fields
            "pageInfo": {"hasNextPage": False},
        }
        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(return_value=bad_response),
        )

        stats = await pipeline.sync_posts(max_pages=1)

        assert stats["skipped"] == 1
        assert stats["posts"] == 0

        pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_handles_api_error(self, mocker):
        """Test that sync_posts handles API errors."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        mocker.patch.object(
            pipeline.client,
            "fetch_posts_page",
            AsyncMock(side_effect=Exception("API Error")),
        )

        stats = await pipeline.sync_posts(max_pages=1)

        assert stats["posts"] == 0

        pipeline.close()


class TestPipelineFullCoverage:
    """Tests to achieve full pipeline coverage."""

    @pytest.mark.asyncio
    async def test_sync_collections_with_data(self, mocker):
        """Test syncing collections with actual data."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # Create user for collection
            pipeline.db.upsert_user({
                "id": "user123",
                "username": "test",
                "name": "Test User",
            })

            mock_collection = {
                "id": "coll123",
                "name": "Test Collection",
                "tagline": "Great stuff",
                "url": "https://test.com",
                "followersCount": 100,
                "isFollowing": False,
                "userId": "user123",
                "user": {
                    "id": "user123",
                    "username": "test",
                    "name": "Test User",
                },
                "posts": [],
                "topics": [],
            }

            mock_response = {
                "nodes": [mock_collection],
                "pageInfo": {"hasNextPage": False},
            }

            mocker.patch.object(
                pipeline.client,
                "fetch_collections_page",
                AsyncMock(return_value=mock_response),
            )

            stats = await pipeline.sync_collections(max_pages=1)

            assert stats["collections"] >= 1
            assert stats["pages"] == 1

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_with_topics_and_makers(self, mocker):
        """Test syncing posts with topics and makers."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            mock_user = {
                "id": "user123",
                "username": "testuser",
                "name": "Test User",
            }

            mock_topic = {
                "id": "topic123",
                "name": "Productivity",
                "slug": "productivity",
            }

            mock_post = {
                "id": "post456",
                "userId": "user123",
                "name": "Amazing Product",
                "tagline": "Best ever",
                "url": "https://test.com",
                "commentsCount": 10,
                "votesCount": 50,
                "reviewsRating": 4.5,
                "reviewsCount": 5,
                "isCollected": False,
                "isVoted": False,
                "createdAt": "2024-01-15T10:00:00Z",
                "thumbnail": {"type": "image", "url": "https://example.com/thumb.jpg"},
                "media": [{"type": "image", "url": "https://example.com/media.jpg"}],
                "productLinks": [{"type": "website", "url": "https://test.com"}],
                "user": mock_user,
                "makers": [mock_user],
                "topics": [mock_topic],
            }

            mock_response = {
                "nodes": [mock_post],
                "pageInfo": {"hasNextPage": False, "endCursor": "cursor123"},
            }

            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                AsyncMock(return_value=mock_response),
            )

            stats = await pipeline.sync_posts(max_pages=1)

            assert stats["posts"] >= 1
            assert stats["users"] >= 1
            assert stats["topics"] >= 1

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_incremental_with_cutoff(self, mocker):
        """Test incremental sync with safety cutoff."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # Set initial crawl state
            pipeline.db.update_crawl_state("posts", "2024-01-15T09:00:00Z")

            mock_post = {
                "id": "post789",
                "userId": "user456",
                "name": "New Product",
                "tagline": "Fresh",
                "url": "https://test.com",
                "commentsCount": 5,
                "votesCount": 25,
                "reviewsRating": 4.0,
                "reviewsCount": 3,
                "isCollected": False,
                "isVoted": False,
                "createdAt": "2024-01-15T10:00:00Z",
                "thumbnail": {"type": "image", "url": "https://test.com/thumb.jpg"},
                "media": [{"type": "image", "url": "https://test.com/media.jpg"}],
                "productLinks": [{"type": "website", "url": "https://test.com"}],
                "user": {
                    "id": "user456",
                    "username": "newuser",
                    "name": "New User",
                },
                "makers": [],
                "topics": [],
            }

            mock_response = {
                "nodes": [mock_post],
                "pageInfo": {"hasNextPage": False},
            }

            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                AsyncMock(return_value=mock_response),
            )

            stats = await pipeline.sync_posts(full_refresh=False, max_pages=1)

            assert stats["posts"] >= 1

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_topics_with_mock_data(self, mocker):
        """Test syncing topics with mock data."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            mock_topic = {
                "id": "topic456",
                "name": "AI",
                "slug": "ai",
                "followersCount": 10000,
                "createdAt": "2024-01-01T00:00:00Z",
            }

            mock_response = {
                "nodes": [mock_topic],
                "pageInfo": {"hasNextPage": False},
            }

            mocker.patch.object(
                pipeline.client,
                "fetch_topics_page",
                AsyncMock(return_value=mock_response),
            )

            stats = await pipeline.sync_topics(max_pages=1)

            assert stats["topics"] >= 1

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_all_with_multiple_pages(self, mocker):
        """Test sync_all with multiple pages."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # Mock viewer
            mocker.patch.object(
                pipeline.client,
                "fetch_viewer",
                AsyncMock(return_value={"user": {"id": "viewer1", "username": "viewer", "name": "Viewer"}}),
            )

            # Mock posts
            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                AsyncMock(return_value={"nodes": [], "pageInfo": {"hasNextPage": False}}),
            )

            # Mock topics
            mocker.patch.object(
                pipeline.client,
                "fetch_topics_page",
                AsyncMock(return_value={"nodes": [], "pageInfo": {"hasNextPage": False}}),
            )

            # Mock collections
            mocker.patch.object(
                pipeline.client,
                "fetch_collections_page",
                AsyncMock(return_value={"nodes": [], "pageInfo": {"hasNextPage": False}}),
            )

            stats = await pipeline.sync_all(
                max_pages=2,
                full_refresh=True,
            )

            assert "total_entities" in stats
            assert stats["total_entities"] >= 0

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_posts_multi_page(self, mocker):
        """Test syncing posts with multiple pages."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # First page with hasNextPage=True
            first_post = {
                "id": "post_page1",
                "userId": "u1",
                "name": "First Post",
                "tagline": "Tag",
                "url": "https://test.com",
                "commentsCount": 0,
                "votesCount": 0,
                "reviewsRating": 0.0,
                "reviewsCount": 0,
                "isCollected": False,
                "isVoted": False,
                "createdAt": "2024-01-15T10:00:00Z",
                "thumbnail": {"type": "image", "url": "https://test.com/thumb.jpg"},
                "media": [{"type": "image", "url": "https://test.com/media.jpg"}],
                "productLinks": [{"type": "website", "url": "https://test.com"}],
                "user": {"id": "u1", "username": "user", "name": "User"},
                "makers": [],
                "topics": [],
            }

            second_post = {
                **first_post,
                "id": "post_page2",
                "name": "Second Post",
            }

            call_count = 0

            async def mock_fetch(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "nodes": [first_post],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    }
                else:
                    return {
                        "nodes": [second_post],
                        "pageInfo": {"hasNextPage": False, "endCursor": "cursor2"},
                    }

            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                AsyncMock(side_effect=mock_fetch),
            )

            stats = await pipeline.sync_posts(max_pages=2)

            assert stats["posts"] >= 2
            assert stats["pages"] == 2

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_topics_multi_page(self, mocker):
        """Test syncing topics with multiple pages."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            first_topic = {
                "id": "topic1",
                "name": "Topic 1",
                "slug": "topic-1",
            }

            second_topic = {
                "id": "topic2",
                "name": "Topic 2",
                "slug": "topic-2",
            }

            call_count = 0

            async def mock_fetch(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "nodes": [first_topic],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    }
                else:
                    return {
                        "nodes": [second_topic],
                        "pageInfo": {"hasNextPage": False},
                    }

            mocker.patch.object(
                pipeline.client,
                "fetch_topics_page",
                AsyncMock(side_effect=mock_fetch),
            )

            stats = await pipeline.sync_topics(max_pages=2)

            assert stats["topics"] >= 2

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_sync_collections_multi_page(self, mocker):
        """Test syncing collections with multiple pages."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            pipeline.db.upsert_user({"id": "u1", "username": "user", "name": "User"})

            first_coll = {
                "id": "coll1",
                "name": "Collection 1",
                "tagline": "Tag",
                "url": "https://test.com",
                "followersCount": 100,
                "isFollowing": False,
                "userId": "u1",
                "user": {"id": "u1", "username": "user", "name": "User"},
                "posts": [],
                "topics": [],
            }

            second_coll = {
                **first_coll,
                "id": "coll2",
                "name": "Collection 2",
            }

            call_count = 0

            async def mock_fetch(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return {
                        "nodes": [first_coll],
                        "pageInfo": {"hasNextPage": True, "endCursor": "cursor1"},
                    }
                else:
                    return {
                        "nodes": [second_coll],
                        "pageInfo": {"hasNextPage": False},
                    }

            mocker.patch.object(
                pipeline.client,
                "fetch_collections_page",
                AsyncMock(side_effect=mock_fetch),
            )

            stats = await pipeline.sync_collections(max_pages=2)

            assert stats["collections"] >= 2

        finally:
            pipeline.close()


class TestPipelineStatistics:
    """Tests for pipeline statistics."""

    def test_get_statistics_empty_db(self, temp_db_path):
        """Test statistics with empty database."""
        from producthuntdb.io import DatabaseManager
        db = DatabaseManager(database_path=temp_db_path)
        db.initialize()

        pipeline = DataPipeline(db=db)

        stats = pipeline.get_statistics()

        assert stats["posts"] == 0
        assert stats["users"] == 0
        assert stats["topics"] == 0

        db.close()

    def test_get_statistics_with_data(self, temp_db_path):
        """Test statistics with actual data."""
        from producthuntdb.io import DatabaseManager
        db = DatabaseManager(database_path=temp_db_path)
        db.initialize()

        # Add data
        db.upsert_user({"id": "u1", "username": "u1", "name": "U1"})
        db.upsert_user({"id": "u2", "username": "u2", "name": "U2"})
        db.upsert_topic({"id": "t1", "name": "T1", "slug": "t1"})

        pipeline = DataPipeline(db=db)

        stats = pipeline.get_statistics()

        assert stats["users"] == 2
        assert stats["topics"] == 1

        db.close()


class TestAsyncOperations:
    """Tests for async operations."""

    @pytest.mark.asyncio
    async def test_pipeline_initialization_twice(self):
        """Test initializing pipeline twice."""
        pipeline = DataPipeline()

        await pipeline.initialize()
        await pipeline.initialize()  # Should handle gracefully

        pipeline.close()

    @pytest.mark.asyncio
    async def test_pipeline_close_without_init(self):
        """Test closing pipeline without initialization."""
        pipeline = DataPipeline()

        # Should not crash
        pipeline.close()
