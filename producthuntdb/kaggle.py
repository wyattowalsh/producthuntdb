"""Kaggle dataset management for ProductHuntDB.

This module handles exporting database to CSV files and publishing to Kaggle datasets.

Reference:
    - Extracted from io.py lines 805-1518

Example:
    >>> from producthuntdb.kaggle import KaggleManager
    >>> 
    >>> km = KaggleManager()
    >>> 
    >>> # Export database to CSV
    >>> km.export_database_to_csv()
    >>> 
    >>> # Publish to Kaggle
    >>> km.publish_dataset()
"""

import json
import shutil
from pathlib import Path

from producthuntdb.config import settings
from producthuntdb.logging import logger


# =============================================================================
# Kaggle Manager
# =============================================================================


class KaggleManager:
    """Manages Kaggle dataset operations.

    Features:
    - Export database tables to CSV files
    - Copy database file with WAL/SHM files
    - Create comprehensive dataset metadata
    - Publish or update Kaggle datasets

    Example:
        >>> km = KaggleManager()
        >>> 
        >>> if km.has_kaggle:
        ...     km.export_database_to_csv()
        ...     km.publish_dataset()
        ... else:
        ...     print("Kaggle credentials not configured")
    """

    def __init__(self):
        """Initialize Kaggle manager.
        
        Checks for Kaggle credentials and initializes Kaggle API if available.
        Sets has_kaggle=False if credentials missing or API import fails.
        """
        self.dataset_slug = settings.kaggle_dataset_slug
        self.has_kaggle = settings.has_kaggle_credentials

        if self.has_kaggle:
            # Import kaggle API only if credentials are available
            try:
                from kaggle import api  # type: ignore[import-not-found]

                self.api = api
                logger.info("✅ Kaggle API initialized")
            except Exception as exc:
                logger.warning(f"⚠️ Kaggle API import failed: {exc}")
                self.has_kaggle = False

    def export_database_to_csv(self, output_dir: Path | None = None) -> None:
        """Export database tables to CSV files and copy database file.

        This method:
        1. Copies SQLite database file to output directory
        2. Copies WAL and SHM files if they exist (for WAL mode)
        3. Exports all tables to individual CSV files

        Args:
            output_dir: Directory to write files (defaults to settings.export_dir)

        Example:
            >>> km.export_database_to_csv()
            # Creates: export/producthunt.db, export/postrow.csv, etc.
        """
        import pandas as pd  # type: ignore[import-not-found]
        from sqlalchemy import create_engine as sa_create_engine

        # Use settings.export_dir if output_dir not provided
        output_dir = output_dir or settings.export_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        # Copy the SQLite database file
        db_path = Path(str(settings.database_path))
        if db_path.exists():
            dest_db = output_dir / "producthunt.db"
            shutil.copy2(db_path, dest_db)
            logger.info(f"✅ Copied database to {dest_db}")

            # Also copy WAL and SHM files if they exist (for WAL mode)
            for ext in ["-wal", "-shm"]:
                wal_path = Path(str(db_path) + ext)
                if wal_path.exists():
                    shutil.copy2(wal_path, output_dir / f"producthunt.db{ext}")

        # Export tables to CSV
        engine = sa_create_engine(settings.database_url)

        tables = [
            "userrow",
            "postrow",
            "topicrow",
            "collectionrow",
            "commentrow",
            "voterow",
            "posttopiclink",
            "makerpostlink",
            "collectionpostlink",
            "crawlstate",
        ]

        for table in tables:
            try:
                df = pd.read_sql_table(table, engine)
                csv_path = output_dir / f"{table}.csv"
                df.to_csv(csv_path, index=False)
                logger.info(f"✅ Exported {table} ({len(df)} rows) to {csv_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to export {table}: {e}")

    def publish_dataset(
        self,
        data_dir: Path | None = None,
        title: str = "ProductHuntDB - Complete Product Hunt Data Archive",
        subtitle: str = "Daily-updated GraphQL API data: products, users, topics, collections, votes & more",
    ) -> None:
        """Publish or update Kaggle dataset.

        Creates comprehensive metadata following Kaggle Data Package specification,
        then either creates new dataset or updates existing one.

        Args:
            data_dir: Directory containing database and CSV files (defaults to settings.export_dir)
            title: Dataset title (6-50 characters)
            subtitle: Dataset subtitle (20-80 characters)

        Example:
            >>> km.publish_dataset()
            # Creates/updates dataset at kaggle.com/datasets/{username}/{dataset-name}
        """
        if not self.has_kaggle:
            logger.warning("⚠️ Kaggle credentials not configured")
            return

        if not self.dataset_slug:
            logger.warning("⚠️ Kaggle dataset slug not configured")
            return

        # Use settings.export_dir if data_dir not provided
        data_dir = data_dir or settings.export_dir

        # Ensure data directory exists
        if not data_dir.exists():
            raise ValueError(f"Data directory does not exist: {data_dir}")

        # Create comprehensive metadata
        metadata = self._create_metadata(title, subtitle)

        metadata_path = data_dir / "dataset-metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✅ Created metadata file: {metadata_path}")

        try:
            # Check if dataset exists
            try:
                self.api.dataset_status(self.dataset_slug)
                # Dataset exists, create new version
                logger.info(f"📤 Updating Kaggle dataset: {self.dataset_slug}")
                self.api.dataset_create_version(
                    str(data_dir),
                    version_notes="Automated update from ProductHuntDB pipeline",
                    dir_mode="zip",
                )
                logger.info("✅ Kaggle dataset updated successfully")
            except Exception:
                # Dataset doesn't exist, create it
                logger.info(f"📤 Creating new Kaggle dataset: {self.dataset_slug}")
                self.api.dataset_create_new(
                    str(data_dir), public=True, quiet=False, dir_mode="zip"
                )
                logger.info("✅ Kaggle dataset created successfully")

        except Exception as e:
            logger.error(f"❌ Failed to publish Kaggle dataset: {e}")
            raise

    def _create_metadata(self, title: str, subtitle: str) -> dict:
        """Create comprehensive Kaggle dataset metadata.

        Args:
            title: Dataset title
            subtitle: Dataset subtitle

        Returns:
            Metadata dictionary following Kaggle Data Package spec
        """
        return {
            "title": title,
            "id": self.dataset_slug,
            "subtitle": subtitle,
            "description": self._get_description(),
            "isPrivate": False,
            "licenses": [{"name": "CC0-1.0"}],
            "keywords": [
                "product-hunt",
                "graphql-api",
                "time-series",
                "products",
                "startups",
                "technology",
                "sqlite",
                "csv",
                "normalized-data",
                "analytics",
                "machine-learning",
            ],
            "collaborators": [],
            "data": [],
            "resources": self._get_resources(),
        }

    def _get_description(self) -> str:
        """Get dataset description in markdown format.

        Returns:
            Comprehensive markdown description
        """
        return """# ProductHunt GraphQL API Data Sink

A comprehensive dataset containing Product Hunt data extracted via the official GraphQL API.

## 📊 Dataset Contents

- **Posts**: Product launches with metadata (~50K-100K rows)
- **Topics**: Product categories and tags (~1K-2K rows)
- **Collections**: Curated product collections (~5K-10K rows)
- **Users**: Maker and user profiles (~100K-200K rows)
- **Comments**: Community discussions (~200K-500K rows)
- **Votes**: Product upvotes (~1M-5M rows)

## 🔄 Update Schedule

**Daily Updates**: Refreshed daily via automated sync (02:00 UTC)

## 🛠️ Data Collection

- **Source**: Official Product Hunt GraphQL API (v2)
- **Sync Strategy**: Incremental updates with cursor-based pagination
- **Data Validation**: Pydantic v2 schemas with type checking

## 📖 Documentation

- **GitHub**: [producthuntdb](https://github.com/wyattowalsh/producthuntdb)
- **License**: CC0-1.0 (Public Domain)

## 💡 Example Usage

```python
import pandas as pd
import sqlite3

# Load SQLite database
conn = sqlite3.connect('producthunt.db')

# Query top products
df = pd.read_sql(\"\"\"
    SELECT name, tagline, votesCount 
    FROM postrow 
    ORDER BY votesCount DESC 
    LIMIT 10
\"\"\", conn)
```
"""

    def _get_resources(self) -> list[dict]:
        """Get resource descriptions for dataset files.

        Returns:
            List of resource metadata dictionaries
        """
        return [
            {
                "path": "producthunt.db",
                "description": "Complete SQLite database with all tables, indexes, and relationships",
            },
            {
                "path": "userrow.csv",
                "description": "User profiles including makers, hunters, and voters",
            },
            {
                "path": "postrow.csv",
                "description": "Product launches with metadata and engagement metrics",
            },
            {
                "path": "topicrow.csv",
                "description": "Product categories and tags",
            },
            {
                "path": "collectionrow.csv",
                "description": "Curated product collections",
            },
            {
                "path": "commentrow.csv",
                "description": "Community comments and discussions",
            },
            {
                "path": "voterow.csv",
                "description": "Individual upvote records",
            },
            {
                "path": "posttopiclink.csv",
                "description": "Many-to-many links between posts and topics",
            },
            {
                "path": "makerpostlink.csv",
                "description": "Many-to-many links between makers and products",
            },
            {
                "path": "collectionpostlink.csv",
                "description": "Many-to-many links between collections and products",
            },
            {
                "path": "crawlstate.csv",
                "description": "System metadata for incremental sync tracking",
            },
        ]


# =============================================================================
# Export Public API
# =============================================================================

__all__ = ["KaggleManager"]
