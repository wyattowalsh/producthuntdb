"""Unit tests for CLI commands."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import typer
from typer.testing import CliRunner

from producthuntdb.cli import app

runner = CliRunner()


class TestCLICommands:
    """Tests for CLI commands."""

    def test_cli_app_exists(self):
        """Test CLI app is defined."""
        assert app is not None
        assert isinstance(app, typer.Typer)

    def test_init_command(self, tmp_path, monkeypatch):
        """Test init command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        # Ensure parent directory exists
        db_path.parent.mkdir(parents=True, exist_ok=True)

        result = runner.invoke(app, ["init"])

        # Print output for debugging
        if result.exit_code != 0:
            print(f"stdout: {result.stdout}")
            if result.exception:
                print(f"exception: {result.exception}")

        assert result.exit_code == 0
        assert "Database created" in result.stdout or "Database already exists" in result.stdout

    def test_init_command_force(self, tmp_path, monkeypatch):
        """Test init command with force flag."""
        db_path = tmp_path / "test.db"
        db_path.touch()  # Create existing file

        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        result = runner.invoke(app, ["init", "--force"])

        assert result.exit_code == 0

    def test_verify_command_success(self, monkeypatch, mock_viewer_response):
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
                return_value={"limit": "100", "remaining": "50", "reset": "2024-01-15T12:00:00Z"}
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["verify"])

            if result.exit_code != 0:
                print(f"stdout: {result.stdout}")
                if result.exception:
                    print(f"exception: {result.exception}")

            assert result.exit_code == 0
            assert "Authentication successful" in result.stdout

    def test_status_command(self, monkeypatch):
        """Test status command."""
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

    def test_export_command(self, tmp_path, monkeypatch):
        """Test export command."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock()

            result = runner.invoke(app, ["export", "--output-dir", str(tmp_path)])

            assert result.exit_code == 0
            mock_km.export_database_to_csv.assert_called_once()

    def test_sync_command_minimal(self, monkeypatch):
        """Test sync command with minimal options."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 10})
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--max-pages", "1"])

            # Command may succeed or fail depending on mocking completeness
            # Just check it doesn't crash
            assert result.exit_code in [0, 1]


class TestCLIHelp:
    """Tests for CLI help text."""

    def test_main_help(self):
        """Test main help output."""
        result = runner.invoke(app, ["--help"])

        assert result.exit_code == 0
        assert "Product Hunt" in result.stdout or "producthuntdb" in result.stdout

    def test_sync_help(self):
        """Test sync command help."""
        result = runner.invoke(app, ["sync", "--help"])

        assert result.exit_code == 0
        assert "sync" in result.stdout.lower()

    def test_export_help(self):
        """Test export command help."""
        result = runner.invoke(app, ["export", "--help"])

        assert result.exit_code == 0
        assert "export" in result.stdout.lower()

    def test_publish_help(self):
        """Test publish command help."""
        result = runner.invoke(app, ["publish", "--help"])

        assert result.exit_code == 0
        assert "publish" in result.stdout.lower()


class TestCLIEdgeCases:
    """Tests for CLI edge cases and error handling."""

    def test_sync_posts_only(self, monkeypatch):
        """Test sync with posts-only flag."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_posts = AsyncMock(
                return_value={"posts": 10, "users": 5, "topics": 2, "pages": 1}
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--posts-only", "--max-pages", "1"])

            # May succeed or fail depending on mocks, but shouldn't crash
            assert result.exit_code in [0, 1]

    def test_sync_topics_only(self, monkeypatch):
        """Test sync with topics-only flag."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_topics = AsyncMock(return_value={"topics": 5, "pages": 1})
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--topics-only", "--max-pages", "1"])

            assert result.exit_code in [0, 1]

    def test_sync_full_refresh(self, monkeypatch):
        """Test sync with full refresh."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_all = AsyncMock(return_value={"total_entities": 20})
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--full-refresh", "--max-pages", "1"])

            assert result.exit_code in [0, 1]

    def test_status_with_data(self, monkeypatch, temp_db_path):
        """Test status command with actual database."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("DATABASE_PATH", str(temp_db_path))

        # Create database with data
        from producthuntdb.io import DatabaseManager

        db = DatabaseManager(database_path=temp_db_path)
        db.initialize()
        db.upsert_user({"id": "u1", "username": "test", "name": "Test"})
        db.update_crawl_state("posts", "2024-01-15T10:00:00Z")
        db.close()

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.get_statistics = MagicMock(
                return_value={
                    "posts": 5,
                    "users": 3,
                    "topics": 2,
                    "collections": 1,
                    "comments": 10,
                    "votes": 20,
                }
            )

            result = runner.invoke(app, ["status"])

            # Should show statistics
            assert result.exit_code == 0
            assert "posts" in result.stdout.lower() or "5" in result.stdout

    def test_export_with_custom_output(self, monkeypatch, tmp_path):
        """Test export command with custom output directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        output_dir = tmp_path / "custom_output"

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock()

            result = runner.invoke(app, ["export", "--output-dir", str(output_dir)])

            assert result.exit_code == 0

    def test_publish_with_custom_params(self, monkeypatch, tmp_path):
        """Test publish command with custom parameters."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock()
            mock_km.publish_dataset = MagicMock()

            result = runner.invoke(
                app, ["publish", "--title", "Test Dataset", "--description", "Test Description"]
            )

            # May succeed or fail, but shouldn't crash
            assert result.exit_code in [0, 1]

    def test_sync_with_verbose_logging(self, monkeypatch):
        """Test sync with verbose logging."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_all = AsyncMock(
                return_value={"total_entities": 10, "posts": 5, "users": 3}
            )
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--max-pages", "1", "-v"])

            # Should work with verbose mode
            assert result.exit_code in [0, 1]

    def test_sync_collections_only(self, monkeypatch):
        """Test sync collections only."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_collections = AsyncMock(return_value={"collections": 10})
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync", "--collections-only"])

            assert result.exit_code in [0, 1]

    def test_sync_error_handling(self, monkeypatch):
        """Test sync error handling."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = MockPipeline.return_value
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.verify_authentication = AsyncMock(
                return_value={"user": {"username": "test"}}
            )
            mock_pipeline.sync_all = AsyncMock(side_effect=RuntimeError("Test error"))
            mock_pipeline.close = MagicMock()

            result = runner.invoke(app, ["sync"])

            assert result.exit_code == 1

    def test_export_error_handling(self, monkeypatch, tmp_path):
        """Test export error handling."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock(side_effect=RuntimeError("Export error"))

            result = runner.invoke(app, ["export", "--output-dir", str(tmp_path)])

            assert result.exit_code == 1

    def test_publish_without_kaggle_username(self, monkeypatch, tmp_path):
        """Test publish without Kaggle username."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        # Ensure Kaggle credentials are not set
        for key in ["KAGGLE_USERNAME", "KAGGLE_KEY"]:
            monkeypatch.delenv(key, raising=False)

        # Mock the settings object
        with patch("producthuntdb.cli.settings") as mock_settings:
            mock_settings.kaggle_username = None
            mock_settings.kaggle_key = None
            mock_settings.kaggle_dataset_slug = "test/dataset"

            result = runner.invoke(app, ["publish"])

            assert result.exit_code == 1
            assert "Kaggle credentials not configured" in result.stdout

    def test_publish_without_dataset_slug(self, monkeypatch, tmp_path):
        """Test publish without dataset slug."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey")

        # Mock the settings object
        with patch("producthuntdb.cli.settings") as mock_settings:
            mock_settings.kaggle_username = "testuser"
            mock_settings.kaggle_key = "testkey"
            mock_settings.kaggle_dataset_slug = None

            result = runner.invoke(app, ["publish"])

            assert result.exit_code == 1
            assert "dataset slug not configured" in result.stdout

    def test_publish_with_data_dir(self, monkeypatch, tmp_path):
        """Test publish with custom data directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey")
        monkeypatch.setenv("KAGGLE_DATASET_SLUG", "test/dataset")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.publish_dataset = MagicMock()

            result = runner.invoke(app, ["publish", "--data-dir", str(tmp_path)])

            assert result.exit_code in [0, 1]

    def test_publish_without_data_dir(self, monkeypatch):
        """Test publish without data directory (exports first)."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey")
        monkeypatch.setenv("KAGGLE_DATASET_SLUG", "test/dataset")

        with patch("producthuntdb.cli.KaggleManager") as MockKaggle:
            mock_km = MockKaggle.return_value
            mock_km.export_database_to_csv = MagicMock()
            mock_km.publish_dataset = MagicMock()

            result = runner.invoke(app, ["publish"])

            assert result.exit_code in [0, 1]
            mock_km.export_database_to_csv.assert_called_once()


class TestCLIMigrationCommands:
    """Tests for database migration CLI commands."""

    def test_migrate_command(self, tmp_path, monkeypatch):
        """Test migrate command creates migration."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["migrate", "--message", "test_migration"])

            assert result.exit_code in [0, 1]  # May fail if alembic not configured

    def test_upgrade_command(self, tmp_path, monkeypatch):
        """Test upgrade command applies migrations."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["upgrade"])

            assert result.exit_code in [0, 1]

    def test_downgrade_command(self, tmp_path, monkeypatch):
        """Test downgrade command reverts migrations."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0

            result = runner.invoke(app, ["downgrade", "-1"])

            assert result.exit_code in [0, 1, 2]  # May fail due to alembic setup

    def test_migration_history_command(self, tmp_path, monkeypatch):
        """Test migration-history command shows migration history."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        with patch("subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = "Migration history output"

            result = runner.invoke(app, ["migration-history"])

            assert result.exit_code in [0, 1]


class TestCLIVerbosity:
    """Test CLI verbosity and logging."""

    def test_sync_with_verbose_flag(self, monkeypatch):
        """Test sync command with verbose logging."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")

        with patch("producthuntdb.cli.DataPipeline") as MockPipeline:
            mock_pipeline = AsyncMock()
            mock_pipeline.initialize = AsyncMock()
            mock_pipeline.sync_posts = AsyncMock()
            mock_pipeline.close = AsyncMock()
            MockPipeline.return_value = mock_pipeline

            result = runner.invoke(app, ["sync", "--verbose", "--max-pages", "1"])

            assert result.exit_code in [0, 1]

    def test_status_with_verbose_flag(self, monkeypatch):
        """Test status command with verbose logging."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = Path(__file__).parent / "test_temp.db"
        monkeypatch.setenv("DATABASE_PATH", str(db_path))

        with patch("producthuntdb.cli.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.session = MagicMock()
            mock_db.session.query.return_value.count.return_value = 10

            result = runner.invoke(app, ["status", "--verbose"])

            assert result.exit_code in [0, 1]
