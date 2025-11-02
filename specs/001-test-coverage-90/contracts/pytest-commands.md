# Pytest Command Line Interface Contract

**Feature**: 001-test-coverage-90  
**Type**: CLI Contract  
**Status**: Design

## Overview

This contract defines the command-line interface for running tests with coverage, parallelization, and Hypothesis property-based testing. All commands MUST be prefixed with `uv run` per project standards.

## Core Commands

### 1. Run Full Test Suite with Coverage

**Command**:
```bash
uv run pytest tests/ \
  --cov=producthuntdb \
  --cov-report=html:logs/htmlcov \
  --cov-report=term-missing \
  --cov-fail-under=90 \
  -n auto
```

**Parameters**:
- `tests/`: Test directory to run
- `--cov=producthuntdb`: Measure coverage for producthuntdb package
- `--cov-report=html:logs/htmlcov`: Generate HTML report at specified path
- `--cov-report=term-missing`: Show missing lines in terminal
- `--cov-fail-under=90`: Exit with error if coverage < 90%
- `-n auto`: Parallel execution with auto-detected workers

**Exit Codes**:
- `0`: All tests passed, coverage ≥ 90%
- `1`: One or more tests failed
- `2`: Coverage < 90%
- `3`: Test collection error

**Expected Output**:
```
================================ test session starts =================================
platform darwin -- Python 3.13.0, pytest-8.3.3, pluggy-1.5.0
plugins: cov-5.0.0, xdist-3.6.1, asyncio-0.23.8, hypothesis-6.92.0
gw0 [500] / gw1 [500] / gw2 [500] / gw3 [500]
...
================================= 500 passed in 240.52s ===============================

----------- coverage: platform darwin, python 3.13.0 -----------
Name                        Stmts   Miss  Cover   Missing
---------------------------------------------------------
producthuntdb/__init__.py       6      0   100%
producthuntdb/api.py          164     22    87%   45-52, 89-95
producthuntdb/cli.py          405    201    50%   123-456, 789-1024
...
---------------------------------------------------------
TOTAL                        2328    209    91%

Required test coverage of 90.0% reached. Total coverage: 91.04%
```

---

### 2. Run Quick Test Suite (No Coverage, No Slow Tests)

**Command**:
```bash
uv run pytest tests/ -m "not slow" -n auto
```

**Parameters**:
- `-m "not slow"`: Skip tests marked with `@pytest.mark.slow`
- `-n auto`: Parallel execution

**Use Cases**:
- Local development rapid feedback
- Pre-commit hooks
- Quick validation before detailed coverage run

**Expected Execution Time**: < 30 seconds (vs < 5 minutes for full suite)

---

### 3. Run Specific Module Tests

**Command**:
```bash
uv run pytest tests/test_kaggle.py -v --cov=producthuntdb.kaggle --cov-report=term
```

**Parameters**:
- `tests/test_kaggle.py`: Specific test file
- `-v`: Verbose output (show individual test names)
- `--cov=producthuntdb.kaggle`: Coverage for specific module only
- `--cov-report=term`: Terminal output only

**Use Cases**:
- Focused development on single module
- Debugging specific test failures
- Iterating on coverage for under-tested modules

---

### 4. Run Property-Based Tests Only

**Command**:
```bash
uv run pytest tests/ -m "hypothesis" --hypothesis-show-statistics
```

**Parameters**:
- `-m "hypothesis"`: Run only tests marked with `@pytest.mark.hypothesis`
- `--hypothesis-show-statistics`: Show Hypothesis execution statistics

**Expected Output**:
```
test_models.py::test_post_row_roundtrip:
  - during reuse phase (0.00s):
    - Typical runtimes: 0-1 ms, ~ 50% in data generation
    - 100 passing examples, 0 failing examples, 0 invalid examples
  - during generate phase (2.50s):
    - Typical runtimes: 2-3 ms, ~ 45% in data generation  
    - 1000 passing examples, 0 failing examples, 5 invalid examples
  - Stopped because settings.max_examples=1000 
```

---

### 5. Reproduce Hypothesis Failure

**Command**:
```bash
uv run pytest tests/test_models.py::test_post_row_validation \
  --hypothesis-seed=12345 \
  --hypothesis-verbosity=verbose
```

**Parameters**:
- `--hypothesis-seed=12345`: Use specific seed to reproduce failure
- `--hypothesis-verbosity=verbose`: Show detailed Hypothesis output

**Use Cases**:
- Debugging property-based test failures
- Reproducing CI failures locally
- Investigating shrinking behavior

---

### 6. Update Hypothesis Example Database

**Command**:
```bash
# Hypothesis automatically updates .hypothesis/examples/ when tests run
uv run pytest tests/ -m "hypothesis"

# Commit changes to git
git add .hypothesis/
git commit -m "Update Hypothesis failure examples"
```

**Contract**:
- Hypothesis MUST persist failures to `.hypothesis/examples/`
- Directory MUST be git-tracked (not in `.gitignore`)
- Team members MUST pull and commit Hypothesis database changes

---

## Pytest Markers

**Standard Markers**:
```python
@pytest.mark.unit          # Unit test (mocked boundaries)
@pytest.mark.integration   # Integration test (real components)
@pytest.mark.e2e           # End-to-end test
@pytest.mark.slow          # Slow test (>5s execution)
@pytest.mark.asyncio       # Async test (requires pytest-asyncio)
@pytest.mark.hypothesis    # Property-based test using Hypothesis
```

**Usage in Tests**:
```python
import pytest
from hypothesis import given, strategies as st

@pytest.mark.unit
def test_simple_function():
    assert simple_function(1) == 2

@pytest.mark.integration
def test_database_integration(temp_database):
    # Uses real database fixture
    pass

@pytest.mark.slow
@pytest.mark.asyncio
async def test_api_rate_limiting():
    # Long-running async test
    pass

@pytest.mark.hypothesis
@given(st.integers())
def test_property_holds_for_all_ints(n):
    assert n + 0 == n
```

---

## Coverage Reports

### HTML Report Contract

**Location**: `logs/htmlcov/index.html`

**Contents**:
- Overall coverage percentage (color-coded: green ≥90%, yellow 75-89%, red <75%)
- Per-module coverage breakdown (sortable table)
- Line-by-line coverage visualization (green = covered, red = not covered)
- Branch coverage indicators
- Links to uncovered line numbers

**Access**:
```bash
# Generate report
uv run pytest --cov=producthuntdb --cov-report=html:logs/htmlcov

# Open in browser
open logs/htmlcov/index.html  # macOS
xdg-open logs/htmlcov/index.html  # Linux
```

### JSON Report Contract

**Location**: `logs/coverage.json`

**Schema**:
```json
{
  "meta": {
    "version": "7.4.0",
    "timestamp": "2025-11-02T12:34:56",
    "branch_coverage": true,
    "show_contexts": false
  },
  "files": {
    "producthuntdb/kaggle.py": {
      "executed_lines": [1, 2, 3, 5, 7, 10],
      "missing_lines": [15, 20, 25],
      "excluded_lines": [],
      "summary": {
        "covered_lines": 6,
        "num_statements": 9,
        "percent_covered": 66.67,
        "missing_branches": 2,
        "num_branches": 4,
        "percent_covered_display": "67"
      }
    }
  },
  "totals": {
    "covered_lines": 2119,
    "num_statements": 2328,
    "percent_covered": 91.04,
    "missing_lines": 209,
    "excluded_lines": 0
  }
}
```

---

## GitHub Actions Integration

**Workflow File**: `.github/workflows/test-coverage.yml`

**Test Execution Step**:
```yaml
- name: Run tests with coverage
  run: |
    uv run pytest tests/ \
      --cov=producthuntdb \
      --cov-report=html:logs/htmlcov \
      --cov-report=json:logs/coverage.json \
      --cov-fail-under=90 \
      -n auto \
      --junitxml=logs/junit.xml
  
- name: Upload coverage report
  uses: actions/upload-artifact@v4
  if: always()
  with:
    name: coverage-report
    path: logs/htmlcov/
    retention-days: 30

- name: Comment coverage on PR
  uses: orgoro/coverage@v3
  with:
    coverageFile: logs/coverage.json
    token: ${{ secrets.GITHUB_TOKEN }}
```

**Exit Code Handling**:
- Workflow fails if `uv run pytest` exits with non-zero code
- Coverage report uploaded even if tests fail (`if: always()`)
- PR comment shows coverage diff (new code vs base branch)

---

## Hypothesis Configuration

**Location**: `tests/conftest.py`

**Configuration Contract**:
```python
from hypothesis import settings, Verbosity, Phase

# Global settings
settings.register_profile("default", max_examples=100, deadline=None)
settings.register_profile("ci", max_examples=1000, deadline=5000)
settings.register_profile("dev", max_examples=50, deadline=None)

# Tiered settings
settings.register_profile("critical", max_examples=1000, deadline=10000)
settings.register_profile("complex", max_examples=500, deadline=5000)
settings.register_profile("standard", max_examples=200, deadline=2000)
settings.register_profile("simple", max_examples=100, deadline=1000)

# Use CI profile in GitHub Actions
import os
if os.getenv("CI"):
    settings.load_profile("ci")
else:
    settings.load_profile("default")
```

**Per-Test Overrides**:
```python
from hypothesis import given, settings, strategies as st

@given(st.integers())
@settings(max_examples=1000)  # Override for critical test
def test_critical_property(n):
    # Uses 1000 examples instead of default 100
    pass
```

---

## Validation Rules

### Command Execution
- ✅ **MUST** prefix all pytest commands with `uv run`
- ✅ **MUST** use `-n auto` for parallel execution (except when debugging)
- ✅ **MUST** use `--cov-fail-under=90` in CI
- ✅ **MUST** generate HTML + JSON coverage reports
- ✅ **SHOULD** use `-m "not slow"` for quick local feedback

### Coverage Thresholds
- ✅ **MUST** achieve ≥90% overall line coverage
- ✅ **MUST** achieve ≥85% branch coverage
- ✅ **SHOULD** achieve ≥85% for critical modules (kaggle, repository, telemetry, pipeline, io, cli)

### Hypothesis Configuration
- ✅ **MUST** use tiered example counts based on function complexity
- ✅ **MUST** commit `.hypothesis/` directory to git
- ✅ **MUST** use fixed seeds for deterministic execution
- ✅ **SHOULD** show statistics for property-based tests

### CI/CD Integration
- ✅ **MUST** run tests on all pushes and PRs
- ✅ **MUST** fail workflow if tests fail or coverage < 90%
- ✅ **MUST** upload HTML reports with 30-day retention
- ✅ **SHOULD** comment coverage diff on PRs

---

## Error Handling

### Test Failures
```
FAILED tests/test_kaggle.py::test_export_success - AssertionError: ...
```
**Action**: Fix the failing test before proceeding

### Coverage Below Threshold
```
FAILED: Required test coverage of 90.0% not reached. Total coverage: 88.50%
```
**Action**: Add tests to increase coverage

### Hypothesis Failure
```
Falsifying example: test_property(n=42)
    assert n + 1 > n  # Fails for n = maxint
```
**Action**: Fix code to handle edge case, example auto-saved to `.hypothesis/`

### Parallel Execution Issues
```
ERROR: xdist worker 'gw2' crashed while running 'test_async_function'
```
**Action**: Check for test isolation issues (shared state, unclosed resources)

