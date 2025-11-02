# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## ⚠️ CRITICAL: Package Manager

**This project uses `uv` exclusively. NEVER use `pip`, `python`, or `pytest` directly.**

```bash
# ❌ WRONG
pip install package
python script.py
pytest tests/

# ✅ RIGHT
uv add package
uv run python script.py
uv run pytest tests/
```

All Python commands MUST be prefixed with `uv run`. The virtual environment is managed automatically by `uv` at `.venv/` and should NOT be activated manually.

## Essential Commands

### Quick Setup
```bash
# Install dependencies
uv sync

# Initialize database
uv run producthuntdb init

# Verify environment
uv run python -c "import producthuntdb; print('✓')"
```

### Development Workflow
```bash
# Run tests (working subset)
make test

# Run tests with coverage (88% minimum enforced)
make test-cov

# Run specific test markers
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests
uv run pytest -m e2e           # End-to-end tests

# Run single test file
uv run pytest tests/test_models.py

# Code quality
make format    # Ruff formatter
make lint      # Ruff linter
uv run mypy producthuntdb/  # Type checking

# Documentation
make docs      # Build HTML docs
make htmllive  # Live-reload dev server
```

### CLI Usage
```bash
# All CLI commands require 'uv run' prefix
uv run producthuntdb init                      # Initialize database
uv run producthuntdb verify                    # Test API authentication
uv run producthuntdb sync                      # Incremental data sync
uv run producthuntdb sync --full-refresh       # Full refresh
uv run producthuntdb status                    # Database statistics
uv run producthuntdb export                    # Export to CSV
uv run producthuntdb publish                   # Publish to Kaggle
```

### Database Migrations
```bash
# Create migration after model changes
uv run producthuntdb migrate "description"

# Apply migrations
uv run producthuntdb upgrade head

# Rollback one revision
uv run producthuntdb downgrade -1

# View migration history
uv run producthuntdb migration-history
```

## Architecture Overview

ProductHuntDB is an ETL pipeline that syncs Product Hunt data to SQLite and publishes to Kaggle datasets.

### Data Flow

```
Product Hunt GraphQL API
         ↓
  AsyncGraphQLClient (api.py)
    - HTTP/2 multiplexing
    - Retry logic with tenacity
    - Rate limiting awareness
         ↓
  Pydantic Models (models.py)
    - API response validation
    - Type safety with v2 validators
         ↓
  DataPipeline (pipeline.py)
    - Orchestration layer
    - Dependency injection
    - Progress tracking
         ↓
  DatabaseManager (database.py)
    - SQLModel ORM
    - Batch operations
    - Crawl state tracking
         ↓
  SQLite Database (data/producthunt.db)
    - WAL mode enabled
    - Indexed for performance
         ↓
  KaggleManager (kaggle.py)
    - CSV export
    - Dataset versioning
```

### Core Components

**1. Pipeline Orchestration** (`pipeline.py`)
- `DataPipeline` class with dependency injection
- Supports both full refresh and incremental updates
- Safety margin for incremental syncs (default: 5 minutes)
- Progress tracking with tqdm

**2. GraphQL Client** (`api.py`)
- Async httpx client with HTTP/2 support
- Exponential backoff retry logic (tenacity)
- Semaphore-based concurrency control
- Rate limit tracking from API responses
- Optional OpenTelemetry tracing

**3. Database Layer** (`database.py`)
- `DatabaseManager` for CRUD operations
- SQLModel for type-safe ORM
- Batch operations for performance (5x faster)
- WAL mode + optimized PRAGMA settings
- Automatic index creation

**4. Data Models** (`models.py`)
- **Pydantic models**: API response validation (User, Post, Topic, Collection)
- **SQLModel tables**: Database persistence (UserRow, PostRow, TopicRow, etc.)
- **Link tables**: Many-to-many relationships (PostTopicLink, MakerPostLink)

**5. Configuration** (`config.py`)
- Pydantic Settings with `.env` support
- Environment profiles (DEVELOPMENT, PRODUCTION, TESTING, STAGING)
- Kaggle environment auto-detection
- Validates constraints (concurrency 1-10, page size 1-100)

### Key Design Patterns

**Dependency Injection** (pipeline.py):
```python
# Default implementations
pipeline = DataPipeline()

# Inject custom implementations for testing
pipeline = DataPipeline(client=MockGraphQLClient(), db=MockDatabaseManager())
```

**Dual Model System** (models.py):
- Pydantic models: Validate GraphQL responses, handle datetime parsing
- SQLModel tables: Database persistence, relationships, indexes
- Separation enables flexible API changes without DB migrations

**Incremental Updates with Safety**:
- `CrawlState` table tracks last sync timestamp per entity type
- Safety margin (default: 5 minutes) prevents missing data during concurrent updates
- Full refresh vs incremental controlled by `--full-refresh` flag

## Configuration

### Required Environment Variables
```bash
PRODUCTHUNT_TOKEN=your_token_here  # Get from api.producthunt.com
```

### Optional Configuration
```bash
# Data storage
DATA_DIR=./data                    # Base directory for all files
DATABASE_PATH=./data/producthunt.db # SQLite database location

# Operational parameters
MAX_CONCURRENCY=3                   # Concurrent API requests (1-10)
PAGE_SIZE=50                        # Items per query (1-100)
SAFETY_MINUTES=5                    # Incremental update margin (0-60)

# Kaggle publishing (optional)
KAGGLE_USERNAME=your_username
KAGGLE_KEY=your_api_key
```

### Environment Profiles
Set `ENVIRONMENT` to control behavior:
- `development` (default): Verbose logging, safe defaults
- `production`: Conservative settings, tracing enabled
- `testing`: In-memory DB, minimal logging
- `staging`: Pre-production validation

## Testing

### Test Structure
- `tests/test_*.py` - Mirror package structure
- `tests/conftest.py` - Fixtures (temp DB, reset loguru handlers)
- Coverage target: **88% minimum** (enforced in CI)

### Test Markers
```bash
uv run pytest -m unit          # Fast, isolated tests
uv run pytest -m integration   # DB/API integration tests
uv run pytest -m e2e           # Full workflow tests
uv run pytest -m slow          # Long-running tests
```

### Coverage Report
After `make test-cov`:
- HTML: `logs/htmlcov/index.html`
- Terminal: Shows missing lines
- JSON: `logs/coverage.json`
- XML: `logs/coverage.xml`

## Database Schema

### Core Tables
- `UserRow` - Product Hunt users (makers, hunters, voters)
- `PostRow` - Product launches with metrics
- `TopicRow` - Categories/tags
- `CollectionRow` - Curated post lists
- `CommentRow` - Discussions and threads
- `VoteRow` - Upvotes on posts/comments
- `MediaRow` - Images/videos with order

### Link Tables (Many-to-Many)
- `PostTopicLink` - Posts ↔ Topics
- `MakerPostLink` - Users ↔ Posts (as makers)
- `CollectionPostLink` - Collections ↔ Posts

### Tracking
- `CrawlState` - Last sync timestamp per entity type (posts, topics, collections)

### Indexes
Automatically created for:
- Post sorting (createdAt, featuredAt, votesCount)
- Foreign keys (userId, post_id, topic_id)
- Lookups (username, slug)
- Composite indexes for complex queries

## Important Conventions

### Module Organization
```
producthuntdb/
├── cli.py          # Typer CLI commands
├── config.py       # Pydantic Settings
├── models.py       # Pydantic + SQLModel models
├── pipeline.py     # ETL orchestration
├── api.py          # Async GraphQL client
├── database.py     # SQLite operations
├── kaggle.py       # Dataset publishing
├── utils.py        # Datetime, GraphQL, list helpers
├── logging.py      # Loguru configuration
├── metrics.py      # Prometheus metrics
├── telemetry.py    # OpenTelemetry tracing
├── types.py        # Type definitions
├── interfaces.py   # Protocol definitions
└── repository.py   # Repository pattern
```

### Code Style
- Type hints required on all public APIs
- Google-style docstrings
- Line length: 100 characters
- Ruff for linting and formatting
- Strict mypy checking with Pydantic plugin

### Async Patterns
- Use `asyncio.run()` for top-level entry points
- `async with` for GraphQL client lifecycle
- Semaphore for concurrency control (`settings.max_concurrency`)
- Tenacity for retry logic with exponential backoff

### Error Handling
- Classify errors as transient (retry) vs permanent (fail fast)
- Transient: Network timeouts, rate limits, 5xx responses
- Permanent: 4xx client errors, validation failures
- Log with structured context (loguru)

### Kaggle Workflow
1. **Local Development**: Use `.env` file for credentials
2. **Kaggle Notebooks**: Use Kaggle Secrets (Add-ons → Secrets)
3. **Publishing**: Dataset slug hardcoded to `wyattowalsh/producthuntdb`
4. **Scheduling**: Notebook supports daily cron jobs (~10 min/run)

## Troubleshooting

### Database Locked
```bash
rm data/producthunt.db* && uv run producthuntdb init
```

### Import Errors
```bash
uv sync && uv run python -c "import producthuntdb; print('✓')"
```

### Test Failures
- Check 88% coverage minimum requirement
- Verify fixtures in `tests/conftest.py`
- Ensure using `uv run pytest` (never run pytest directly)

### Missing Dependencies
```bash
uv sync --all-groups  # Install all dependency groups (docs, notebook, quality, test)
```

## References

- **AGENTS.md** - Complete development guide with test coverage tracking
- **README.md** - User documentation and quickstart
- **pyproject.toml** - Dependencies and tool configuration
- **docs/** - Sphinx documentation (MyST Markdown + Shibuya theme)
- **tests/AGENTS.md** - Testing strategies and coverage targets
