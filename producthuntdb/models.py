"""Data models for ProductHuntDB.

This module defines both Pydantic validation models (for API responses)
and SQLModel ORM models (for database persistence).

Models are organized into three sections:
1. Pydantic models for GraphQL API responses
2. SQLModel tables for database persistence
3. Link tables for many-to-many relationships
"""

import json
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator
from sqlmodel import Field, SQLModel

from producthuntdb.utils import format_iso, parse_datetime

# =============================================================================
# Section 1: Pydantic Models for GraphQL API Responses
# =============================================================================


class PageInfo(BaseModel):
    """Pagination metadata from GraphQL connection.

    Attributes:
        startCursor: Cursor to the first edge returned
        endCursor: Cursor to the last edge returned
        hasNextPage: True if another page can be fetched forward
        hasPreviousPage: True if another page can be fetched backward
    """

    model_config = ConfigDict(extra="ignore")

    startCursor: Optional[str] = None
    endCursor: Optional[str] = None
    hasNextPage: bool
    hasPreviousPage: Optional[bool] = None


class Error(BaseModel):
    """GraphQL mutation error payload.

    Attributes:
        code: Error code identifier
        message: Human-readable error message
    """

    model_config = ConfigDict(extra="ignore")

    code: Optional[str] = None
    message: Optional[str] = None


class User(BaseModel):
    """Product Hunt user account.

    Attributes:
        id: Unique user ID
        username: User handle on Product Hunt
        name: Display name
        headline: Short bio/headline
        twitterUsername: Twitter/X username
        websiteUrl: Personal site URL
        url: Public profile URL on Product Hunt
        createdAt: Account creation timestamp (UTC)
        profileImage: Avatar URL
        coverImage: Cover image URL
        isMaker: Whether user is a maker
        isFollowing: Whether viewer is following this user
        isViewer: True if this user is the authenticated viewer
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    username: str
    name: str
    headline: Optional[str] = None
    twitterUsername: Optional[str] = None
    websiteUrl: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[datetime] = None
    profileImage: Optional[str] = None
    coverImage: Optional[str] = None
    isMaker: Optional[bool] = None
    isFollowing: Optional[bool] = None
    isViewer: Optional[bool] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Topic(BaseModel):
    """Product Hunt topic for categorizing posts.

    Attributes:
        id: Unique topic ID
        name: Topic display name
        slug: URL slug
        description: Topic description
        url: Public URL
        createdAt: Creation timestamp UTC
        followersCount: Number of followers
        postsCount: Number of associated posts
        isFollowing: Whether viewer follows this topic
        image: Topic image URL
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    slug: str
    description: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[datetime] = None
    followersCount: Optional[int] = None
    postsCount: Optional[int] = None
    isFollowing: Optional[bool] = None
    image: Optional[str] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Collection(BaseModel):
    """Curated collection of Product Hunt posts.

    Attributes:
        id: Unique collection ID
        name: Title of the collection
        tagline: Short tagline
        description: Longer description
        url: Public URL
        coverImage: Background/cover image URL
        createdAt: Creation timestamp UTC
        featuredAt: When the collection was featured
        followersCount: Follower count
        isFollowing: Whether viewer follows this collection
        userId: ID of the curator user
        user: Curator user object
        posts: Lightweight posts listing
        topics: Lightweight topics listing
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    tagline: str
    description: Optional[str] = None
    url: str
    coverImage: Optional[str] = None
    createdAt: Optional[datetime] = None
    featuredAt: Optional[datetime] = None
    followersCount: int
    isFollowing: bool
    userId: str
    user: Optional[User] = None
    posts: Optional[list[dict]] = None
    topics: Optional[list[dict]] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("featuredAt", mode="before")
    @classmethod
    def _coerce_featured_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Vote(BaseModel):
    """Upvote on a post or comment.

    Attributes:
        id: Unique vote ID
        createdAt: Timestamp of the vote (UTC)
        user: The user who cast the vote
        userId: The voter's user ID
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    createdAt: Optional[datetime] = None
    user: Optional[User] = None
    userId: str

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Media(BaseModel):
    """Media object (image/video) associated with a post.

    Attributes:
        type: Type of media (e.g., "image", "video")
        url: Public URL for the media (thumbnail for videos)
        videoUrl: Video URL if type is video
    """

    model_config = ConfigDict(extra="ignore")

    type: str
    url: str
    videoUrl: Optional[str] = None


class Comment(BaseModel):
    """Comment in a Product Hunt thread.

    Attributes:
        id: Unique comment ID
        body: Markdown/text body
        url: Public URL to the comment
        createdAt: Creation timestamp (UTC)
        isVoted: Whether viewer has voted for this comment
        votesCount: Total number of votes
        user: Author of the comment
        parentId: ID of parent comment (for threads)
        parent: Parent comment object
        replies: Reply comments
        votes: Vote objects
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    body: str
    url: str
    createdAt: Optional[datetime] = None
    isVoted: bool
    votesCount: int
    user: User
    parentId: Optional[str] = None
    parent: Optional["Comment"] = None
    replies: Optional[list["Comment"]] = None
    votes: Optional[list[Vote]] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Post(BaseModel):
    """Product Hunt post/launch.

    Attributes:
        id: Unique post ID
        userId: ID of the submitting user
        name: Product name
        tagline: Short blurb
        description: Longer description text
        slug: Post slug
        url: Public Product Hunt URL
        website: External product website
        createdAt: Creation timestamp UTC
        featuredAt: Time it was featured
        commentsCount: Number of comments
        votesCount: Number of votes
        reviewsRating: Average review rating
        reviewsCount: Number of reviews
        isCollected: Whether viewer collected it
        isVoted: Whether viewer upvoted it
        user: Submitter/hunter
        makers: Makers of the product
        topics: Topics assigned to the post
        thumbnail: Thumbnail media object
        media: Additional screenshots/media objects
        productLinks: Related product links
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    userId: str
    name: str
    tagline: str
    description: Optional[str] = None
    slug: Optional[str] = None
    url: str
    website: Optional[str] = None
    createdAt: Optional[datetime] = None
    featuredAt: Optional[datetime] = None
    commentsCount: int
    votesCount: int
    reviewsRating: float
    reviewsCount: int
    isCollected: bool
    isVoted: bool
    user: User
    makers: list[User]
    topics: Optional[list[Topic]] = None
    thumbnail: Optional[Media] = None
    media: Optional[list[Media]] = None
    productLinks: Optional[list[dict]] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("featuredAt", mode="before")
    @classmethod
    def _coerce_featured_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("topics", mode="before")
    @classmethod
    def _extract_topics_nodes(cls, v):
        """Extract nodes from GraphQL connection object if needed."""
        if v is None:
            return None
        if isinstance(v, dict) and "nodes" in v:
            return v["nodes"]
        return v

    @field_validator("thumbnail", mode="before")
    @classmethod
    def _coerce_thumbnail(cls, v):
        """Convert thumbnail dict to Media object if needed."""
        if v is None or isinstance(v, Media):
            return v
        if isinstance(v, dict):
            return Media(**v)
        return v

    @field_validator("media", mode="before")
    @classmethod
    def _coerce_media(cls, v):
        """Convert media dicts to Media objects if needed."""
        if v is None:
            return None
        if isinstance(v, list):
            return [Media(**m) if isinstance(m, dict) else m for m in v]
        return v


class MakerProject(BaseModel):
    """A maker's project on Product Hunt.

    Attributes:
        id: Unique project ID
        name: Project name
        tagline: Short description
        image: Project image URL
        url: Public URL
        lookingForOtherMakers: Whether seeking collaborators
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    tagline: str
    image: Optional[str] = None
    url: str
    lookingForOtherMakers: bool


class MakerGroup(BaseModel):
    """A maker group (Space) on Product Hunt.

    Attributes:
        id: Unique group ID
        name: Group name
        tagline: Short description
        description: Full description
        url: Public URL
        membersCount: Number of members
        goalsCount: Number of goals created
        isMember: Whether viewer is a member
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    tagline: str
    description: str
    url: str
    membersCount: int
    goalsCount: int
    isMember: bool


class Goal(BaseModel):
    """A maker's goal on Product Hunt.

    Attributes:
        id: Unique goal ID
        title: Goal title
        userId: ID of user who created the goal
        groupId: ID of the maker group this goal belongs to
        projectId: ID of the maker project (optional)
        createdAt: Creation timestamp UTC
        dueAt: Due date timestamp UTC (optional)
        completedAt: Completion timestamp UTC (optional)
        currentUntil: Timestamp until this is the current goal
        current: Whether this is the user's current goal
        cheerCount: Number of cheers
        isCheered: Whether viewer has cheered
        focusedDuration: Time spent in focus mode (seconds)
        url: Public URL
        user: User who created the goal
        group: MakerGroup this goal belongs to
        project: MakerProject (optional)
    """

    model_config = ConfigDict(extra="ignore")

    id: str
    title: str
    userId: str
    groupId: str
    projectId: Optional[str] = None
    createdAt: Optional[datetime] = None
    dueAt: Optional[datetime] = None
    completedAt: Optional[datetime] = None
    currentUntil: Optional[datetime] = None
    current: bool
    cheerCount: int
    isCheered: bool
    focusedDuration: int
    url: str
    user: Optional[User] = None
    group: Optional[MakerGroup] = None
    project: Optional[MakerProject] = None

    @field_validator("createdAt", mode="before")
    @classmethod
    def _coerce_created_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("dueAt", mode="before")
    @classmethod
    def _coerce_due_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("completedAt", mode="before")
    @classmethod
    def _coerce_completed_at(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)

    @field_validator("currentUntil", mode="before")
    @classmethod
    def _coerce_current_until(cls, v: Optional[str]) -> Optional[datetime]:
        return parse_datetime(v)


class Viewer(BaseModel):
    """Authenticated viewer information.

    Attributes:
        user: The viewer's own User object (isViewer=True)
    """

    model_config = ConfigDict(extra="ignore")

    user: User


# =============================================================================
# Section 2: SQLModel Tables for Database Persistence
# =============================================================================


class CrawlState(SQLModel, table=True):
    """Tracks incremental crawl progress checkpoints.

    Attributes:
        entity: Logical entity name (e.g., "posts") - primary key
        last_timestamp: Most recent fully-processed timestamp (ISO8601 UTC)
        updated_at: Timestamp of when this row was last updated
    """

    entity: str = Field(primary_key=True)
    last_timestamp: Optional[str] = None
    updated_at: str


class UserRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt User.

    Attributes:
        id: User ID (primary key)
        username: Product Hunt handle
        name: Display name
        headline: User headline/bio
        twitterUsername: X/Twitter handle
        websiteUrl: Personal site
        url: Public Product Hunt profile URL
        createdAt: ISO8601 UTC creation timestamp (indexed)
        isMaker: Whether PH considers them a maker
        isFollowing: Whether viewer is following them
        isViewer: True if this row is the authenticated viewer
        profileImage: Avatar URL
        coverImage: Cover image URL
    """

    id: str = Field(primary_key=True)
    username: str
    name: str
    headline: Optional[str] = None
    twitterUsername: Optional[str] = None
    websiteUrl: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[str] = Field(default=None, index=True)
    isMaker: Optional[bool] = None
    isFollowing: Optional[bool] = None
    isViewer: Optional[bool] = None
    profileImage: Optional[str] = None
    coverImage: Optional[str] = None

    @classmethod
    def from_pydantic(cls, user: User) -> "UserRow":
        """Create UserRow from Pydantic User model."""
        return cls(
            id=user.id,
            username=user.username,
            name=user.name,
            headline=user.headline,
            twitterUsername=user.twitterUsername,
            websiteUrl=user.websiteUrl,
            url=user.url,
            createdAt=format_iso(user.createdAt),
            isMaker=user.isMaker,
            isFollowing=user.isFollowing,
            isViewer=user.isViewer,
            profileImage=user.profileImage,
            coverImage=user.coverImage,
        )


class PostRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt Post.

    Attributes:
        id: Post ID (primary key)
        userId: FK to submitting UserRow.id
        name: Product name
        tagline: Short blurb
        description: Longer description
        slug: Slug
        url: PH URL
        website: External website
        createdAt: ISO8601 UTC creation timestamp (indexed)
        featuredAt: ISO8601 UTC featured timestamp
        commentsCount: Comment count
        votesCount: Vote count
        reviewsRating: Average review rating
        reviewsCount: Review count
        isCollected: Viewer collected?
        isVoted: Viewer voted?
        thumbnail_type: Thumbnail media type
        thumbnail_url: Thumbnail URL
        thumbnail_videoUrl: Thumbnail video URL (if video)
        productlinks_json: JSON stringified list of productLinks dicts
    """

    id: str = Field(primary_key=True)
    userId: str = Field(foreign_key="userrow.id")
    name: str
    tagline: str
    description: Optional[str] = None
    slug: Optional[str] = None
    url: str
    website: Optional[str] = None
    createdAt: Optional[str] = Field(default=None, index=True)
    featuredAt: Optional[str] = None
    commentsCount: int
    votesCount: int
    reviewsRating: float
    reviewsCount: int
    isCollected: bool
    isVoted: bool
    thumbnail_type: Optional[str] = None
    thumbnail_url: Optional[str] = None
    thumbnail_videoUrl: Optional[str] = None
    productlinks_json: Optional[str] = None

    @classmethod
    def from_pydantic(cls, post: Post) -> "PostRow":
        """Create PostRow from Pydantic Post model."""
        return cls(
            id=post.id,
            userId=post.userId,
            name=post.name,
            tagline=post.tagline,
            description=post.description,
            slug=post.slug,
            url=post.url,
            website=post.website,
            createdAt=format_iso(post.createdAt),
            featuredAt=format_iso(post.featuredAt),
            commentsCount=post.commentsCount,
            votesCount=post.votesCount,
            reviewsRating=post.reviewsRating,
            reviewsCount=post.reviewsCount,
            isCollected=post.isCollected,
            isVoted=post.isVoted,
            thumbnail_type=post.thumbnail.type if post.thumbnail else None,
            thumbnail_url=post.thumbnail.url if post.thumbnail else None,
            thumbnail_videoUrl=post.thumbnail.videoUrl if post.thumbnail else None,
            productlinks_json=json.dumps(post.productLinks)
            if post.productLinks
            else None,
        )


class TopicRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt Topic.

    Attributes:
        id: Topic ID (primary key)
        name: Topic name
        slug: Slug
        description: Description
        url: Public URL
        createdAt: ISO8601 UTC creation timestamp
        followersCount: Follower count (indexed)
        postsCount: Number of posts tagged with this topic
        isFollowing: Whether viewer follows this topic
        image: Topic image URL
    """

    id: str = Field(primary_key=True)
    name: str
    slug: str
    description: Optional[str] = None
    url: Optional[str] = None
    createdAt: Optional[str] = None
    followersCount: Optional[int] = Field(default=None, index=True)
    postsCount: Optional[int] = None
    isFollowing: Optional[bool] = None
    image: Optional[str] = None

    @classmethod
    def from_pydantic(cls, topic: Topic) -> "TopicRow":
        """Create TopicRow from Pydantic Topic model."""
        return cls(
            id=topic.id,
            name=topic.name,
            slug=topic.slug,
            description=topic.description,
            url=topic.url,
            createdAt=format_iso(topic.createdAt),
            followersCount=topic.followersCount,
            postsCount=topic.postsCount,
            isFollowing=topic.isFollowing,
            image=topic.image,
        )


class CollectionRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt Collection.

    Attributes:
        id: Collection ID (primary key)
        name: Title
        tagline: Tagline
        description: Description
        url: Public URL
        coverImage: Cover image URL
        createdAt: ISO8601 UTC creation timestamp
        featuredAt: ISO8601 UTC featured timestamp
        followersCount: Follower count (indexed)
        isFollowing: Viewer follows?
        userId: FK to curator's UserRow.id
    """

    id: str = Field(primary_key=True)
    name: str
    tagline: str
    description: Optional[str] = None
    url: str
    coverImage: Optional[str] = None
    createdAt: Optional[str] = None
    featuredAt: Optional[str] = None
    followersCount: int = Field(index=True)
    isFollowing: bool
    userId: str = Field(foreign_key="userrow.id")

    @classmethod
    def from_pydantic(cls, collection: Collection) -> "CollectionRow":
        """Create CollectionRow from Pydantic Collection model."""
        return cls(
            id=collection.id,
            name=collection.name,
            tagline=collection.tagline,
            description=collection.description,
            url=collection.url,
            coverImage=collection.coverImage,
            createdAt=format_iso(collection.createdAt),
            featuredAt=format_iso(collection.featuredAt),
            followersCount=collection.followersCount,
            isFollowing=collection.isFollowing,
            userId=collection.userId,
        )


class CommentRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt Comment.

    Attributes:
        id: Comment ID (primary key)
        post_id: FK to PostRow.id (indexed)
        parentId: Parent comment ID if threaded
        body: Body text (Markdown/plain)
        url: Public URL
        createdAt: ISO8601 UTC creation timestamp (indexed)
        isVoted: Viewer voted?
        votesCount: Vote count
        userId: FK to UserRow.id (comment author)
    """

    id: str = Field(primary_key=True)
    post_id: str = Field(foreign_key="postrow.id", index=True)
    parentId: Optional[str] = None
    body: str
    url: str
    createdAt: Optional[str] = Field(default=None, index=True)
    isVoted: bool
    votesCount: int
    userId: str = Field(foreign_key="userrow.id")


class VoteRow(SQLModel, table=True):
    """Persisted representation of a Product Hunt Vote.

    Attributes:
        id: Vote ID (primary key)
        createdAt: ISO8601 UTC timestamp of the vote (indexed)
        userId: FK to UserRow.id of the voter
        post_id: FK to PostRow.id if this vote targets a post
        comment_id: FK to CommentRow.id if this vote targets a comment
    """

    id: str = Field(primary_key=True)
    createdAt: Optional[str] = Field(default=None, index=True)
    userId: str = Field(foreign_key="userrow.id")
    post_id: Optional[str] = Field(default=None, foreign_key="postrow.id")
    comment_id: Optional[str] = Field(default=None, foreign_key="commentrow.id")

    @classmethod
    def from_pydantic(
        cls,
        vote: Vote,
        post_id: Optional[str] = None,
        comment_id: Optional[str] = None,
    ) -> "VoteRow":
        """Create VoteRow from Pydantic Vote model."""
        return cls(
            id=vote.id,
            createdAt=format_iso(vote.createdAt),
            userId=vote.userId,
            post_id=post_id,
            comment_id=comment_id,
        )


class MediaRow(SQLModel, table=True):
    """Persisted representation of a Media object.

    Attributes:
        id: Auto-incremented primary key
        post_id: FK to PostRow.id this media belongs to
        type: Media type (e.g., "image", "video")
        url: Public URL for the media
        videoUrl: Video URL if type is video
        order_index: Order position in the post's media array
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: str = Field(foreign_key="postrow.id", index=True)
    type: str
    url: str
    videoUrl: Optional[str] = None
    order_index: int = 0

    @classmethod
    def from_pydantic(cls, media: Media, post_id: str, order_index: int = 0) -> "MediaRow":
        """Create MediaRow from Pydantic Media model."""
        return cls(
            post_id=post_id,
            type=media.type,
            url=media.url,
            videoUrl=media.videoUrl,
            order_index=order_index,
        )


class MakerProjectRow(SQLModel, table=True):
    """Persisted representation of a MakerProject.

    Attributes:
        id: Project ID (primary key)
        name: Project name
        tagline: Short description
        image: Project image URL
        url: Public URL
        lookingForOtherMakers: Whether seeking collaborators
    """

    id: str = Field(primary_key=True)
    name: str
    tagline: str
    image: Optional[str] = None
    url: str
    lookingForOtherMakers: bool

    @classmethod
    def from_pydantic(cls, project: MakerProject) -> "MakerProjectRow":
        """Create MakerProjectRow from Pydantic MakerProject model."""
        return cls(
            id=project.id,
            name=project.name,
            tagline=project.tagline,
            image=project.image,
            url=project.url,
            lookingForOtherMakers=project.lookingForOtherMakers,
        )


class MakerGroupRow(SQLModel, table=True):
    """Persisted representation of a MakerGroup (Space).

    Attributes:
        id: Group ID (primary key)
        name: Group name
        tagline: Short description
        description: Full description
        url: Public URL
        membersCount: Number of members (indexed)
        goalsCount: Number of goals created (indexed)
        isMember: Whether viewer is a member
    """

    id: str = Field(primary_key=True)
    name: str
    tagline: str
    description: str
    url: str
    membersCount: int = Field(index=True)
    goalsCount: int = Field(index=True)
    isMember: bool

    @classmethod
    def from_pydantic(cls, group: MakerGroup) -> "MakerGroupRow":
        """Create MakerGroupRow from Pydantic MakerGroup model."""
        return cls(
            id=group.id,
            name=group.name,
            tagline=group.tagline,
            description=group.description,
            url=group.url,
            membersCount=group.membersCount,
            goalsCount=group.goalsCount,
            isMember=group.isMember,
        )


class GoalRow(SQLModel, table=True):
    """Persisted representation of a Goal.

    Attributes:
        id: Goal ID (primary key)
        title: Goal title
        userId: FK to UserRow.id
        groupId: FK to MakerGroupRow.id
        projectId: FK to MakerProjectRow.id (optional)
        createdAt: ISO8601 UTC creation timestamp (indexed)
        dueAt: ISO8601 UTC due date (indexed)
        completedAt: ISO8601 UTC completion timestamp (indexed)
        currentUntil: ISO8601 UTC timestamp until this is current
        current: Whether this is the user's current goal
        cheerCount: Number of cheers
        isCheered: Whether viewer has cheered
        focusedDuration: Time spent in focus mode (seconds)
        url: Public URL
    """

    id: str = Field(primary_key=True)
    title: str
    userId: str = Field(foreign_key="userrow.id", index=True)
    groupId: str = Field(foreign_key="makergrouprow.id", index=True)
    projectId: Optional[str] = Field(default=None, foreign_key="makerprojectrow.id")
    createdAt: Optional[str] = Field(default=None, index=True)
    dueAt: Optional[str] = Field(default=None, index=True)
    completedAt: Optional[str] = Field(default=None, index=True)
    currentUntil: Optional[str] = None
    current: bool
    cheerCount: int
    isCheered: bool
    focusedDuration: int
    url: str

    @classmethod
    def from_pydantic(cls, goal: Goal) -> "GoalRow":
        """Create GoalRow from Pydantic Goal model."""
        return cls(
            id=goal.id,
            title=goal.title,
            userId=goal.userId,
            groupId=goal.groupId,
            projectId=goal.projectId,
            createdAt=format_iso(goal.createdAt),
            dueAt=format_iso(goal.dueAt),
            completedAt=format_iso(goal.completedAt),
            currentUntil=format_iso(goal.currentUntil),
            current=goal.current,
            cheerCount=goal.cheerCount,
            isCheered=goal.isCheered,
            focusedDuration=goal.focusedDuration,
            url=goal.url,
        )


# =============================================================================
# Section 3: Link Tables for Many-to-Many Relationships
# =============================================================================


class PostTopicLink(SQLModel, table=True):
    """Link table between posts and topics (many-to-many).

    Attributes:
        post_id: FK to PostRow.id (part of composite PK)
        topic_id: FK to TopicRow.id (part of composite PK)
    """

    post_id: str = Field(primary_key=True, foreign_key="postrow.id")
    topic_id: str = Field(primary_key=True, foreign_key="topicrow.id")


class MakerPostLink(SQLModel, table=True):
    """Link table between makers (User) and posts (many-to-many).

    Attributes:
        post_id: FK to PostRow.id (part of composite PK)
        user_id: FK to UserRow.id (part of composite PK)
    """

    post_id: str = Field(primary_key=True, foreign_key="postrow.id")
    user_id: str = Field(primary_key=True, foreign_key="userrow.id")


class CollectionPostLink(SQLModel, table=True):
    """Link table relating collections and posts (many-to-many).

    Attributes:
        collection_id: FK to CollectionRow.id (part of composite PK)
        post_id: FK to PostRow.id (part of composite PK)
    """

    collection_id: str = Field(primary_key=True, foreign_key="collectionrow.id")
    post_id: str = Field(primary_key=True, foreign_key="postrow.id")


class UserFollowingLink(SQLModel, table=True):
    """Link table for user following relationships.

    Attributes:
        follower_id: FK to UserRow.id (user who follows)
        following_id: FK to UserRow.id (user being followed)
    """

    follower_id: str = Field(primary_key=True, foreign_key="userrow.id")
    following_id: str = Field(primary_key=True, foreign_key="userrow.id")


class UserCollectionFollowLink(SQLModel, table=True):
    """Link table for users following collections.

    Attributes:
        user_id: FK to UserRow.id
        collection_id: FK to CollectionRow.id
    """

    user_id: str = Field(primary_key=True, foreign_key="userrow.id")
    collection_id: str = Field(primary_key=True, foreign_key="collectionrow.id")


class UserTopicFollowLink(SQLModel, table=True):
    """Link table for users following topics.

    Attributes:
        user_id: FK to UserRow.id
        topic_id: FK to TopicRow.id
    """

    user_id: str = Field(primary_key=True, foreign_key="userrow.id")
    topic_id: str = Field(primary_key=True, foreign_key="topicrow.id")


class MakerGroupMemberLink(SQLModel, table=True):
    """Link table for maker group memberships.

    Attributes:
        user_id: FK to UserRow.id
        group_id: FK to MakerGroupRow.id
    """

    user_id: str = Field(primary_key=True, foreign_key="userrow.id")
    group_id: str = Field(primary_key=True, foreign_key="makergrouprow.id")

