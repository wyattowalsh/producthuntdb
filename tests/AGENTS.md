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

**Minimum**: 88% (enforced by `--cov-fail-under=88` in `pyproject.toml`)  
**Reports**: HTML coverage at `logs/htmlcov/index.html`

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

**1:1 mapping**: One test file per source module

- `producthuntdb/models.py` → `tests/test_models.py`
- `producthuntdb/cli.py` → `tests/test_cli.py`

**Test file structure**:

```python
"""Tests for producthuntdb.module_name."""

# Test classes group related tests
class TestClassName:
    def test_specific_behavior(self, fixture_name):
        # Arrange, Act, Assert
```

## Fixtures & Test Data

### Key Fixtures

Available in all tests (from `conftest.py`):

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

**Test data**: Created dynamically in fixtures (no external data files)  
**Mocking**: External APIs always mocked, database uses real SQLite (temp files)  
**Cleanup**: Auto-cleaned via pytest tmpdir and custom fixtures

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
4. **Mark tests appropriately** (`@pytest.mark.unit`, etc.)
5. **Mock external dependencies** (API calls, file I/O)
6. **Test edge cases** and error conditions
7. **Keep tests fast** (unit tests < 100ms)

## Useful pytest Options

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

# Specific module coverage
uv run pytest --cov=producthuntdb.models --cov-report=term-missing tests/test_models.py
```

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

## References

- [Root AGENTS.md](../AGENTS.md) - Project-wide conventions
- [conftest.py](conftest.py) - All test fixtures and configuration
- [pyproject.toml](../pyproject.toml) - Test configuration (`[tool.pytest.ini_options]`, `[tool.coverage]`)
- [pytest documentation](https://docs.pytest.org/) (observed: 2025-10-30)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) (observed: 2025-10-30)
