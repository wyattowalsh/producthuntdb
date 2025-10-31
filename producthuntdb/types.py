"""Type definitions for ProductHuntDB.

This module provides TypedDict definitions for Product Hunt API responses,
providing IDE autocomplete, type checking, and clear documentation of data structures.

Reference:
    - PEP 589 TypedDict: https://peps.python.org/pep-0589/
    - docs/source/refactoring-enhancements.md lines 688-750

Example:
    >>> from producthuntdb.types import PostData, PageInfo
    >>> post: PostData = {
    ...     "id": "123",
    ...     "name": "MyProduct",
    ...     "tagline": "A cool product",
    ...     "slug": "myproduct",
    ...     "url": "https://...",
    ...     "userId": "456",
    ...     "votesCount": 100,
    ...     "commentsCount": 20,
    ...     "createdAt": "2024-01-01T00:00:00Z",
    ... }
"""

from typing import NotRequired, Required, TypedDict


# =============================================================================
# Core Entity Types
# =============================================================================


class UserData(TypedDict, total=False):
    """User/Maker data structure from Product Hunt API.

    Attributes:
        id: Required unique identifier
        username: Required username
        name: Required display name
        headline: Optional tagline/bio
        profileImage: Optional avatar URL
        websiteUrl: Optional personal website
        url: Optional Product Hunt profile URL
    """

    id: Required[str]
    username: Required[str]
    name: Required[str]
    headline: NotRequired[str | None]
    profileImage: NotRequired[str | None]
    websiteUrl: NotRequired[str | None]
    url: NotRequired[str | None]


class TopicData(TypedDict, total=False):
    """Topic/Tag data structure from Product Hunt API.

    Attributes:
        id: Required unique identifier
        name: Required display name
        slug: Required URL slug
        description: Optional topic description
        followersCount: Optional follower count
        postsCount: Optional number of posts
    """

    id: Required[str]
    name: Required[str]
    slug: Required[str]
    description: NotRequired[str | None]
    followersCount: NotRequired[int]
    postsCount: NotRequired[int]


class MediaData(TypedDict, total=False):
    """Media (images/videos) data structure from Product Hunt API.

    Attributes:
        type: Required media type (image, video)
        url: Required media URL
        videoUrl: Optional video URL for video type
        imageUuid: Optional image identifier
    """

    type: Required[str]
    url: Required[str]
    videoUrl: NotRequired[str | None]
    imageUuid: NotRequired[str | None]


class ProductLinkData(TypedDict, total=False):
    """Product external link data structure.

    Attributes:
        type: Required link type (website, iOS, Android, etc.)
        url: Required link URL
    """

    type: Required[str]
    url: Required[str]


class GoalData(TypedDict, total=False):
    """Product launch goal data structure.

    Attributes:
        id: Required unique identifier
        name: Required goal name
        externalId: Optional external identifier
    """

    id: Required[str]
    name: Required[str]
    externalId: NotRequired[str | None]


class CollectionData(TypedDict, total=False):
    """Collection data structure from Product Hunt API.

    Attributes:
        id: Required unique identifier
        name: Required collection name
        tagline: Required collection tagline
        url: Required collection URL
        createdAt: Required creation timestamp
        userId: Required owner user ID
        postsCount: Optional number of posts
        backgroundImage: Optional background image URL
        user: Optional owner user data
    """

    id: Required[str]
    name: Required[str]
    tagline: Required[str]
    url: Required[str]
    createdAt: Required[str]
    userId: Required[str]
    postsCount: NotRequired[int]
    backgroundImage: NotRequired[str | None]
    user: NotRequired[UserData]


class CommentData(TypedDict, total=False):
    """Comment data structure from Product Hunt API.

    Attributes:
        id: Required unique identifier
        body: Required comment text
        createdAt: Required creation timestamp
        userId: Required author user ID
        postId: Required parent post ID
        parentCommentId: Optional parent comment (for replies)
        votesCount: Optional vote count
        user: Optional author user data
    """

    id: Required[str]
    body: Required[str]
    createdAt: Required[str]
    userId: Required[str]
    postId: Required[str]
    parentCommentId: NotRequired[str | None]
    votesCount: NotRequired[int]
    user: NotRequired[UserData]


class VoteData(TypedDict, total=False):
    """Vote data structure from Product Hunt API.

    Attributes:
        id: Required unique identifier
        createdAt: Required vote timestamp
        userId: Required voter user ID
        postId: Required voted post ID
        user: Optional voter user data
    """

    id: Required[str]
    createdAt: Required[str]
    userId: Required[str]
    postId: Required[str]
    user: NotRequired[UserData]


class PostData(TypedDict, total=False):
    """Post (Product) data structure from Product Hunt API.

    This is the primary entity containing comprehensive product information.

    Attributes:
        id: Required unique identifier
        name: Required product name
        tagline: Required one-line description
        slug: Required URL slug
        url: Required Product Hunt URL
        userId: Required owner user ID
        votesCount: Required vote count
        commentsCount: Required comment count
        createdAt: Required creation timestamp

        description: Optional full description
        featuredAt: Optional featured timestamp
        website: Optional product website
        reviewsRating: Optional average rating
        reviewsCount: Optional review count
        isCollected: Optional collection status
        isVoted: Optional user vote status

        user: Optional owner user data
        makers: Optional list of maker user data
        topics: Optional topics/tags connection
        media: Optional media items
        productLinks: Optional external links
        goals: Optional launch goals
    """

    id: Required[str]
    name: Required[str]
    tagline: Required[str]
    slug: Required[str]
    url: Required[str]
    userId: Required[str]
    votesCount: Required[int]
    commentsCount: Required[int]
    createdAt: Required[str]

    # Optional fields
    description: NotRequired[str | None]
    featuredAt: NotRequired[str | None]
    website: NotRequired[str | None]
    reviewsRating: NotRequired[float | None]
    reviewsCount: NotRequired[int]
    isCollected: NotRequired[bool]
    isVoted: NotRequired[bool]

    # Nested entities
    user: NotRequired[UserData]
    makers: NotRequired[list[UserData]]
    topics: NotRequired["TopicsConnection"]
    media: NotRequired[list[MediaData]]
    productLinks: NotRequired[list[ProductLinkData]]
    goals: NotRequired[list[GoalData]]


# =============================================================================
# GraphQL Connection Types (Pagination)
# =============================================================================


class PageInfo(TypedDict):
    """GraphQL pagination information.

    Standard GraphQL Cursor Connections Specification structure.

    Attributes:
        hasNextPage: True if more results available after current page
        hasPreviousPage: True if results exist before current page
        startCursor: Cursor for first item in current page (nullable)
        endCursor: Cursor for last item in current page (nullable)

    Reference:
        - GraphQL Cursor Connections: https://relay.dev/graphql/connections.htm
    """

    hasNextPage: bool
    hasPreviousPage: bool
    startCursor: str | None
    endCursor: str | None


class PostsConnection(TypedDict):
    """GraphQL connection structure for posts.

    Attributes:
        nodes: List of post entities
        pageInfo: Pagination metadata
    """

    nodes: list[PostData]
    pageInfo: PageInfo


class TopicsConnection(TypedDict):
    """GraphQL connection structure for topics.

    Attributes:
        nodes: List of topic entities
        pageInfo: Pagination metadata
    """

    nodes: list[TopicData]
    pageInfo: PageInfo


class CollectionsConnection(TypedDict):
    """GraphQL connection structure for collections.

    Attributes:
        nodes: List of collection entities
        pageInfo: Pagination metadata
    """

    nodes: list[CollectionData]
    pageInfo: PageInfo


class CommentsConnection(TypedDict):
    """GraphQL connection structure for comments.

    Attributes:
        nodes: List of comment entities
        pageInfo: Pagination metadata
    """

    nodes: list[CommentData]
    pageInfo: PageInfo


class VotesConnection(TypedDict):
    """GraphQL connection structure for votes.

    Attributes:
        nodes: List of vote entities
        pageInfo: Pagination metadata
    """

    nodes: list[VoteData]
    pageInfo: PageInfo


# =============================================================================
# API Response Wrappers
# =============================================================================


class PostsResponse(TypedDict):
    """Top-level API response for posts query.

    Attributes:
        posts: Posts connection with nodes and pagination
    """

    posts: PostsConnection


class TopicsResponse(TypedDict):
    """Top-level API response for topics query.

    Attributes:
        topics: Topics connection with nodes and pagination
    """

    topics: TopicsConnection


class ViewerResponse(TypedDict):
    """Top-level API response for viewer (authenticated user) query.

    Attributes:
        viewer: Current authenticated user data
    """

    viewer: UserData


class GraphQLResponse(TypedDict):
    """Standard GraphQL response wrapper.

    Attributes:
        data: Response data (structure varies by query)
        errors: Optional list of GraphQL errors
    """

    data: dict[str, object]
    errors: NotRequired[list[dict[str, object]]]


# =============================================================================
# Type Aliases for Common Patterns
# =============================================================================

# Entity data types for batch operations
EntityData = PostData | UserData | TopicData | CollectionData | CommentData | VoteData

# Pagination cursor type
PaginationCursor = str | None

# Timestamp string type
ISOTimestamp = str
