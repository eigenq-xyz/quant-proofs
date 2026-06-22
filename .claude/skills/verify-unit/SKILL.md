---
name: verify-unit
description: >
  Level 2 verification: Python unit tests, mypy strict, and ruff for backtest-proofs
  and mortgage-proofs. Runs after verify-lean passes. Use when any .py or .pyx
  file changes, or as step 2 of /verify.
paths:
  - "**/*.py"
  - "**/*.pyx"
  - "**/pyproject.toml"
allowed-tools: Bash(uv run *) Bash(uv sync *)
---

# Verify Unit — Level 2

## Commands

### backtest-proofs/python

```bash
cd backtest-proofs/python

# If Lean changed since last run, rebuild the Cython FFI extension first
uv run python setup_ffi.py build_ext --inplace

uv sync --extra dev
uv run pytest -q --cov=src --cov-report=term-missing
uv run mypy src/ --strict
uv run ruff check src/ tests/
```

### mortgage-proofs

```bash
cd extensions/mortgage-proofs
uv sync --all-extras
uv run pytest -m "not integration" -q --cov=src --cov-report=term-missing
uv run mypy src/ --strict
uv run ruff check src/ tests/
```

## Coverage requirement

New code: ≥ 80% coverage. Check with `--cov-report=term-missing` to see uncovered lines.

## Model consistency

The most important unit tests are those that verify Python matches the Lean model
on synthetic inputs — e.g., `test_ffi.py::test_portfolio_value_via_lean_ffi`.
If these fail, the formal guarantee is broken even if the Lean proof passes.

## Common failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ImportError: lean_ffi.so` | Cython extension not rebuilt | `uv run python setup_ffi.py build_ext --inplace` |
| `mypy: error: Function is missing a return type` | Missing annotation | Add return type annotation |
| `error: Argument 1 has incompatible type "float"` | Float where int expected | Use `to_bp()` before passing to FFI |
| `ruff: B006` | Mutable default argument | Use `None` default + guard inside |

## Passes when

Both packages: pytest exits 0, mypy exits 0, ruff exits 0.
