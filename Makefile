# Makefile for ProductHuntDB
# Root-level targets for common development tasks

.PHONY: help docs htmllive livehtml docs-build docs-clean test test-cov lint format init

# Default target: show help
help:
	@echo "ProductHuntDB - Makefile Targets"
	@echo ""
	@echo "Documentation:"
	@echo "  make docs          Build documentation"
	@echo "  make htmllive      Start live documentation server with auto-rebuild"
	@echo "  make livehtml      Alias for htmllive"
	@echo "  make docs-clean    Clean documentation build"
	@echo ""
	@echo "Development:"
	@echo "  make init          Initialize database"
	@echo "  make test          Run tests"
	@echo "  make test-cov      Run tests with coverage report"
	@echo "  make lint          Run linters"
	@echo "  make format        Format code"
	@echo ""

# Documentation targets
docs:
	@echo "Building documentation..."
	@cd docs && $(MAKE) html

htmllive:
	@echo "Starting live documentation server..."
	@cd docs && $(MAKE) htmllive

livehtml: htmllive

docs-build: docs

docs-clean:
	@echo "Cleaning documentation..."
	@cd docs && $(MAKE) clean

# Development targets
init:
	@echo "Initializing database..."
	@uv run producthuntdb init

test:
	@echo "Running tests (working subset)..."
	uv run pytest tests/test_api_retry.py tests/test_config.py tests/test_models.py tests/test_logging.py tests/test_database.py tests/test_cli.py -v --tb=short

test-cov:
	@echo "Running full test suite with coverage (target: 90%+)..."
	uv run pytest tests/test_api_retry.py tests/test_config.py tests/test_models.py \
		tests/test_logging.py tests/test_database.py tests/test_cli.py \
		tests/test_utils.py tests/test_types.py tests/test_repository.py \
		tests/test_metrics.py tests/test_simple_coverage.py \
		--cov=producthuntdb \
		--cov-report=term-missing \
		--cov-report=html:logs/htmlcov \
		--cov-report=json:logs/coverage.json \
		--cov-fail-under=90 \
		-v

lint:
	@echo "Running linters..."
	@uv run ruff check producthuntdb/

format:
	@echo "Formatting code..."
	@uv run ruff format producthuntdb/
