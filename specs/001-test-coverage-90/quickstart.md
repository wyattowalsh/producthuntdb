# Quick Start: Test Coverage Development

**Feature**: 001-test-coverage-90  
**Audience**: Developers implementing test coverage improvements  
**Est. Time**: 10 minutes to get started

## Prerequisites

- ProductHuntDB repository cloned
- `uv` package manager installed
- Python 3.11+ available
- On branch `001-test-coverage-90`

## Installation

### 1. Install Test Dependencies

```bash
cd /path/to/producthuntdb

# Add new testing dependencies
uv add --group test pytest-xdist hypothesis

# Sync all dependencies
uv sync --all-groups
```

**Expected output**:
```
Resolved 127 packages in 1.2s
Installed 2 packages in 450ms
 + hypothesis==6.92.0
 + pytest-xdist==3.5.0
```

### 2. Verify Installation

```bash
# Check pytest plugins loaded
uv run pytest --version

# Expected: pytest 8.3.3
# plugins: cov-5.0.0, xdist-3.6.1, asyncio-0.23.8, hypothesis-6.92.0
```

## Quick Validation

### Run Existing Tests

```bash
# Quick run (no coverage, skip slow tests)
uv run pytest tests/ -m "not slow" -n auto

# Expected: ~351 tests passing in ~30 seconds
```

### Check Current Coverage

```bash
# Full coverage report
uv run pytest tests/ \
  --cov=producthuntdb \
  --cov-report=term-missing \
  --cov-report=html:logs/htmlcov \
  -n auto

# Open HTML report
open logs/htmlcov/index.html  # macOS
xdg-open logs/htmlcov/index.html  # Linux
```

**Expected baseline**:
- Overall coverage: ~58.5%
- 351 tests passing
- 5 tests failing (test_metrics.py)

## Development Workflow

### Phase 1: Fix Existing Failures (BLOCKING)

**Goal**: Achieve zero test failures before adding new tests

```bash
# Run only test_metrics.py to see failures
uv run pytest tests/test_metrics.py -v

# Expected: 5 failures related to Prometheus registry issues
```

**Fix strategy**:
1. Identify root cause (registry not cleared between tests)
2. Add cleanup logic to conftest.py or test teardown
3. Re-run until all pass
4. Commit: `git commit -m "Fix test_metrics.py registry cleanup"`

**Success criteria**: `uv run pytest tests/` shows 0 failures

---

### Phase 2: Add Tests for Lowest-Coverage Module

**Priority order**: kaggle.py (0%) → repository.py (0%) → telemetry.py (3.9%) → ...

#### Example: Adding tests for kaggle.py

```bash
# Check current coverage
uv run pytest tests/test_kaggle.py --cov=producthuntdb.kaggle --cov-report=term

# Expected: 0% coverage (or low if tests exist but disabled)
```

**Test file structure** (create if doesn't exist):
```python
# tests/test_kaggle.py
import pytest
from hypothesis import given, strategies as st
from producthuntdb.kaggle import KaggleExporter
from producthuntdb.models import PostRow

@pytest.mark.unit
def test_kaggle_exporter_init(temp_database):
    """Test KaggleExporter initialization."""
    exporter = KaggleExporter(database_path=temp_database)
    assert exporter.database_path == temp_database

@pytest.mark.unit  
def test_export_to_csv(temp_database, tmp_path):
    """Test CSV export functionality."""
    exporter = KaggleExporter(database_path=temp_database)
    output_file = tmp_path / "export.csv"
    
    # Add test data to database
    # ... (mock or use fixture)
    
    exporter.export(output_file)
    assert output_file.exists()
    # ... verify CSV contents

@pytest.mark.hypothesis
@given(st.builds(PostRow))  # Use custom strategy
def test_post_row_serialization_roundtrip(post):
    """Property: PostRow serialization is lossless."""
    serialized = post.model_dump_json()
    deserialized = PostRow.model_validate_json(serialized)
    assert deserialized == post
```

**Iteration loop**:
```bash
# 1. Add tests
# 2. Run with coverage
uv run pytest tests/test_kaggle.py --cov=producthuntdb.kaggle --cov-report=term -v

# 3. Check uncovered lines
# Coverage report shows: "kaggle.py: 45-52, 78-85 not covered"

# 4. Add tests for uncovered lines
# 5. Repeat until module reaches 85% coverage
```

**Success criteria**: `producthuntdb/kaggle.py` shows ≥85% coverage

---

### Phase 3: Add Property-Based Tests

**When**: After module has basic test coverage (≥50%)

**Example**: Add property tests for validation logic

```python
# tests/test_models.py (add to existing file)
from hypothesis import given, strategies as st, settings
from producthuntdb.models import PostRow
import pytest

# Define custom strategy with business rules
@st.composite
def post_row_strategy(draw):
    """Generate valid PostRow instances."""
    return PostRow(
        post_id=draw(st.integers(min_value=1)),
        name=draw(st.text(min_size=1, max_size=100)),
        tagline=draw(st.text(max_size=200)),
        created_at=draw(st.datetimes(
            min_value=datetime(2013, 1, 1),  # Product Hunt launch
            max_value=datetime.now()
        )),
        votes_count=draw(st.integers(min_value=0)),
    )

@pytest.mark.hypothesis
@given(post_row_strategy())
@settings(max_examples=200)  # Standard complexity
def test_post_row_validation_accepts_valid_data(post):
    """Property: All generated PostRows are valid."""
    # If Hypothesis generates it, Pydantic should accept it
    assert post.model_validate(post.model_dump()) == post

@pytest.mark.hypothesis  
@given(post_row_strategy())
@settings(max_examples=1000)  # Critical complexity
def test_post_row_database_roundtrip(post, temp_database):
    """Property: Database persistence is lossless."""
    # Save to database
    db = DatabaseManager(temp_database)
    db.save_post(post)
    
    # Retrieve from database
    retrieved = db.get_post(post.post_id)
    assert retrieved == post
```

**Run property tests**:
```bash
uv run pytest tests/ -m "hypothesis" --hypothesis-show-statistics
```

**Success criteria**: Property tests generate 100-1000 examples per test, all pass

---

## Common Commands

### Development

```bash
# Quick feedback loop (no coverage)
uv run pytest tests/test_module.py -v

# With coverage for specific module
uv run pytest tests/test_module.py --cov=producthuntdb.module --cov-report=term

# Run only unit tests
uv run pytest -m unit

# Run only property-based tests  
uv run pytest -m hypothesis --hypothesis-show-statistics
```

### Coverage Analysis

```bash
# Full coverage report
uv run pytest --cov=producthuntdb --cov-report=html:logs/htmlcov --cov-report=term -n auto

# Open HTML report
open logs/htmlcov/index.html

# Check if meets 90% threshold
uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto
```

### Debugging

```bash
# Run single test with verbose output
uv run pytest tests/test_module.py::test_function -vv

# Show print statements
uv run pytest tests/test_module.py -s

# Drop into debugger on failure
uv run pytest tests/test_module.py --pdb

# Reproduce Hypothesis failure
uv run pytest tests/test_module.py::test_property \
  --hypothesis-seed=12345 \
  --hypothesis-verbosity=verbose
```

## CI/CD Preview

### Local CI Simulation

```bash
# Run exactly what CI runs
uv sync --all-groups
uv run pytest tests/ \
  --cov=producthuntdb \
  --cov-report=html:logs/htmlcov \
  --cov-report=json:logs/coverage.json \
  --cov-fail-under=90 \
  -n auto

# Check exit code
echo $?  # Should be 0 for success
```

### GitHub Actions

Once merged, every push/PR will:
1. Install dependencies (`uv sync --all-groups`)
2. Run full test suite with coverage
3. Fail if tests fail or coverage < 90%
4. Upload HTML coverage report (30-day retention)
5. Comment coverage diff on PR

**View reports**: GitHub Actions → Workflow run → Artifacts → `coverage-report`

## Troubleshooting

### "5 tests failing in test_metrics.py"

**Cause**: Prometheus registry not cleared between tests  
**Fix**: Add registry cleanup to conftest.py or test teardown  
**Priority**: Fix FIRST before adding new tests

### "Coverage lower after adding tests"

**Cause**: New code added without tests, or tests don't actually execute code  
**Fix**: Check coverage report HTML to see uncovered lines, add targeted tests

### "Tests exceed 5-minute timeout"

**Cause**: Too many Hypothesis examples or slow integration tests  
**Fix**: 
- Reduce example counts for non-critical tests
- Use `-m "not slow"` for quick runs
- Ensure `-n auto` for parallelization

### "Hypothesis generates invalid data"

**Cause**: Strategy doesn't respect business rules  
**Fix**: Add constraints to strategy (min_value, max_size, filters)

### "Tests pass locally but fail in CI"

**Cause**: Environment differences or missing Hypothesis database  
**Fix**: 
- Commit `.hypothesis/` directory to git
- Ensure `uv sync --all-groups` runs in CI
- Check Python version matches (3.11+)

## Next Steps

1. ✅ **Fix existing failures** - Run `uv run pytest tests/test_metrics.py`, fix until 0 failures
2. ✅ **Verify baseline** - Run `uv run pytest --cov=producthuntdb --cov-report=term -n auto`
3. ✅ **Pick first module** - Start with kaggle.py (0% coverage)
4. ✅ **Add basic tests** - Cover main functions and error paths
5. ✅ **Add property tests** - Use Hypothesis for complex validation/transformation
6. ✅ **Check coverage** - Ensure module reaches ≥85%
7. ✅ **Move to next module** - Follow priority order (repository.py, telemetry.py, ...)
8. ✅ **Repeat** - Until overall coverage ≥90%

## Getting Help

- **Coverage gaps**: Check `logs/htmlcov/index.html` for line-by-line visualization
- **Test strategy**: See `data-model.md` for entity relationships and validation rules
- **Hypothesis examples**: See `pytest-commands.md` contract for configuration
- **Project context**: See root `AGENTS.md` for package management and testing standards

## Success Metrics

- ✅ Overall coverage: ≥90%
- ✅ Branch coverage: ≥85%
- ✅ Test count: ≥500
- ✅ Failing tests: 0
- ✅ Execution time: <5 minutes
- ✅ Critical modules: ≥85% each

Run `uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto` to validate!

