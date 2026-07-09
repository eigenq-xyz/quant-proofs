---
name: write-python-code
description: >
  Python coding standards for the quant-proofs monorepo. Use whenever writing
  or modifying Python or Cython code in research-pipeline/, foundations/quant-core/,
  foundations/portfolio-proofs/ (the one live Cython FFI boundary), or
  extensions/mortgage-proofs/. Covers types, docstrings, validation, FFI rules, and the
  pre-commit checklist.
paths:
  - "**/*.py"
  - "**/*.pyx"
  - "**/*.pxd"
  - "**/pyproject.toml"
---

# Writing Python Code — quant-proofs

Type everything, validate at boundaries, never float across a bps FFI boundary.
Full detail: REFERENCE.md (naming/tooling), EXAMPLES.md (good/bad code),
ANTI_PATTERNS.md (what linters reject).

---

## Project layout

Most projects use the `src/` layout:

```
research-pipeline/
  src/
    research_pipeline/
      __init__.py
      ...
  tests/
  pyproject.toml

foundations/quant-core/python/
  src/
    quant_core/
      __init__.py
      ...
  tests/

extensions/mortgage-proofs/
  src/
    mortgage_proofs/
      __init__.py
      ...
  tests/
  pyproject.toml
```

**Exception:** `portfolio-proofs/` is flat (no `src/` root) — `lean_pgd.py`,
`lean_pgd_direct.py`, `lean_pgd_ffi.py` sit under the project root next to `tests/`.
`lean_pgd_ffi.py` is the Cython FFI wrapper; `optimization-proofs/ffi/` holds the
matching `.pyx`/`setup_ffi.py` that compiles it against the Lean IR.

Package name = directory name with underscores (`research_pipeline`, `quant_core`,
`mortgage_proofs`). `portfolio-proofs` has no installable package name — modules
import directly by path. `extensions/hedge-proofs` is Lean-only today: a
`@[export hedge_*]` FFI surface with no Python bindings yet.

---

## Environment and tooling

| Task | Command |
|------|---------|
| Install (including dev deps) | `uv sync --extra dev` |
| Run tests | `uv run pytest` |
| Run a single test | `uv run pytest tests/test_foo.py::test_bar -v` |
| Type-check | `uv run mypy --strict src/` |
| Lint + format | `uv run ruff check src/ tests/` and `uv run ruff format src/ tests/` |
| Rebuild Cython extension | `uv run python setup_ffi.py build_ext --inplace` |

Run `uv sync --extra dev` once after cloning or after any `pyproject.toml` change.
Never `pip install` directly — `uv` manages the lockfile.

---

## Type annotations

**All public functions and methods need type annotations.** No exceptions.

`from __future__ import annotations` at the top of every module — enables PEP 563,
so forward references need no quotes.

- **No bare `Any`.** Dynamic → `object` or `Protocol`. Unavoidable (no third-party
  stubs) → `# type: ignore[misc]` with a one-line explanation.
- `Protocol` for duck typing, not `Union` over concrete types.
- `TypeAlias` for type expressions repeated more than twice.
- `Sequence[T]` over `list[T]` when read-only; `list[T]` when mutating.
- `Mapping[K, V]` over `dict[K, V]` when read-only.

---

## Docstrings

Google style. Every public function, method, and class needs one:
one-line summary (imperative, no period), blank line, longer description if needed
(why, not what), `Args:`/`Returns:`/`Raises:` (omit each if not applicable).

Skip only for trivially obvious, non-public functions (e.g., `_validate_foo()`).
When in doubt, write it.

---

## Validation rules

Validate at the boundary; trust internal invariants after that.

- **Validate:** user inputs, CLI args, external API responses, FFI return values,
  deserialized JSON/CSV.
- **Trust:** values already validated inside internal pure functions — don't
  re-validate what the type signature already documents.
- Pydantic models (mortgage-proofs) or `if not isinstance(...)` guards
  (research-pipeline, quant-core, portfolio-proofs). Raise `ValueError` with a
  descriptive message.

---

## FFI rules — two boundaries, two conventions, never conflate them

**Cython boundary** (`portfolio-proofs` + `optimization-proofs`): `pgd_ffi.pyx` bridges
Python and the Lean 4 PGD kernel; `lean_pgd_ffi.py` wraps it. Opt-in, not default —
`lean_pgd.py`'s subprocess bridge to the compiled `pgd_solve` binary is primary. Wire
format is `float64` directly, not basis points.

Rebuild after any `optimization-proofs` Lean change:
```
cd foundations/optimization-proofs && python ffi/setup_ffi.py build_ext --inplace
```
Never test against a stale `.so`.

**Basis-point boundary** (`extensions/hedge-proofs`, Lean-only, no Cython): Lean
`@[export hedge_*]` wrappers in `BacktestProofs/Accounting.lean`. **Contract is basis
points (int64), never floats** — use `to_bp`/`from_bp` from `quant_core.pricer.conventions`
if Python bindings ever get written:

| Correct | Incorrect |
|---------|-----------|
| `delta_bps: int = int(round(delta * 10_000))` | `delta: float = 0.0123` |
| `pnl_bps: int` | `pnl: float` |

---

## Pre-commit hooks

Every commit runs `ruff` (lint + format) and `mypy --strict`; any failure blocks the
commit. Run manually: `uv run pre-commit run --all-files`. Fix the actual type error —
**never** `[[tool.mypy.overrides]]` or `ignore_missing_imports = true`. Missing
third-party stubs: `py.typed` marker (internal packages) or a narrow
`# type: ignore[import-untyped]` with a one-line explanation, never a blanket suppression.

### Pre-commit checklist

- [ ] `uv run ruff check src/ tests/` exits 0
- [ ] `uv run ruff format --check src/ tests/` exits 0
- [ ] `uv run mypy --strict src/` exits 0
- [ ] `uv run pytest` exits 0
- [ ] No bare `Any` without a justifying comment
- [ ] No floats across the hedge-proofs bps FFI boundary (Cython boundary is `float64`
  by design — exempt)
- [ ] Cython extension rebuilt after any `optimization-proofs` Lean change
- [ ] No licensed data staged (`git diff --cached --name-only`: no `.csv`/`.parquet`/`.h5`)
- [ ] Docstrings on all new public functions/methods/classes
- [ ] `from __future__ import annotations` in every new module
