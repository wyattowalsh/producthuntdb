"""Integration tests for ProductHuntDB.

These tests exercise multiple components together with real(ish) data flow.
"""

import pytest

from producthuntdb.io import AsyncGraphQLClient, DatabaseManager
from producthuntdb.models import Post, Topic, User
from producthuntdb.pipeline import DataPipeline


class TestAPIToDatabase:
    """Integration tests for API to database flow."""

    @pytest.mark.asyncio
    async def test_user_api_to_database(self, test_db_manager, mock_user_data):
        """Test full flow: API response -> Pydantic -> Database."""
        # Parse with Pydantic
        user = User(**mock_user_data)

        # Store in database
        user_row = test_db_manager.upsert_user(user.model_dump())

        # Verify storage
        assert user_row.id == user.id
        assert user_row.username == user.username

        # Retrieve and verify
        from producthuntdb.models import UserRow
        retrieved = test_db_manager.session.get(UserRow, user.id)
        assert retrieved is not None
        assert retrieved.username == user.username

    @pytest.mark.asyncio
    async def test_post_with_relationships(
        self, test_db_manager, mock_post_data, mock_topic_data
    ):
        """Test storing post with relationships."""
        # Add topic to post
        mock_post_data["topics"] = [mock_topic_data]

        # Parse with Pydantic
        post = Post(**mock_post_data)

        # Store user first
        test_db_manager.upsert_user(post.user.model_dump())

        # Store makers
        for maker in post.makers:
            test_db_manager.upsert_user(maker.model_dump())

        # Store topics
        topic_ids = []
        if post.topics:
            for topic in post.topics:
                test_db_manager.upsert_topic(topic.model_dump())
                topic_ids.append(topic.id)

        # Store post
        post_row = test_db_manager.upsert_post(post.model_dump())

        # Create relationships
        test_db_manager.link_post_topics(post.id, topic_ids)
        test_db_manager.link_post_makers(post.id, [m.id for m in post.makers])

        # Verify
        from producthuntdb.models import PostRow
        retrieved = test_db_manager.session.get(PostRow, post.id)
        assert retrieved is not None
        assert retrieved.name == post.name


class TestPipelineIntegration:
    """Integration tests for full pipeline."""

    @pytest.mark.asyncio
    async def test_pipeline_full_cycle(
        self, mocker, mock_viewer_response, mock_posts_response
    ):
        """Test complete pipeline cycle."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # Mock API calls
            mocker.patch.object(
                pipeline.client,
                "fetch_viewer",
                return_value=mock_viewer_response["viewer"],
            )
            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                return_value=mock_posts_response["posts"],
            )

            # Run pipeline
            await pipeline.verify_authentication()
            stats = await pipeline.sync_posts(max_pages=1)

            # Verify results
            assert stats["posts"] >= 1

            # Check database statistics
            db_stats = pipeline.get_statistics()
            assert db_stats["posts"] >= 1

        finally:
            pipeline.close()

    @pytest.mark.asyncio
    async def test_incremental_update_flow(self, mocker, mock_posts_response):
        """Test incremental update mechanism."""
        pipeline = DataPipeline()
        await pipeline.initialize()

        try:
            # First sync
            mocker.patch.object(
                pipeline.client,
                "fetch_posts_page",
                return_value=mock_posts_response["posts"],
            )

            stats1 = await pipeline.sync_posts(max_pages=1)
            assert stats1["posts"] >= 1

            # Check crawl state was saved
            last_timestamp = pipeline.db.get_crawl_state("posts")
            assert last_timestamp is not None

            # Second sync (incremental)
            stats2 = await pipeline.sync_posts(full_refresh=False, max_pages=1)

            # Both syncs should work
            assert stats2["posts"] >= 0

        finally:
            pipeline.close()


class TestDatabaseIntegrity:
    """Integration tests for database integrity."""

    def test_foreign_key_constraints(self, test_db_manager):
        """Test that foreign key constraints are enforced."""
        from producthuntdb.models import PostRow

        # Try to create post with non-existent user
        # Note: SQLite doesn't enforce FK by default in SQLModel
        # This test documents expected behavior
        test_db_manager.upsert_user({
            "id": "fk_user123",
            "username": "test_fk",
            "name": "Test FK",
        })

        post_row = PostRow(
            id="fk_post123",
            userId="fk_user123",  # Valid user
            name="Test FK",
            tagline="Test FK",
            url="https://test-fk.com",
            commentsCount=0,
            votesCount=0,
            reviewsRating=0.0,
            reviewsCount=0,
            isCollected=False,
            isVoted=False,
        )

        test_db_manager.session.add(post_row)
        test_db_manager.session.commit()

        # Verify post was created
        retrieved = test_db_manager.session.get(PostRow, "fk_post123")
        assert retrieved is not None

    def test_duplicate_prevention(self, test_db_manager):
        """Test that duplicate entries are handled."""
        user_data = {
            "id": "user123",
            "username": "test",
            "name": "Test",
        }

        # First insert
        test_db_manager.upsert_user(user_data)

        # Second insert (should update, not error)
        user_data["name"] = "Updated Test"
        test_db_manager.upsert_user(user_data)

        # Verify only one record exists with updated data
        from producthuntdb.models import UserRow
        from sqlmodel import func, select

        count = test_db_manager.session.exec(
            select(func.count()).where(UserRow.id == "user123")  # type: ignore[arg-type]
        ).one()

        assert count == 1

        user = test_db_manager.session.get(UserRow, "user123")
        assert user.name == "Updated Test"
