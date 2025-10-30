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

**Available commands**: `sync`, `export`, `publish`, `status`, `verify`, `init`, `migrate`, `upgrade`, `downgrade`, `migration-history`

## Build & Test

### Testing

```bash
# Full test suite with 88% coverage minimum
make test-cov

# Quick test (skips slow I/O tests)
make test

# Specific test markers
uv run pytest -m unit          # Unit tests only
uv run pytest -m integration   # Integration tests
uv run pytest -m e2e          # End-to-end tests

# Parallel execution (faster)
uv run pytest -n auto tests/
```

**Coverage**: 88% minimum (enforced), reports at `logs/htmlcov/index.html`  
**Test markers**: `unit`, `integration`, `e2e`, `slow`, `asyncio` (see `pyproject.toml`)  
**CI Parity**: No CI workflows configured yet. Local commands should match CI when added.

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
```

**Do NOT use `pip` directly.** Always use `uv` for package operations.

**Dependency groups** (optional): `docs`, `notebook`, `quality`, `test` (see `pyproject.toml`)  
**Virtual environment**: `.venv/` (managed by uv, activate with `source .venv/bin/activate` or use `uv run`)

## Development Workflow

1. Create feature branch
2. Make changes (type hints + docstrings required)
3. Add/update tests (maintain 88%+ coverage)
4. Run quality checks: `make format && make lint && make test-cov`
5. Update docs if needed: `make docs`
6. Commit with descriptive message

### Quick Health Check

```bash
# Verify environment setup
uv sync && uv run python -c "import producthuntdb; print('✓')"
uv run producthuntdb init && ls data/producthunt.db && echo "✓ DB"
uv run pytest -m unit tests/ && echo "✓ Tests"
make lint && echo "✓ Lint"
uv run mypy producthuntdb/ && echo "✓ Types"
make docs && echo "✓ Docs"
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

**When adding CI**, ensure local commands match CI exactly:

```yaml
# Example .github/workflows/ci.yml
- run: uv sync --all-groups
- run: make test-cov
- run: make lint
- run: uv run mypy producthuntdb/
- run: make docs
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

