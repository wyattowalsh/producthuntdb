# Research: Test Coverage Implementation

**Feature**: 001-test-coverage-90  
**Date**: 2025-11-02  
**Status**: Phase 0 Complete

## Research Tasks

### 1. Parallel Test Execution Strategy

**Decision**: Use `pytest-xdist` with auto-detected worker count

**Rationale**:
- Industry standard for Python test parallelization
- Auto-detection (`pytest -n auto`) adapts to environment (local vs CI)
- Typically uses `CPU cores - 1` to avoid resource exhaustion
- Minimal configuration overhead
- Already compatible with pytest-cov for coverage collection
- Handles test isolation automatically (each worker gets own database fixture)

**Alternatives Considered**:
- **pytest-parallel**: Less mature, limited coverage support
- **unittest parallel**: Requires migration from pytest
- **Manual multiprocessing**: Complex, error-prone, reinvents wheel
- **Sequential only**: Would exceed 5-minute constraint with 500+ tests

**Implementation**: Add `pytest-xdist` to test dependencies, use `-n auto` flag

---

### 2. Hypothesis Integration Best Practices

**Decision**: Tiered example counts + custom strategies + git-tracked database

**Rationale**:
- **Tiered counts**: Balances thoroughness with execution time
  - Critical (security, data integrity): 1000 examples
  - Complex (multi-step transformations): 500 examples
  - Standard (validation, formatting): 200 examples
  - Simple (getters, setters): 100 examples
- **Custom strategies**: Domain-specific generators ensure valid test data
  - `st.builds()` for Pydantic models
  - Composite strategies for GraphQL responses
  - Constrained strategies for business rules
- **Git-tracked database**: `.hypothesis/examples/` persists failures
  - Team-wide reproducibility
  - CI gets same failing examples
  - Hypothesis recommended practice for teams

**Alternatives Considered**:
- **Fixed 100 examples**: Too shallow for critical functions
- **Fixed 1000 examples**: Would exceed 5-minute execution time
- **No custom strategies**: Generates invalid data, wastes time
- **Local-only database**: Failures not reproducible across team

**Implementation**: Configure Hypothesis in `conftest.py`, commit `.hypothesis/` directory

---

### 3. Coverage Report Artifact Storage

**Decision**: GitHub Actions artifacts with 30-day retention

**Rationale**:
- **30 days**: GitHub Actions default, sufficient for PR review cycles
- Balances storage costs with practical needs (monthly trend analysis)
- Automatic cleanup prevents unbounded growth
- HTML reports viewable directly from Actions UI
- JSON reports available for programmatic analysis
- Coverage diffs available for PR comparisons

**Alternatives Considered**:
- **7 days**: Too short for long-running PRs or quarterly reviews
- **90 days**: Higher storage costs with marginal benefit
- **Indefinite**: Expensive, unnecessary for most use cases
- **External service** (Codecov): Adds dependency, requires account

**Implementation**: Use `actions/upload-artifact@v4` with `retention-days: 30`

---

### 4. Module Priority Ordering Strategy

**Decision**: Lowest coverage first (kaggle.py → repository.py → telemetry.py → pipeline.py → io.py → cli.py)

**Rationale**:
- **Maximizes rapid progress**: 0%→85% shows dramatic gains
- **Psychological momentum**: Quick wins motivate continued work
- **Risk reduction**: Identifies integration issues early
- **Simpler modules first**: kaggle.py (76 lines) easier than cli.py (405 lines)
- **Dependency order**: Core modules (repository, models) before consumers

**Alternatives Considered**:
- **By importance**: Subjective, harder to measure progress
- **By complexity**: Would tackle hardest (cli.py) first, slower progress
- **By dependency order**: Less visible progress in early phases

**Implementation**: Phase coverage work in 6 sub-tasks, lowest coverage first

---

### 5. Documentation Structure

**Decision**: README (quick start) + tests/AGENTS.md (agent instructions) + TESTING.md (comprehensive guide)

**Rationale**:
- **Three-tier approach** serves different audiences:
  - README: New users, quick start, high-level overview
  - tests/AGENTS.md: AI agents, automation context, test execution
  - TESTING.md: Contributors, deep dive, best practices, troubleshooting
- **Existing structure**: tests/AGENTS.md already exists, maintain consistency
- **Single source**: TESTING.md is canonical, README/AGENTS.md link to it
- **Discoverability**: README in repo root, TESTING.md in docs/, AGENTS.md in tests/

**Alternatives Considered**:
- **README only**: Would become too long, overwhelming for quick start
- **CONTRIBUTING.md only**: Buries testing info in broader guide
- **Sphinx docs only**: Less discoverable, requires doc build to view

**Implementation**: Update README testing section, expand tests/AGENTS.md, create TESTING.md

---

### 6. Test Failure Resolution Approach

**Decision**: Fix all 5 existing failures in test_metrics.py before adding new tests

**Rationale**:
- **Clean baseline**: Zero failures = clear signal for new issues
- **Prevents confusion**: Can't distinguish old vs new failures
- **Risk reduction**: Existing failures may indicate deeper issues
- **Quick win**: 5 failures likely quick to fix (registry issues per AGENTS.md)
- **Blocks PR**: Can't merge with failing tests anyway

**Alternatives Considered**:
- **Parallel approach**: Risk of conflict, coordination overhead
- **Fix after coverage**: Would ship with known failures
- **Fix only if blocking**: Technical debt accumulation

**Implementation**: Task 1 in execution plan: Fix test_metrics.py failures (blocking)

---

### 7. Hypothesis Failure Database Location

**Decision**: Git-tracked `.hypothesis/` directory in repository root

**Rationale**:
- **Hypothesis default location**: `.hypothesis/examples/`
- **Version control**: Git tracks failing examples for reproducibility
- **Team-wide sharing**: All developers get same failure database
- **CI consistency**: GitHub Actions sees same examples
- **No configuration**: Default Hypothesis behavior, zero setup

**Alternatives Considered**:
- **Gitignored**: Failures not reproducible across team
- **CI-only artifacts**: Local developers miss failures
- **External storage**: Added complexity, network dependency

**Implementation**: Add `.hypothesis/` directory, ensure it's NOT in `.gitignore`

---

### 8. Coverage Threshold Enforcement Strategy

**Decision**: Fail GitHub Actions workflow if coverage < 90% or any tests fail

**Rationale**:
- **pytest-cov flags**: `--cov-fail-under=90` for hard threshold
- **Immediate feedback**: PR checks show red status on violations
- **Prevent degradation**: Can't merge code that lowers coverage
- **Clear error messages**: pytest-cov shows which modules need coverage

**Alternatives Considered**:
- **Warning only**: No enforcement, coverage drifts down
- **Per-module thresholds**: Complex configuration, harder to maintain
- **Manual review**: Human error, inconsistent enforcement

**Implementation**: Add `--cov-fail-under=90` to pytest command in GitHub Actions

---

## Technology Stack Summary

| Component | Choice | Version |
|-----------|--------|---------|
| Test Runner | pytest | Latest (via uv) |
| Coverage | pytest-cov (coverage.py) | Latest (via uv) |
| Parallelization | pytest-xdist | Latest (via uv) |
| Property Testing | hypothesis | Latest (via uv) |
| Async Testing | pytest-asyncio | Latest (via uv, already present) |
| CI Platform | GitHub Actions | N/A (SaaS) |
| Package Manager | uv | Current version (per AGENTS.md) |

**All dependencies installable via**: `uv add --group test pytest-xdist hypothesis`

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Tests exceed 5-minute limit | Medium | High | Parallel execution (-n auto), tiered Hypothesis examples |
| Hypothesis generates too much data | Low | Medium | Configure max_examples per tier, use targeted strategies |
| Coverage overhead slows tests | Low | Low | Disable coverage locally, enable only in CI |
| Failing tests block development | Medium | Medium | Fix existing 5 failures first, maintain clean baseline |
| Documentation becomes out of sync | Medium | Low | Single source (TESTING.md), README/AGENTS.md link to it |
| Git repository bloat from .hypothesis/ | Low | Low | Hypothesis database is small (<1MB typical) |

---

## Dependencies to Add

```toml
[project.optional-dependencies]
test = [
    "pytest>=8.0",
    "pytest-cov>=4.1",
    "pytest-asyncio>=0.23",  # Already present
    "pytest-xdist>=3.5",     # NEW: Parallel execution
    "hypothesis>=6.92",      # NEW: Property-based testing
]
```

**Installation command**: `uv add --group test pytest-xdist hypothesis`

---

## Open Questions

**None remaining** - all technical unknowns resolved through research.

---

## Next Steps

**Phase 1: Design & Contracts**
1. Generate data-model.md (test entities and relationships)
2. Create contracts/ directory (test API contracts, if applicable)
3. Write quickstart.md (developer quick start guide)
4. Update agent context (cursor-agent specific additions)

