# Implementation Tasks: Comprehensive Test Coverage with Property-Based Testing

**Feature**: 001-test-coverage-90  
**Branch**: `001-test-coverage-90`  
**Generated**: 2025-11-02  
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Overview

This document provides a complete, dependency-ordered task list for achieving ≥90% test coverage using advanced Hypothesis property-based testing. Tasks are organized by user story priority to enable independent implementation and testing of each increment.

**Current State**: 58.5% coverage, 351 tests passing, 5 failures  
**Target State**: ≥90% coverage, ≥500 tests passing, 0 failures, <5 min execution

## Task Summary

- **Total Tasks**: 45
- **Parallelizable**: 24 tasks marked [P]
- **User Stories**: 4 (P1-P4)
- **Estimated Duration**: 3-5 days for MVP (P1), 5-8 days for complete feature

## Implementation Strategy

**MVP Scope** (Minimum Viable Product):
- **User Story 1 only** (P1): Fix failures + achieve 90% coverage
- Delivers: Zero test failures, ≥90% overall coverage, parallel execution
- Independent test: Run `uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto`
- Can ship to production after P1 completion

**Incremental Delivery**:
- P1 → P2 → P3 → P4 (each story independently testable)
- Each story adds value without blocking the next
- Property tests (P2) enhance but don't replace basic coverage (P1)
- CI enforcement (P3) automates what works locally (P1+P2)
- Documentation (P4) captures established practices (P1+P2+P3)

---

## Phase 1: Setup & Environment

**Goal**: Install dependencies and configure test infrastructure

**Duration**: 30 minutes

### Tasks

- [ ] T001 Install pytest-xdist for parallel test execution via `uv add --group test pytest-xdist`
- [ ] T002 Install hypothesis for property-based testing via `uv add --group test hypothesis`
- [ ] T003 Verify pytest plugins loaded by running `uv run pytest --version` (expect: pytest-cov, pytest-xdist, pytest-asyncio, hypothesis)
- [ ] T004 Create `.hypothesis/` directory in repository root for failure database persistence
- [ ] T005 Verify `.hypothesis/` is NOT in `.gitignore` (should be git-tracked for reproducibility)
- [ ] T006 Run baseline coverage measurement: `uv run pytest --cov=producthuntdb --cov-report=term --cov-report=html:logs/htmlcov -n auto`

**Acceptance Criteria**:
- ✅ All dependencies installed and verified
- ✅ `.hypothesis/` directory exists and is git-tracked
- ✅ Baseline coverage report generated showing ~58.5%
- ✅ No new test failures introduced

---

## Phase 2: Foundational Prerequisites (BLOCKING)

**Goal**: Fix existing failures to establish clean baseline (MUST complete before user stories)

**Duration**: 2-4 hours

**Rationale**: Zero test failures required before adding new tests per clarification decision

### Tasks

- [ ] T007 Investigate 5 failing tests in tests/test_metrics.py by running `uv run pytest tests/test_metrics.py -vv`
- [ ] T008 Identify root cause of Prometheus registry issues (likely: registry not cleared between tests)
- [ ] T009 Implement registry cleanup in tests/conftest.py or test teardown hooks
- [ ] T010 Re-run test_metrics.py until all 5 tests pass: `uv run pytest tests/test_metrics.py -v`
- [ ] T011 Verify full test suite passes with zero failures: `uv run pytest tests/ -n auto`
- [ ] T012 Commit fixes: `git add tests/test_metrics.py tests/conftest.py && git commit -m "Fix test_metrics.py registry cleanup (5 failures → 0)"`

**Acceptance Criteria**:
- ✅ Zero test failures when running `uv run pytest tests/`
- ✅ test_metrics.py shows 43/43 tests passing
- ✅ No regression in other test modules
- ✅ Clean baseline established for coverage work

**Dependencies**: None (blocking for all user stories)

---

## Phase 3: User Story 1 - Developer Validates Code Quality (Priority: P1)

**Story Goal**: Achieve ≥90% test coverage with comprehensive unit/integration tests for 6 critical modules

**Independent Test**: `uv run pytest --cov=producthuntdb --cov-report=term --cov-fail-under=90 -n auto` exits with code 0

**Duration**: 2-3 days

**Module Priority Order** (lowest coverage first per clarification):
1. kaggle.py (0% → 85%)
2. repository.py (0% → 85%)
3. telemetry.py (3.9% → 85%)
4. pipeline.py (10.1% → 85%)
5. io.py (21.7% → 85%)
6. cli.py (50.5% → 85%)

### Sub-Phase 3.1: kaggle.py Coverage (0% → 85%)

- [ ] T013 [P] [US1] Analyze producthuntdb/kaggle.py to identify testable functions and classes
- [ ] T014 [P] [US1] Create/enhance tests/test_kaggle.py with unit tests for KaggleExporter initialization
- [ ] T015 [P] [US1] Add unit tests for CSV export functionality in tests/test_kaggle.py
- [ ] T016 [P] [US1] Add unit tests for dataset metadata generation in tests/test_kaggle.py
- [ ] T017 [P] [US1] Add integration tests for complete export workflow in tests/test_kaggle.py
- [ ] T018 [US1] Run coverage check: `uv run pytest tests/test_kaggle.py --cov=producthuntdb.kaggle --cov-report=term` (target: ≥85%)
- [ ] T019 [US1] Address uncovered lines in kaggle.py by adding targeted tests
- [ ] T020 [US1] Verify kaggle.py reaches 85% coverage, commit: `git commit -m "Add tests for kaggle.py (0% → 85%)"`

### Sub-Phase 3.2: repository.py Coverage (0% → 85%)

- [ ] T021 [P] [US1] Analyze producthuntdb/repository.py to identify Repository[T] pattern methods
- [ ] T022 [P] [US1] Create/enhance tests/test_repository.py fixing collection warning (TestEntity class issue)
- [ ] T023 [P] [US1] Add unit tests for CRUD operations (create, read, update, delete) in tests/test_repository.py
- [ ] T024 [P] [US1] Add unit tests for query helpers (find_by, count, exists, get_or_create) in tests/test_repository.py
- [ ] T025 [P] [US1] Add tests for RepositoryFactory with multiple entity types in tests/test_repository.py
- [ ] T026 [US1] Run coverage check: `uv run pytest tests/test_repository.py --cov=producthuntdb.repository --cov-report=term` (target: ≥85%)
- [ ] T027 [US1] Verify repository.py reaches 85% coverage, commit: `git commit -m "Add tests for repository.py (0% → 85%)"`

### Sub-Phase 3.3: telemetry.py Coverage (3.9% → 85%)

- [ ] T028 [P] [US1] Analyze producthuntdb/telemetry.py to identify OpenTelemetry integration points
- [ ] T029 [P] [US1] Create/enhance tests/test_telemetry_comprehensive.py with TracerProvider initialization tests
- [ ] T030 [P] [US1] Add tests for span operations (attributes, exceptions, status) in tests/test_telemetry_comprehensive.py
- [ ] T031 [P] [US1] Add tests for context synchronization with logging in tests/test_telemetry_comprehensive.py
- [ ] T032 [P] [US1] Add tests for shutdown and cleanup workflows in tests/test_telemetry_comprehensive.py
- [ ] T033 [US1] Run coverage check: `uv run pytest tests/test_telemetry_comprehensive.py --cov=producthuntdb.telemetry --cov-report=term` (target: ≥85%)
- [ ] T034 [US1] Verify telemetry.py reaches 85% coverage, commit: `git commit -m "Add tests for telemetry.py (3.9% → 85%)"`

### Sub-Phase 3.4: pipeline.py Coverage (10.1% → 85%)

- [ ] T035 [P] [US1] Analyze producthuntdb/pipeline.py to identify DataPipeline workflows
- [ ] T036 [P] [US1] Create/enhance tests/test_pipeline_comprehensive.py fixing async cleanup issues
- [ ] T037 [P] [US1] Add tests for sync_posts (full refresh and incremental) in tests/test_pipeline_comprehensive.py
- [ ] T038 [P] [US1] Add tests for sync_topics, sync_collections, sync_all in tests/test_pipeline_comprehensive.py
- [ ] T039 [P] [US1] Add tests for error handling and safety cutoffs in tests/test_pipeline_comprehensive.py
- [ ] T040 [US1] Run coverage check: `uv run pytest tests/test_pipeline_comprehensive.py --cov=producthuntdb.pipeline --cov-report=term` (target: ≥85%)
- [ ] T041 [US1] Verify pipeline.py reaches 85% coverage, commit: `git commit -m "Add tests for pipeline.py (10.1% → 85%)"`

### Sub-Phase 3.5: io.py Coverage (21.7% → 85%)

- [ ] T042 [P] [US1] Analyze producthuntdb/io.py to identify DataSink operations
- [ ] T043 [P] [US1] Create/enhance tests/test_io.py fixing API mismatches
- [ ] T044 [P] [US1] Add tests for batch operations and transaction handling in tests/test_io.py
- [ ] T045 [P] [US1] Add tests for export workflows (CSV, JSON) in tests/test_io.py
- [ ] T046 [P] [US1] Add tests for error conditions (network failures, invalid data) in tests/test_io.py
- [ ] T047 [US1] Run coverage check: `uv run pytest tests/test_io.py --cov=producthuntdb.io --cov-report=term` (target: ≥85%)
- [ ] T048 [US1] Verify io.py reaches 85% coverage, commit: `git commit -m "Add tests for io.py (21.7% → 85%)"`

### Sub-Phase 3.6: cli.py Coverage (50.5% → 85%)

- [ ] T049 [P] [US1] Analyze producthuntdb/cli.py to identify CLI command handlers
- [ ] T050 [P] [US1] Create/enhance tests/test_cli_comprehensive.py fixing mocking issues (16 failures)
- [ ] T051 [P] [US1] Add tests for command execution (init, sync, export, publish, status, verify) in tests/test_cli_comprehensive.py
- [ ] T052 [P] [US1] Add tests for error handling and user feedback in tests/test_cli_comprehensive.py
- [ ] T053 [P] [US1] Add tests for helper functions (setup_logging, run_async) in tests/test_cli_comprehensive.py
- [ ] T054 [US1] Run coverage check: `uv run pytest tests/test_cli_comprehensive.py --cov=producthuntdb.cli --cov-report=term` (target: ≥85%)
- [ ] T055 [US1] Verify cli.py reaches 85% coverage, commit: `git commit -m "Add tests for cli.py (50.5% → 85%)"`

### Sub-Phase 3.7: Parallel Execution Configuration

- [ ] T056 [US1] Configure pytest to use parallel execution by default in pyproject.toml (addopts = "-n auto")
- [ ] T057 [US1] Test parallel execution with full suite: `uv run pytest tests/ -n auto` (verify: uses multiple workers, <5 min)
- [ ] T058 [US1] Verify test isolation (no shared state issues, no database lock errors)
- [ ] T059 [US1] Commit parallel execution config: `git commit -m "Configure pytest parallel execution (-n auto)"`

### Sub-Phase 3.8: Coverage Validation

- [ ] T060 [US1] Run final coverage check: `uv run pytest --cov=producthuntdb --cov-report=html:logs/htmlcov --cov-report=term --cov-fail-under=90 -n auto`
- [ ] T061 [US1] Verify overall coverage ≥90% and all critical modules ≥85%
- [ ] T062 [US1] Review HTML coverage report (logs/htmlcov/index.html) for any remaining gaps
- [ ] T063 [US1] Verify test count ≥500 and zero skipped tests
- [ ] T064 [US1] Verify execution time <5 minutes with parallel execution
- [ ] T065 [US1] Commit final coverage milestone: `git commit -m "Achieve 90% test coverage (58.5% → 90%+)"`

**User Story 1 Acceptance Criteria**:
- ✅ Overall line coverage ≥90%
- ✅ All 6 critical modules ≥85% coverage
- ✅ Test suite ≥500 tests, 0 failures, 0 skipped
- ✅ Execution time <5 minutes with parallel execution
- ✅ HTML coverage report generated with line-by-line visualization
- ✅ Independent test passes: `uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto` exits 0

**Dependencies**: Phase 2 (foundational fixes) MUST be complete

---

## Phase 4: User Story 2 - Developer Writes Property-Based Tests (Priority: P2)

**Story Goal**: Implement Hypothesis property-based tests with custom strategies and tiered example counts

**Independent Test**: `uv run pytest -m hypothesis --hypothesis-show-statistics` shows ≥10 property tests generating 100-1000 examples each

**Duration**: 1-2 days

**Depends On**: User Story 1 (basic coverage established)

### Sub-Phase 4.1: Hypothesis Configuration

- [ ] T066 [US2] Configure Hypothesis settings in tests/conftest.py with tiered profiles (critical=1000, complex=500, standard=200, simple=100)
- [ ] T067 [US2] Set up CI detection in tests/conftest.py to use higher example counts in GitHub Actions
- [ ] T068 [US2] Configure Hypothesis database location (default: `.hypothesis/` in repo root)
- [ ] T069 [US2] Add pytest marker for hypothesis tests in pyproject.toml: `markers = ["hypothesis: Property-based tests using Hypothesis"]`
- [ ] T070 [US2] Commit Hypothesis configuration: `git commit -m "Configure Hypothesis with tiered example counts"`

### Sub-Phase 4.2: Custom Hypothesis Strategies

- [ ] T071 [P] [US2] Create custom strategy for PostRow in tests/conftest.py using st.builds()
- [ ] T072 [P] [US2] Create custom strategy for UserRow in tests/conftest.py with business rule constraints
- [ ] T073 [P] [US2] Create custom strategy for CollectionRow in tests/conftest.py
- [ ] T074 [P] [US2] Create custom strategy for TopicRow in tests/conftest.py
- [ ] T075 [P] [US2] Create custom strategy for GraphQL API responses in tests/conftest.py
- [ ] T076 [P] [US2] Create custom strategy for configuration objects (Config class) in tests/conftest.py
- [ ] T077 [P] [US2] Create composite strategies for complex scenarios (post with votes, comments) in tests/conftest.py
- [ ] T078 [US2] Verify ≥10 custom strategies created and documented
- [ ] T079 [US2] Commit custom strategies: `git commit -m "Add 10+ custom Hypothesis strategies for domain types"`

### Sub-Phase 4.3: Property-Based Tests - Models

- [ ] T080 [P] [US2] Add property test for PostRow serialization roundtrip in tests/test_models.py (@given, critical=1000 examples)
- [ ] T081 [P] [US2] Add property test for UserRow validation accepts all valid data in tests/test_models.py
- [ ] T082 [P] [US2] Add property test for datetime handling across all models in tests/test_models.py
- [ ] T083 [P] [US2] Add property test for ID normalization functions in tests/test_models.py
- [ ] T084 [US2] Run property tests: `uv run pytest tests/test_models.py -m hypothesis --hypothesis-show-statistics`

### Sub-Phase 4.4: Property-Based Tests - Utils & Transformations

- [ ] T085 [P] [US2] Add property test for GraphQL query builder in tests/test_utils.py (standard=200 examples)
- [ ] T086 [P] [US2] Add property test for token redaction function in tests/test_utils.py
- [ ] T087 [P] [US2] Add property test for list operations (chunking, deduplication) in tests/test_utils.py
- [ ] T088 [US2] Run property tests: `uv run pytest tests/test_utils.py -m hypothesis --hypothesis-show-statistics`

### Sub-Phase 4.5: Property-Based Tests - Data Integrity

- [ ] T089 [P] [US2] Add property test for database persistence roundtrip in tests/test_database.py (critical=1000 examples)
- [ ] T090 [P] [US2] Add property test for batch insert operations preserve all data in tests/test_database.py
- [ ] T091 [P] [US2] Add property test for query results consistency in tests/test_database.py
- [ ] T092 [US2] Run property tests: `uv run pytest tests/test_database.py -m hypothesis --hypothesis-show-statistics`

### Sub-Phase 4.6: Property-Based Tests - API & Validation

- [ ] T093 [P] [US2] Add property test for API response parsing in tests/test_api_retry.py (complex=500 examples)
- [ ] T094 [P] [US2] Add property test for configuration validation in tests/test_config.py
- [ ] T095 [US2] Run property tests: `uv run pytest -m hypothesis --hypothesis-show-statistics`

### Sub-Phase 4.7: Hypothesis Failure Handling

- [ ] T096 [US2] Simulate Hypothesis failure by adding intentionally failing property test
- [ ] T097 [US2] Verify Hypothesis shrinks to minimal failing example
- [ ] T098 [US2] Verify failure persisted to `.hypothesis/examples/` directory
- [ ] T099 [US2] Fix the intentional failure and verify example archived
- [ ] T100 [US2] Commit `.hypothesis/` directory changes: `git add .hypothesis/ && git commit -m "Add Hypothesis failure database"`

### Sub-Phase 4.8: Property-Based Test Validation

- [ ] T101 [US2] Run all property tests with statistics: `uv run pytest -m hypothesis --hypothesis-show-statistics -v`
- [ ] T102 [US2] Verify ≥20 property-based tests exist across modules
- [ ] T103 [US2] Verify tiered example counts applied correctly (check statistics output)
- [ ] T104 [US2] Verify test execution time remains <5 minutes with property tests included
- [ ] T105 [US2] Commit property-based test milestone: `git commit -m "Add 20+ property-based tests with Hypothesis"`

**User Story 2 Acceptance Criteria**:
- ✅ ≥10 custom Hypothesis strategies for domain types
- ✅ ≥20 property-based tests across modules
- ✅ Tiered example counts applied (critical=1000, complex=500, standard=200, simple=100)
- ✅ Hypothesis database (`.hypothesis/`) git-tracked
- ✅ Property tests discover edge cases (verify with --hypothesis-show-statistics)
- ✅ Independent test passes: `uv run pytest -m hypothesis --hypothesis-show-statistics` shows all passing

**Dependencies**: User Story 1 (basic coverage) MUST be complete

---

## Phase 5: User Story 3 - GitHub Actions Enforces Quality Gates (Priority: P3)

**Story Goal**: Configure GitHub Actions workflow to enforce 90% coverage threshold and fail on test failures

**Independent Test**: Push commit to GitHub and verify workflow runs, passes/fails appropriately

**Duration**: 4-6 hours

**Depends On**: User Story 1 + User Story 2 (tests working locally)

### Sub-Phase 5.1: GitHub Actions Workflow Creation

- [ ] T106 [US3] Create .github/workflows/ directory if it doesn't exist
- [ ] T107 [US3] Create .github/workflows/test-coverage.yml workflow file
- [ ] T108 [US3] Configure workflow triggers (on: [push, pull_request]) in test-coverage.yml
- [ ] T109 [US3] Add Python setup step with uv installation in test-coverage.yml
- [ ] T110 [US3] Add dependency installation step (`uv sync --all-groups`) in test-coverage.yml
- [ ] T111 [US3] Commit initial workflow: `git commit -m "Create GitHub Actions test coverage workflow"`

### Sub-Phase 5.2: Test Execution Configuration

- [ ] T112 [US3] Add test execution step with coverage and parallel execution in test-coverage.yml: `uv run pytest tests/ --cov=producthuntdb --cov-report=html:logs/htmlcov --cov-report=json:logs/coverage.json --cov-fail-under=90 -n auto --junitxml=logs/junit.xml`
- [ ] T113 [US3] Configure workflow to fail if pytest exits with non-zero code
- [ ] T114 [US3] Add test result reporting step using junit.xml
- [ ] T115 [US3] Commit test execution config: `git commit -m "Configure test execution in GitHub Actions"`

### Sub-Phase 5.3: Coverage Report Artifacts

- [ ] T116 [US3] Add artifact upload step for HTML coverage report in test-coverage.yml using actions/upload-artifact@v4
- [ ] T117 [US3] Configure 30-day retention for coverage artifacts
- [ ] T118 [US3] Ensure artifacts uploaded even if tests fail (if: always())
- [ ] T119 [US3] Commit artifact configuration: `git commit -m "Configure coverage artifact upload (30-day retention)"`

### Sub-Phase 5.4: Coverage Diff PR Comments

- [ ] T120 [US3] Add PR comment step using orgoro/coverage@v3 or similar action
- [ ] T121 [US3] Configure coverage diff to show impact on overall coverage
- [ ] T122 [US3] Ensure PR comments only on pull_request events
- [ ] T123 [US3] Commit PR comment config: `git commit -m "Add coverage diff PR comments"`

### Sub-Phase 5.5: Workflow Validation

- [ ] T124 [US3] Push workflow to GitHub: `git push origin 001-test-coverage-90`
- [ ] T125 [US3] Verify workflow appears in GitHub Actions tab
- [ ] T126 [US3] Trigger workflow run by pushing trivial commit
- [ ] T127 [US3] Verify workflow passes with green status (coverage ≥90%, all tests pass)
- [ ] T128 [US3] Test failure scenario: temporarily lower coverage threshold to 95% and verify workflow fails
- [ ] T129 [US3] Test artifact upload: download coverage report from workflow run and verify it opens correctly
- [ ] T130 [US3] Restore correct threshold (90%) and push: `git commit -m "Verify GitHub Actions workflow enforcement"`

**User Story 3 Acceptance Criteria**:
- ✅ GitHub Actions workflow runs on all pushes and PRs
- ✅ Workflow fails if any tests fail
- ✅ Workflow fails if coverage < 90%
- ✅ HTML coverage reports uploaded with 30-day retention
- ✅ PR comments show coverage diff
- ✅ Independent test passes: Push commit and verify workflow succeeds with green status

**Dependencies**: User Story 1 + User Story 2 (tests passing locally)

---

## Phase 6: User Story 4 - Team Maintains High Quality Over Time (Priority: P4)

**Story Goal**: Create comprehensive testing documentation for contributors and maintainers

**Independent Test**: New contributor can run tests, interpret coverage, and write property tests using only the documentation

**Duration**: 4-6 hours

**Depends On**: User Story 1 + User Story 2 + User Story 3 (everything working)

### Sub-Phase 6.1: README.md Updates

- [ ] T131 [US4] Add "Testing" section to README.md with quick start commands
- [ ] T132 [US4] Document how to run tests: `uv run pytest tests/`
- [ ] T133 [US4] Document how to check coverage: `uv run pytest --cov=producthuntdb --cov-report=html:logs/htmlcov -n auto`
- [ ] T134 [US4] Document how to run property tests: `uv run pytest -m hypothesis --hypothesis-show-statistics`
- [ ] T135 [US4] Add link to comprehensive TESTING.md guide
- [ ] T136 [US4] Commit README updates: `git commit -m "Update README.md with testing quick start"`

### Sub-Phase 6.2: tests/AGENTS.md Updates

- [ ] T137 [US4] Expand tests/AGENTS.md with test execution instructions for AI agents
- [ ] T138 [US4] Document coverage measurement workflow in tests/AGENTS.md
- [ ] T139 [US4] Document property-based testing approach in tests/AGENTS.md
- [ ] T140 [US4] Document common test fixtures and mocking patterns in tests/AGENTS.md
- [ ] T141 [US4] Add troubleshooting section for test failures in tests/AGENTS.md
- [ ] T142 [US4] Commit AGENTS.md updates: `git commit -m "Expand tests/AGENTS.md with comprehensive test instructions"`

### Sub-Phase 6.3: Dedicated Testing Guide (TESTING.md)

- [ ] T143 [US4] Create docs/TESTING.md as comprehensive testing reference
- [ ] T144 [US4] Document test structure (unit, integration, property-based) in TESTING.md
- [ ] T145 [US4] Document pytest markers and when to use each in TESTING.md
- [ ] T146 [US4] Document Hypothesis strategies and tiered example counts in TESTING.md
- [ ] T147 [US4] Document coverage interpretation (reading HTML reports, identifying gaps) in TESTING.md
- [ ] T148 [US4] Document parallel execution and performance considerations in TESTING.md
- [ ] T149 [US4] Document GitHub Actions workflow and CI/CD integration in TESTING.md
- [ ] T150 [US4] Add examples of writing effective tests (unit, integration, property) in TESTING.md
- [ ] T151 [US4] Add troubleshooting guide (common errors, debugging strategies) in TESTING.md
- [ ] T152 [US4] Add contribution workflow (run tests before commit, fix failures first) in TESTING.md
- [ ] T153 [US4] Commit TESTING.md: `git commit -m "Create comprehensive TESTING.md guide"`

### Sub-Phase 6.4: Documentation Synchronization

- [ ] T154 [US4] Review all three documentation sources (README, tests/AGENTS.md, TESTING.md) for consistency
- [ ] T155 [US4] Ensure command examples are identical across all docs
- [ ] T156 [US4] Ensure coverage thresholds (90%, 85%) documented consistently
- [ ] T157 [US4] Add cross-references between docs (README → TESTING.md, AGENTS.md → TESTING.md)
- [ ] T158 [US4] Commit documentation synchronization: `git commit -m "Synchronize testing documentation across README, AGENTS.md, TESTING.md"`

### Sub-Phase 6.5: Documentation Validation

- [ ] T159 [US4] Verify README testing section is concise (<50 lines) and links to TESTING.md
- [ ] T160 [US4] Verify tests/AGENTS.md has agent-specific context and links to TESTING.md
- [ ] T161 [US4] Verify TESTING.md is comprehensive (>200 lines) with examples and troubleshooting
- [ ] T162 [US4] Test documentation with fresh clone: follow quick start guide end-to-end
- [ ] T163 [US4] Commit documentation validation: `git commit -m "Validate testing documentation completeness"`

**User Story 4 Acceptance Criteria**:
- ✅ README.md has concise testing quick start (<50 lines)
- ✅ tests/AGENTS.md expanded with test execution and coverage workflows
- ✅ TESTING.md created as comprehensive guide (>200 lines)
- ✅ All three docs synchronized (consistent commands, thresholds)
- ✅ Cross-references exist between docs
- ✅ Independent test passes: New contributor can run tests and interpret coverage using only docs

**Dependencies**: User Story 1 + User Story 2 + User Story 3 (everything implemented and working)

---

## Phase 7: Polish & Cross-Cutting Concerns

**Goal**: Final validation, optimization, and cleanup

**Duration**: 2-4 hours

### Tasks

- [ ] T164 Verify overall test coverage ≥90% with `uv run pytest --cov=producthuntdb --cov-report=term --cov-fail-under=90 -n auto`
- [ ] T165 Verify test suite execution time <5 minutes with parallel execution
- [ ] T166 Verify zero test failures and zero skipped tests
- [ ] T167 Verify GitHub Actions workflow passes on latest commit
- [ ] T168 Review HTML coverage report for any remaining critical gaps
- [ ] T169 Run linter and type checker: `make lint && uv run mypy producthuntdb/`
- [ ] T170 Update AGENTS.md with final coverage metrics (58.5% → 90%+)
- [ ] T171 Update CHANGELOG.md with test coverage feature summary
- [ ] T172 Create PR description summarizing: coverage improvement, property tests added, CI configured, docs created
- [ ] T173 Request code review focusing on test quality and documentation
- [ ] T174 Address review feedback and iterate
- [ ] T175 Final commit: `git commit -m "Complete test coverage feature (90%+ coverage, 500+ tests, Hypothesis, CI)"`

**Acceptance Criteria**:
- ✅ All user stories (P1-P4) complete and independently tested
- ✅ Overall coverage ≥90%, all critical modules ≥85%
- ✅ ≥500 tests passing, 0 failures, 0 skipped
- ✅ Execution time <5 minutes
- ✅ GitHub Actions enforcing thresholds
- ✅ Documentation complete and synchronized
- ✅ Code review approved
- ✅ Ready for merge to main

---

## Dependency Graph

```
Phase 1 (Setup)
    ↓
Phase 2 (Foundational - BLOCKING)
    ↓
    ├─→ Phase 3 (User Story 1 - P1) ← MVP SCOPE
    │      ↓
    │   Phase 4 (User Story 2 - P2)
    │      ↓
    │      ├─→ Phase 5 (User Story 3 - P3)
    │      └─→ Phase 6 (User Story 4 - P4)
    │             ↓
    └──────────→ Phase 7 (Polish)
```

**Critical Path**: Setup → Foundational → US1 (P1)  
**Parallelizable After US1**: US2 (P2) can start immediately after US1  
**Parallelizable After US2**: US3 (P3) and US4 (P4) can run in parallel after US2

**Incremental Delivery Points**:
1. **After Phase 3 (US1)**: MVP ready - 90% coverage, 500+ tests, parallel execution
2. **After Phase 4 (US2)**: Enhanced - Property-based tests discovering edge cases
3. **After Phase 5 (US3)**: Automated - CI enforcement preventing regressions
4. **After Phase 6 (US4)**: Sustainable - Documentation enabling team maintenance

---

## Parallel Execution Opportunities

### Phase 3 (User Story 1) - Module Coverage

**Modules can be tackled in parallel** once foundational phase is complete:

```bash
# Developer A: kaggle.py + repository.py (Tasks T013-T027)
uv run pytest tests/test_kaggle.py tests/test_repository.py --cov=producthuntdb.kaggle --cov=producthuntdb.repository

# Developer B: telemetry.py + pipeline.py (Tasks T028-T041)
uv run pytest tests/test_telemetry_comprehensive.py tests/test_pipeline_comprehensive.py --cov=producthuntdb.telemetry --cov=producthuntdb.pipeline

# Developer C: io.py + cli.py (Tasks T042-T055)
uv run pytest tests/test_io.py tests/test_cli_comprehensive.py --cov=producthuntdb.io --cov=producthuntdb.cli
```

**Coordination**: Merge frequently to avoid conflicts in conftest.py fixtures

### Phase 4 (User Story 2) - Property-Based Tests

**Custom strategies can be created in parallel** (Tasks T071-T079):

```bash
# Developer A: Model strategies (PostRow, UserRow, CollectionRow)
# Developer B: API strategies (GraphQL responses, Config objects)
# Developer C: Composite strategies (complex scenarios)
```

**Property tests can be added in parallel** across modules (Tasks T080-T095):

```bash
# Developer A: test_models.py property tests
# Developer B: test_utils.py + test_database.py property tests
# Developer C: test_api_retry.py + test_config.py property tests
```

### Phase 6 (User Story 4) - Documentation

**All three documentation files can be updated in parallel** (Tasks T131-T153):

```bash
# Developer A: README.md updates (Tasks T131-T136)
# Developer B: tests/AGENTS.md updates (Tasks T137-T142)
# Developer C: TESTING.md creation (Tasks T143-T153)
```

**Coordination**: Synchronization pass (Tasks T154-T158) after parallel updates complete

---

## Success Metrics

### Coverage Metrics
- ✅ Overall line coverage: 58.5% → ≥90%
- ✅ Overall branch coverage: ≥85%
- ✅ Critical modules: All 6 reach ≥85%
- ✅ Test count: 351 → ≥500
- ✅ Test failures: 5 → 0
- ✅ Skipped tests: 0

### Performance Metrics
- ✅ Test execution time: <5 minutes (with parallel execution)
- ✅ Coverage measurement overhead: <10%
- ✅ Parallel workers: Auto-detected (typically CPU cores - 1)

### Quality Metrics
- ✅ Property-based tests: ≥20 tests with ≥10 custom strategies
- ✅ GitHub Actions: Workflow passes on green builds
- ✅ Documentation: 3 files synchronized (README, AGENTS.md, TESTING.md)
- ✅ Hypothesis database: Git-tracked, reproducible failures

### Validation Commands

```bash
# Overall coverage
uv run pytest --cov=producthuntdb --cov-report=term --cov-fail-under=90 -n auto

# Property tests
uv run pytest -m hypothesis --hypothesis-show-statistics

# Execution time
time uv run pytest tests/ -n auto  # Should be <5 minutes

# CI simulation
uv sync --all-groups && uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto
```

---

## Notes

- **MVP Scope**: Phase 3 (User Story 1) delivers 90% coverage - can ship after this phase
- **Tests Are Implementation**: This feature implements test infrastructure, not production code
- **Parallel Opportunities**: 24 tasks marked [P] can run concurrently with proper coordination
- **Independent Stories**: Each user story (P1-P4) can be tested independently per acceptance criteria
- **Documentation**: Created after implementation (P4) to capture actual practices vs planned
- **Hypothesis Database**: `.hypothesis/` directory must be committed for team reproducibility
- **GitHub Actions**: Requires GitHub repository with Actions enabled

---

## Quick Start

**For immediate development**:

1. **Start with MVP (User Story 1)**:
   ```bash
   # Phase 1: Setup (T001-T006)
   uv add --group test pytest-xdist hypothesis
   mkdir .hypothesis
   
   # Phase 2: Fix failures (T007-T012)
   uv run pytest tests/test_metrics.py -vv
   # ... fix registry issues ...
   
   # Phase 3: Add coverage (T013-T065)
   # Start with kaggle.py (lowest coverage first)
   uv run pytest tests/test_kaggle.py --cov=producthuntdb.kaggle --cov-report=term
   ```

2. **Validate MVP Complete**:
   ```bash
   uv run pytest --cov=producthuntdb --cov-fail-under=90 -n auto
   # Exit code 0 = MVP success, can ship!
   ```

3. **Add Property Tests (User Story 2)**:
   ```bash
   # Phase 4: Hypothesis (T066-T105)
   # Configure in conftest.py, create strategies, add property tests
   uv run pytest -m hypothesis --hypothesis-show-statistics
   ```

4. **Enable CI (User Story 3)**:
   ```bash
   # Phase 5: GitHub Actions (T106-T130)
   # Create .github/workflows/test-coverage.yml
   git push origin 001-test-coverage-90
   # Verify workflow runs and passes
   ```

5. **Document (User Story 4)**:
   ```bash
   # Phase 6: Documentation (T131-T163)
   # Update README, tests/AGENTS.md, create TESTING.md
   ```

**See**: [quickstart.md](./quickstart.md) for detailed development workflow

