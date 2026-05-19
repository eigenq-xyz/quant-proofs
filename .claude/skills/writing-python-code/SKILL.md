---
name: writing-python-code
description: >
  Python coding standards for the quant-proofs monorepo. Use whenever writing
  or modifying Python or Cython code in backtest-proofs/ or mortgage-proofs/.
  Covers types, docstrings, validation, FFI rules, and the pre-commit checklist.
paths:
  - "**/*.py"
  - "**/*.pyx"
  - "**/*.pxd"
  - "**/pyproject.toml"
---

# Writing Python Code — quant-proofs

See REFERENCE.md for full naming conventions, ruff/mypy config details, and uv
commands. See EXAMPLES.md for annotated good/bad examples. See ANTI_PATTERNS.md
for a quick list of things the linters will reject.

---

## Project layout

Both Python projects use the `src/` layout:

```
backtest-proofs/python/
  src/
    backtest_proofs/
      __init__.py
      ...
  tests/
  pyproject.toml
  setup_ffi.py          # compiles Cython extension against Lean IR

mortgage-proofs/
  src/
    mortgage_proofs/
      __init__.py
      ...
  tests/
  pyproject.toml
```

The package name matches the directory name with underscores: `backtest_proofs`,
`mortgage_proofs`.

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
Do not use `pip install` directly — `uv` manages the lockfile.

---

## Type annotations

All public functions and methods **must** have type annotations. No exceptions.

```python
from __future__ import annotations
```

Place this at the top of every module. It enables PEP 563 postponed evaluation,
which lets you use forward references without quotes.

Rules:
- No bare `Any`. If the type is genuinely dynamic, use `object` or define a
  `Protocol`. If `Any` is unavoidable (e.g., third-party library without stubs),
  add a `# type: ignore[misc]` comment with a one-line explanation.
- Use `Protocol` for duck typing instead of `Union` over concrete types.
- Use `TypeAlias` for complex type expressions repeated more than twice.
- Use `Sequence[T]` over `list[T]` in function signatures when you only read;
  use `list[T]` when you mutate.
- Use `Mapping[K, V]` over `dict[K, V]` in function signatures when you only read.

---

## Docstrings

Follow Google style. Every public function, method, and class needs a docstring.

Structure:
1. One-line summary (imperative mood, no period).
2. Blank line.
3. Longer description if needed (explain why, not just what).
4. `Args:` section (omit if no args).
5. `Returns:` section (omit if returns None).
6. `Raises:` section (omit if raises nothing documented).

Skip the docstring only if the function is trivially obvious and has no public
callers outside its own module (e.g., a private `_validate_foo()` helper with an
obvious name). When in doubt, write it.

---

## Validation rules

Validate at the boundary; trust internal invariants.

- **Validate:** user inputs, CLI arguments, external API responses, FFI return values,
  deserialized JSON/CSV data.
- **Trust:** values that have already passed validation and are flowing through
  internal pure functions. Don't re-validate inside a function that documents its
  preconditions in the type signature.
- Use Pydantic models (mortgage-proofs) or explicit `if not isinstance(...)` guards
  (backtest-proofs) at boundaries. Raise `ValueError` with a descriptive message
  when validation fails.

---

## Cython FFI rules (backtest-proofs only)

The Cython extension bridges Python and the Lean 4 accounting kernel.

**Critical constraint: all monetary values cross the FFI boundary in basis points
(int64). Never pass floats.**

| Correct | Incorrect |
|---------|-----------|
| `delta_bps: int = int(round(delta * 10_000))` | `delta: float = 0.0123` |
| `pnl_bps: int` | `pnl: float` |

Rationale: Lean's integer arithmetic guarantees that the formally verified
accounting invariants are preserved. Floating-point representation breaks those
guarantees.

After any change to Lean source files, rebuild the extension:
```
uv run python setup_ffi.py build_ext --inplace
```

Do not run tests against a stale `.so` file — the test suite will silently use
the old binary.

---

## Pre-commit hooks

Both projects run pre-commit hooks on every commit. A commit will **fail** if any
hook does not pass.

Hooks installed:
- `ruff` — linting (E, F, I, UP rule sets) and formatting
- `mypy` — `--strict` type checking

Run hooks manually at any time:
```
uv run pre-commit run --all-files
```

### Pre-commit checklist

Before committing Python or Cython changes, verify:

- [ ] `uv run ruff check src/ tests/` exits 0 (no linting errors)
- [ ] `uv run ruff format --check src/ tests/` exits 0 (no formatting drift)
- [ ] `uv run mypy --strict src/` exits 0 (no type errors)
- [ ] `uv run pytest` exits 0 (all tests pass)
- [ ] No bare `Any` annotations added without a comment justifying them
- [ ] No floats crossing the FFI boundary (backtest-proofs)
- [ ] Cython extension rebuilt after any Lean changes (`setup_ffi.py build_ext --inplace`)
- [ ] No licensed data files staged (`git diff --cached --name-only` must not include `.csv`, `.parquet`, `.h5`)
- [ ] Docstrings present on all new public functions/methods/classes
- [ ] `from __future__ import annotations` at the top of every new module
