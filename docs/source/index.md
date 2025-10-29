# ProductHuntDB Documentation

```{toctree}
:maxdepth: 2
:hidden:
:caption: Contents:

Home <self>
tools/index
changelog
```

Welcome to **ProductHuntDB** - a production-grade data pipeline for harvesting, storing, and publishing Product Hunt data! 🚀

ProductHuntDB provides:
- 📊 **Complete API Coverage** - All publicly available Product Hunt entities and relationships
- 💾 **Advanced SQLite Database** - Optimized schema with strategic indexing
- 🔄 **Intelligent Syncing** - Incremental updates with rate limit management
- 📦 **Kaggle Integration** - Automated dataset publishing
- 🛠️ **Database Migrations** - Version-controlled schema changes with Alembic
- ✅ **79.4% Test Coverage** - Comprehensive test suite with 160+ tests

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/wyattowalsh/producthuntdb.git
cd producthuntdb

# Install dependencies with uv
uv sync

# Initialize database
producthuntdb init
```

### First Sync

```bash
# Verify API authentication
producthuntdb verify

# Sync all data (incremental mode)
producthuntdb sync

# Check status
producthuntdb status
```

### Export & Publish

```bash
# Export to CSV files
producthuntdb export

# Publish to Kaggle (requires credentials)
producthuntdb publish
```

---

## 📖 CLI Reference

### Core Commands

#### `producthuntdb sync`
Synchronize data from Product Hunt API to local database.

```bash
# Incremental sync (default)
producthuntdb sync

# Full refresh (re-fetch everything)
producthuntdb sync --full-refresh

# Posts only (skip topics and collections)
producthuntdb sync --posts-only

# Limit pages for testing
producthuntdb sync --max-pages 5

# With verbose logging
producthuntdb sync --verbose
```

**Options:**
- `--full-refresh, -f` - Perform full refresh instead of incremental update
- `--max-pages, -n <int>` - Maximum pages to fetch per entity (for testing)
- `--posts-only` - Only sync posts (skip topics and collections)
- `--verbose, -v` - Enable detailed logging

#### `producthuntdb export`
Export database tables to CSV files.

```bash
# Export to default directory (./data/export)
producthuntdb export

# Export to custom directory
producthuntdb export --output-dir /path/to/export

# Include copy of database file
producthuntdb export
```

**Options:**
- `--output-dir, -o <path>` - Output directory for CSV files (default: `./data/export`)

#### `producthuntdb publish`
Publish or update Kaggle dataset with latest data.

```bash
# Publish/update dataset
producthuntdb publish

# Publish with verbose logging
producthuntdb publish --verbose
```

**Requirements:**
- Kaggle API credentials (`~/.kaggle/kaggle.json`)
- Kaggle username and dataset slug in config

#### `producthuntdb status`
Show database statistics and pipeline status.

```bash
producthuntdb status
```

Displays:
- Total counts for all entities (Posts, Users, Comments, etc.)
- Latest post timestamp
- Database file size and path
- Last sync time
- API rate limit status

#### `producthuntdb verify`
Verify API authentication and connectivity.

```bash
producthuntdb verify

# With verbose logging
producthuntdb verify --verbose
```

Tests:
- Product Hunt API token validity
- GraphQL endpoint connectivity
- Rate limit status

---

### Database Management

#### `producthuntdb init`
Initialize database and verify setup.

```bash
producthuntdb init
```

Creates:
- Database directory structure
- SQLite database file
- Initial schema (runs migrations)

#### `producthuntdb migrate`
Create a new database migration.

```bash
# Auto-generate migration from model changes
producthuntdb migrate --message "add new column"

# Create empty migration for manual edits
producthuntdb migrate --message "custom logic" --no-autogenerate
```

**Options:**
- `--message, -m <text>` - Migration description (required)
- `--no-autogenerate` - Create empty migration for manual editing

#### `producthuntdb upgrade`
Upgrade database to a specific revision.

```bash
# Upgrade to latest
producthuntdb upgrade

# Upgrade to specific revision
producthuntdb upgrade abc123

# Upgrade one step
producthuntdb upgrade +1
```

#### `producthuntdb downgrade`
Downgrade database to a previous revision.

```bash
# Downgrade one step
producthuntdb downgrade

# Downgrade to specific revision
producthuntdb downgrade abc123

# Downgrade to base (empty database)
producthuntdb downgrade base
```

#### `producthuntdb migration-history`
Show database migration history.

```bash
producthuntdb migration-history
```

Displays:
- Current revision
- Migration history with timestamps
- Available revisions

---

## 📊 Data Coverage

ProductHuntDB captures **all publicly available entities and fields** from the Product Hunt GraphQL API v2.

### Core Entities (10 Tables)

#### 1. **Posts** (`PostRow`)
Product launches and their metadata.

**Key Fields:**
- `id`, `userId`, `name`, `tagline`, `description`
- `slug`, `url`, `website`
- `createdAt`, `featuredAt` (ISO8601 UTC, indexed)
- `commentsCount`, `votesCount`
- `reviewsRating`, `reviewsCount`
- `thumbnail_type`, `thumbnail_url`, `thumbnail_videoUrl`
- `productlinks_json`

**Indexes:** `createdAt`, `featuredAt`, `votesCount`

#### 2. **Users** (`UserRow`)
Product Hunt user accounts and profiles.

**Key Fields:**
- `id`, `username`, `name`, `headline`
- `twitterUsername`, `websiteUrl`, `url`
- `createdAt` (indexed)
- `isMaker`, `isFollowing`, `isViewer`
- `profileImage`, `coverImage`

**Indexes:** `createdAt`, `username`

#### 3. **Media** (`MediaRow`)
Structured media objects (images, videos) for posts.

**Key Fields:**
- `id` (auto-increment PK)
- `post_id` (FK, indexed)
- `type` ("image" or "video")
- `url`, `videoUrl`
- `order_index` (position in array)

**Indexes:** `post_id`

#### 4. **Comments** (`CommentRow`)
User comments and discussion threads.

**Key Fields:**
- `id`, `postId` (FK), `userId` (FK), `parentCommentId` (FK)
- `body` (comment text)
- `createdAt` (indexed)
- `votesCount`
- `isVoted`, `isMaker`

**Indexes:** `postId`, `userId`, `createdAt`

#### 5. **Votes** (`VoteRow`)
Upvotes on posts and comments.

**Key Fields:**
- `id`, `postId` (FK), `userId` (FK)
- `createdAt` (indexed)

**Indexes:** `postId`, `userId`, `createdAt`

#### 6. **Topics** (`TopicRow`)
Product categories and tags.

**Key Fields:**
- `id`, `name`, `slug`
- `description`
- `followersCount`
- `url`, `image`

#### 7. **Collections** (`CollectionRow`)
Curated product collections.

**Key Fields:**
- `id`, `name`, `slug`
- `tagline`, `title`
- `userId` (FK, curator)
- `createdAt`, `featuredAt`
- `postsCount`, `followersCount`

#### 8. **Goals** (`GoalRow`)
Maker goals with completion tracking.

**Key Fields:**
- `id`, `userId` (FK), `groupId` (FK)
- `title`, `completed`
- `createdAt`, `dueAt`, `completedAt`, `currentUntil`

**Indexes:** `userId`, `groupId`

#### 9. **MakerGroups** (`MakerGroupRow`)
Maker communities (Spaces).

**Key Fields:**
- `id`, `name`, `slug`
- `description`, `membersCount`
- `url`, `image`

#### 10. **MakerProjects** (`MakerProjectRow`)
Maker projects and collaborations.

**Key Fields:**
- `id`, `userId` (FK)
- `name`, `url`
- `description`

**Indexes:** `userId`

---

### Relationships (7 Link Tables)

#### `PostTopicLink`
Many-to-many: Posts ↔ Topics

**Fields:** `post_id` (FK), `topic_id` (FK)  
**Indexes:** Composite PK on both fields

#### `MakerPostLink`
Many-to-many: Makers (Users) ↔ Posts

**Fields:** `user_id` (FK), `post_id` (FK)  
**Indexes:** Composite PK, `user_id`, `post_id`

#### `CollectionPostLink`
Many-to-many: Collections ↔ Posts

**Fields:** `collection_id` (FK), `post_id` (FK)  
**Indexes:** Composite PK on both fields

#### `UserFollowingLink`
Social graph: Users ↔ Users they follow

**Fields:** `follower_id` (FK), `followee_id` (FK)  
**Indexes:** Composite PK, both fields individually

#### `UserCollectionFollowLink`
Users ↔ Collections they follow

**Fields:** `user_id` (FK), `collection_id` (FK)  
**Indexes:** Composite PK on both fields

#### `UserTopicFollowLink`
Users ↔ Topics they follow

**Fields:** `user_id` (FK), `topic_id` (FK)  
**Indexes:** Composite PK on both fields

#### `MakerGroupMemberLink`
Users ↔ MakerGroup memberships

**Fields:** `user_id` (FK), `group_id` (FK)  
**Indexes:** Composite PK on both fields

---

### Data Quality Features

✅ **Strategic Indexing** - Optimized for temporal and popularity queries  
✅ **Foreign Key Constraints** - Referential integrity enforced  
✅ **ISO8601 Timestamps** - Consistent datetime handling (UTC)  
✅ **Structured Media** - No JSON blobs, proper relational design  
✅ **Comprehensive Coverage** - All public API fields captured  

---

## 🗄️ Database Migrations

ProductHuntDB uses [Alembic](https://alembic.sqlalchemy.org/) for database schema version control.

### Migration Workflow

#### 1. Modify Models

Edit SQLModel classes in `producthuntdb/models.py`:

```python
class PostRow(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    # Add new field
    category: Optional[str] = None  # New column
```

#### 2. Generate Migration

```bash
producthuntdb migrate --message "add category to posts"
```

This creates: `alembic/versions/abc123_add_category_to_posts.py`

#### 3. Review Migration

Open the generated file and verify:

```python
def upgrade() -> None:
    op.add_column('postrow', sa.Column('category', sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column('postrow', 'category')
```

#### 4. Apply Migration

```bash
producthuntdb upgrade
```

### Data Directory Structure

```
data/
├── producthunt.db          # Main SQLite database
├── producthunt.db-wal      # Write-Ahead Log (WAL mode)
├── producthunt.db-shm      # Shared memory file
└── export/                 # CSV exports for Kaggle
    ├── userrow.csv
    ├── postrow.csv
    ├── topicrow.csv
    └── ...
```

### Configuration

Override database path via environment variables:

```bash
export DATABASE_PATH=/path/to/database.db
# or
export DATA_DIR=/path/to/data
```

### Best Practices

1. **Always review** auto-generated migrations
2. **Test migrations** on a database copy first
3. **Add data migrations** when transforming columns
4. **Version control** all migration files
5. **Backup before** applying migrations

### Troubleshooting

**Migration Conflicts:**
```bash
uv run alembic heads  # Show conflicting heads
uv run alembic merge -m "merge" head1 head2
producthuntdb upgrade
```

**Reset Database:**
```bash
rm data/producthunt.db*
producthuntdb upgrade
```

**Locked Database:**
```bash
# Close all connections, then:
rm data/producthunt.db-wal data/producthunt.db-shm
```

---

## Testing

ProductHuntDB has **160 passing tests** with **79.4% code coverage** (target: 90%).

### Running Tests

```bash
# Run all tests (excluding problematic Kaggle tests)
uv run pytest --ignore=tests/test_io.py tests/ --cov=producthuntdb --cov-report=term

# Run specific module
uv run pytest tests/test_models.py -v

# Generate HTML coverage report
uv run pytest tests/ --ignore=tests/test_io.py --cov=producthuntdb --cov-report=html
# Open logs/htmlcov/index.html
```

### Test Organization

One test module per source module:

- `test_cli.py` → CLI commands (18 tests)
- `test_config.py` → Configuration (21 tests)
- `test_io.py` → Database & Kaggle (40 tests, some excluded)
- `test_models.py` → Data models (38 tests)
- `test_pipeline.py` → Data sync pipeline (27 tests)
- `test_utils.py` → Utilities (43 tests)
- `test_integration.py` → Integration tests (6 tests)
- `test_e2e.py` → End-to-end tests (7 tests)

### Coverage by Module

| Module | Coverage | Status |
|--------|----------|--------|
| `__init__.py` | 100.0% | ✅ Complete |
| `models.py` | 98.8% | ✅ Excellent |
| `utils.py` | 94.9% | ✅ Excellent |
| `cli.py` | 85.0% | ⚠️ Good |
| `config.py` | 84.9% | ⚠️ Good |
| `pipeline.py` | 83.6% | ⚠️ Good |
| `io.py` | 55.1% | ⚠️ Needs work |
| **TOTAL** | **79.4%** | **Target: 90%** |

### Known Issues

**Kaggle API Tests** - Currently excluded due to hanging issues:
- `test_kaggle_manager_initialization_*`
- `test_publish_dataset_*`
- `test_kaggle_with_credentials`

These account for most of the coverage gap.

### Test Fixtures

Available in `tests/conftest.py`:

- `temp_db_path` - Temporary database file
- `test_db_manager` - Initialized DatabaseManager
- `mock_settings` - Mocked Settings object
- `mock_httpx_response` - HTTP response mocking
- `mock_posts_response` - GraphQL posts response

### Contributing Tests

When adding features:

1. ✅ Write tests first (TDD)
2. ✅ Aim for >90% coverage
3. ✅ Use descriptive test names
4. ✅ Mock external dependencies
5. ✅ Follow existing patterns
6. ✅ Add docstrings

---

## Project Structure

```
producthuntdb/
├── producthuntdb/          # Main package
│   ├── __init__.py         # Version and exports
│   ├── cli.py              # CLI commands
│   ├── config.py           # Settings management
│   ├── io.py               # Database & Kaggle I/O
│   ├── models.py           # SQLModel data models
│   ├── pipeline.py         # Data sync pipeline
│   └── utils.py            # Utilities (GraphQL, logging)
├── alembic/                # Database migrations
│   ├── env.py              # Alembic configuration
│   └── versions/           # Migration scripts
├── tests/                  # Test suite
│   ├── conftest.py         # Shared fixtures
│   ├── test_*.py           # Test modules
│   └── AGENTS.md           # Testing agent instructions
├── docs/                   # Documentation (you are here!)
│   ├── source/             # Sphinx source files
│   ├── build/              # Built HTML docs
│   └── Makefile            # Build commands
├── data/                   # Data directory
│   ├── producthunt.db      # SQLite database
│   └── export/             # CSV exports
├── export/                 # Kaggle dataset files
├── pyproject.toml          # Project configuration
├── alembic.ini             # Alembic config
└── README.md               # Project overview
```

---

## Architecture

ProductHuntDB follows a clean architecture with clear separation of concerns:

```{mermaid}
graph TB
    subgraph "ProductHuntDB Pipeline"
        subgraph "� Data Layer"
            db["SQLite Database<br/>producthunt.db"]
            csv["CSV Exports<br/>Kaggle Dataset"]
        end
        
        subgraph "🔄 Pipeline Layer"
            sync["Data Sync<br/>GraphQL Client"]
            export["Export Manager<br/>CSV Generation"]
            kaggle["Kaggle Manager<br/>Dataset Publishing"]
        end
        
        subgraph "🛠️ Core Layer"
            models["SQLModel Models<br/>Schema Definition"]
            config["Settings<br/>Configuration"]
            utils["Utils<br/>GraphQL, Logging"]
        end
        
        subgraph "👤 Interface Layer"
            cli["CLI Commands<br/>producthuntdb"]
        end
        
        subgraph "🌐 External Services"
            phapi["Product Hunt API<br/>GraphQL v2"]
            kaggleapi["Kaggle API<br/>Dataset Publishing"]
        end
    end
    
    %% Flow connections
    cli --> sync
    cli --> export
    cli --> kaggle
    
    sync --> models
    sync --> db
    sync --> phapi
    
    export --> db
    export --> csv
    
    kaggle --> csv
    kaggle --> kaggleapi
    
    models --> config
    sync --> utils
    sync --> config
    
    %% Styling
    classDef dataStyle fill:#da532c,stroke:#cc4400,stroke-width:2px,color:#fff
    classDef pipelineStyle fill:#ff7a6a,stroke:#ff6154,stroke-width:2px,color:#fff
    classDef coreStyle fill:#475569,stroke:#334155,stroke-width:2px,color:#fff
    classDef interfaceStyle fill:#64748b,stroke:#475569,stroke-width:2px,color:#fff
    classDef externalStyle fill:#1e293b,stroke:#0f172a,stroke-width:2px,color:#fff
    
    class db,csv dataStyle
    class sync,export,kaggle pipelineStyle
    class models,config,utils coreStyle
    class cli interfaceStyle
    class phapi,kaggleapi externalStyle
```

---

## CLI Reference

### Data Synchronization

```bash
# Sync all entities
producthuntdb sync-all

# Sync specific entities
producthuntdb sync-posts
producthuntdb sync-users
producthuntdb sync-comments
producthuntdb sync-topics
producthuntdb sync-collections
producthuntdb sync-votes
```

### Database Management

```bash
# Initialize database
producthuntdb upgrade

# Create migration
producthuntdb migrate --message "description"

# Rollback migration
producthuntdb downgrade

# View migration history
producthuntdb migration-history
```

### Data Export

```bash
# Export all tables to CSV
producthuntdb export

# Publish to Kaggle
producthuntdb publish
```

### Utilities

```bash
# Verify GraphQL schema
producthuntdb verify

# Check version
producthuntdb --version
```

---

## Configuration

ProductHuntDB is configured via environment variables or `.env` file:

### Required Variables

```bash
# Product Hunt API
PRODUCTHUNT_API_TOKEN=your_api_token

# Kaggle API (optional, for publishing)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_key
```

### Optional Variables

```bash
# Database
DATABASE_PATH=./data/producthunt.db
DATA_DIR=./data

# Kaggle Dataset
KAGGLE_DATASET_SLUG=username/producthunt-database
KAGGLE_DATASET_TITLE="Product Hunt Database"

# Logging
LOG_LEVEL=INFO
LOG_FILE=./logs/producthuntdb.log
```

---

## Resources

- **GitHub**: [wyattowalsh/producthuntdb](https://github.com/wyattowalsh/producthuntdb)
- **Product Hunt API**: [GraphQL v2 Documentation](https://api.producthunt.com/v2/docs)
- **SQLModel**: [Documentation](https://sqlmodel.tiangolo.com/)
- **Alembic**: [Documentation](https://alembic.sqlalchemy.org/)
- **Kaggle API**: [Documentation](https://github.com/Kaggle/kaggle-api)

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Write tests for your changes
4. Ensure tests pass (`uv run pytest`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/wyattowalsh/producthuntdb/blob/main/LICENSE) file for details.

---

**Happy Data Mining! 🚀**
