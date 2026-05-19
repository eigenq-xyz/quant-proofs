.PHONY: help setup test lint typecheck clean

help:
	@echo "quant-core Python Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  setup     - Install dependencies via uv"
	@echo "  test      - Run tests with coverage"
	@echo "  lint      - Run ruff linter"
	@echo "  typecheck - Run mypy strict"
	@echo "  clean     - Remove build artifacts"

setup:
	uv sync --extra dev

test:
	uv run pytest -v --cov=quant_core --cov-report=term-missing

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

typecheck:
	uv run mypy src/ --strict

clean:
	rm -rf .venv __pycache__ src/**/__pycache__ .mypy_cache .ruff_cache
