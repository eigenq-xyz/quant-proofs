---
name: review-code-quality
description: >
  QA checklist for Lean 4, Python, Cython, and FFI code in quant-proofs. Use when
  reviewing a PR, before merging, or as a pre-submission self-check. This skill
  reads code and reports issues — it does not edit files.
paths:
  - "**/*.py"
  - "**/*.lean"
  - "**/*.pyx"
disallowedTools:
  - Edit
  - Write
---

# Reviewing Code Quality — quant-proofs

This skill is read-only. Report issues found; do not fix them. The author fixes issues
and re-requests review.

---

## How to use this checklist

Work through each section that applies to the PR. Mark each item:
- **Pass** — verified clean
- **Fail** — describe the specific file/line and the issue
- **N/A** — section doesn't apply to this PR

A PR is ready to merge only when all applicable items are **Pass**.

---

## Lean 4 checklist

### Zero sorry

- [ ] Run `grep -rn sorry --include="*.lean" <subdir>/lean/` and confirm the output is
  empty. `-- sorry` in a comment is fine; a bare `sorry` term in a proof body is a hard
  block.

### Build

- [ ] `lake build` exits 0 in the affected subdir with no errors or warnings.
- [ ] If `foundations/options-proofs/` changes, also run `lake build` in
  `foundations/ftap-proofs/` — the dependency chain must stay intact.

### Namespace convention

- [ ] Top-level namespace matches the subdir convention:
  - `extensions/hedge-proofs/` → `BacktestProofs` (historical name, kept for continuity)
  - `foundations/ftap-proofs/` → `FtapProofs`
  - `foundations/options-proofs/` → `OptionsProofs`
  - `extensions/mortgage-proofs/lean/` → `MortgageProofs`
- [ ] No theorem or definition uses a namespace from another subdir without an explicit
  import.

### Imports

- [ ] No `import Mathlib` (wildcard). All imports are specific:
  ```lean
  -- Bad
  import Mathlib
  -- Good
  import Mathlib.Probability.Martingale.Basic
  import Mathlib.Analysis.SpecialFunctions.Log.Basic
  ```
  Wildcard mathlib imports slow the build and obscure dependencies.

### Docstrings

- [ ] Every exported `theorem`, `def`, and `structure` (no leading `_` or `private`
  keyword) has a `/-- ... -/` docstring.
- [ ] Each docstring states the mathematical content in plain English before the formal
  statement. A docstring that only restates the Lean syntax is insufficient.
- [ ] Key references are cited in the docstring (e.g., Harrison-Pliska 1981 for FTAP
  results, Cox-Ross-Rubinstein 1979 for binomial model results).

### Proof structure

- [ ] `-- Proof sketch:` comment is present at the top of each non-trivial proof,
  describing the high-level argument in one to three sentences.
- [ ] `have` and `suffices` steps are named (not anonymous `_`).

---

## Python checklist

### Type checking

- [ ] `uv run mypy --strict src/` exits 0 with no errors.
- [ ] No bare `Any` annotations without a comment explaining why `Any` is unavoidable and
  a `# type: ignore[...]` with a specific error code.
- [ ] All new public functions, methods, and classes have full type annotations.
- [ ] `from __future__ import annotations` is present at the top of every new module.

### Linting

- [ ] `uv run ruff check src/ tests/` exits 0.
- [ ] `uv run ruff format --check src/ tests/` exits 0 (no formatting drift).

### Tests

- [ ] `uv run pytest` exits 0 with all tests passing.
- [ ] New code has at least 80% test coverage. Check with:
  ```
  uv run pytest --cov=src/ --cov-report=term-missing
  ```
- [ ] No test asserts floating-point equality without a tolerance (`pytest.approx` or
  `math.isclose`).
- [ ] No bare `except:` or `except Exception:` without a logged traceback and a re-raise
  or structured error return.

### Code style

- [ ] No mutable default arguments (ruff B006 catches most, but review manually for
  Pydantic `Field` defaults).
- [ ] No `os.system()` calls (use `subprocess.run(check=True)`).
- [ ] No `import *`.
- [ ] No magic numeric literals in arithmetic expressions or function calls. Every bare
  integer or float with domain meaning (prices, fees, tenors, basis-point factors) must
  be a named constant or use `to_bp`/`from_bp`. Pay extra attention near FFI call sites,
  where a wrong unit is a silent correctness failure.

---

## FFI checklist (Cython FFI: foundations/optimization-proofs + foundations/portfolio-proofs
only — this is the one live Cython/FFI boundary in the repo today, and it is opt-in, not the
default path; `lean_pgd.py`'s subprocess bridge is primary, `lean_pgd_ffi.py` is the Cython
alternative. `extensions/hedge-proofs` also exports a Lean `@[export hedge_*]` FFI surface in
`BacktestProofs/Accounting.lean`, but has no Cython wrapper or Python bindings yet — the
Cython-specific items below (`.pyx`/`.pxd`/`setup_ffi.py`) don't apply there.)

- [ ] All monetary/numeric values crossing the Lean/Python FFI boundary use the
  convention documented for that boundary (e.g. basis-point `int` for hedge-proofs'
  exports; `float64` per the wire protocol for `optimization-proofs`/`portfolio-proofs`).
  No silent unit mismatches at the boundary.
- [ ] Cython `.pyx` file has been rebuilt after any Lean source changes:
  ```
  cd foundations/optimization-proofs && python ffi/setup_ffi.py build_ext --inplace
  ```
  Verify the `.so` modification timestamp is newer than the Lean source files.
- [ ] Cython function signatures match the Lean-exported interface. Check that
  `cdef extern` declarations in the `.pxd`/`.pyx` file match the current Lean IR exports.
- [ ] Integration tests in `foundations/portfolio-proofs/tests/` cover the new or changed
  FFI function (see `test_lean_pgd.py` for the existing pattern).

---

## Documentation checklist

- [ ] README commands are runnable as written. Test at least the build and test commands
  from a clean checkout.
- [ ] `CLAUDE.md` is ≤ 1 screen (roughly 50 lines). If it's grown beyond that, flag it —
  content may belong in a skill file instead.
- [ ] No private content in any public file: no personal timelines, no target firm names
  in strategy framing, no grades or application context.
- [ ] New theorems have plain-English descriptions in the README or a proof docstring,
  accessible to a non-Lean reader.

---

## Reporting format

When reporting issues, use this format for each finding:

```
[SECTION] [SEVERITY] File: path/to/file.lean, Line: 42
Issue: <description of what is wrong>
Required fix: <what needs to change>
```

Severity levels:
- **BLOCK** — must be fixed before merge (sorry, mypy failure, lake build failure, float
  across FFI boundary)
- **WARN** — should be fixed; may merge with documented justification
- **NOTE** — style or documentation improvement; does not block merge
