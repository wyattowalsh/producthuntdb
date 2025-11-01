"""Comprehensive tests for pipeline.py to improve coverage.

These tests focus on actually covered code paths rather than mocking everything.
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from producthuntdb.pipeline import DataPipeline


class TestPipelineBasics:
    """Test basic pipeline operations."""

    def test_init_default(self):
        """Test pipeline initialization with default dependencies."""
        pipeline = DataPipeline()
        assert pipeline.client is not None
        assert pipeline.db is not None

    def test_init_with_client(self):
        """Test pipeline initialization with custom client."""
        mock_client = Mock()
        pipeline = DataPipeline(client=mock_client)
        assert pipeline.client is mock_client

    def test_init_with_db(self):
        """Test pipeline initialization with custom database."""
        mock_db = Mock()
        pipeline = DataPipeline(db=mock_db)
        assert pipeline.db is mock_db

    def test_init_with_both(self):
        """Test pipeline initialization with both custom dependencies."""
        mock_client = Mock()
        mock_db = Mock()
        pipeline = DataPipeline(client=mock_client, db=mock_db)
        assert pipeline.client is mock_client
        assert pipeline.db is mock_db

    @pytest.mark.asyncio
    async def test_initialize(self, tmp_path):
        """Test pipeline initialize method."""
        mock_db = Mock()
        mock_db.initialize = Mock()
        pipeline = DataPipeline(db=mock_db)

        await pipeline.initialize()
        mock_db.initialize.assert_called_once()

    def test_close(self):
        """Test pipeline close method."""
        mock_db = Mock()
        mock_db.close = Mock()
        pipeline = DataPipeline(db=mock_db)

        pipeline.close()
        mock_db.close.assert_called_once()


class TestSafetyCutoff:
    """Test safety cutoff calculation."""

    def test_safety_cutoff_with_none(self):
        """Test safety cutoff with None timestamp."""
        pipeline = DataPipeline()
        result = pipeline._get_safety_cutoff(None)
        assert result is None

    def test_safety_cutoff_with_valid_timestamp(self):
        """Test safety cutoff with valid ISO timestamp."""
        pipeline = DataPipeline()
        # Use a timestamp from 2 hours ago
        now = datetime.utcnow()
        timestamp = now.isoformat() + "Z"
        result = pipeline._get_safety_cutoff(timestamp)
        
        # Should return a datetime earlier than the input
        assert result is not None
        assert isinstance(result, datetime)
        assert result < now

    def test_safety_cutoff_with_none_parse_result(self):
        """Test safety cutoff when parse_datetime returns None."""
        pipeline = DataPipeline()
        
        # patch parse_datetime to return None
        with patch("producthuntdb.pipeline.parse_datetime", return_value=None):
            result = pipeline._get_safety_cutoff("2024-01-01T00:00:00Z")
            assert result is None


class TestVerifyAuthentication:
    """Test API authentication verification."""

    @pytest.mark.asyncio
    async def test_verify_success(self):
        """Test successful authentication."""
        mock_client = Mock()
        mock_client.fetch_viewer = AsyncMock(
            return_value={
                "user": {
                    "username": "testuser",
                    "name": "Test User",
                    "id": "123",
                }
            }
        )
        pipeline = DataPipeline(client=mock_client)

        result = await pipeline.verify_authentication()
        assert "user" in result
        assert result["user"]["username"] == "testuser"

    @pytest.mark.asyncio
    async def test_verify_no_user_data(self):
        """Test authentication with missing user data."""
        mock_client = Mock()
        mock_client.fetch_viewer = AsyncMock(return_value={})
        pipeline = DataPipeline(client=mock_client)

        with pytest.raises(RuntimeError, match="Failed to authenticate"):
            await pipeline.verify_authentication()

    @pytest.mark.asyncio
    async def test_verify_none_response(self):
        """Test authentication with None response."""
        mock_client = Mock()
        mock_client.fetch_viewer = AsyncMock(return_value=None)
        pipeline = DataPipeline(client=mock_client)

        with pytest.raises(RuntimeError, match="Failed to authenticate"):
            await pipeline.verify_authentication()

    @pytest.mark.asyncio
    async def test_verify_exception(self):
        """Test authentication with exception."""
        mock_client = Mock()
        mock_client.fetch_viewer = AsyncMock(side_effect=Exception("API Error"))
        pipeline = DataPipeline(client=mock_client)

        with pytest.raises(Exception, match="API Error"):
            await pipeline.verify_authentication()


class TestGetStatistics:
    """Test get_statistics method."""

    def test_get_statistics_with_data(self):
        """Test get_statistics with actual data."""
        mock_db = Mock()
        mock_db.get_statistics = Mock(
            return_value={
                "posts": 100,
                "topics": 50,
                "collections": 20,
                "users": 75,
            }
        )
        pipeline = DataPipeline(db=mock_db)

        stats = pipeline.get_statistics()
        assert stats["posts"] == 100
        assert stats["topics"] == 50
        assert stats["collections"] == 20
        assert stats["users"] == 75
        mock_db.get_statistics.assert_called_once()

    def test_get_statistics_empty(self):
        """Test get_statistics with empty database."""
        mock_db = Mock()
        mock_db.get_statistics = Mock(
            return_value={
                "posts": 0,
                "topics": 0,
                "collections": 0,
                "users": 0,
            }
        )
        pipeline = DataPipeline(db=mock_db)

        stats = pipeline.get_statistics()
        assert all(v == 0 for v in stats.values())


class TestSyncPosts:
    """Test sync_posts method with mocked client."""

    @pytest.mark.asyncio
    async def test_sync_posts_full_refresh_empty(self):
        """Test sync_posts with full refresh and no data."""
        mock_client = Mock()
        mock_client.fetch_posts_page = AsyncMock(
            return_value={
                "posts": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
            }
        )
        mock_db = Mock()
        mock_db.get_last_crawl_timestamp = Mock(return_value=None)
        mock_db.upsert_posts = Mock()
        
        pipeline = DataPipeline(client=mock_client, db=mock_db)

        with patch("producthuntdb.pipeline.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__aenter__ = AsyncMock(return_value=Mock())
            mock_tqdm.return_value.__aexit__ = AsyncMock()
            
            stats = await pipeline.sync_posts(full_refresh=True)
            
            # Should process at least one page
            assert mock_client.fetch_posts_page.called

    @pytest.mark.asyncio
    async def test_sync_posts_incremental_with_timestamp(self):
        """Test sync_posts incremental update with existing timestamp."""
        mock_client = Mock()
        mock_client.fetch_posts_page = AsyncMock(
            return_value={
                "posts": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
            }
        )
        mock_db = Mock()
        mock_db.get_last_crawl_timestamp = Mock(return_value="2024-01-01T00:00:00Z")
        mock_db.upsert_posts = Mock()
        
        pipeline = DataPipeline(client=mock_client, db=mock_db)

        with patch("producthuntdb.pipeline.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__aenter__ = AsyncMock(return_value=Mock())
            mock_tqdm.return_value.__aexit__ = AsyncMock()
            
            stats = await pipeline.sync_posts(full_refresh=False)
            
            # Should fetch with timestamp
            mock_db.get_last_crawl_timestamp.assert_called_once()


class TestSyncTopics:
    """Test sync_topics method."""

    @pytest.mark.asyncio
    async def test_sync_topics_empty(self):
        """Test sync_topics with no data."""
        mock_client = Mock()
        mock_client.fetch_topics_page = AsyncMock(
            return_value={
                "topics": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
            }
        )
        mock_db = Mock()
        mock_db.upsert_topics = Mock()
        
        pipeline = DataPipeline(client=mock_client, db=mock_db)

        with patch("producthuntdb.pipeline.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__aenter__ = AsyncMock(return_value=Mock())
            mock_tqdm.return_value.__aexit__ = AsyncMock()
            
            stats = await pipeline.sync_topics()
            
            assert mock_client.fetch_topics_page.called


class TestSyncCollections:
    """Test sync_collections method."""

    @pytest.mark.asyncio
    async def test_sync_collections_empty(self):
        """Test sync_collections with no data."""
        mock_client = Mock()
        mock_client.fetch_collections_page = AsyncMock(
            return_value={
                "collections": {"nodes": [], "pageInfo": {"hasNextPage": False, "endCursor": None}}
            }
        )
        mock_db = Mock()
        mock_db.upsert_collections = Mock()
        
        pipeline = DataPipeline(client=mock_client, db=mock_db)

        with patch("producthuntdb.pipeline.tqdm") as mock_tqdm:
            mock_tqdm.return_value.__aenter__ = AsyncMock(return_value=Mock())
            mock_tqdm.return_value.__aexit__ = AsyncMock()
            
            stats = await pipeline.sync_collections()
            
            assert mock_client.fetch_collections_page.called


class TestSyncAll:
    """Test sync_all method."""

    @pytest.mark.asyncio
    async def test_sync_all_calls_all_methods(self):
        """Test that sync_all calls all sync methods."""
        pipeline = DataPipeline()
        
        # Mock all the sync methods
        pipeline.sync_posts = AsyncMock(return_value={"posts": 0, "pages": 0})
        pipeline.sync_topics = AsyncMock(return_value={"topics": 0, "pages": 0})
        pipeline.sync_collections = AsyncMock(return_value={"collections": 0, "pages": 0})
        
        stats = await pipeline.sync_all()
        
        # All methods should be called
        pipeline.sync_posts.assert_called_once()
        pipeline.sync_topics.assert_called_once()
        pipeline.sync_collections.assert_called_once()
        
        # Stats should combine all results
        assert "posts" in stats
        assert "topics" in stats
        assert "collections" in stats
