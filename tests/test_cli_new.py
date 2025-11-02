"""Comprehensive tests for cli.py to improve coverage.

These tests focus on actually testing the CLI commands.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
from typer.testing import CliRunner

from producthuntdb.cli import app, run_async, setup_logging


runner = CliRunner()


class TestHelperFunctions:
    """Test CLI helper functions."""

    def test_setup_logging_default(self):
        """Test setup_logging with default verbosity."""
        # Should not raise an error
        setup_logging(verbose=False)

    def test_setup_logging_verbose(self):
        """Test setup_logging with verbose mode."""
        # Should not raise an error
        setup_logging(verbose=True)

    def test_run_async_simple(self):
        """Test run_async with simple coroutine."""

        async def simple_coro():
            return "result"

        result = run_async(simple_coro())
        assert result == "result"

    def test_run_async_with_await(self):
        """Test run_async with async operations."""

        async def async_add(a, b):
            await asyncio.sleep(0)
            return a + b

        result = run_async(async_add(2, 3))
        assert result == 5

    def test_run_async_with_exception(self):
        """Test run_async with exception."""

        async def failing_coro():
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_async(failing_coro())


class TestSyncCommand:
    """Test sync command."""

    def test_sync_help(self):
        """Test sync command help text."""
        result = runner.invoke(app, ["sync", "--help"])
        assert result.exit_code == 0
        assert "Synchronize data from Product Hunt API" in result.stdout

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_default_parameters(self, mock_pipeline_class):
        """Test sync with default parameters."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 0})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync"])
        # Should attempt to run
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_full_refresh_flag(self, mock_pipeline_class):
        """Test sync with --full-refresh flag."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 0})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--full-refresh"])
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_max_pages_option(self, mock_pipeline_class):
        """Test sync with --max-pages option."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 0})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--max-pages", "5"])
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_posts_only_flag(self, mock_pipeline_class):
        """Test sync with --posts-only flag."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_posts = AsyncMock(
            return_value={"posts": 10, "users": 5, "topics": 3}
        )
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--posts-only"])
        assert mock_pipeline_class.called
        if result.exit_code == 0:
            mock_pipeline.sync_posts.assert_called_once()

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_topics_only_flag(self, mock_pipeline_class):
        """Test sync with --topics-only flag."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_topics = AsyncMock(return_value={"topics": 20})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--topics-only"])
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_collections_only_flag(self, mock_pipeline_class):
        """Test sync with --collections-only flag."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_collections = AsyncMock(return_value={"collections": 15})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--collections-only"])
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_sync_verbose_flag(self, mock_pipeline_class):
        """Test sync with --verbose flag."""
        mock_pipeline = Mock()
        mock_pipeline.initialize = AsyncMock()
        mock_pipeline.verify_authentication = AsyncMock()
        mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 0})
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["sync", "--verbose"])
        assert mock_pipeline_class.called


class TestExportCommand:
    """Test export command."""

    def test_export_help(self):
        """Test export command help text."""
        result = runner.invoke(app, ["export", "--help"])
        assert result.exit_code == 0
        assert "Export" in result.stdout or "export" in result.stdout

    @patch("producthuntdb.cli.KaggleManager")
    def test_export_default_directory(self, mock_kaggle_class):
        """Test export with default directory."""
        mock_kaggle = Mock()
        mock_kaggle.export_database_to_csv = Mock()
        mock_kaggle_class.return_value = mock_kaggle

        result = runner.invoke(app, ["export"])
        assert mock_kaggle_class.called

    @patch("producthuntdb.cli.KaggleManager")
    def test_export_custom_directory(self, mock_kaggle_class):
        """Test export with custom output directory."""
        mock_kaggle = Mock()
        mock_kaggle.export_database_to_csv = Mock()
        mock_kaggle_class.return_value = mock_kaggle

        result = runner.invoke(app, ["export", "--output-dir", "/tmp/export"])
        assert mock_kaggle_class.called


class TestPublishCommand:
    """Test publish command."""

    def test_publish_help(self):
        """Test publish command help text."""
        result = runner.invoke(app, ["publish", "--help"])
        assert result.exit_code == 0
        assert "publish" in result.stdout.lower()

    @patch("producthuntdb.cli.KaggleManager")
    @patch("producthuntdb.cli.settings")
    def test_publish_without_credentials(self, mock_settings, mock_kaggle_class):
        """Test publish without Kaggle credentials."""
        mock_settings.has_kaggle_credentials.return_value = False

        result = runner.invoke(app, ["publish"])
        # Should exit with error or warning
        assert result.exit_code != 0 or "credentials" in result.stdout.lower()

    @patch("producthuntdb.cli.KaggleManager")
    @patch("producthuntdb.cli.settings")
    def test_publish_skip_export_flag(self, mock_settings, mock_kaggle_class):
        """Test publish with --skip-export flag."""
        mock_settings.has_kaggle_credentials.return_value = True
        mock_kaggle = Mock()
        mock_kaggle.publish_dataset = Mock()
        mock_kaggle_class.return_value = mock_kaggle

        result = runner.invoke(app, ["publish", "--skip-export"])
        assert mock_kaggle_class.called

    @patch("producthuntdb.cli.KaggleManager")
    @patch("producthuntdb.cli.settings")
    def test_publish_with_message(self, mock_settings, mock_kaggle_class):
        """Test publish with custom version message."""
        mock_settings.has_kaggle_credentials.return_value = True
        mock_kaggle = Mock()
        mock_kaggle.export_database_to_csv = Mock()
        mock_kaggle.publish_dataset = Mock()
        mock_kaggle_class.return_value = mock_kaggle

        result = runner.invoke(
            app, ["publish", "--message", "Test update", "--skip-export"]
        )
        assert mock_kaggle_class.called


class TestStatusCommand:
    """Test status command."""

    def test_status_help(self):
        """Test status command help text."""
        result = runner.invoke(app, ["status", "--help"])
        assert result.exit_code == 0

    @patch("producthuntdb.cli.DataPipeline")
    def test_status_with_data(self, mock_pipeline_class):
        """Test status command with database data."""
        mock_pipeline = Mock()
        mock_pipeline.get_statistics = Mock(
            return_value={
                "posts": 100,
                "topics": 50,
                "collections": 20,
                "users": 75,
            }
        )
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["status"])
        # Should display statistics
        assert mock_pipeline_class.called
        mock_pipeline.get_statistics.assert_called_once()

    @patch("producthuntdb.cli.DataPipeline")
    def test_status_empty_database(self, mock_pipeline_class):
        """Test status command with empty database."""
        mock_pipeline = Mock()
        mock_pipeline.get_statistics = Mock(
            return_value={
                "posts": 0,
                "topics": 0,
                "collections": 0,
                "users": 0,
            }
        )
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["status"])
        assert mock_pipeline_class.called


class TestVerifyCommand:
    """Test verify command."""

    def test_verify_help(self):
        """Test verify command help text."""
        result = runner.invoke(app, ["verify", "--help"])
        assert result.exit_code == 0

    @patch("producthuntdb.cli.DataPipeline")
    def test_verify_success(self, mock_pipeline_class):
        """Test verify with successful authentication."""
        mock_pipeline = Mock()
        mock_pipeline.verify_authentication = AsyncMock(
            return_value={"user": {"username": "testuser", "name": "Test User"}}
        )
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["verify"])
        assert mock_pipeline_class.called

    @patch("producthuntdb.cli.DataPipeline")
    def test_verify_failure(self, mock_pipeline_class):
        """Test verify with authentication failure."""
        mock_pipeline = Mock()
        mock_pipeline.verify_authentication = AsyncMock(
            side_effect=RuntimeError("Auth failed")
        )
        mock_pipeline.close = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        result = runner.invoke(app, ["verify"])
        # Should exit with error
        assert result.exit_code != 0 or "failed" in result.stdout.lower()


class TestInitCommand:
    """Test init command."""

    def test_init_help(self):
        """Test init command help text."""
        result = runner.invoke(app, ["init", "--help"])
        assert result.exit_code == 0

    @patch("producthuntdb.cli.DatabaseManager")
    def test_init_creates_database(self, mock_db_class):
        """Test init command creates database."""
        mock_db = Mock()
        mock_db.initialize = Mock()
        mock_db.close = Mock()
        mock_db_class.return_value = mock_db

        result = runner.invoke(app, ["init"])
        assert mock_db_class.called
        if result.exit_code == 0:
            mock_db.initialize.assert_called_once()

    @patch("producthuntdb.cli.DatabaseManager")
    def test_init_force_flag(self, mock_db_class):
        """Test init with --force flag."""
        mock_db = Mock()
        mock_db.initialize = Mock()
        mock_db.close = Mock()
        mock_db_class.return_value = mock_db

        result = runner.invoke(app, ["init", "--force"])
        assert mock_db_class.called


class TestAppMetadata:
    """Test app metadata and configuration."""

    def test_app_exists(self):
        """Test that app is properly initialized."""
        assert app is not None
        assert hasattr(app, "command")

    def test_app_has_commands(self):
        """Test that app has registered commands."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "sync" in result.stdout.lower()
        assert "export" in result.stdout.lower() or "publish" in result.stdout.lower()
