# ProductHuntDB

Product Hunt GraphQL API data sink with SQLite storage and Kaggle dataset management.

## ⚠️ CRITICAL: Package Manager

**This project uses `uv` exclusively. NEVER use `pip`, `python`, or `pytest` directly.**

- ❌ WRONG: `pip install`, `python script.py`, `pytest tests/`
- ✅ RIGHT: `uv add <package>`, `uv run python script.py`, `uv run pytest tests/`

See [Package Manager](#package-manager) section for complete details.

## Overview

ProductHuntDB syncs Product Hunt API data to SQLite and exports to Kaggle datasets. Uses `uv` for Python package management, Typer for CLI, and Pydantic for config validation.

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

**Key commands**: `sync`, `export`, `publish`, `status`, `verify`, `init`, `migrate`, `upgrade`, `downgrade`, `migration-history`

## Build & Test

### Testing

**ALWAYS use `uv run` prefix for all test commands.**

```bash
# Full test suite with 88% coverage minimum
make test-cov                  # Uses uv internally

# Quick test (skips slow I/O tests)
make test                      # Uses uv internally

# Specific test markers (ALWAYS prefix with 'uv run')
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests
uv run pytest -m e2e           # End-to-end tests

# Parallel execution (faster)
uv run pytest -n auto tests/

# ❌ WRONG: pytest tests/
# ✅ RIGHT: uv run pytest tests/
```

**Coverage**: 88% minimum (enforced), reports at `logs/htmlcov/index.html`  
**Test markers**: `unit`, `integration`, `e2e`, `slow`, `asyncio` (see `pyproject.toml`)  
**CI Parity**: No CI workflows configured yet. Local commands should match CI when added.

### Database Migrations

**ALWAYS use `uv run` prefix for all migration commands.**

```bash
# Create migration after model changes
uv run producthuntdb migrate "description"

# Apply migrations
uv run producthuntdb upgrade head

# Rollback one revision
uv run producthuntdb downgrade -1

# View migration history
uv run producthuntdb migration-history

# ❌ WRONG: producthuntdb migrate "description"
# ✅ RIGHT: uv run producthuntdb migrate "description"
```

Migration scripts: `alembic/versions/` | Config: `alembic.ini`

## Code Quality

```bash
# Format and lint
make format    # Ruff formatter
make lint      # Ruff linter
uv run mypy producthuntdb/  # Type checking

# Pre-commit hooks (optional)
uv sync --group quality
uv run pre-commit install
```

**Configuration**: `[tool.ruff]`, `[tool.mypy]`, `[tool.pylint]` in `pyproject.toml`  
**Line length**: 100 | **Python**: 3.11+ | **Type hints**: Required on public APIs

**Key conventions**:

- Pydantic v2 for validation | SQLModel for database | httpx for async HTTP
- Rich for CLI output | loguru for structured logging
- Google-style docstrings | Strict type checking with mypy

## Documentation

```bash
# Build HTML docs
make docs

# Live-reload dev server (auto-opens browser at http://127.0.0.1:8000)
make htmllive

# Clean build artifacts
cd docs && make clean
```

**Format**: MyST Markdown + reStructuredText | **Theme**: Shibuya | **Engine**: Sphinx  
**Source**: `docs/source/` | **Build**: `docs/build/html/` | **Config**: `docs/source/conf.py`  
**Details**: See [docs/AGENTS.md](docs/AGENTS.md) for documentation-specific instructions

## Security & Secrets

**CRITICAL**: Never commit `.env` or API tokens to version control.

### Environment Setup

```bash
# Local development
cp .env.example .env
# Edit .env and add credentials
```

### Required Secrets

- `PRODUCTHUNT_TOKEN`: Product Hunt API token ([get here](https://api.producthunt.com/v2/oauth/applications))

### Optional Secrets (for Kaggle publishing)

- `KAGGLE_USERNAME`, `KAGGLE_KEY`, `KAGGLE_DATASET_SLUG`

**Config management**: `producthuntdb/config.py` (Pydantic Settings with validation)  
**Kaggle notebooks**: Use Kaggle Secrets (Settings → Add-ons → Secrets)

## CLI Usage

**CRITICAL: ALWAYS use `uv run` prefix for all CLI commands.**

```bash
# Core workflow
uv run producthuntdb init           # Initialize database
uv run producthuntdb verify         # Test API authentication
uv run producthuntdb sync           # Sync data from Product Hunt
uv run producthuntdb status         # Show database statistics
uv run producthuntdb export         # Export to CSV
uv run producthuntdb publish        # Publish to Kaggle (requires credentials)

# Database migrations
uv run producthuntdb migrate "description"     # Create migration
uv run producthuntdb upgrade head              # Apply migrations
uv run producthuntdb downgrade -1              # Rollback
uv run producthuntdb migration-history         # View history

# ❌ WRONG: producthuntdb sync
# ✅ RIGHT: uv run producthuntdb sync
```

Entry point: `producthuntdb.cli:main` | Full help: `uv run producthuntdb --help`

## Project Structure

```text
producthuntdb/
├── producthuntdb/      # Main package (cli, config, io, models, pipeline, utils)
├── tests/              # pytest suite (see tests/AGENTS.md)
├── docs/               # Sphinx docs (see docs/AGENTS.md)
├── alembic/            # Database migrations
├── data/               # SQLite database (gitignored)
├── export/             # CSV exports
└── logs/               # Coverage reports
```

**Key modules**: `cli.py` (Typer CLI), `config.py` (Pydantic Settings), `io.py` (API/DB/Kaggle), `models.py` (SQLModel), `pipeline.py` (data sync), `utils.py` (retry/rate limiting)

## Package Manager

This project uses **`uv`** exclusively ([docs](https://docs.astral.sh/uv/), observed: 2025-10-30).

```bash
uv sync                              # Install/sync all dependencies
uv sync --group docs                 # Install with specific group
uv sync --all-groups                 # Install everything
uv add <package>                     # Add new dependency
uv run <command>                     # Run in virtual environment
uv run python <script.py>            # Run Python scripts
uv run pytest <test_file>            # Run tests
```

**CRITICAL: ALWAYS use `uv` for ALL Python operations.**

- ❌ **NEVER use**: `pip install`, `pip uninstall`, `python -m pip`, `python script.py`, `pytest`
- ✅ **ALWAYS use**: `uv add`, `uv remove`, `uv run python script.py`, `uv run pytest`
- ❌ **NEVER activate venv manually** and run commands directly
- ✅ **ALWAYS prefix with** `uv run` or use `uv sync` to manage environment

**Dependency groups** (optional): `docs`, `notebook`, `quality`, `test` (see `pyproject.toml`)  
**Virtual environment**: `.venv/` (managed by uv automatically, DO NOT activate manually)

## Development Workflow

1. Create feature branch
2. Make changes (type hints + docstrings required)
3. Add/update tests (maintain 88%+ coverage)
4. Run quality checks: `make format && make lint && make test-cov`
5. Update docs if needed: `make docs`
6. Commit with descriptive message

### Quick Health Check

**CRITICAL: ALL commands must use `uv run` prefix.**

```bash
# Verify environment setup
uv sync && uv run python -c "import producthuntdb; print('✓')"
uv run producthuntdb init && ls data/producthunt.db && echo "✓ DB"
uv run pytest -m unit tests/ && echo "✓ Tests"
make lint && echo "✓ Lint"
uv run mypy producthuntdb/ && echo "✓ Types"
make docs && echo "✓ Docs"

# ❌ WRONG: python -c "import producthuntdb"
# ✅ RIGHT: uv run python -c "import producthuntdb"
```

All checks must pass before submitting pull requests.

## Troubleshooting

### Database Locked

```bash
rm data/producthunt.db* && uv run producthuntdb init
```

### Import Errors

```bash
uv sync && uv run python -c "import producthuntdb; print('OK')"
```

### Test Failures

- 88% coverage minimum enforced
- Temporary DBs auto-cleaned via `conftest.py` fixtures
- Loguru handlers reset per test

## CI/CD

**Status**: No CI workflows configured yet.

**When adding CI**, ensure local commands match CI exactly. Recommended structure:

```yaml
# .github/workflows/ci.yml (example)
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v3
        with:
          version: "latest"
      - name: Install dependencies
        run: uv sync --all-groups
      - name: Run tests
        run: make test-cov
      - name: Lint
        run: make lint
      - name: Type check
        run: uv run mypy producthuntdb/
      - name: Build docs
        run: make docs
```

**Local verification before push**:

```bash
# Match CI commands exactly
uv sync --all-groups && make test-cov && make lint && uv run mypy producthuntdb/ && make docs
```

## References

- [README.md](README.md) - User documentation
- [pyproject.toml](pyproject.toml) - Dependencies & tool config
- [Makefile](Makefile) - Development tasks
- [tests/AGENTS.md](tests/AGENTS.md) - Testing instructions
- [docs/AGENTS.md](docs/AGENTS.md) - Documentation instructions
- [AGENTS.md specification](https://agents.md) (observed: 2025-10-30)
- [uv documentation](https://docs.astral.sh/uv/) (observed: 2025-10-30)
- [pytest documentation](https://docs.pytest.org/) (observed: 2025-10-30)
