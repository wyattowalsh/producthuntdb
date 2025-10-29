# ProductHuntDB - Testing

**Note**: This file contains testing-specific instructions. See [root AGENTS.md](../AGENTS.md) for project-wide setup and conventions.

## Test Execution

### Quick Commands

```bash
# From project root:

# Full test suite with coverage report
make test-cov

# Fast tests (skip I/O-heavy tests)
make test
# or: uv run pytest --ignore=tests/test_io.py tests/

# Specific test types
uv run pytest -m unit              # Unit tests only
uv run pytest -m integration       # Integration tests
uv run pytest -m e2e              # End-to-end tests

# Single test file
uv run pytest tests/test_models.py -v

# Single test function
uv run pytest tests/test_models.py::test_post_row_creation -v

# Parallel execution (faster)
uv run pytest -n auto tests/
```

### Coverage Requirements

- **Minimum**: 88% (enforced by `--cov-fail-under=88` in `pyproject.toml`)
- **Target**: 90%+ per module
- **Reports**: HTML coverage at `logs/htmlcov/index.html`

```bash
# View coverage after running tests
open logs/htmlcov/index.html
```

## Test Structure

### Test Markers

Defined in `pyproject.toml`:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Tests with external dependencies (DB, API mocks)
- `@pytest.mark.e2e` - Full end-to-end scenarios
- `@pytest.mark.slow` - Long-running tests (can be skipped during dev)
- `@pytest.mark.asyncio` - Async/await tests (auto-detected)

### File Organization

- **1:1 mapping**: One test file per source module
  - `producthuntdb/models.py` → `tests/test_models.py`
  - `producthuntdb/cli.py` → `tests/test_cli.py`
  
- **Test file structure**:
  ```python
  """Tests for producthuntdb.module_name."""
  
  # Test classes group related tests
  class TestClassName:
      def test_specific_behavior(self, fixture_name):
          # Arrange, Act, Assert
  ```

## Fixtures & Test Data

### Key Fixtures (from conftest.py)

Available in all tests:

```python
# Configuration
test_settings: Settings              # Test-specific settings with temp directories
temp_db_path: Path                   # Unique temporary database per test

# Database
test_db_manager: DatabaseManager     # Pre-configured DB manager
test_session: Session                # SQLModel session

# API Mocking
mock_api_client: AsyncGraphQLClient  # Mocked API client
mock_api_response: dict              # Sample API response data

# Data Models
sample_post: PostRow                 # Example PostRow instance
sample_user: UserRow                 # Example UserRow instance
sample_topic: TopicRow               # Example TopicRow instance
# ... (see conftest.py for full list)
```

### Test Data Location

- **Fixtures**: `tests/conftest.py` (437 lines of shared fixtures)
- **Mock data**: Created dynamically in fixtures (no `tests/data/` directory needed)
- **Temporary files**: Auto-cleaned via pytest tmpdir and custom fixtures

### Mocking Strategy

- **External APIs**: Always mocked (use `mock_api_client` fixture)
- **Database**: Real SQLite in-memory or temp files (via `temp_db_path`)
- **File I/O**: Use pytest's `tmp_path` fixture
- **Environment variables**: Set in `test_settings` fixture

Example:
```python
def test_api_call(mock_api_client):
    # mock_api_client is pre-configured with sample responses
    result = await mock_api_client.fetch_posts()
    assert result is not None
```

## Pytest Configuration

Configuration in `[tool.pytest.ini_options]` (pyproject.toml):

- **Test discovery**: `test_*.py` files, `Test*` classes, `test_*` functions
- **Async**: Auto-detected via `asyncio_mode = "auto"`
- **Timeout**: 300s per test (prevents hangs)
- **Output**: Verbose with instant failure reporting (`--instafail`), emoji indicators
- **Coverage**: Branch coverage enabled, 88% minimum
- **Warnings**: Deprecation warnings ignored

### Useful pytest Options

```bash
# Show print statements
uv run pytest -s

# Stop on first failure
uv run pytest -x

# Verbose output
uv run pytest -v

# Show slowest tests
uv run pytest --durations=10

# Re-run failed tests
uv run pytest --lf

# Run tests in parallel (faster, uses pytest-xdist)
uv run pytest -n auto tests/

# Watch mode (requires pytest-watch)
uv run ptw tests/
```

### Test Parallelization

The project includes `pytest-xdist` for parallel test execution:

```bash
# Auto-detect CPU cores and parallelize
uv run pytest -n auto tests/

# Use specific number of workers
uv run pytest -n 4 tests/

# Parallel with coverage (slower but thorough)
uv run pytest -n auto --cov=producthuntdb tests/
```

**Note**: Some tests with shared resources may need `@pytest.mark.serial` to avoid conflicts.

### Property-Based Testing

The project includes `hypothesis` for property-based testing:

```python
from hypothesis import given
from hypothesis import strategies as st

@given(st.integers(min_value=1, max_value=100))
def test_page_size_validation(page_size):
    """Property test: page_size always validates correctly."""
    config = Settings(PAGE_SIZE=page_size)
    assert 1 <= config.PAGE_SIZE <= 100
```

Use for testing invariants and edge cases automatically.

## Writing New Tests

### Template

```python
"""Tests for producthuntdb.new_module."""

import pytest
from producthuntdb.new_module import MyClass


class TestMyClass:
    """Tests for MyClass."""

    def test_basic_functionality(self):
        """Test basic MyClass behavior."""
        # Arrange
        obj = MyClass(param="value")
        
        # Act
        result = obj.method()
        
        # Assert
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_method(self, mock_api_client):
        """Test async MyClass method."""
        result = await mock_api_client.async_method()
        assert result is not None

    @pytest.mark.integration
    def test_with_database(self, test_db_manager):
        """Integration test with real database."""
        # Uses test_db_manager fixture
        pass
```

### Best Practices

1. **One assertion per test** (when possible)
2. **Descriptive names**: `test_<what>_<when>_<expected>`
3. **Use fixtures** for setup/teardown
4. **Mark tests appropriately** (@pytest.mark.unit, etc.)
5. **Mock external dependencies** (API calls, file I/O)
6. **Test edge cases** and error conditions
7. **Keep tests fast** (unit tests < 100ms)
8. **Clean up resources** (fixtures handle this automatically)

## Coverage Configuration

Coverage settings in `[tool.coverage]` (pyproject.toml):

- **Branch coverage**: Enabled (tracks conditional branches)
- **Minimum**: 88% (CI gate)
- **Target**: 90%+ per module
- **Reports**: HTML (`logs/htmlcov/`), XML (`logs/coverage.xml`), terminal

```bash
# View detailed coverage
open logs/htmlcov/index.html

# Check specific module coverage
uv run pytest --cov=producthuntdb.models --cov-report=term-missing tests/test_models.py
```

### Test Timeouts

Tests have 300-second timeout (configured in `pyproject.toml`):

```python
# Override timeout for slow tests
@pytest.mark.timeout(600)
def test_slow_operation():
    pass

# Disable timeout for specific test
@pytest.mark.timeout(0)
def test_no_timeout():
    pass
```

## CI/CD Integration

**Note**: No CI workflows configured yet. When adding CI:

```yaml
# .github/workflows/test.yml (example)
- name: Run tests
  run: |
    uv sync --group test
    uv run pytest --cov=producthuntdb --cov-report=xml
```

Local test commands should match CI exactly.

## Troubleshooting

### Common Issues

**Database locked errors**:
- Each test gets unique temp DB via `temp_db_path` fixture
- Automatic cleanup after test completion

**Async test warnings**:
- Mark async tests with `@pytest.mark.asyncio` (auto-detected in this project)

**Coverage not meeting 88%**:
- Check uncovered lines: `logs/htmlcov/index.html`
- Add tests for missing branches and edge cases

**Import errors in tests**:
```bash
# Ensure test dependencies installed
uv sync --group test

# Verify pytest can find producthuntdb
uv run python -c "import producthuntdb; print('OK')"
```

## References

- [Root AGENTS.md](../AGENTS.md) - Project-wide conventions
- [conftest.py](conftest.py) - All test fixtures and configuration
- [pytest documentation](https://docs.pytest.org/) (observed: 2025-10-29)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) (observed: 2025-10-29)
