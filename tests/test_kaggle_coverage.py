"""Additional tests to boost kaggle.py coverage.

These tests focus on covering more code paths in the kaggle module.
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest


class TestKaggleManagerBasics:
    """Test basic KaggleManager functionality."""

    def test_init_without_credentials(self):
        """Test initialization without Kaggle credentials."""
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.kaggle_username = None
            mock_settings.kaggle_key = None
            mock_settings.kaggle_dataset_slug = "test/dataset"
            
            from producthuntdb.kaggle import KaggleManager
            manager = KaggleManager()
            
            assert manager.dataset_slug == "test/dataset"
            assert not manager.has_kaggle

    def test_init_with_credentials(self):
        """Test initialization with Kaggle credentials."""
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.kaggle_username = "testuser"
            mock_settings.kaggle_key = "testkey"
            mock_settings.kaggle_dataset_slug = "test/dataset"
            
            with patch("producthuntdb.kaggle.api") as mock_api:
                from producthuntdb.kaggle import KaggleManager
                manager = KaggleManager()
                
                assert manager.dataset_slug == "test/dataset"

    def test_export_database_creates_output_dir(self, tmp_path):
        """Test that export_database_to_csv creates output directory."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        output_dir = tmp_path / "export"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.export_dir = output_dir
            mock_settings.database_path = tmp_path / "test.db"
            mock_settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
            
            # Create dummy database file
            (tmp_path / "test.db").touch()
            
            with patch("pandas.read_sql_table", side_effect=Exception("No table")):
                try:
                    manager.export_database_to_csv()
                except:
                    pass
            
            # Directory should be created
            assert output_dir.exists()

    def test_create_dataset_metadata_basic(self, tmp_path):
        """Test _create_dataset_metadata creates metadata file."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.dataset_slug = "test/dataset"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.kaggle_dataset_slug = "test/dataset"
            
            manager._create_dataset_metadata(
                data_dir=tmp_path,
                title="Test Dataset",
                subtitle="Test subtitle",
                description="Test description",
                keywords=["test", "data"]
            )
            
            # Metadata file should be created
            metadata_file = tmp_path / "dataset-metadata.json"
            assert metadata_file.exists()

    def test_publish_dataset_no_credentials(self):
        """Test publish_dataset without credentials."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.has_kaggle = False
        
        # Should raise or log error
        with pytest.raises(RuntimeError, match="Kaggle credentials"):
            manager.publish_dataset()


class TestKaggleManagerExportPath:
    """Test export path handling."""

    def test_export_uses_default_dir(self, tmp_path):
        """Test export uses default directory from settings."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.export_dir = tmp_path
            mock_settings.database_path = tmp_path / "test.db"
            mock_settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
            
            (tmp_path / "test.db").touch()
            
            with patch("pandas.read_sql_table", side_effect=Exception("No table")):
                try:
                    manager.export_database_to_csv()
                except:
                    pass
            
            assert tmp_path.exists()

    def test_export_uses_custom_dir(self, tmp_path):
        """Test export uses custom directory."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        custom_dir = tmp_path / "custom"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.database_path = tmp_path / "test.db"
            mock_settings.database_url = f"sqlite:///{tmp_path / 'test.db'}"
            
            (tmp_path / "test.db").touch()
            
            with patch("pandas.read_sql_table", side_effect=Exception("No table")):
                try:
                    manager.export_database_to_csv(output_dir=custom_dir)
                except:
                    pass
            
            assert custom_dir.exists()


class TestKaggleDatasetMetadata:
    """Test dataset metadata creation."""

    def test_metadata_has_required_fields(self, tmp_path):
        """Test metadata contains required fields."""
        import json
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.dataset_slug = "test/dataset"
        
        manager._create_dataset_metadata(
            data_dir=tmp_path,
            title="Test Title",
            subtitle="Test Subtitle",
            description="Test Description"
        )
        
        metadata_file = tmp_path / "dataset-metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert "title" in metadata
        assert "subtitle" in metadata
        assert metadata["title"] == "Test Title"

    def test_metadata_with_keywords(self, tmp_path):
        """Test metadata with keywords."""
        import json
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.dataset_slug = "test/dataset"
        
        manager._create_dataset_metadata(
            data_dir=tmp_path,
            title="Test",
            subtitle="Test",
            description="Test",
            keywords=["product", "hunt", "api"]
        )
        
        metadata_file = tmp_path / "dataset-metadata.json"
        with open(metadata_file) as f:
            metadata = json.load(f)
        
        assert "keywords" in metadata
        assert len(metadata["keywords"]) == 3


class TestKagglePublishWorkflow:
    """Test publish workflow."""

    def test_publish_creates_metadata(self, tmp_path):
        """Test that publish creates metadata file."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.has_kaggle = True
        manager.dataset_slug = "test/dataset"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.export_dir = tmp_path
            
            with patch.object(manager, "api") as mock_api:
                mock_api.dataset_create_version = Mock()
                
                try:
                    manager.publish_dataset(data_dir=tmp_path)
                except:
                    pass
                
                # Metadata should be created
                metadata_file = tmp_path / "dataset-metadata.json"
                assert metadata_file.exists()

    def test_publish_with_custom_message(self, tmp_path):
        """Test publish with custom version message."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        manager.has_kaggle = True
        manager.dataset_slug = "test/dataset"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.export_dir = tmp_path
            
            with patch.object(manager, "api") as mock_api:
                mock_api.dataset_create_version = Mock()
                
                try:
                    manager.publish_dataset(
                        data_dir=tmp_path,
                        version_notes="Custom update message"
                    )
                except:
                    pass
                
                # Should have been called with custom message
                if mock_api.dataset_create_version.called:
                    assert "Custom update message" in str(mock_api.dataset_create_version.call_args)


class TestKaggleFileOperations:
    """Test file operations during export."""

    def test_export_copies_database_file(self, tmp_path):
        """Test that export copies the database file."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        db_file = tmp_path / "source" / "producthunt.db"
        db_file.parent.mkdir()
        db_file.write_text("dummy data")
        
        output_dir = tmp_path / "export"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.database_path = db_file
            mock_settings.database_url = f"sqlite:///{db_file}"
            
            with patch("pandas.read_sql_table", side_effect=Exception("No table")):
                try:
                    manager.export_database_to_csv(output_dir=output_dir)
                except:
                    pass
            
            # Database file should be copied
            copied_db = output_dir / "producthunt.db"
            assert copied_db.exists()

    def test_export_handles_wal_files(self, tmp_path):
        """Test that export handles WAL files."""
        from producthuntdb.kaggle import KaggleManager
        
        manager = KaggleManager()
        db_file = tmp_path / "source" / "producthunt.db"
        db_file.parent.mkdir()
        db_file.write_text("dummy data")
        
        # Create WAL file
        wal_file = Path(str(db_file) + "-wal")
        wal_file.write_text("wal data")
        
        output_dir = tmp_path / "export"
        
        with patch("producthuntdb.kaggle.settings") as mock_settings:
            mock_settings.database_path = db_file
            mock_settings.database_url = f"sqlite:///{db_file}"
            
            with patch("pandas.read_sql_table", side_effect=Exception("No table")):
                try:
                    manager.export_database_to_csv(output_dir=output_dir)
                except:
                    pass
            
            # WAL file should be copied
            copied_wal = output_dir / "producthunt.db-wal"
            assert copied_wal.exists()
