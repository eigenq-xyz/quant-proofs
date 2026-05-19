---
name: reviewing-code-quality
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

This skill is read-only. Report issues found; do not fix them directly. The author
fixes the issues and re-requests review.

---

## How to use this checklist

Work through each section that applies to the PR. For each item, mark it:
- **Pass** — verified clean
- **Fail** — describe the specific file/line and the issue
- **N/A** — section does not apply to this PR

A PR is ready to merge only when all applicable items are **Pass**.

---

## Lean 4 checklist

### Zero sorry

- [ ] Run `grep -rn sorry --include="*.lean" <subdir>/lean/` and confirm the output
  is empty. `-- sorry` in a comment is fine; a bare `sorry` term in a proof body
  is a hard block.

### Build

- [ ] `lake build` exits 0 in the affected subdir with no errors or warnings.
- [ ] If `options-proofs/` is changed, also run `lake build` in `ftap-proofs/` —
  the dependency chain must remain intact.

### Namespace convention

- [ ] Top-level namespace matches the subdir convention:
  - `backtest-proofs/lean/` → `BacktestProofs`
  - `ftap-proofs/` → `FtapProofs`
  - `options-proofs/` → `OptionsProofs`
  - `mortgage-proofs/lean/` → `MortgageProofs`
- [ ] No theorem or definition uses a namespace from another subdir without an
  explicit import.

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

- [ ] Every exported `theorem`, `def`, and `structure` (those without a leading `_`
  or `private` keyword) has a `/-- ... -/` docstring.
- [ ] Each docstring states the mathematical content in plain English before the
  formal statement. A docstring that only restates the Lean syntax is insufficient.
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
- [ ] No bare `Any` annotations added without a comment explaining why `Any` is
  unavoidable and a `# type: ignore[...]` with a specific error code.
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
- [ ] No test uses `assert` on floating-point equality without a tolerance
  (`pytest.approx` or `math.isclose`).
- [ ] No bare `except:` or `except Exception:` without a logged traceback and a
  re-raise or structured error return.

### Code style

- [ ] No mutable default arguments (ruff B006 catches most, but review manually for
  Pydantic `Field` defaults).
- [ ] No `os.system()` calls (use `subprocess.run(check=True)`).
- [ ] No `import *`.
- [ ] No magic numeric literals in arithmetic expressions or function calls. Every
  bare integer or float with domain meaning (prices, fees, tenors, basis-point
  factors) must be a named constant or use `to_bp`/`from_bp`. Pay extra attention
  near FFI call sites where a wrong unit is a silent correctness failure.

---

## FFI checklist (backtest-proofs only)

- [ ] All monetary values crossing the Lean/Python FFI boundary are `int` in basis
  points. No `float` arguments or return values at the FFI boundary.
- [ ] Cython `.pyx` file has been rebuilt after any Lean source changes:
  ```
  uv run python setup_ffi.py build_ext --inplace
  ```
  Verify that the `.so` modification timestamp is newer than the Lean source files.
- [ ] Cython function signatures match the Lean-exported interface. Check that
  `cdef extern` declarations in the `.pxd` file match the current Lean IR exports.
- [ ] Integration tests in `tests/integration/test_ffi.py` cover the new or changed
  FFI function.

---

## Documentation checklist

- [ ] README commands are runnable as written. Test at least the build and test
  commands from a clean checkout.
- [ ] `CLAUDE.md` is ≤ 1 screen (roughly 50 lines). If it has grown beyond that,
  flag it — content may belong in a skill file instead.
- [ ] No private content in any public file: no personal timelines, no target firm
  names in strategy framing, no grades or application context.
- [ ] New theorems have corresponding plain-English descriptions in the README or
  in a proof docstring accessible to a non-Lean reader.

---

## Reporting format

When reporting issues, use this format for each finding:

```
[SECTION] [SEVERITY] File: path/to/file.lean, Line: 42
Issue: <description of what is wrong>
Required fix: <what needs to change>
```

Severity levels:
- **BLOCK** — must be fixed before merge (sorry, mypy failure, lake build failure,
  float across FFI boundary)
- **WARN** — should be fixed; may merge with documented justification
- **NOTE** — style or documentation improvement; does not block merge
