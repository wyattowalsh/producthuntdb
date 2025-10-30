# Data Model

ProductHuntDB mirrors Product Hunt's public GraphQL schema with normalized SQLModel tables and supporting link tables. This page documents the most important structures and how they map to pipeline behaviour.

## Core Entities

### Posts (`PostRow`)

- Launch metadata (`name`, `tagline`, `description`, `slug`, `url`).
- Engagement metrics (`votesCount`, `commentsCount`, `reviewsRating`).
- Temporal fields (`createdAt`, `featuredAt`) for trending analysis.
- Media payloads exposed via a dedicated `MediaRow`.

Indexes: `createdAt`, `featuredAt`, `votesCount`.

### Users (`UserRow`)

- Profile attributes (`username`, `headline`, `websiteUrl`).
- Maker flags (`isMaker`, `isFollowing`, `isViewer`).
- Imagery (`profileImage`, `coverImage`).

Indexes: `createdAt`, `username`.

### Media (`MediaRow`)

- Stores ordered assets for posts (`type`, `url`, `videoUrl`, `order_index`).
- Foreign key back to `PostRow` with cascade deletes.

Indexes: `post_id`.

### Comments (`CommentRow`)

- Threaded structure with `parentCommentId`.
- Audit fields (`createdAt`, `votesCount`, `isMaker`).

Indexes: `postId`, `userId`, `createdAt`.

### Votes (`VoteRow`)

- Captures voter → post relationships with vote timestamps.

Indexes: `postId`, `userId`, `createdAt`.

### Topics (`TopicRow`) & Collections (`CollectionRow`)

- Taxonomy metadata (names, slugs, counts, imagery).
- Collection curator relationships tracked via link tables.

### Maker Goals, Groups, and Projects

- Maker productivity surfaces (`GoalRow`, `MakerGroupRow`, `MakerProjectRow`) with progress tracking and membership data.

## Relationship Tables

- `PostTopicLink`: many-to-many posts ↔ topics with composite primary key.
- `MakerPostLink`: makers ↔ product launches.
- `CollectionPostLink`: curated lists ↔ posts.
- `UserFollowingLink`: social graph adjacency list.
- `UserCollectionFollowLink`: users following collections.
- `UserTopicFollowLink`: users following topics.
- `MakerGroupMemberLink`: maker communities and membership.

Each link table enforces foreign keys and composite indexes to keep lookups performant.

## Incremental Sync Strategy

- `DataPipeline` tracks the most recent `createdAt` per entity to drive incremental pulls.
- A five-minute safety window (configurable via `Settings.safety_minutes`) ensures late-arriving records are re-fetched.
- Upserts rely on SQLModel's ORM semantics to avoid duplicates across link tables.

## Extending the Schema

1. Add fields or new models in `producthuntdb.models`.
2. Regenerate migrations with `uv run producthuntdb migrate "describe change"`.
3. Update the relevant sections here and rerun `make docs`.
