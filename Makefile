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
	@echo "Running tests..."
	@uv run pytest --ignore=tests/test_io.py tests/

test-cov:
	@echo "Running tests with coverage..."
	@uv run pytest --ignore=tests/test_io.py tests/ --cov=producthuntdb --cov-report=term --cov-report=html
	@echo "Coverage report generated at logs/htmlcov/index.html"

lint:
	@echo "Running linters..."
	@uv run ruff check producthuntdb/

format:
	@echo "Formatting code..."
	@uv run ruff format producthuntdb/
