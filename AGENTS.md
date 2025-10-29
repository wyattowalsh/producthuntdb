# ProductHuntDB

Product Hunt GraphQL API data sink with SQLite storage and Kaggle dataset management.

## Quickstart

```bash
# Clone and setup
git clone https://github.com/wyattowalsh/producthuntdb.git
cd producthuntdb

# Install dependencies
uv sync

# Configure environment (required)
cp .env.example .env
# Edit .env and add your PRODUCTHUNT_TOKEN

# Initialize database
uv run producthuntdb init

# Verify installation
uv run producthuntdb --help
```

## Build & Test

### Testing

Run full test suite with coverage (88% minimum required):

```bash
# All tests with coverage
make test-cov

# Quick test without slow tests
uv run pytest --ignore=tests/test_io.py tests/

# Specific test types (via markers)
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e

# Single test file
uv run pytest tests/test_models.py
```

Coverage reports: `logs/htmlcov/index.html`

**CI Parity**: No CI workflows configured yet. Local tests match expected CI behavior.

### Database Migrations

```bash
# Create migration after model changes
uv run alembic revision --autogenerate -m "description"

# Apply migrations
uv run alembic upgrade head

# Rollback
uv run alembic downgrade -1
```

Migration scripts: `alembic/versions/`

## Code Quality

### Linting & Formatting

```bash
# Format code
make format
# or: uv run ruff format producthuntdb/

# Lint
make lint
# or: uv run ruff check producthuntdb/

# Type checking
uv run mypy producthuntdb/
```

Configuration:

- Ruff: `[tool.ruff]` in `pyproject.toml` (line length 100, Python 3.11+)
- mypy: `[tool.mypy]` in `pyproject.toml` (strict mode, Pydantic plugin)
- Style: Ruff handles both linting and formatting (isort, flake8-bugbear, pyupgrade)

### Pre-commit Hooks

Optional but recommended for consistent quality checks:

```bash
# Install pre-commit hooks (one-time setup)
uv sync --group quality
uv run pre-commit install

# Run hooks manually on all files
uv run pre-commit run --all-files

# Run hooks on staged files (automatic on git commit)
git commit -m "your message"
```

Pre-commit automatically runs Ruff (format + lint) and mypy on staged files before each commit.

### Key Conventions

- Python 3.11+ required
- Type hints on all public functions and methods
- Pydantic v2 for data validation
- SQLModel for database models
- Async/await for API calls (httpx)
- Rich console output for CLI
- Structured logging via loguru

## Documentation

```bash
# Build HTML docs
make docs
# or: cd docs && make html

# Live-reload dev server (opens browser on http://127.0.0.1:8000)
make htmllive
# or: cd docs && make livehtml

# Clean build
cd docs && make clean
```


Documentation structure:

- Source: `docs/source/` (MyST Markdown + reStructuredText)
- Config: `docs/source/conf.py` (Sphinx + Shibuya theme)
- Build output: `docs/build/html/`
- Tool docs: `docs/source/tools/` (per-library references)


Docs use Shibuya theme with extensions: myst-parser, autodoc-pydantic, sphinx-design, sphinx-copybutton, sphinxcontrib-mermaid, and more. See dependency group `docs` in `pyproject.toml`.

## Security & Secrets

**CRITICAL**: Never commit `.env` file or API tokens to version control.

### Secrets Management

1. **Local development**: Copy `.env.example` to `.env` and fill in credentials
2. **Kaggle notebooks**: Use Kaggle Secrets (Settings → Add-ons → Secrets)

### Required Secrets

- `PRODUCTHUNT_TOKEN`: Product Hunt API token (required)
  - Get from: <https://api.producthunt.com/v2/oauth/applications>


### Optional Secrets

- `KAGGLE_USERNAME`: For dataset publishing
- `KAGGLE_KEY`: Kaggle API key
- `KAGGLE_DATASET_SLUG`: Dataset identifier (username/dataset-name)

Configuration managed via `producthuntdb/config.py` (Pydantic Settings with validation).

## CLI Usage

```bash
# Initialize database and schema
uv run producthuntdb init

# Harvest data (full or incremental)
uv run producthuntdb harvest         # Incremental (default)
uv run producthuntdb harvest --full  # Full refresh

# Export to CSV
uv run producthuntdb export

# Publish to Kaggle (requires Kaggle credentials)
uv run producthuntdb kaggle-publish

# Show configuration
uv run producthuntdb info
```

Entry point: `producthuntdb.cli:main`

## Project Structure

```text
producthuntdb/
├── producthuntdb/      # Main package
│   ├── cli.py          # Typer CLI commands
│   ├── config.py       # Pydantic Settings
│   ├── io.py           # AsyncGraphQLClient, DatabaseManager, KaggleManager
│   ├── models.py       # SQLModel database models
│   ├── pipeline.py     # Data harvesting pipeline
│   └── utils.py        # Retry logic, rate limiting
├── tests/              # pytest test suite (see tests/AGENTS.md)
├── docs/               # Sphinx documentation (see docs/AGENTS.md)
├── alembic/            # Database migrations
├── data/               # SQLite database (not in repo)
├── export/             # CSV exports
└── logs/               # Coverage reports
```


## Package Manager

This project uses **`uv`** exclusively ([installation guide](https://docs.astral.sh/uv/)).

Common commands:

- `uv sync` - Install/sync all dependencies
- `uv sync --group docs` - Install with docs dependencies
- `uv add <package>` - Add new dependency
- `uv run <command>` - Run in virtual environment
- `uv pip list` - List installed packages

**Do NOT use `pip` directly.** Use `uv` for all package operations.


### Dependency Groups

Optional dependency groups defined in `pyproject.toml`:

- **`docs`**: Sphinx documentation tools (Shibuya theme, MyST parser, extensions)
- **`notebook`**: Jupyter/JupyterLab with extensions
- **`quality`**: Linting and type checking (Ruff, mypy, pre-commit, pylint)
- **`test`**: Testing frameworks (pytest, coverage, hypothesis, mocks)

Install specific groups:

```bash
uv sync --group docs --group test    # Multiple groups
uv sync --all-groups                 # Install everything
```


### Virtual Environment

uv creates and manages a virtual environment at `.venv/`:

```bash
# Activate manually (optional, uv run handles this)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

## Development Workflow

1. Create feature branch
2. Make changes with type hints and docstrings
3. Add/update tests (maintain 88%+ coverage)
4. Format: `make format`
5. Lint: `make lint`
6. Test: `make test-cov`
7. Update docs if needed
8. Commit with descriptive message

## Quick Health Check

Verify your development environment is working correctly:

```bash
# 1. Check dependencies
uv sync
uv run python -c "import producthuntdb; print('✓ Package imports')"

# 2. Check database
uv run producthuntdb init
ls data/producthunt.db && echo "✓ Database initialized"

# 3. Run fast tests
uv run pytest -m unit tests/ && echo "✓ Unit tests pass"

# 4. Check code quality
uv run ruff check producthuntdb/ && echo "✓ Linting passes"
uv run mypy producthuntdb/ && echo "✓ Type checking passes"

# 5. Build docs
make docs && echo "✓ Documentation builds"
```

All checks should pass before opening a pull request.

## Troubleshooting

### Database Locked Errors

SQLite uses WAL mode for better concurrency. If locked:

```bash
# Delete database and reinitialize
rm data/producthunt.db*
uv run producthuntdb init
```

### Import Errors

```bash
# Ensure all dependencies are synced
uv sync

# Verify environment
uv run python -c "import producthuntdb; print('OK')"
```

### Test Failures

- Check coverage requirement: 88% minimum
- Temporary DBs auto-cleaned via `conftest.py` fixtures
- Loguru handlers reset per test to avoid I/O errors

## References

- [Project README](README.md) - User-facing documentation
- [pyproject.toml](pyproject.toml) - Dependencies and tool configuration
- [Makefile](Makefile) - Common development tasks
- [AGENTS.md specification](https://agents.md) (observed: 2025-10-29)
- [uv documentation](https://docs.astral.sh/uv/) (observed: 2025-10-29)
- [Shibuya theme docs](https://shibuya.lepture.com/) (observed: 2025-10-29)

