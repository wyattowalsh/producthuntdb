"""Unit tests for DataPipeline to boost coverage."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from producthuntdb.pipeline import DataPipeline


class TestPipelineInitialization:
    """Test pipeline initialization and setup."""

    @pytest.mark.asyncio
    async def test_pipeline_initialize(self, monkeypatch):
        """Test pipeline initialization."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client:
            mock_client.initialize = AsyncMock()
            await pipeline.initialize()
            mock_client.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_pipeline_verify_authentication(self, monkeypatch):
        """Test authentication verification."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client:
            mock_client.verify_authentication = AsyncMock(
                return_value={"user": {"username": "testuser"}}
            )
            result = await pipeline.verify_authentication()
            
            assert result == {"user": {"username": "testuser"}}
            mock_client.verify_authentication.assert_called_once()


class TestPipelineStatistics:
    """Test pipeline statistics methods."""

    def test_get_statistics(self, monkeypatch):
        """Test get_statistics method."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'db') as mock_db:
            mock_db.get_entity_counts = MagicMock(
                return_value={
                    "posts": 100,
                    "users": 50,
                    "topics": 25,
                    "collections": 10,
                    "comments": 200,
                    "votes": 300,
                }
            )
            
            stats = pipeline.get_statistics()
            
            assert stats["posts"] == 100
            assert stats["users"] == 50
            assert stats["topics"] == 25


class TestPipelineSyncPosts:
    """Test post synchronization."""

    @pytest.mark.asyncio
    async def test_sync_posts_success(self, monkeypatch):
        """Test successful post sync."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client, \
             patch.object(pipeline, 'db') as mock_db:
            
            # Mock client methods
            mock_client.fetch_posts_by_date = AsyncMock(
                return_value=([
                    {
                        "id": "1",
                        "name": "Test Post",
                        "tagline": "Test tagline",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "featuredAt": "2024-01-01T00:00:00Z",
                        "url": "https://test.com",
                        "votesCount": 100,
                        "commentsCount": 10,
                        "user": {
                            "id": "user1",
                            "username": "testuser",
                            "name": "Test User",
                            "headline": "Test headline",
                            "url": "https://test.com/user",
                            "createdAt": "2024-01-01T00:00:00Z",
                        },
                        "topics": [],
                        "makers": [],
                    }
                ], False)
            )
            
            # Mock DB methods
            mock_db.get_crawl_state = MagicMock(return_value=None)
            mock_db.batch_upsert_users = MagicMock()
            mock_db.batch_upsert_posts = MagicMock()
            mock_db.save_crawl_state = MagicMock()
            
            result = await pipeline.sync_posts(full_refresh=True, max_pages=1)
            
            assert result["posts"] == 1
            assert result["users"] >= 0


class TestPipelineSyncTopics:
    """Test topic synchronization."""

    @pytest.mark.asyncio
    async def test_sync_topics_success(self, monkeypatch):
        """Test successful topic sync."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client, \
             patch.object(pipeline, 'db') as mock_db:
            
            # Mock client methods
            mock_client.fetch_topics = AsyncMock(
                return_value=([
                    {
                        "id": "1",
                        "name": "Test Topic",
                        "slug": "test-topic",
                        "description": "Test description",
                        "url": "https://test.com",
                        "followersCount": 100,
                        "createdAt": "2024-01-01T00:00:00Z",
                    }
                ], False)
            )
            
            # Mock DB methods
            mock_db.batch_upsert_topics = MagicMock()
            
            result = await pipeline.sync_topics(max_pages=1)
            
            assert result["topics"] == 1


class TestPipelineSyncCollections:
    """Test collection synchronization."""

    @pytest.mark.asyncio
    async def test_sync_collections_success(self, monkeypatch):
        """Test successful collection sync."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client, \
             patch.object(pipeline, 'db') as mock_db:
            
            # Mock client methods
            mock_client.fetch_collections = AsyncMock(
                return_value=([
                    {
                        "id": "1",
                        "name": "Test Collection",
                        "slug": "test-collection",
                        "tagline": "Test tagline",
                        "url": "https://test.com",
                        "createdAt": "2024-01-01T00:00:00Z",
                        "featuredAt": "2024-01-01T00:00:00Z",
                        "postsCount": 10,
                        "collectionsCount": 5,
                        "user": {
                            "id": "user1",
                            "username": "testuser",
                            "name": "Test User",
                            "headline": "Test headline",
                            "url": "https://test.com/user",
                            "createdAt": "2024-01-01T00:00:00Z",
                        },
                        "posts": [],
                    }
                ], False)
            )
            
            # Mock DB methods
            mock_db.batch_upsert_users = MagicMock()
            mock_db.batch_upsert_collections = MagicMock()
            
            result = await pipeline.sync_collections(max_pages=1)
            
            assert result["collections"] == 1


class TestPipelineSyncAll:
    """Test sync_all method."""

    @pytest.mark.asyncio
    async def test_sync_all_success(self, monkeypatch):
        """Test successful full sync."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'sync_posts', new=AsyncMock(return_value={"posts": 10, "users": 5})) as mock_sync_posts, \
             patch.object(pipeline, 'sync_topics', new=AsyncMock(return_value={"topics": 3})) as mock_sync_topics, \
             patch.object(pipeline, 'sync_collections', new=AsyncMock(return_value={"collections": 2})) as mock_sync_collections:
            
            result = await pipeline.sync_all(full_refresh=True, max_pages=1)
            
            assert result["total_entities"] >= 15
            mock_sync_posts.assert_called_once()
            mock_sync_topics.assert_called_once()
            mock_sync_collections.assert_called_once()


class TestPipelineClose:
    """Test pipeline cleanup."""

    def test_close(self, monkeypatch):
        """Test pipeline close method."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client, \
             patch.object(pipeline, 'db') as mock_db:
            mock_client.close = MagicMock()
            mock_db.close = MagicMock()
            
            pipeline.close()
            
            mock_client.close.assert_called_once()
            mock_db.close.assert_called_once()


class TestPipelineErrorHandling:
    """Test error handling in pipeline."""

    @pytest.mark.asyncio
    async def test_sync_posts_with_error(self, monkeypatch):
        """Test error handling in sync_posts."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_123")
        
        pipeline = DataPipeline()
        
        with patch.object(pipeline, 'client') as mock_client:
            mock_client.fetch_posts_by_date = AsyncMock(
                side_effect=Exception("API Error")
            )
            
            with pytest.raises(Exception, match="API Error"):
                await pipeline.sync_posts(full_refresh=True, max_pages=1)
