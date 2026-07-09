---
name: verify-unit
description: >
  Level 2 verification: Python unit tests, mypy strict, and ruff for research-pipeline,
  foundations/quant-core, foundations/portfolio-proofs, and extensions/mortgage-proofs —
  the subdirs with a Python test suite. Runs after verify-lean passes. Use when any .py or
  .pyx file changes, or as step 2 of /verify.
paths:
  - "**/*.py"
  - "**/*.pyx"
  - "**/pyproject.toml"
allowed-tools: Bash(uv run *) Bash(uv sync *)
---

# Verify Unit — Level 2

## Commands

### research-pipeline

```bash
cd research-pipeline
pip install -e ".[dev]"
pytest -q
mypy --strict src/
ruff check .
```

### foundations/quant-core/python

```bash
cd foundations/quant-core/python
uv run pytest -q
```

### foundations/portfolio-proofs (Cython FFI extension — rebuild after any Lean change)

```bash
cd foundations/portfolio-proofs
uv sync --extra dev

# If optimization-proofs' Lean source changed since last run, rebuild the Cython FFI
# extension and the pgd_solve binary first
(cd ../optimization-proofs && python ffi/setup_ffi.py build_ext --inplace && lake build pgd_solve)

uv run pytest tests/test_lean_pgd.py -v -k "not integration"   # no binary required
uv run pytest tests/ -v                                         # full suite, needs pgd_solve
uv run mypy lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/ --strict
uv run ruff check lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/
```

### extensions/mortgage-proofs

```bash
cd extensions/mortgage-proofs
uv sync --all-extras
uv run pytest -m "not integration" -q --cov=src --cov-report=term-missing
uv run mypy src/ --strict
uv run ruff check src/ tests/
```

Note: `extensions/hedge-proofs` has no Python package or test suite yet (Lean-only; see
`/verify-lean`). Its `@[export hedge_*]` FFI surface in `BacktestProofs/Accounting.lean` has
no Python bindings today.

### Trace verification (mortgage-proofs only)

The mortgage pipeline emits `DecisionRecord` JSON traces. Validate each against the Lean
invariants (e.g., `compliance_before_underwriter`, `risk_score_nonneg`):

```bash
cd extensions/mortgage-proofs
lake exe verify-trace traces/latest.json          # single trace
for f in traces/*.json; do lake exe verify-trace "$f" || echo "FAILED: $f"; done  # all traces
```

Exit 0 required. A failure means a `DecisionRecord` violates an invariant.

## Coverage requirement

New code: ≥ 80% coverage. `--cov-report=term-missing` shows uncovered lines.

## Model consistency

For any subdir with an FFI boundary to Lean, the highest-value unit tests verify Python
matches the Lean model on synthetic inputs — e.g.,
`foundations/portfolio-proofs/tests/test_lean_pgd.py`'s integration tests against `pgd_solve`.
If these fail, the formal guarantee is broken even when the Lean proof passes.

## Common failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `ImportError: lean_pgd_ffi...so` | Cython extension not rebuilt | `cd foundations/optimization-proofs && python ffi/setup_ffi.py build_ext --inplace` |
| `mypy: error: Function is missing a return type` | Missing annotation | Add return type annotation |
| `error: Argument 1 has incompatible type "float"` | Float where int expected at a basis-point FFI boundary | Use `to_bp()` (from `quant_core.pricer.conventions`) before passing to FFI |
| `ruff: B006` | Mutable default argument | Use `None` default + guard inside |

## Passes when

All Python-bearing subdirs above: pytest exits 0, mypy exits 0, ruff exits 0.
