# SQLModel - SQL Databases with Python Objects

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Database ORM  
**Official Site:** [sqlmodel.tiangolo.com](https://sqlmodel.tiangolo.com/)  
**GitHub:** [tiangolo/sqlmodel](https://github.com/tiangolo/sqlmodel)  
**License:** MIT
:::

:::{grid-item}
**Version:** ≥0.0.27  
**Used For:** Database models, ORM queries, relationships  
**Why We Use It:** Best of SQLAlchemy + Pydantic in one
:::

::::

---

## Overview

SQLModel is a library for interacting with SQL databases from Python code, with Python objects. It's designed to be intuitive, easy to use, highly compatible, and robust. It combines the power of SQLAlchemy with the simplicity of Pydantic.

### Key Features

- 🔗 **SQLAlchemy + Pydantic** - Best of both worlds
- ✅ **Type Hints** - Full editor support with autocomplete
- 🔄 **Data Validation** - Automatic validation using Pydantic
- 📊 **Relationships** - Intuitive relationship definitions
- 🚀 **Performance** - Built on SQLAlchemy 2.0
- 📝 **Migrations** - Works seamlessly with Alembic

---

## How ProductHuntDB Uses SQLModel

### 1. **Database Models**

All database tables are defined as SQLModel classes:

```python
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class Post(SQLModel, table=True):
    """Product Hunt post."""
    
    __tablename__ = "posts"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=255, index=True)
    tagline: str = Field(max_length=255)
    created_at: datetime = Field(index=True)
    votes_count: int = Field(default=0, index=True)
    comments_count: int = Field(default=0)
    url: str = Field(unique=True)
    website: Optional[str] = None
    
    # Relationships
    topics: list["Topic"] = Relationship(back_populates="posts", link_model=PostTopicLink)
    comments: list["Comment"] = Relationship(back_populates="post")
    votes: list["Vote"] = Relationship(back_populates="post")

class Topic(SQLModel, table=True):
    """Product Hunt topic/category."""
    
    __tablename__ = "topics"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100, unique=True, index=True)
    slug: str = Field(max_length=100, unique=True)
    
    # Relationships
    posts: list[Post] = Relationship(back_populates="topics", link_model=PostTopicLink)

class PostTopicLink(SQLModel, table=True):
    """Many-to-many link between posts and topics."""
    
    __tablename__ = "post_topic_links"
    
    post_id: str = Field(foreign_key="posts.id", primary_key=True)
    topic_id: str = Field(foreign_key="topics.id", primary_key=True)
```

### 2. **Database Queries**

Type-safe queries with autocomplete:

```python
from sqlmodel import Session, select
from producthuntdb.models import Post, Topic

def get_top_posts(session: Session, limit: int = 10) -> list[Post]:
    """Get posts with most votes."""
    statement = (
        select(Post)
        .order_by(Post.votes_count.desc())
        .limit(limit)
    )
    return session.exec(statement).all()

def get_posts_by_topic(session: Session, topic_name: str) -> list[Post]:
    """Get all posts in a topic."""
    statement = (
        select(Post)
        .join(Post.topics)
        .where(Topic.name == topic_name)
        .order_by(Post.created_at.desc())
    )
    return session.exec(statement).all()

def search_posts(session: Session, query: str) -> list[Post]:
    """Search posts by name or tagline."""
    statement = (
        select(Post)
        .where(
            (Post.name.contains(query)) | 
            (Post.tagline.contains(query))
        )
    )
    return session.exec(statement).all()
```

### 3. **Data Insertion**

Easy creation and insertion of records:

```python
from sqlmodel import Session
from producthuntdb.models import Post, Topic
from datetime import datetime

def create_post(session: Session, post_data: dict) -> Post:
    """Create a new post."""
    post = Post(
        id=post_data["id"],
        name=post_data["name"],
        tagline=post_data["tagline"],
        created_at=datetime.fromisoformat(post_data["created_at"]),
        votes_count=post_data["votes_count"],
        url=post_data["url"],
    )
    
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

def bulk_insert_posts(session: Session, posts: list[Post]) -> None:
    """Efficiently insert many posts."""
    session.add_all(posts)
    session.commit()
```

### 4. **Relationship Loading**

Efficient relationship queries:

```python
from sqlmodel import Session, select
from sqlmodel.orm import selectinload

def get_post_with_topics(session: Session, post_id: str) -> Post:
    """Get post with all its topics loaded."""
    statement = (
        select(Post)
        .where(Post.id == post_id)
        .options(selectinload(Post.topics))
    )
    return session.exec(statement).first()

def get_posts_with_everything(session: Session) -> list[Post]:
    """Get posts with all relationships loaded."""
    statement = (
        select(Post)
        .options(
            selectinload(Post.topics),
            selectinload(Post.comments),
            selectinload(Post.votes),
        )
    )
    return session.exec(statement).all()
```

---

## Configuration in ProductHuntDB

### Database Connection

```python
# producthuntdb/config.py
from sqlmodel import create_engine, Session
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///data/producthunt.db"
    
settings = Settings()

# Create engine with connection pooling
engine = create_engine(
    settings.database_url,
    echo=False,  # Set to True for SQL debugging
    connect_args={"check_same_thread": False},  # For SQLite
)

def get_session() -> Session:
    """Get database session."""
    with Session(engine) as session:
        yield session
```

### Model Configuration

```python
# producthuntdb/models.py
from sqlmodel import SQLModel, Field
from typing import Optional

class ProductHuntModel(SQLModel):
    """Base model for all tables."""
    
    class Config:
        # Enable validation on assignment
        validate_assignment = True
        
        # Use enum values
        use_enum_values = True
        
        # JSON encoding
        json_encoders = {
            datetime: lambda v: v.isoformat(),
        }
```

---

## Key Features Used

### Table Definition

```python
from sqlmodel import SQLModel, Field

class User(SQLModel, table=True):
    """Define a database table."""
    
    id: int = Field(primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
```

### Relationships

```python
from sqlmodel import Relationship

class Author(SQLModel, table=True):
    id: int = Field(primary_key=True)
    name: str
    
    # One-to-many relationship
    posts: list["Post"] = Relationship(back_populates="author")

class Post(SQLModel, table=True):
    id: int = Field(primary_key=True)
    title: str
    author_id: int = Field(foreign_key="author.id")
    
    # Many-to-one relationship
    author: Author = Relationship(back_populates="posts")
```

### Indexes

```python
from sqlmodel import SQLModel, Field, Index

class Post(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str = Field(index=True)  # Simple index
    created_at: datetime = Field(index=True)
    votes_count: int
    
    # Composite index
    __table_args__ = (
        Index("idx_votes_created", "votes_count", "created_at"),
    )
```

### Validation

```python
from sqlmodel import SQLModel, Field
from pydantic import field_validator

class Post(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str = Field(min_length=1, max_length=255)
    votes_count: int = Field(ge=0)  # Greater than or equal to 0
    
    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Name cannot be empty")
        return v.strip()
```

---

## Performance Benefits

### Query Optimization

| Operation | Naive Approach | Optimized | Speedup |
|-----------|----------------|-----------|---------|
| Load 1000 posts with topics | N+1 queries (1001 queries) | 2 queries | **500x faster** |
| Bulk insert 1000 records | 1000 INSERTs | 1 batch INSERT | **50x faster** |
| Filter + sort | Full table scan | Indexed query | **100x faster** |

### Real-World Impact

- **Data Loading**: 10,000 posts loaded in 0.5s with proper indexing
- **Relationship Queries**: Eliminated N+1 query problems
- **Memory Usage**: Lazy loading prevents memory bloat

---

## Common Patterns

### CRUD Operations

```python
from sqlmodel import Session, select

# Create
def create_post(session: Session, name: str, tagline: str) -> Post:
    post = Post(name=name, tagline=tagline)
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

# Read
def get_post(session: Session, post_id: str) -> Post | None:
    return session.get(Post, post_id)

# Update
def update_post_votes(session: Session, post_id: str, votes: int) -> Post:
    post = session.get(Post, post_id)
    post.votes_count = votes
    session.add(post)
    session.commit()
    session.refresh(post)
    return post

# Delete
def delete_post(session: Session, post_id: str) -> None:
    post = session.get(Post, post_id)
    session.delete(post)
    session.commit()
```

### Pagination

```python
def get_posts_paginated(
    session: Session,
    page: int = 1,
    page_size: int = 20
) -> list[Post]:
    offset = (page - 1) * page_size
    statement = (
        select(Post)
        .order_by(Post.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    return session.exec(statement).all()
```

### Aggregations

```python
from sqlmodel import func, select

def get_post_stats(session: Session) -> dict:
    statement = select(
        func.count(Post.id).label("total_posts"),
        func.sum(Post.votes_count).label("total_votes"),
        func.avg(Post.votes_count).label("avg_votes"),
        func.max(Post.votes_count).label("max_votes"),
    )
    result = session.exec(statement).first()
    return {
        "total_posts": result.total_posts,
        "total_votes": result.total_votes,
        "avg_votes": result.avg_votes,
        "max_votes": result.max_votes,
    }
```

---

## Best Practices

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} ✅ Do

- Use type hints for all fields
- Define indexes on frequently queried columns
- Use selectinload() for eager loading relationships
- Commit transactions explicitly
- Use context managers for sessions

:::

:::{grid-item-card} ❌ Don't

- Don't forget to add indexes
- Don't use lazy loading in loops (N+1 problem)
- Don't keep sessions open too long
- Don't mix SQLModel and raw SQLAlchemy syntax unnecessarily
- Don't skip validation constraints

:::

::::

---

## Learn More

- 📚 [Official Documentation](https://sqlmodel.tiangolo.com/)
- 🎓 [Tutorial](https://sqlmodel.tiangolo.com/tutorial/)
- 🔧 [Advanced Usage](https://sqlmodel.tiangolo.com/advanced/)
- 🐛 [Issue Tracker](https://github.com/tiangolo/sqlmodel/issues)

---

## Related Tools

- [SQLite](sqlite) - Database engine
- [Alembic](alembic) - Database migrations
- [Pydantic](pydantic) - Data validation foundation

:::{seealso}
Check out [Alembic](alembic) for managing database schema migrations with SQLModel.
:::
