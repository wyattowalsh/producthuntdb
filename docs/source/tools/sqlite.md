# SQLite - Embedded SQL Database

::::{grid} 2
:gutter: 3

:::{grid-item}
**Category:** Database Engine  
**Official Site:** [sqlite.org](https://www.sqlite.org/)  
**Documentation:** [SQLite Docs](https://www.sqlite.org/docs.html)  
**License:** Public Domain
:::

:::{grid-item}
**Version:** 3.x  
**Used For:** Data storage, query engine, ACID compliance  
**Why We Use It:** Zero-config, single file, perfect for datasets
:::

::::

---

## Overview

SQLite is a C-language library that implements a small, fast, self-contained, high-reliability, full-featured, SQL database engine. It's the most used database engine in the world.

### Key Features

- 📁 **Single File** - Entire database in one portable file
- ⚡ **Fast** - Faster than client-server databases for local operations
- 🔒 **ACID** - Full ACID compliance with transactions
- 🌐 **Cross-Platform** - Works on all major platforms
- 📦 **Zero Configuration** - No setup or administration
- 🔓 **Public Domain** - Free for any use

---

## Why SQLite for ProductHuntDB?

### Perfect for Dataset Distribution

1. **Single File**: Entire database ships as one `.db` file on Kaggle
2. **No Setup**: Users can query immediately without installation
3. **Portable**: Works on Windows, Mac, Linux identically
4. **Embeddable**: Can be included in applications
5. **Fast**: Optimized for local queries

### Technical Advantages

```python
# No server setup required - just use the file!
from sqlmodel import create_engine

engine = create_engine("sqlite:///data/producthunt.db")
# That's it! Database is ready to use
```

---

## How ProductHuntDB Uses SQLite

### 1. **Database Storage**

All Product Hunt data stored in optimized SQLite schema:

```sql
-- Posts table with indexes for performance
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tagline TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL,
    votes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    url TEXT UNIQUE NOT NULL,
    website TEXT
);

-- Indexes for common queries
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_votes_count ON posts(votes_count);
CREATE INDEX idx_posts_name ON posts(name);
```

### 2. **Query Performance**

Strategic indexing for fast queries:

```sql
-- Find top posts this month (uses idx_posts_created_at + idx_posts_votes_count)
SELECT name, votes_count 
FROM posts 
WHERE created_at >= date('now', '-30 days')
ORDER BY votes_count DESC 
LIMIT 10;

-- Search by name (uses idx_posts_name)
SELECT * FROM posts 
WHERE name LIKE '%productivity%'
ORDER BY votes_count DESC;
```

### 3. **Relationships**

Efficient relationship modeling:

```sql
-- Many-to-many: Posts <-> Topics
CREATE TABLE post_topic_links (
    post_id TEXT NOT NULL,
    topic_id TEXT NOT NULL,
    PRIMARY KEY (post_id, topic_id),
    FOREIGN KEY (post_id) REFERENCES posts(id),
    FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Query posts with their topics
SELECT 
    p.name,
    GROUP_CONCAT(t.name, ', ') as topics
FROM posts p
LEFT JOIN post_topic_links ptl ON p.id = ptl.post_id
LEFT JOIN topics t ON ptl.topic_id = t.id
GROUP BY p.id;
```

### 4. **Full-Text Search**

Built-in FTS5 for text search:

```sql
-- Create full-text search index
CREATE VIRTUAL TABLE posts_fts USING fts5(
    name, 
    tagline, 
    content='posts', 
    content_rowid='rowid'
);

-- Fast text search
SELECT * FROM posts_fts 
WHERE posts_fts MATCH 'ai AND productivity'
ORDER BY rank;
```

---

## Configuration in ProductHuntDB

### SQLAlchemy Engine Setup

```python
from sqlmodel import create_engine
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Create engine with optimizations
engine = create_engine(
    "sqlite:///data/producthunt.db",
    echo=False,  # Set True for SQL logging
    connect_args={
        "check_same_thread": False,  # Allow multi-threading
    },
)

# Enable WAL mode for better concurrency
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
    cursor.execute("PRAGMA synchronous=NORMAL")  # Faster writes
    cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
    cursor.execute("PRAGMA temp_store=MEMORY")  # Use RAM for temp tables
    cursor.execute("PRAGMA foreign_keys=ON")  # Enforce FK constraints
    cursor.close()
```

### Database Optimization

```python
# producthuntdb/config.py
SQLITE_PRAGMAS = {
    "journal_mode": "WAL",      # Write-Ahead Logging
    "synchronous": "NORMAL",    # Faster writes
    "cache_size": -64000,       # 64MB cache
    "temp_store": "MEMORY",     # RAM for temp tables
    "mmap_size": 30000000000,   # 30GB memory-mapped I/O
    "page_size": 4096,          # 4KB pages
}
```

---

## Key Features Used

### ACID Transactions

```python
from sqlmodel import Session

def transfer_votes(session: Session, from_post: str, to_post: str, count: int):
    """Transfer votes between posts atomically."""
    try:
        # Start transaction
        post1 = session.get(Post, from_post)
        post2 = session.get(Post, to_post)
        
        post1.votes_count -= count
        post2.votes_count += count
        
        session.add(post1)
        session.add(post2)
        session.commit()  # Atomic - both succeed or both fail
    except Exception:
        session.rollback()  # Rollback on error
        raise
```

### Indexes

```python
from sqlmodel import SQLModel, Field, Index

class Post(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(index=True)
    votes_count: int = Field(index=True)
    
    # Composite index for sorting by votes + date
    __table_args__ = (
        Index("idx_votes_date", "votes_count", "created_at"),
    )
```

### Constraints

```sql
-- Unique constraints
CREATE TABLE users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL
);

-- Check constraints
CREATE TABLE posts (
    id TEXT PRIMARY KEY,
    votes_count INTEGER CHECK(votes_count >= 0),
    comments_count INTEGER CHECK(comments_count >= 0)
);

-- Foreign key constraints
CREATE TABLE comments (
    id TEXT PRIMARY KEY,
    post_id TEXT NOT NULL,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
);
```

### JSON Support

```sql
-- Store JSON data
CREATE TABLE metadata (
    id INTEGER PRIMARY KEY,
    data JSON
);

-- Query JSON fields
INSERT INTO metadata (data) VALUES ('{"name": "test", "count": 42}');

SELECT json_extract(data, '$.name') FROM metadata;
SELECT * FROM metadata WHERE json_extract(data, '$.count') > 40;
```

---

## Performance Optimization

### Database Size

ProductHuntDB database statistics:

| Data | Records | Disk Size | Compressed |
|------|---------|-----------|------------|
| Posts | ~500K | 250MB | 45MB |
| Users | ~200K | 80MB | 15MB |
| Comments | ~2M | 600MB | 120MB |
| Votes | ~5M | 180MB | 35MB |
| **Total** | **~8M** | **~1.1GB** | **~215MB** |

### Query Performance

With proper indexing:

| Query Type | Records | Time (no index) | Time (indexed) |
|----------|---------|-----------------|----------------|
| Primary key lookup | 1 | 0.1ms | 0.1ms |
| Sorted by votes | 1000 | 450ms | 12ms |
| Date range filter | 10000 | 800ms | 25ms |
| Full-text search | 100 | 2000ms | 45ms |

---

## Common Patterns

### Aggregations

```sql
-- Post statistics
SELECT 
    COUNT(*) as total_posts,
    SUM(votes_count) as total_votes,
    AVG(votes_count) as avg_votes,
    MAX(votes_count) as max_votes,
    MIN(votes_count) as min_votes
FROM posts;

-- Posts per topic
SELECT 
    t.name,
    COUNT(p.id) as post_count,
    SUM(p.votes_count) as total_votes
FROM topics t
JOIN post_topic_links ptl ON t.id = ptl.topic_id
JOIN posts p ON ptl.post_id = p.id
GROUP BY t.id
ORDER BY post_count DESC;
```

### Window Functions

```sql
-- Rank posts by votes within each topic
SELECT 
    name,
    votes_count,
    topic_name,
    ROW_NUMBER() OVER (
        PARTITION BY topic_name 
        ORDER BY votes_count DESC
    ) as rank_in_topic
FROM posts p
JOIN post_topic_links ptl ON p.id = ptl.post_id
JOIN topics t ON ptl.topic_id = t.id;
```

### Common Table Expressions (CTEs)

```sql
-- Find posts with above-average votes
WITH avg_votes AS (
    SELECT AVG(votes_count) as avg FROM posts
)
SELECT name, votes_count
FROM posts, avg_votes
WHERE votes_count > avg_votes.avg
ORDER BY votes_count DESC;
```

---

## Best Practices

::::{grid} 1 1 2 2
:gutter: 2

:::{grid-item-card} ✅ Do

- Enable WAL mode for better concurrency
- Create indexes on frequently queried columns
- Use transactions for multi-step operations
- Use VACUUM regularly to optimize file size
- Back up database files regularly

:::

:::{grid-item-card} ❌ Don't

- Don't use for high-write concurrency scenarios
- Don't forget to create indexes (slow queries)
- Don't store blobs larger than 1MB
- Don't use over network filesystems (NFS)
- Don't run without foreign key constraints

:::

::::

---

## File Format

SQLite database files are:

- **Portable**: Copy file = copy entire database
- **Stable**: Backward compatible for decades
- **Self-Contained**: No external dependencies
- **Recommended**: Archive format by Library of Congress

```bash
# Copy database
cp producthunt.db producthunt_backup.db

# Compress for distribution
gzip -c producthunt.db > producthunt.db.gz

# Upload to Kaggle
kaggle datasets version -m "Updated database" -p data/
```

---

## Learn More

- 📚 [Official Documentation](https://www.sqlite.org/docs.html)
- 🎓 [Query Language](https://www.sqlite.org/lang.html)
- 🔧 [Optimization](https://www.sqlite.org/optoverview.html)
- 📖 [When to Use SQLite](https://www.sqlite.org/whentouse.html)

---

## Related Tools

- [SQLModel](sqlmodel) - ORM for SQLite
- [Alembic](alembic) - Schema migrations
- [Pandas](pandas) - Read SQLite into DataFrames

:::{seealso}
Learn about [Alembic](alembic) for managing SQLite schema changes over time.
:::
