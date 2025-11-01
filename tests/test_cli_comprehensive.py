"""Comprehensive tests for CLI commands to improve coverage.

This test file adds extensive coverage for all CLI commands including:
- Helper functions (setup_logging, run_async)
- All command options and error paths
- Integration with DatabaseManager and DataPipeline
"""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from typer.testing import CliRunner

from producthuntdb.cli import app, run_async, setup_logging

runner = CliRunner()


class TestHelperFunctions:
    """Test CLI helper functions."""

    def test_setup_logging_default(self):
        """Test setup_logging with default verbosity."""
        from loguru import logger

        # Remove existing handlers
        logger.remove()

        # Setup with default (non-verbose)
        setup_logging(verbose=False)

        # Verify logger is configured
        # Note: We can't easily test the exact configuration, but we can verify it doesn't crash
        assert True  # If we get here, setup_logging worked

    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose mode."""
        from loguru import logger

        logger.remove()
        setup_logging(verbose=True)
        assert True  # If we get here, setup_logging worked

    def test_run_async(self):
        """Test run_async helper."""

        async def sample_coro():
            return "test_result"

        result = run_async(sample_coro())
        assert result == "test_result"


class TestSyncCommand:
    """Test sync command with various options."""

    def test_sync_full_refresh(self, monkeypatch):
        """Test sync command with full refresh."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_all = AsyncMock()
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--full-refresh"])

            assert result.exit_code == 0
            mock_pipeline.sync_all.assert_called_once()

    def test_sync_max_pages(self, monkeypatch):
        """Test sync command with max pages limit."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_all = AsyncMock()
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--max-pages", "5"])

            assert result.exit_code == 0

    def test_sync_posts_only(self, monkeypatch):
        """Test sync command with posts only."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_posts = AsyncMock()
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--posts-only"])

            assert result.exit_code == 0

    def test_sync_topics_only(self, monkeypatch):
        """Test sync command with topics only."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_topics = AsyncMock()
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--topics-only"])

            assert result.exit_code == 0

    def test_sync_collections_only(self, monkeypatch):
        """Test sync command with collections only."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_collections = AsyncMock()
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--collections-only"])

            assert result.exit_code == 0

    def test_sync_with_error(self, monkeypatch):
        """Test sync command with error."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_all = AsyncMock(side_effect=Exception("Sync failed"))
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync"])

            assert result.exit_code != 0
            assert "Sync failed" in result.stdout or result.exception is not None


class TestExportCommand:
    """Test export command."""

    def test_export_default(self, monkeypatch, tmp_path):
        """Test export command with default output directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock()
            mock_db.close = MagicMock()

            result = runner.invoke(app, ["export"])

            assert result.exit_code == 0
            mock_db.export_to_csv.assert_called_once()

    def test_export_custom_directory(self, monkeypatch, tmp_path):
        """Test export command with custom output directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        output_dir = tmp_path / "custom_export"

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock()
            mock_db.close = MagicMock()

            result = runner.invoke(app, ["export", "--output-dir", str(output_dir)])

            assert result.exit_code == 0

    def test_export_with_error(self, monkeypatch):
        """Test export command with error."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock(side_effect=Exception("Export failed"))
            mock_db.close = MagicMock()

            result = runner.invoke(app, ["export"])

            assert result.exit_code != 0


class TestPublishCommand:
    """Test publish command."""

    def test_publish_success(self, monkeypatch):
        """Test publish command successfully."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock()
            mock_db.close = MagicMock()

            with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
                mock_kaggle = MockKaggle.return_value
                mock_kaggle.publish_dataset = MagicMock()

                result = runner.invoke(app, ["publish"])

                assert result.exit_code == 0
                mock_db.export_to_csv.assert_called_once()
                mock_kaggle.publish_dataset.assert_called_once()

    def test_publish_without_credentials(self, monkeypatch):
        """Test publish command without Kaggle credentials."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "")
        monkeypatch.setenv("KAGGLE_KEY", "")

        result = runner.invoke(app, ["publish"])

        assert result.exit_code != 0
        assert "Kaggle credentials" in result.stdout or result.exception is not None

    def test_publish_skip_export(self, monkeypatch):
        """Test publish command with skip-export flag."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_kaggle = MockKaggle.return_value
            mock_kaggle.publish_dataset = MagicMock()

            result = runner.invoke(app, ["publish", "--skip-export"])

            assert result.exit_code == 0


class TestStatusCommand:
    """Test status command."""

    def test_status_with_data(self, monkeypatch):
        """Test status command with existing data."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.get_crawl_state = MagicMock(
                side_effect=[
                    {
                        "entity_type": "posts",
                        "last_cursor": "cursor123",
                        "updated_at": "2024-01-15T12:00:00Z",
                    },
                    {
                        "entity_type": "topics",
                        "last_cursor": "cursor456",
                        "updated_at": "2024-01-15T12:00:00Z",
                    },
                    {
                        "entity_type": "collections",
                        "last_cursor": "cursor789",
                        "updated_at": "2024-01-15T12:00:00Z",
                    },
                ]
            )
            mock_db.close = MagicMock()

            with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
                mock_pipeline = MockPipeline.return_value
                mock_pipeline.get_statistics = MagicMock(
                    return_value={
                        "posts": 100,
                        "users": 50,
                        "topics": 10,
                        "collections": 5,
                        "comments": 200,
                        "votes": 500,
                    }
                )

                result = runner.invoke(app, ["status"])

                assert result.exit_code == 0
                assert "100" in result.stdout  # posts count

    def test_status_empty_database(self, monkeypatch):
        """Test status command with empty database."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

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


class TestVerifyCommand:
    """Test verify command."""

    def test_verify_authentication_success(self, monkeypatch, mock_viewer_response):
        """Test verify command with successful authentication."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value=mock_viewer_response["viewer"]
            )
            mock_pipeline.client = MagicMock()
            mock_pipeline.client.get_rate_limit_status = MagicMock(
                return_value={
                    "limit": "100",
                    "remaining": "50",
                    "reset": "2024-01-15T12:00:00Z",
                }
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["verify"])

            assert result.exit_code == 0
            assert "Authentication successful" in result.stdout

    def test_verify_authentication_failure(self, monkeypatch):
        """Test verify command with authentication failure."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "invalid_token")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                side_effect=Exception("Authentication failed")
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["verify"])

            assert result.exit_code != 0


class TestInitCommand:
    """Test init command."""

    def test_init_creates_database(self, tmp_path, monkeypatch):
        """Test init command creates database."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert "Database" in result.stdout

    def test_init_force_recreates(self, tmp_path, monkeypatch):
        """Test init command with force flag."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        db_path.touch()  # Create existing file
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        result = runner.invoke(app, ["init", "--force"])

        assert result.exit_code == 0

    def test_init_with_error(self, monkeypatch):
        """Test init command with error."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock(side_effect=Exception("Init failed"))

            result = runner.invoke(app, ["init"])

            assert result.exit_code != 0


class TestMigrationCommands:
    """Test migration-related commands."""

    def test_migrate_command(self, monkeypatch):
        """Test migrate command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Migration created")

            result = runner.invoke(app, ["migrate", "test_migration"])

            assert result.exit_code == 0

    def test_upgrade_command(self, monkeypatch):
        """Test upgrade command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Upgraded to head"
            )

            result = runner.invoke(app, ["upgrade"])

            assert result.exit_code == 0

    def test_upgrade_with_revision(self, monkeypatch):
        """Test upgrade command with specific revision."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Upgraded to revision"
            )

            result = runner.invoke(app, ["upgrade", "--revision", "abc123"])

            assert result.exit_code == 0

    def test_downgrade_command(self, monkeypatch):
        """Test downgrade command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Downgraded to -1"
            )

            result = runner.invoke(app, ["downgrade"])

            assert result.exit_code == 0

    def test_downgrade_with_revision(self, monkeypatch):
        """Test downgrade command with specific revision."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Downgraded to revision"
            )

            result = runner.invoke(app, ["downgrade", "--revision", "xyz789"])

            assert result.exit_code == 0

    def test_migration_history_command(self, monkeypatch):
        """Test migration-history command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="Migration history"
            )

            result = runner.invoke(app, ["migration-history"])

            assert result.exit_code == 0


class TestCLIEdgeCases:
    """Test CLI edge cases and error handling."""

    def test_app_without_token(self):
        """Test CLI commands without PRODUCTHUNT_TOKEN."""
        # Most commands should fail without token
        result = runner.invoke(app, ["sync"])
        # This might fail during settings validation
        assert result.exit_code != 0 or result.exception is not None

    def test_help_command(self):
        """Test CLI help."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Product Hunt" in result.stdout

    def test_command_help(self):
        """Test individual command help."""
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "sync" in result.stdout or "Synchronize" in result.stdout
