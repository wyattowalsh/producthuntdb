"""ProductHuntDB - Product Hunt API data sink and Kaggle dataset manager.

This package provides a production-grade data pipeline for harvesting data from
the Product Hunt GraphQL API, storing it in SQLite, and publishing to Kaggle.

Example:
    >>> from producthuntdb import DataPipeline
    >>> import asyncio
    >>>
    >>> async def main():
    ...     pipeline = DataPipeline()
    ...     await pipeline.initialize()
    ...     await pipeline.sync_posts()
    ...     pipeline.close()
    >>>
    >>> asyncio.run(main())
"""

from producthuntdb.config import settings
from producthuntdb.io import AsyncGraphQLClient, DatabaseManager, KaggleManager
from producthuntdb.models import (
    Collection,
    CollectionRow,
    Comment,
    CommentRow,
    Post,
    PostRow,
    Topic,
    TopicRow,
    User,
    UserRow,
    Vote,
    VoteRow,
)
from producthuntdb.pipeline import DataPipeline

__version__ = "0.1.0"

__all__ = [
    # Main components
    "DataPipeline",
    "AsyncGraphQLClient",
    "DatabaseManager",
    "KaggleManager",
    # Configuration
    "settings",
    # Pydantic models
    "Post",
    "User",
    "Topic",
    "Collection",
    "Comment",
    "Vote",
    # SQLModel tables
    "PostRow",
    "UserRow",
    "TopicRow",
    "CollectionRow",
    "CommentRow",
    "VoteRow",
]

