# Data Model: Test Coverage Entities

**Feature**: 001-test-coverage-90  
**Date**: 2025-11-02  
**Status**: Phase 1 Design

## Overview

This feature enhances the testing infrastructure without modifying production data models. The "entities" here represent test artifacts, coverage metrics, and testing workflows rather than business domain objects.

## Core Entities

### 1. TestSuite

**Purpose**: Represents the complete collection of tests for the producthuntdb package

**Attributes**:
- `total_count: int` - Total number of tests (target: ≥500)
- `passing_count: int` - Number of passing tests
- `failing_count: int` - Number of failing tests (target: 0)
- `skipped_count: int` - Number of skipped tests (target: 0)
- `execution_time: float` - Total execution time in seconds (target: <300s)
- `coverage_percentage: float` - Overall line coverage (target: ≥90%)
- `branch_coverage_percentage: float` - Branch coverage (target: ≥85%)
- `parallel_workers: int` - Number of parallel workers used (auto-detected)

**Relationships**:
- Contains many `TestModule` entities (one per source module)
- Generates one `CoverageReport` per execution
- Persists `HypothesisExample` failures across runs

**State Transitions**:
```
[Idle] → [Running] → [Complete]
         ↓
      [Failed] (if any test fails or coverage < 90%)
```

**Validation Rules**:
- `failing_count` MUST be 0 before deployment
- `coverage_percentage` MUST be ≥ 90%
- `execution_time` MUST be < 300 seconds
- `skipped_count` SHOULD be 0 (all tests enabled)

---

### 2. TestModule

**Purpose**: Represents tests for a single source module (e.g., test_kaggle.py tests kaggle.py)

**Attributes**:
- `module_name: str` - Source module name (e.g., "kaggle", "repository")
- `test_file_path: Path` - Path to test file (e.g., "tests/test_kaggle.py")
- `source_file_path: Path` - Path to source module (e.g., "producthuntdb/kaggle.py")
- `test_count: int` - Number of tests in this module
- `line_coverage: float` - Line coverage percentage (0-100)
- `branch_coverage: float` - Branch coverage percentage (0-100)
- `lines_covered: int` - Number of lines covered
- `lines_total: int` - Total lines in source module
- `uncovered_lines: List[int]` - Line numbers not covered by tests
- `priority: int` - Implementation priority (1=highest)
- `target_coverage: float` - Target coverage (85% for critical modules, 90% otherwise)

**Relationships**:
- Belongs to one `TestSuite`
- Contains many `TestCase` entities
- Has many `PropertyTest` entities (if using Hypothesis)
- Generates `ModuleCoverageReport`

**Priority Order** (lowest coverage first):
1. kaggle.py (0% → 85%) - Priority 1
2. repository.py (0% → 85%) - Priority 2
3. telemetry.py (3.9% → 85%) - Priority 3
4. pipeline.py (10.1% → 85%) - Priority 4
5. io.py (21.7% → 85%) - Priority 5
6. cli.py (50.5% → 85%) - Priority 6

**Validation Rules**:
- `line_coverage` MUST be ≥ target_coverage before marking complete
- `test_file_path` MUST mirror `source_file_path` structure
- Unit tests MUST mock all external boundaries (network, DB, filesystem)

---

### 3. TestCase

**Purpose**: Individual test function (example-based or integration test)

**Attributes**:
- `test_name: str` - Test function name (e.g., "test_export_success")
- `test_type: Enum` - Type: unit, integration, e2e
- `status: Enum` - Status: pass, fail, skip, xfail
- `execution_time: float` - Time in seconds
- `failure_message: Optional[str]` - Error message if failed
- `markers: List[str]` - pytest markers (e.g., ["asyncio", "slow"])
- `covered_lines: Set[int]` - Lines covered by this test

**Relationships**:
- Belongs to one `TestModule`
- May use multiple `Fixture` entities
- Covers specific source code paths

**State Transitions**:
```
[Queued] → [Running] → [Pass]
                    ↓
                  [Fail] → [Fixed] → [Pass]
                    ↓
                  [Skip] (intentional or conditional)
```

**Validation Rules**:
- `status` MUST NOT be "fail" in main branch
- `execution_time` SHOULD be < 10s for unit tests
- Unit tests MUST have `test_type = unit` and mock external calls

---

### 4. PropertyTest

**Purpose**: Hypothesis property-based test that generates many examples

**Attributes**:
- `property_name: str` - Property being tested (e.g., "roundtrip_serialization")
- `function_complexity: Enum` - Critical, Complex, Standard, Simple
- `example_count: int` - Number of examples to generate (based on complexity)
- `strategy_type: str` - Hypothesis strategy used (e.g., "st.builds(PostRow)")
- `seed: int` - Random seed for reproducibility
- `shrink_steps: int` - Number of shrinking steps if failure found
- `minimal_failing_example: Optional[Any]` - Smallest input that causes failure

**Relationships**:
- Belongs to one `TestModule`
- Uses one or more `HypothesisStrategy` entities
- May generate `HypothesisExample` failures

**Example Count Tiers**:
| Complexity | Example Count | Use Cases |
|-----------|---------------|-----------|
| Critical | 1000 | Security, data integrity, authentication, payment |
| Complex | 500 | Multi-step transformations, state machines |
| Standard | 200 | Validation, formatting, parsing |
| Simple | 100 | Getters, setters, simple utils |

**Validation Rules**:
- `example_count` MUST match `function_complexity` tier
- `seed` MUST be fixed for deterministic execution
- Failing examples MUST be persisted to `.hypothesis/examples/`

---

### 5. HypothesisStrategy

**Purpose**: Custom data generator for domain-specific types

**Attributes**:
- `strategy_name: str` - Strategy identifier (e.g., "post_row_strategy")
- `target_type: Type` - Python type being generated (e.g., PostRow)
- `constraints: Dict` - Business rules and invariants
- `generation_logic: str` - Strategy definition (for documentation)

**Relationships**:
- Used by many `PropertyTest` entities
- Generates instances of domain types (PostRow, UserRow, etc.)

**Example Strategies**:
```python
# Strategy for PostRow Pydantic model
post_row_strategy = st.builds(
    PostRow,
    post_id=st.integers(min_value=1),
    name=st.text(min_size=1, max_size=100),
    tagline=st.text(max_size=200),
    created_at=st.datetimes(
        min_value=datetime(2013, 1, 1),  # Product Hunt launch date
        max_value=datetime.now()
    ),
    votes_count=st.integers(min_value=0),
    # ... constrained to business rules
)

# Strategy for GraphQL API responses
graphql_response_strategy = st.fixed_dictionaries({
    "data": st.one_of(
        st.fixed_dictionaries({"posts": st.lists(post_row_strategy)}),
        st.none()  # Error case
    ),
    "errors": st.one_of(
        st.lists(st.fixed_dictionaries({"message": st.text()})),
        st.none()
    )
})
```

**Target Count**: ≥10 custom strategies

---

### 6. HypothesisExample

**Purpose**: Persisted failing example from Hypothesis test

**Attributes**:
- `example_id: str` - Unique identifier
- `property_test_name: str` - Test that failed
- `input_data: Any` - Minimal failing input (shrunk)
- `exception_type: str` - Exception raised
- `traceback: str` - Full stack trace
- `discovered_at: datetime` - When failure was found
- `fixed_at: Optional[datetime]` - When code was fixed

**Relationships**:
- Generated by one `PropertyTest`
- Persisted to `.hypothesis/examples/` directory
- Git-tracked for team-wide reproducibility

**State Transitions**:
```
[Discovered] → [Reproduced] → [Fixed] → [Archived]
              ↓
            [False Positive] → [Suppressed]
```

**Validation Rules**:
- Examples MUST be git-tracked in `.hypothesis/` directory
- Examples MUST be reproducible across all environments
- Fixed examples SHOULD be added as regression tests

---

### 7. CoverageReport

**Purpose**: Coverage analysis output for a test run

**Attributes**:
- `report_id: str` - Unique identifier (timestamp-based)
- `overall_coverage: float` - Total line coverage percentage
- `overall_branch_coverage: float` - Total branch coverage percentage
- `module_reports: List[ModuleCoverageReport]` - Per-module breakdowns
- `uncovered_lines: Dict[str, List[int]]` - Lines missing coverage by file
- `generated_at: datetime` - Report generation time
- `html_path: Path` - Path to HTML report
- `json_path: Path` - Path to JSON report

**Relationships**:
- Generated by one `TestSuite` execution
- Contains many `ModuleCoverageReport` entities
- Uploaded as GitHub Actions artifact (30-day retention)

**Output Formats**:
1. **Terminal**: Color-coded summary with pass/fail status
2. **HTML**: Interactive line-by-line visualization (`logs/htmlcov/index.html`)
3. **JSON**: Programmatic access for CI/CD (`logs/coverage.json`)
4. **XML**: CodeCov/Coveralls integration (`logs/coverage.xml`)

**Validation Rules**:
- `overall_coverage` MUST be ≥ 90% to pass CI
- HTML reports MUST be uploaded to GitHub Actions artifacts
- Reports MUST show line-by-line coverage status

---

### 8. Fixture

**Purpose**: pytest fixture providing test dependencies (mocks, databases, configs)

**Attributes**:
- `fixture_name: str` - Fixture function name (e.g., "temp_database")
- `scope: str` - Fixture scope: function, class, module, session
- `autouse: bool` - Whether fixture runs automatically
- `dependencies: List[str]` - Other fixtures this depends on

**Relationships**:
- Used by many `TestCase` entities
- Defined in `conftest.py` or test modules
- May create temporary resources (databases, files)

**Key Fixtures** (from conftest.py):
- `temp_database`: Temporary SQLite database for tests
- `mock_api_client`: Mocked httpx client for API calls
- `sample_post_data`: Fixture providing test data
- `loguru_reset`: Cleans up loguru handlers between tests

**Validation Rules**:
- Fixtures MUST clean up resources (databases, files, handlers)
- Fixtures SHOULD use appropriate scope (avoid session scope unless necessary)
- Mock fixtures MUST simulate realistic responses

---

### 9. GitHubActionsWorkflow

**Purpose**: CI workflow configuration for automated testing

**Attributes**:
- `workflow_name: str` - Workflow identifier
- `trigger_events: List[str]` - Events that trigger workflow (push, pull_request)
- `python_version: str` - Python version to test against
- `coverage_threshold: float` - Minimum coverage to pass (90%)
- `artifact_retention_days: int` - How long to keep reports (30)
- `parallel_workers: str` - Worker count configuration ("auto")

**Relationships**:
- Executes `TestSuite` on push/PR
- Uploads `CoverageReport` as artifact
- Fails if `TestSuite` fails or coverage < threshold

**Workflow Steps**:
1. Checkout code
2. Setup Python + uv
3. Install dependencies (`uv sync --all-groups`)
4. Run tests with coverage (`uv run pytest -n auto --cov=producthuntdb --cov-fail-under=90`)
5. Upload HTML coverage report (30-day retention)
6. Comment coverage diff on PR

**Validation Rules**:
- Workflow MUST run on all pushes and PRs
- Workflow MUST fail if any tests fail
- Workflow MUST fail if coverage < 90%

---

## Entity Relationships Diagram

```
TestSuite
├── contains → TestModule (many)
│   ├── contains → TestCase (many)
│   │   └── uses → Fixture (many)
│   └── contains → PropertyTest (many)
│       ├── uses → HypothesisStrategy (many)
│       └── generates → HypothesisExample (many, on failure)
├── generates → CoverageReport (one per run)
│   └── contains → ModuleCoverageReport (many)
└── executed_by → GitHubActionsWorkflow (on push/PR)
```

---

## Non-Functional Attributes

### Performance
- Test execution: <5 minutes for full suite
- Coverage overhead: <10% execution time increase
- Parallel workers: Auto-detected (typically CPU cores - 1)

### Scalability
- Supports 500+ tests without degradation
- Handles 2300+ lines of code under test
- Generates 10,000+ Hypothesis examples per run

### Reliability
- Deterministic execution (fixed seeds)
- Reproducible failures (git-tracked Hypothesis database)
- Zero flaky tests (property-based tests expose non-determinism)

### Observability
- Terminal output: Real-time progress + summary
- HTML reports: Line-by-line coverage visualization
- GitHub Actions: Artifact upload + PR comments

---

## Implementation Notes

**No production data model changes** - this feature only affects test infrastructure. All entities are test artifacts (test files, coverage reports, CI configurations) rather than business domain objects.

**Existing fixtures remain** - leverage existing `conftest.py` fixtures (temp_database, mock clients, etc.) and extend where needed.

**Property-based tests supplement, don't replace** - maintain existing example-based tests and add property tests for complex logic.

