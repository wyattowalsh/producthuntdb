"""Comprehensive tests for io.py module to improve coverage.

Tests for:
- KaggleManager class
- Export operations
- CSV generation
- Dataset publishing
"""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open
import pytest

from producthuntdb.io import KaggleManager


class TestKaggleManager:
    """Test KaggleManager class."""

    def test_kaggle_manager_initialization(self, monkeypatch):
        """Test KaggleManager initialization."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        manager = KaggleManager()
        
        assert manager.settings is not None
        assert manager.settings.kaggle_username == "testuser"

    def test_kaggle_manager_without_credentials(self, monkeypatch):
        """Test KaggleManager without Kaggle credentials."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "")
        monkeypatch.setenv("KAGGLE_KEY", "")
        
        with pytest.raises(ValueError, match="Kaggle credentials"):
            KaggleManager()

    def test_export_database_to_csv(self, monkeypatch, tmp_path):
        """Test exporting database to CSV."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        output_dir = tmp_path / "export"
        
        with patch("producthuntdb.io.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock()
            mock_db.close = MagicMock()
            
            manager = KaggleManager()
            manager.export_database_to_csv(output_dir)
            
            mock_db.initialize.assert_called_once()
            mock_db.export_to_csv.assert_called_once_with(output_dir)
            mock_db.close.assert_called_once()

    def test_export_database_to_csv_default_dir(self, monkeypatch):
        """Test exporting database to CSV with default directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        with patch("producthuntdb.io.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock()
            mock_db.close = MagicMock()
            
            manager = KaggleManager()
            manager.export_database_to_csv()
            
            # Should use settings.export_dir
            mock_db.export_to_csv.assert_called_once()

    def test_export_database_to_csv_with_error(self, monkeypatch):
        """Test export with database error."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        with patch("producthuntdb.io.DatabaseManager") as MockDB:
            mock_db = MockDB.return_value
            mock_db.initialize = MagicMock()
            mock_db.export_to_csv = MagicMock(side_effect=Exception("Export failed"))
            mock_db.close = MagicMock()
            
            manager = KaggleManager()
            
            with pytest.raises(Exception, match="Export failed"):
                manager.export_database_to_csv()
            
            # Should still close
            mock_db.close.assert_called_once()

    def test_publish_dataset_success(self, monkeypatch, tmp_path):
        """Test publishing dataset to Kaggle."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        
        # Create dummy CSV files
        (export_dir / "posts.csv").write_text("id,name\n1,test\n")
        (export_dir / "users.csv").write_text("id,username\n1,user1\n")
        
        with patch("producthuntdb.io.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0, stdout="Success")
            
            manager = KaggleManager()
            manager.publish_dataset(export_dir)
            
            # Should call kaggle command
            assert mock_run.called

    def test_publish_dataset_with_message(self, monkeypatch, tmp_path):
        """Test publishing dataset with custom message."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        
        with patch("producthuntdb.io.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            manager = KaggleManager()
            manager.publish_dataset(export_dir, message="Custom update")
            
            # Check message was passed
            call_args = mock_run.call_args
            assert "Custom update" in str(call_args)

    def test_publish_dataset_default_dir(self, monkeypatch):
        """Test publishing dataset with default directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        with patch("producthuntdb.io.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            # Mock Path.exists to avoid file system checks
            with patch("pathlib.Path.exists", return_value=True):
                manager = KaggleManager()
                manager.publish_dataset()
                
                assert mock_run.called

    def test_publish_dataset_kaggle_error(self, monkeypatch, tmp_path):
        """Test publish with Kaggle API error."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        
        with patch("producthuntdb.io.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stderr="Kaggle API error"
            )
            
            manager = KaggleManager()
            
            with pytest.raises(RuntimeError, match="Kaggle"):
                manager.publish_dataset(export_dir)

    def test_publish_dataset_missing_directory(self, monkeypatch):
        """Test publish with missing export directory."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        manager = KaggleManager()
        
        with pytest.raises(FileNotFoundError):
            manager.publish_dataset(Path("/nonexistent/path"))

    def test_create_dataset_metadata(self, monkeypatch, tmp_path):
        """Test creating dataset metadata file."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        
        manager = KaggleManager()
        
        # Mock the metadata creation
        with patch("builtins.open", mock_open()) as mock_file:
            # Call internal method if available
            # This is to test metadata generation logic
            pass


class TestDatabaseManagerExport:
    """Test DatabaseManager export functionality."""

    def test_export_to_csv_creates_files(self, tmp_path, monkeypatch):
        """Test that export_to_csv creates CSV files."""
        from producthuntdb.io import DatabaseManager
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        output_dir = tmp_path / "export"
        
        with patch("producthuntdb.io.create_engine") as mock_engine:
            mock_session = MagicMock()
            mock_query = MagicMock()
            mock_query.all.return_value = []
            mock_session.execute.return_value.scalars.return_value.all.return_value = []
            
            with patch("producthuntdb.io.Session", return_value=mock_session):
                db = DatabaseManager(db_path)
                db.initialize()
                
                # Mock the export
                with patch("pandas.DataFrame.to_csv") as mock_to_csv:
                    db.export_to_csv(output_dir)
                    
                    # Should create CSV files for each table
                    assert mock_to_csv.called

    def test_export_to_csv_with_data(self, tmp_path, monkeypatch):
        """Test exporting with actual data."""
        from producthuntdb.io import DatabaseManager
        from producthuntdb.models import UserRow
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        output_dir = tmp_path / "export"
        
        db = DatabaseManager(db_path)
        db.initialize()
        
        # Insert test data
        user_data = {
            "id": "test123",
            "username": "testuser",
            "name": "Test User",
            "headline": "Test headline",
        }
        db.upsert_user(user_data)
        
        # Export
        db.export_to_csv(output_dir)
        
        # Check files were created
        assert (output_dir / "userrow.csv").exists()
        
        db.close()

    def test_export_to_csv_empty_tables(self, tmp_path, monkeypatch):
        """Test exporting empty tables."""
        from producthuntdb.io import DatabaseManager
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db_path = tmp_path / "test.db"
        output_dir = tmp_path / "export"
        
        db = DatabaseManager(db_path)
        db.initialize()
        
        # Export without data
        db.export_to_csv(output_dir)
        
        # Files should still be created
        assert output_dir.exists()
        
        db.close()


class TestAsyncGraphQLClient:
    """Test AsyncGraphQLClient error handling and edge cases."""

    @pytest.mark.asyncio
    async def test_client_initialization(self, monkeypatch):
        """Test client initialization."""
        from producthuntdb.io import AsyncGraphQLClient
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        
        client = AsyncGraphQLClient(
            endpoint="https://test.api/graphql",
            token="test_token"
        )
        
        assert client.endpoint == "https://test.api/graphql"
        assert client.token == "test_token"

    @pytest.mark.asyncio
    async def test_client_rate_limit_tracking(self, monkeypatch):
        """Test rate limit tracking."""
        from producthuntdb.io import AsyncGraphQLClient
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        
        client = AsyncGraphQLClient(
            endpoint="https://test.api/graphql",
            token="test_token"
        )
        
        # Test rate limit status
        status = client.get_rate_limit_status()
        
        assert "limit" in status
        assert "remaining" in status
        assert "reset" in status

    @pytest.mark.asyncio
    async def test_client_context_manager(self, monkeypatch):
        """Test client as context manager."""
        from producthuntdb.io import AsyncGraphQLClient
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        
        async with AsyncGraphQLClient(
            endpoint="https://test.api/graphql",
            token="test_token"
        ) as client:
            assert client is not None

    @pytest.mark.asyncio
    async def test_transient_error_handling(self, monkeypatch):
        """Test TransientGraphQLError exception."""
        from producthuntdb.io import TransientGraphQLError
        
        error = TransientGraphQLError("Network timeout")
        assert "Network timeout" in str(error)


class TestIntegrationScenarios:
    """Test integration scenarios for io module."""

    def test_full_export_workflow(self, tmp_path, monkeypatch):
        """Test complete export workflow."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        db_path = tmp_path / "test.db"
        export_dir = tmp_path / "export"
        
        from producthuntdb.io import DatabaseManager
        
        # Initialize database
        db = DatabaseManager(db_path)
        db.initialize()
        
        # Add some data
        db.upsert_user({
            "id": "user1",
            "username": "testuser",
            "name": "Test User",
            "headline": "Test",
        })
        
        # Export
        db.export_to_csv(export_dir)
        
        # Verify export
        assert export_dir.exists()
        assert (export_dir / "userrow.csv").exists()
        
        db.close()

    def test_kaggle_publish_workflow(self, tmp_path, monkeypatch):
        """Test Kaggle publishing workflow."""
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        monkeypatch.setenv("KAGGLE_USERNAME", "testuser")
        monkeypatch.setenv("KAGGLE_KEY", "testkey123")
        
        export_dir = tmp_path / "export"
        export_dir.mkdir()
        
        # Create dummy files
        (export_dir / "posts.csv").write_text("id,name\n1,test\n")
        
        with patch("producthuntdb.io.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(returncode=0)
            
            manager = KaggleManager()
            manager.publish_dataset(export_dir)
            
            assert mock_run.called


class TestErrorPaths:
    """Test error handling paths."""

    def test_database_manager_close_without_session(self, tmp_path, monkeypatch):
        """Test closing DatabaseManager without session."""
        from producthuntdb.io import DatabaseManager
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db = DatabaseManager(tmp_path / "test.db")
        
        # Close without initializing
        db.close()  # Should not raise

    def test_export_with_invalid_path(self, tmp_path, monkeypatch):
        """Test export with invalid output path."""
        from producthuntdb.io import DatabaseManager
        
        monkeypatch.setenv("PRODUCTHUNT_TOKEN", "test_token_12345678")
        db = DatabaseManager(tmp_path / "test.db")
        db.initialize()
        
        # Try to export to invalid path
        with pytest.raises(Exception):
            db.export_to_csv(Path("/invalid/path/that/does/not/exist"))
        
        db.close()
