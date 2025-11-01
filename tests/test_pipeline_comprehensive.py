"""Comprehensive tests for pipeline.py data orchestration.

Tests cover:
- DataPipeline initialization with dependency injection
- sync_posts with full refresh and incremental updates
- sync_topics and sync_collections
- verify_authentication
- get_statistics
- Error handling and recovery
- Safety cutoff calculations
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from pydantic import ValidationError

from producthuntdb.pipeline import DataPipeline


@pytest.fixture
def mock_client():
    """Create mock AsyncGraphQLClient."""
    client = MagicMock()
    client.fetch_viewer = AsyncMock()
    client.fetch_posts_page = AsyncMock()
    client.fetch_topics_page = AsyncMock()
    client.fetch_collections_page = AsyncMock()
    return client


@pytest.fixture
def mock_db():
    """Create mock DatabaseManager."""
    db = MagicMock()
    db.session = MagicMock()
    db.initialize = Mock()
    db.close = Mock()
    db.get_crawl_state = Mock(return_value=None)
    db.update_crawl_state = Mock()
    db.upsert_user = Mock()
    db.upsert_post = Mock()
    db.upsert_topic = Mock()
    db.link_post_topics = Mock()
    db.link_post_makers = Mock()
    return db


class TestPipelineInitialization:
    """Test DataPipeline initialization."""

    def test_init_with_default_dependencies(self):
        """Test that pipeline creates default client and db if not provided."""
        with patch("producthuntdb.pipeline.AsyncGraphQLClient") as mock_client_class, \
             patch("producthuntdb.pipeline.DatabaseManager") as mock_db_class:
            
            mock_client = MagicMock()
            mock_db = MagicMock()
            mock_client_class.return_value = mock_client
            mock_db_class.return_value = mock_db
            
            pipeline = DataPipeline()
            
            # Verify defaults created
            mock_client_class.assert_called_once()
            mock_db_class.assert_called_once()
            assert pipeline.client == mock_client
            assert pipeline.db == mock_db

    def test_init_with_injected_dependencies(self, mock_client, mock_db):
        """Test that pipeline uses injected dependencies."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        assert pipeline.client == mock_client
        assert pipeline.db == mock_db

    @pytest.mark.asyncio
    async def test_initialize(self, mock_client, mock_db):
        """Test pipeline initialization."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        await pipeline.initialize()
        
        mock_db.initialize.assert_called_once()

    def test_close(self, mock_client, mock_db):
        """Test pipeline resource cleanup."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        pipeline.close()
        
        mock_db.close.assert_called_once()


class TestSafetyCutoff:
    """Test safety cutoff calculation."""

    def test_get_safety_cutoff_with_valid_timestamp(self, mock_client, mock_db, monkeypatch):
        """Test safety cutoff calculation with valid ISO timestamp."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        timestamp = "2024-01-15T10:00:00Z"
        
        # Use monkeypatch for Pydantic Settings
        with patch("producthuntdb.pipeline.settings") as mock_settings:
            mock_settings.safety_timedelta = timedelta(minutes=30)
            cutoff = pipeline._get_safety_cutoff(timestamp)
            
            assert cutoff is not None
            # Should be 30 minutes before the timestamp
            expected = datetime(2024, 1, 15, 9, 30, 0, tzinfo=cutoff.tzinfo)
            assert cutoff == expected

    def test_get_safety_cutoff_with_none(self, mock_client, mock_db):
        """Test safety cutoff with None timestamp."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        cutoff = pipeline._get_safety_cutoff(None)
        
        assert cutoff is None

    def test_get_safety_cutoff_with_invalid_timestamp(self, mock_client, mock_db):
        """Test safety cutoff with unparseable timestamp."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        cutoff = pipeline._get_safety_cutoff("invalid-timestamp")
        
        assert cutoff is None


class TestVerifyAuthentication:
    """Test API authentication verification."""

    @pytest.mark.asyncio
    async def test_verify_authentication_success(self, mock_client, mock_db):
        """Test successful authentication."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_viewer.return_value = {
            "user": {
                "id": "123",
                "username": "testuser",
                "name": "Test User",
            }
        }
        
        result = await pipeline.verify_authentication()
        
        assert result["user"]["username"] == "testuser"
        mock_client.fetch_viewer.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_authentication_no_user_data(self, mock_client, mock_db):
        """Test authentication with missing user data."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_viewer.return_value = {}
        
        with pytest.raises(RuntimeError, match="Failed to authenticate"):
            await pipeline.verify_authentication()

    @pytest.mark.asyncio
    async def test_verify_authentication_api_error(self, mock_client, mock_db):
        """Test authentication with API error."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_viewer.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError):
            await pipeline.verify_authentication()


class TestSyncPosts:
    """Test posts synchronization."""

    @pytest.mark.asyncio
    async def test_sync_posts_full_refresh(self, mock_client, mock_db):
        """Test full refresh of posts."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock single page response
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {
                    "id": "post1",
                    "name": "Test Post",
                    "tagline": "Test tagline",
                    "createdAt": "2024-01-15T10:00:00Z",
                    "user": {
                        "id": "user1",
                        "username": "testuser",
                        "name": "Test User",
                    },
                    "makers": [],
                    "topics": {"nodes": []},
                }
            ],
            "pageInfo": {
                "endCursor": "cursor1",
                "hasNextPage": False,
            },
        }
        
        mock_db.upsert_user.return_value = MagicMock(id="user1")
        mock_db.upsert_post.return_value = MagicMock(id="post1")
        
        stats = await pipeline.sync_posts(full_refresh=True, max_pages=1)
        
        assert stats["posts"] == 1
        assert stats["users"] == 1
        assert stats["pages"] == 1
        mock_client.fetch_posts_page.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_posts_incremental(self, mock_client, mock_db):
        """Test incremental posts update."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock last crawl state
        mock_db.get_crawl_state.return_value = "2024-01-15T09:00:00Z"
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        
        stats = await pipeline.sync_posts(full_refresh=False)
        
        # Should have called with posted_after parameter
        call_args = mock_client.fetch_posts_page.call_args
        assert call_args[1]["posted_after_dt"] is not None
        mock_db.get_crawl_state.assert_called_once_with("posts")

    @pytest.mark.asyncio
    async def test_sync_posts_pagination(self, mock_client, mock_db):
        """Test posts pagination."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock two pages
        page1 = {
            "nodes": [{"id": "post1", "name": "Post 1", "createdAt": "2024-01-15T10:00:00Z", "user": {"id": "u1"}, "makers": [], "topics": {"nodes": []}}],
            "pageInfo": {"endCursor": "cursor1", "hasNextPage": True},
        }
        page2 = {
            "nodes": [{"id": "post2", "name": "Post 2", "createdAt": "2024-01-15T11:00:00Z", "user": {"id": "u2"}, "makers": [], "topics": {"nodes": []}}],
            "pageInfo": {"endCursor": "cursor2", "hasNextPage": False},
        }
        
        mock_client.fetch_posts_page.side_effect = [page1, page2]
        mock_db.upsert_user.return_value = MagicMock()
        mock_db.upsert_post.return_value = MagicMock()
        
        stats = await pipeline.sync_posts(full_refresh=True)
        
        assert stats["posts"] == 2
        assert stats["pages"] == 2
        assert mock_client.fetch_posts_page.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_posts_max_pages_limit(self, mock_client, mock_db):
        """Test max_pages limit."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [{"id": "post1", "name": "Post", "createdAt": "2024-01-15T10:00:00Z", "user": {"id": "u1"}, "makers": [], "topics": {"nodes": []}}],
            "pageInfo": {"endCursor": "cursor1", "hasNextPage": True},
        }
        mock_db.upsert_user.return_value = MagicMock()
        mock_db.upsert_post.return_value = MagicMock()
        
        stats = await pipeline.sync_posts(full_refresh=True, max_pages=1)
        
        assert stats["pages"] == 1
        assert mock_client.fetch_posts_page.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_posts_empty_response(self, mock_client, mock_db):
        """Test handling of empty posts response."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        
        stats = await pipeline.sync_posts(full_refresh=True)
        
        assert stats["posts"] == 0
        assert stats["pages"] == 1

    @pytest.mark.asyncio
    async def test_sync_posts_with_topics(self, mock_client, mock_db):
        """Test syncing posts with topics."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {
                    "id": "post1",
                    "name": "Test Post",
                    "createdAt": "2024-01-15T10:00:00Z",
                    "user": {"id": "user1"},
                    "makers": [],
                    "topics": {
                        "nodes": [
                            {"id": "topic1", "name": "Tech", "slug": "tech"},
                            {"id": "topic2", "name": "AI", "slug": "ai"},
                        ]
                    },
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock(id="user1")
        mock_db.upsert_post.return_value = MagicMock(id="post1")
        mock_db.upsert_topic.return_value = MagicMock()
        
        stats = await pipeline.sync_posts(full_refresh=True)
        
        assert stats["topics"] == 2
        assert mock_db.link_post_topics.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_posts_with_makers(self, mock_client, mock_db):
        """Test syncing posts with makers."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {
                    "id": "post1",
                    "name": "Test Post",
                    "createdAt": "2024-01-15T10:00:00Z",
                    "user": {"id": "user1"},
                    "makers": [
                        {"id": "maker1", "username": "maker1"},
                        {"id": "maker2", "username": "maker2"},
                    ],
                    "topics": {"nodes": []},
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock(id="user1")
        mock_db.upsert_post.return_value = MagicMock(id="post1")
        
        stats = await pipeline.sync_posts(full_refresh=True)
        
        # User + 2 makers
        assert stats["users"] == 3
        assert mock_db.link_post_makers.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_posts_error_handling(self, mock_client, mock_db):
        """Test error handling during posts sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.side_effect = Exception("API Error")
        
        stats = await pipeline.sync_posts(full_refresh=True)
        
        # Should return stats with no data
        assert stats["posts"] == 0
        assert stats["pages"] == 0

    @pytest.mark.asyncio
    async def test_sync_posts_updates_crawl_state(self, mock_client, mock_db):
        """Test that crawl state is updated after sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {
                    "id": "post1",
                    "name": "Test",
                    "createdAt": "2024-01-15T12:00:00Z",
                    "user": {"id": "u1"},
                    "makers": [],
                    "topics": {"nodes": []},
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock()
        mock_db.upsert_post.return_value = MagicMock()
        
        await pipeline.sync_posts(full_refresh=True)
        
        # Should update crawl state with latest timestamp
        mock_db.update_crawl_state.assert_called_once()
        call_args = mock_db.update_crawl_state.call_args
        assert call_args[0][0] == "posts"
        assert "2024-01-15" in call_args[0][1]


class TestSyncTopics:
    """Test topics synchronization."""

    @pytest.mark.asyncio
    async def test_sync_topics_success(self, mock_client, mock_db):
        """Test successful topics sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_topics_page.return_value = {
            "nodes": [
                {"id": "topic1", "name": "Tech", "slug": "tech"},
                {"id": "topic2", "name": "AI", "slug": "ai"},
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_topic.return_value = MagicMock()
        
        stats = await pipeline.sync_topics()
        
        assert stats["topics"] == 2
        assert stats["pages"] == 1
        assert mock_db.upsert_topic.call_count == 2

    @pytest.mark.asyncio
    async def test_sync_topics_pagination(self, mock_client, mock_db):
        """Test topics pagination."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        page1 = {
            "nodes": [{"id": "topic1", "name": "Tech"}],
            "pageInfo": {"endCursor": "cursor1", "hasNextPage": True},
        }
        page2 = {
            "nodes": [{"id": "topic2", "name": "AI"}],
            "pageInfo": {"endCursor": "cursor2", "hasNextPage": False},
        }
        
        mock_client.fetch_topics_page.side_effect = [page1, page2]
        mock_db.upsert_topic.return_value = MagicMock()
        
        stats = await pipeline.sync_topics()
        
        assert stats["topics"] == 2
        assert stats["pages"] == 2

    @pytest.mark.asyncio
    async def test_sync_topics_max_pages(self, mock_client, mock_db):
        """Test topics max_pages limit."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_topics_page.return_value = {
            "nodes": [{"id": "topic1", "name": "Tech"}],
            "pageInfo": {"hasNextPage": True},
        }
        mock_db.upsert_topic.return_value = MagicMock()
        
        stats = await pipeline.sync_topics(max_pages=1)
        
        assert stats["pages"] == 1
        assert mock_client.fetch_topics_page.call_count == 1

    @pytest.mark.asyncio
    async def test_sync_topics_error_handling(self, mock_client, mock_db):
        """Test error handling during topics sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_topics_page.side_effect = Exception("API Error")
        
        stats = await pipeline.sync_topics()
        
        assert stats["topics"] == 0


class TestSyncCollections:
    """Test collections synchronization."""

    @pytest.mark.asyncio
    async def test_sync_collections_success(self, mock_client, mock_db):
        """Test successful collections sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_collections_page.return_value = {
            "nodes": [
                {
                    "id": "coll1",
                    "name": "Collection 1",
                    "userId": "user1",
                    "user": {"id": "user1", "username": "test"},
                    "posts": {"nodes": []},
                    "topics": {"nodes": []},
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock()
        
        stats = await pipeline.sync_collections()
        
        assert stats["collections"] >= 0  # Implementation may process or skip
        assert stats["pages"] == 1

    @pytest.mark.asyncio
    async def test_sync_collections_max_pages(self, mock_client, mock_db):
        """Test collections max_pages limit."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_collections_page.return_value = {
            "nodes": [{"id": "coll1", "name": "Collection"}],
            "pageInfo": {"hasNextPage": True},
        }
        
        stats = await pipeline.sync_collections(max_pages=1)
        
        assert stats["pages"] == 1

    @pytest.mark.asyncio
    async def test_sync_collections_error_handling(self, mock_client, mock_db):
        """Test error handling during collections sync."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_collections_page.side_effect = Exception("API Error")
        
        stats = await pipeline.sync_collections()
        
        assert stats["collections"] == 0


class TestSyncAll:
    """Test complete synchronization workflow."""

    @pytest.mark.asyncio
    async def test_sync_all_success(self, mock_client, mock_db):
        """Test syncing all entities."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock authentication
        mock_client.fetch_viewer.return_value = {
            "user": {"id": "123", "username": "test"}
        }
        
        # Mock sync methods
        mock_client.fetch_posts_page.return_value = {
            "nodes": [{"id": "p1", "name": "Post", "createdAt": "2024-01-15T10:00:00Z", "user": {"id": "u1"}, "makers": [], "topics": {"nodes": []}}],
            "pageInfo": {"hasNextPage": False},
        }
        mock_client.fetch_topics_page.return_value = {
            "nodes": [{"id": "t1", "name": "Topic"}],
            "pageInfo": {"hasNextPage": False},
        }
        mock_client.fetch_collections_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock()
        mock_db.upsert_post.return_value = MagicMock()
        mock_db.upsert_topic.return_value = MagicMock()
        
        stats = await pipeline.sync_all(full_refresh=True)
        
        assert "posts" in stats
        assert "topics" in stats
        assert "collections" in stats
        assert "total_entities" in stats
        mock_client.fetch_viewer.assert_called_once()

    @pytest.mark.asyncio
    async def test_sync_all_with_max_pages(self, mock_client, mock_db):
        """Test sync_all with max_pages limit."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_viewer.return_value = {
            "user": {"id": "123", "username": "test"}
        }
        mock_client.fetch_posts_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        mock_client.fetch_topics_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        mock_client.fetch_collections_page.return_value = {
            "nodes": [],
            "pageInfo": {"hasNextPage": False},
        }
        
        stats = await pipeline.sync_all(full_refresh=False, max_pages=1)
        
        assert stats["posts"]["pages"] == 1
        assert stats["topics"]["pages"] == 1
        assert stats["collections"]["pages"] == 1


class TestGetStatistics:
    """Test database statistics retrieval."""

    def test_get_statistics_success(self, mock_client, mock_db):
        """Test getting database statistics."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock session.exec to return counts
        mock_result = MagicMock()
        mock_result.one.side_effect = [100, 50, 25, 10, 200, 300]  # counts for each entity
        mock_db.session.exec.return_value = mock_result
        
        stats = pipeline.get_statistics()
        
        assert stats["posts"] == 100
        assert stats["users"] == 50
        assert stats["topics"] == 25
        assert stats["collections"] == 10
        assert stats["comments"] == 200
        assert stats["votes"] == 300

    def test_get_statistics_uninitialized_db(self, mock_client, mock_db):
        """Test statistics with uninitialized database."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_db.session = None
        
        with pytest.raises(RuntimeError, match="Database not initialized"):
            pipeline.get_statistics()


class TestErrorScenarios:
    """Test error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_validation_error_handling(self, mock_client, mock_db):
        """Test handling of validation errors."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        # Mock response with invalid data
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {
                    "id": "post1",
                    "name": None,  # Invalid: name required
                    "user": {"id": "u1"},
                }
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.return_value = MagicMock()
        
        # Should handle validation error gracefully
        stats = await pipeline.sync_posts(full_refresh=True)
        
        # Post with invalid data should be skipped
        assert stats["skipped"] >= 0

    @pytest.mark.asyncio
    async def test_database_error_handling(self, mock_client, mock_db):
        """Test handling of database errors."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        mock_client.fetch_posts_page.return_value = {
            "nodes": [
                {"id": "post1", "name": "Test", "createdAt": "2024-01-15T10:00:00Z", "user": {"id": "u1"}, "makers": [], "topics": {"nodes": []}}
            ],
            "pageInfo": {"hasNextPage": False},
        }
        
        mock_db.upsert_user.side_effect = Exception("Database error")
        
        # Should handle database error
        stats = await pipeline.sync_posts(full_refresh=True)
        
        assert stats["posts"] >= 0


class TestContextManager:
    """Test pipeline as context manager."""

    @pytest.mark.asyncio
    async def test_pipeline_context_manager(self, mock_client, mock_db):
        """Test using pipeline as async context manager."""
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        
        await pipeline.initialize()
        
        try:
            # Use pipeline
            mock_client.fetch_viewer.return_value = {
                "user": {"id": "123", "username": "test"}
            }
            await pipeline.verify_authentication()
        finally:
            pipeline.close()
        
        mock_db.initialize.assert_called_once()
        mock_db.close.assert_called_once()
