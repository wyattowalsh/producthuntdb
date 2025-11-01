"""Tests for type definitions.

This module tests TypedDict definitions to ensure they accept valid data
and provide proper type hints for IDE autocomplete.

Coverage Target: types.py 0% → 60% (+65 lines)
Priority: High - Type safety verification
"""

from typing import get_type_hints

import pytest

from producthuntdb.types import (
    CollectionData,
    CommentData,
    MediaData,
    PageInfo,
    PostData,
    ProductLinkData,
    TopicData,
    UserData,
    VoteData,
)


# =============================================================================
# UserData Tests
# =============================================================================


def test_user_data_required_fields():
    """Test UserData with required fields only."""
    user: UserData = {
        "id": "user123",
        "username": "testuser",
        "name": "Test User",
    }
    assert user["id"] == "user123"
    assert user["username"] == "testuser"
    assert user["name"] == "Test User"


def test_user_data_all_fields():
    """Test UserData with all fields."""
    user: UserData = {
        "id": "user123",
        "username": "testuser",
        "name": "Test User",
        "headline": "Building awesome things",
        "profileImage": "https://example.com/avatar.jpg",
        "websiteUrl": "https://example.com",
        "url": "https://producthunt.com/@testuser",
    }
    assert user["headline"] == "Building awesome things"
    assert user["profileImage"] == "https://example.com/avatar.jpg"


def test_user_data_optional_none():
    """Test UserData with None optional fields."""
    user: UserData = {
        "id": "user123",
        "username": "testuser",
        "name": "Test User",
        "headline": None,
        "profileImage": None,
    }
    assert user["headline"] is None


# =============================================================================
# TopicData Tests
# =============================================================================


def test_topic_data_required_fields():
    """Test TopicData with required fields."""
    topic: TopicData = {
        "id": "topic123",
        "name": "Productivity",
        "slug": "productivity",
    }
    assert topic["id"] == "topic123"
    assert topic["name"] == "Productivity"


def test_topic_data_all_fields():
    """Test TopicData with all fields."""
    topic: TopicData = {
        "id": "topic123",
        "name": "Productivity",
        "slug": "productivity",
        "description": "Tools to get things done",
        "url": "https://producthunt.com/topics/productivity",
        "createdAt": "2024-01-01T00:00:00Z",
        "followersCount": 5000,
        "postsCount": 1000,
        "isFollowing": False,
        "image": "https://example.com/topic.jpg",
    }
    assert topic["followersCount"] == 5000


# =============================================================================
# PostData Tests
# =============================================================================


def test_post_data_required_fields():
    """Test PostData with required fields."""
    post: PostData = {
        "id": "post123",
        "userId": "user123",
        "name": "Awesome Product",
        "tagline": "The best thing ever",
        "slug": "awesome-product",
        "url": "https://producthunt.com/posts/awesome-product",
        "votesCount": 100,
        "commentsCount": 20,
        "createdAt": "2024-01-15T10:00:00Z",
    }
    assert post["id"] == "post123"
    assert post["votesCount"] == 100


def test_post_data_with_nested_objects():
    """Test PostData with nested user and topics."""
    post: PostData = {
        "id": "post123",
        "userId": "user123",
        "name": "Product",
        "tagline": "Great",
        "slug": "product",
        "url": "https://test.com",
        "votesCount": 50,
        "commentsCount": 10,
        "createdAt": "2024-01-15T10:00:00Z",
        "user": {
            "id": "user123",
            "username": "test",
            "name": "Test",
        },
        "makers": [
            {
                "id": "maker1",
                "username": "maker",
                "name": "Maker",
            }
        ],
        "topics": [
            {
                "id": "topic1",
                "name": "AI",
                "slug": "ai",
            }
        ],
    }
    assert post["user"]["username"] == "test"
    assert len(post["makers"]) == 1
    assert len(post["topics"]) == 1


# =============================================================================
# MediaData Tests
# =============================================================================


def test_media_data_image():
    """Test MediaData for image type."""
    media: MediaData = {
        "type": "image",
        "url": "https://example.com/image.jpg",
    }
    assert media["type"] == "image"
    assert media["url"] == "https://example.com/image.jpg"


def test_media_data_video():
    """Test MediaData for video type."""
    media: MediaData = {
        "type": "video",
        "url": "https://example.com/thumb.jpg",
        "videoUrl": "https://example.com/video.mp4",
    }
    assert media["type"] == "video"
    assert media["videoUrl"] == "https://example.com/video.mp4"


# =============================================================================
# ProductLinkData Tests
# =============================================================================


def test_product_link_data():
    """Test ProductLinkData structure."""
    link: ProductLinkData = {
        "type": "website",
        "url": "https://example.com",
    }
    assert link["type"] == "website"
    assert link["url"] == "https://example.com"


# =============================================================================
# PageInfo Tests
# =============================================================================


def test_page_info_has_next():
    """Test PageInfo with next page."""
    page_info: PageInfo = {
        "hasNextPage": True,
        "endCursor": "cursor123",
    }
    assert page_info["hasNextPage"] is True
    assert page_info["endCursor"] == "cursor123"


def test_page_info_no_next():
    """Test PageInfo without next page."""
    page_info: PageInfo = {
        "hasNextPage": False,
        "endCursor": None,
    }
    assert page_info["hasNextPage"] is False
    assert page_info["endCursor"] is None


# =============================================================================
# CollectionData Tests
# =============================================================================


def test_collection_data_required_fields():
    """Test CollectionData with required fields."""
    collection: CollectionData = {
        "id": "coll123",
        "name": "Best Products 2024",
        "tagline": "Top picks",
        "url": "https://producthunt.com/collections/best-2024",
        "userId": "user123",
    }
    assert collection["id"] == "coll123"
    assert collection["name"] == "Best Products 2024"


def test_collection_data_with_nested():
    """Test CollectionData with nested user, posts, topics."""
    collection: CollectionData = {
        "id": "coll123",
        "name": "Collection",
        "tagline": "Great stuff",
        "url": "https://test.com",
        "userId": "user123",
        "user": {
            "id": "user123",
            "username": "curator",
            "name": "Curator",
        },
        "posts": [
            {
                "id": "post1",
                "userId": "user1",
                "name": "Product1",
                "tagline": "Cool",
                "slug": "product1",
                "url": "https://test.com/p1",
                "votesCount": 10,
                "commentsCount": 2,
                "createdAt": "2024-01-01T00:00:00Z",
            }
        ],
        "topics": [
            {
                "id": "topic1",
                "name": "Tech",
                "slug": "tech",
            }
        ],
    }
    assert collection["user"]["username"] == "curator"
    assert len(collection["posts"]) == 1
    assert len(collection["topics"]) == 1


# =============================================================================
# CommentData Tests
# =============================================================================


def test_comment_data_required_fields():
    """Test CommentData with required fields."""
    comment: CommentData = {
        "id": "comment123",
        "body": "Great product!",
        "url": "https://producthunt.com/posts/p/comments/c",
        "createdAt": "2024-01-15T12:00:00Z",
        "userId": "user123",
    }
    assert comment["id"] == "comment123"
    assert comment["body"] == "Great product!"


def test_comment_data_with_user():
    """Test CommentData with nested user."""
    comment: CommentData = {
        "id": "comment123",
        "body": "Nice!",
        "url": "https://test.com",
        "createdAt": "2024-01-15T12:00:00Z",
        "userId": "user123",
        "user": {
            "id": "user123",
            "username": "commenter",
            "name": "Commenter",
        },
    }
    assert comment["user"]["username"] == "commenter"


# =============================================================================
# VoteData Tests
# =============================================================================


def test_vote_data_required_fields():
    """Test VoteData with required fields."""
    vote: VoteData = {
        "id": "vote123",
        "userId": "user123",
        "createdAt": "2024-01-15T11:00:00Z",
    }
    assert vote["id"] == "vote123"
    assert vote["userId"] == "user123"


def test_vote_data_with_user():
    """Test VoteData with nested user."""
    vote: VoteData = {
        "id": "vote123",
        "userId": "user123",
        "createdAt": "2024-01-15T11:00:00Z",
        "user": {
            "id": "user123",
            "username": "voter",
            "name": "Voter",
        },
    }
    assert vote["user"]["username"] == "voter"


# =============================================================================
# Type Hint Tests
# =============================================================================


def test_type_hints_exist():
    """Test that TypedDict classes have proper type hints."""
    user_hints = get_type_hints(UserData)
    assert "id" in user_hints
    assert "username" in user_hints
    assert "name" in user_hints

    post_hints = get_type_hints(PostData)
    assert "id" in post_hints
    assert "votesCount" in post_hints

    topic_hints = get_type_hints(TopicData)
    assert "id" in topic_hints
    assert "slug" in topic_hints


# =============================================================================
# Edge Cases
# =============================================================================


def test_empty_optional_lists():
    """Test TypedDicts with empty optional lists."""
    post: PostData = {
        "id": "post123",
        "userId": "user123",
        "name": "Product",
        "tagline": "Great",
        "slug": "product",
        "url": "https://test.com",
        "votesCount": 0,
        "commentsCount": 0,
        "createdAt": "2024-01-01T00:00:00Z",
        "makers": [],
        "topics": [],
    }
    assert post["makers"] == []
    assert post["topics"] == []


def test_none_optional_fields():
    """Test TypedDicts with None optional fields."""
    post: PostData = {
        "id": "post123",
        "userId": "user123",
        "name": "Product",
        "tagline": "Great",
        "slug": "product",
        "url": "https://test.com",
        "votesCount": 0,
        "commentsCount": 0,
        "createdAt": "2024-01-01T00:00:00Z",
        "description": None,
        "website": None,
        "featuredAt": None,
    }
    assert post["description"] is None
    assert post["website"] is None
