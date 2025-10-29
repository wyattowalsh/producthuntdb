"""Configuration management for ProductHuntDB.

This module provides centralized configuration using Pydantic Settings,
supporting both environment variables and Kaggle Secrets.

Example:
    >>> from producthuntdb.config import settings
    >>> print(settings.graphql_endpoint)
    https://api.producthunt.com/v2/api/graphql
"""

import os
from datetime import timedelta
from enum import StrEnum
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class PostsOrder(StrEnum):
    """Post sorting options for GraphQL queries."""

    RANKING      = "RANKING"
    NEWEST       = "NEWEST"
    FEATURED_AT  = "FEATURED_AT"
    VOTES        = "VOTES"


class TopicsOrder(StrEnum):
    """Topic sorting options for GraphQL queries."""

    FOLLOWERS_COUNT = "FOLLOWERS_COUNT"
    NEWEST          = "NEWEST"


class CollectionsOrder(StrEnum):
    """Collection sorting options for GraphQL queries."""

    FEATURED_AT     = "FEATURED_AT"
    FOLLOWERS_COUNT = "FOLLOWERS_COUNT"
    NEWEST          = "NEWEST"


class CommentsOrder(StrEnum):
    """Comment sorting options for GraphQL queries."""

    NEWEST       = "NEWEST"
    VOTES_COUNT  = "VOTES_COUNT"


class Settings(BaseSettings):
    """Application settings with environment variable support.

    Attributes:
        producthunt_token: Product Hunt API token (required)
        kaggle_username: Kaggle username for dataset publishing
        kaggle_key: Kaggle API key for dataset publishing
        graphql_endpoint: Product Hunt GraphQL API endpoint
        database_path: Path to SQLite database file
        max_concurrency: Maximum concurrent API requests
        page_size: Number of items per GraphQL query page
        safety_minutes: Safety margin for incremental updates (minutes)
        kaggle_dataset_slug: Kaggle dataset identifier (username/dataset-name)
        is_kaggle: Flag indicating if running in Kaggle environment
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Configuration
    producthunt_token: str = Field(
        ...,
        alias="PRODUCTHUNT_TOKEN",
        description="Product Hunt API authentication token",
    )

    # Kaggle Configuration
    kaggle_username: Optional[str] = Field(
        None,
        alias="KAGGLE_USERNAME",
        description="Kaggle username for dataset publishing",
    )
    kaggle_key: Optional[str] = Field(
        None,
        alias="KAGGLE_KEY",
        description="Kaggle API key for authentication",
    )
    kaggle_dataset_slug: Optional[str] = Field(
        "wyattowalsh/producthuntdb",
        description="Kaggle dataset identifier (username/dataset-name)",
    )

    # API Endpoints
    graphql_endpoint: str = Field(
        "https://api.producthunt.com/v2/api/graphql",
        description="Product Hunt GraphQL API endpoint",
    )

    # Data Directory Configuration
    data_dir: Path = Field(
        Path("./data"),
        description="Base directory for all data files (database, exports, etc.)",
    )

    # Database Configuration
    database_path: Path = Field(
        Path("producthunt.db"),  # Will be updated to data_dir/producthunt.db by validator
        description="Path to SQLite database file (defaults to data_dir/producthunt.db)",
    )

    # Operational Parameters
    max_concurrency: int = Field(
        3,
        ge=1,
        le=10,
        description="Maximum concurrent API requests",
    )
    page_size: int = Field(
        50,
        ge=1,
        le=100,
        description="Number of items per GraphQL query page",
    )
    safety_minutes: int = Field(
        5,
        ge=0,
        le=60,
        description="Safety margin for incremental updates (minutes)",
    )

    # Environment Detection
    is_kaggle: bool = Field(
        default_factory=lambda: "KAGGLE_KERNEL_RUN_TYPE" in os.environ,
        description="Flag indicating if running in Kaggle environment",
    )

    @field_validator("data_dir", mode="before")
    @classmethod
    def expand_data_dir(cls, v: str | Path) -> Path:
        """Expand and resolve data directory path."""
        path = Path(v).expanduser().resolve()
        # Ensure directory exists
        path.mkdir(parents=True, exist_ok=True)
        return path

    @model_validator(mode="after")
    def set_database_path_default(self) -> "Settings":
        """Set database_path to data_dir/producthunt.db if not explicitly provided."""
        # Check if database_path is still the placeholder
        if self.database_path == Path("producthunt.db"):
            self.database_path = self.data_dir / "producthunt.db"
        # Ensure parent directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        return self

    @field_validator("producthunt_token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        """Validate Product Hunt token format."""
        if not v or len(v) < 10:
            raise ValueError("Product Hunt token must be at least 10 characters")
        return v

    @property
    def safety_timedelta(self) -> timedelta:
        """Get safety margin as timedelta."""
        return timedelta(minutes=self.safety_minutes)

    @property
    def export_dir(self) -> Path:
        """Get export directory path."""
        export_path = self.data_dir / "export"
        export_path.mkdir(parents=True, exist_ok=True)
        return export_path

    @property
    def database_url(self) -> str:
        """Get SQLAlchemy database URL."""
        return f"sqlite:///{self.database_path}"

    def redact_token(self, token: Optional[str] = None) -> str:
        """Redact sensitive token for logging.

        Args:
            token: Token to redact (defaults to producthunt_token)

        Returns:
            Redacted token string
        """
        token = token or self.producthunt_token
        if not token:
            return "None"
        return f"{token[:8]}...{token[-4:]}" if len(token) > 12 else "***"

    def configure_kaggle_env(self) -> None:
        """Configure Kaggle environment variables if credentials are available."""
        if self.kaggle_username:
            os.environ["KAGGLE_USERNAME"] = self.kaggle_username
        if self.kaggle_key:
            os.environ["KAGGLE_KEY"] = self.kaggle_key


def load_kaggle_secrets() -> dict[str, str]:
    """Load secrets from Kaggle Secrets if available.

    Returns:
        Dictionary of secret name to value mappings

    Note:
        Only works in Kaggle notebook environment.
    """
    try:
        from kaggle_secrets import UserSecretsClient  # type: ignore[import-untyped]

        client = UserSecretsClient()
        return {
            "PRODUCTHUNT_TOKEN": client.get_secret("PRODUCTHUNT_TOKEN") or "",
            "KAGGLE_USERNAME": client.get_secret("KAGGLE_USERNAME") or "",
            "KAGGLE_KEY": client.get_secret("KAGGLE_KEY") or "",
        }
    except ImportError:
        return {}


def get_settings() -> Settings:
    """Get settings instance with Kaggle secrets support.

    Returns:
        Configured Settings instance
    """
    # Try loading Kaggle secrets first
    kaggle_secrets = load_kaggle_secrets()

    if kaggle_secrets:
        # Override environment with Kaggle secrets
        for key, value in kaggle_secrets.items():
            if value:
                os.environ[key] = value

    settings_instance = Settings()  # type: ignore[call-arg]
    settings_instance.configure_kaggle_env()
    return settings_instance


# Global settings instance
settings = get_settings()

