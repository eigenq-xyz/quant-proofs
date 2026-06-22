.PHONY: help setup build test lint clean

help:
	@echo "quant-core Makefile"
	@echo ""
	@echo "Targets:"
	@echo "  setup  - Install Lean (elan) + Python (uv) dependencies"
	@echo "  build  - Build Lean proofs + Python package"
	@echo "  test   - Run all Lean + Python tests"
	@echo "  lint   - Ruff lint + mypy typecheck on Python"
	@echo "  clean  - Remove all build artifacts"

setup:
	$(MAKE) -C lean setup
	cd python && uv sync --extra dev

build:
	$(MAKE) -C lean build
	cd python && uv sync

test:
	$(MAKE) -C lean test
	cd python && uv run pytest -q

lint:
	cd python && uv run ruff check src/ tests/
	cd python && uv run mypy src/ --strict

clean:
	$(MAKE) -C lean clean
	cd python && rm -rf .venv __pycache__ src/**/__pycache__
