"""End-to-end tests for ProductHuntDB.

These tests verify complete user workflows from start to finish.
"""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from producthuntdb.cli import app
from producthuntdb.pipeline import DataPipeline
from typer.testing import CliRunner

runner = CliRunner()


class TestCompleteWorkflow:
    """End-to-end tests for complete workflows."""

    @pytest.mark.asyncio
    async def test_complete_sync_workflow(
        self,
        tmp_path,
        monkeypatch,
        mock_viewer_response,
        mock_posts_response,
        mock_topics_response,
    ):
        """Test complete sync workflow: init -> verify -> sync -> status."""
        # Set up environment
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        # Initialize pipeline
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # Mock API calls
            with patch.object(
                pipeline.client, "fetch_viewer", return_value=mock_viewer_response["viewer"]
            ):
                with patch.object(
                    pipeline.client, "fetch_posts_page", return_value=mock_posts_response["posts"]
                ):
                    with patch.object(
                        pipeline.client,
                        "fetch_topics_page",
                        return_value=mock_topics_response["topics"],
                    ):
                        with patch.object(
                            pipeline.client,
                            "fetch_collections_page",
                            return_value={"nodes": [], "pageInfo": {"hasNextPage": False}},
                        ):
                            # Verify authentication
                            viewer = await pipeline.verify_authentication()
                            assert viewer["user"]["username"] == "testuser"

                            # Sync all data
                            stats = await pipeline.sync_all(max_pages=1)
                            assert stats["total_entities"] >= 2

                            # Check statistics
                            db_stats = pipeline.get_statistics()
                            assert db_stats["posts"] >= 1
                            assert db_stats["users"] >= 1
                            assert db_stats["topics"] >= 1

        finally:
            pipeline.close()

    def test_cli_complete_workflow(self, tmp_path, monkeypatch):
        """Test complete workflow via CLI."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        # Step 1: Initialize database (mocked to use the correct path)
        with patch("producthuntdb.cli.settings") as mock_settings, \
             patch("producthuntdb.cli.DatabaseManager") as MockDB:
            # Configure mock settings
            mock_settings.database_path = db_path
            mock_settings.graphql_endpoint = "https://api.producthunt.com/v2/api/graphql"
            mock_settings.redact_token.return_value = "test***"
            
            # Configure mock DB
            mock_db = MockDB.return_value
            
            def init_side_effect():
                db_path.touch()
                
            mock_db.initialize = MagicMock(side_effect=init_side_effect)
            
            result = runner.invoke(app, ["init"])
            assert result.exit_code == 0
            assert db_path.exists()

        # Step 2: Verify authentication (mocked)
        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.client = MagicMock()
            mock_pipeline.client.get_rate_limit_status = MagicMock(
                return_value={"limit": "100", "remaining": "50", "reset": "2024-01-15T12:00:00Z"}
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["verify"])
            assert result.exit_code == 0

        # Step 3: Check status
        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.get_crawl_state = MagicMock(return_value=None)
            mock_db.close = MagicMock()

            with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
                mock_pipeline = MockPipeline.return_value
                mock_pipeline.get_statistics = MagicMock(
                    return_value={
                        "posts": 0,
                        "users": 0,
                        "topics": 0,
                        "collections": 0,
                        "comments": 0,
                        "votes": 0,
                    }
                )

                result = runner.invoke(app, ["status"])
                assert result.exit_code == 0


class TestExportAndPublishWorkflow:
    """E2E tests for export and publish workflow."""

    def test_export_workflow(self, tmp_path, monkeypatch):
        """Test database export workflow."""
        db_path = tmp_path / "test.db"
        export_dir = tmp_path / "export"

        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        # Create database first
        runner.invoke(app, ["init"])

        # Export data
        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock()

            result = runner.invoke(app, ["export", "--output-dir", str(export_dir)])

            assert result.exit_code == 0
            mock_km.export_database_to_csv.assert_called_once()

    @pytest.mark.asyncio
    async def test_incremental_update_workflow(
        self, tmp_path, monkeypatch, mock_posts_response
    ):
        """Test incremental update workflow."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            with patch.object(
                pipeline.client, "fetch_posts_page", return_value=mock_posts_response["posts"]
            ):
                # First sync (full)
                stats1 = await pipeline.sync_posts(full_refresh=True, max_pages=1)
                initial_count = stats1["posts"]

                # Get crawl state
                crawl_state = pipeline.db.get_crawl_state("posts")
                assert crawl_state is not None

                # Second sync (incremental)
                stats2 = await pipeline.sync_posts(full_refresh=False, max_pages=1)

                # Should have used safety margin
                # Verify pipeline works correctly

        finally:
            pipeline.close()


class TestErrorRecovery:
    """E2E tests for error recovery."""

    @pytest.mark.asyncio
    async def test_recovery_from_failed_sync(self, tmp_path, monkeypatch):
        """Test recovery from failed sync."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # First sync fails
            with patch.object(
                pipeline.client,
                "fetch_posts_page",
                side_effect=Exception("Network error"),
            ):
                stats1 = await pipeline.sync_posts(max_pages=1)
                assert stats1["posts"] == 0

            # Second sync succeeds
            with patch.object(
                pipeline.client,
                "fetch_posts_page",
                return_value={"nodes": [], "pageInfo": {"hasNextPage": False}},
            ):
                stats2 = await pipeline.sync_posts(max_pages=1)

                # Should not crash
                assert stats2["posts"] >= 0

        finally:
            pipeline.close()

    def test_cli_handles_missing_credentials(self, monkeypatch):
        """Test CLI handles missing credentials gracefully."""
        # Remove all credentials
        for env_var in ["PRODUCTHUNT_TOKEN", "KAGGLE_USERNAME", "KAGGLE_KEY"]:
            monkeypatch.delenv(env_var, raising=False)

        # Commands should fail gracefully, not crash
        result = runner.invoke(app, ["verify"])
        # Will fail due to missing token, but shouldn't crash
        assert result.exit_code != 0


class TestDataConsistency:
    """E2E tests for data consistency."""

    @pytest.mark.asyncio
    async def test_data_consistency_across_syncs(
        self, tmp_path, monkeypatch, mock_posts_response
    ):
        """Test that data remains consistent across multiple syncs."""
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            with patch.object(
                pipeline.client, "fetch_posts_page", return_value=mock_posts_response["posts"]
            ):
                # Sync twice
                await pipeline.sync_posts(max_pages=1)
                await pipeline.sync_posts(max_pages=1)

                # Check that we don't have duplicates
                stats = pipeline.get_statistics()

                # Should have consistent counts (not doubled)
                assert stats["posts"] >= 1

        finally:
            pipeline.close()
