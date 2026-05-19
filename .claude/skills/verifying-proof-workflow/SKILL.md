---
name: verifying-proof-workflow
description: >
  Complete verification pipeline for the quant-proofs monorepo.
  Use before opening any PR, when diagnosing a CI failure, or when
  doing a full QA pass on any subproject. Covers the Lean side
  (lake build, sorry check, trace verification), Python side
  (pytest, mypy --strict), and pre-commit hooks.
paths:
  - "**/*.lean"
  - "**/*.py"
  - "**/*.pyx"
---

# Verifying the proof workflow

## The full QA sequence

Run these in order. Each step gates the next — do not skip.

```
1. Sorry check      (Lean, any subdir)
2. lake build       (Lean, the subdir you changed)
3. lake build       (Lean, downstream deps — binomial-proofs if you changed ftap-proofs)
4. Python tests     (if the subdir has a Python layer)
5. mypy --strict    (if the subdir has a Python layer)
6. Trace verify     (mortgage-proofs only)
```

---

## Step 1 — Sorry check

A `sorry` means the theorem is unproven. Zero tolerance on `main`.

```bash
# For a specific subdir:
grep -rn sorry --include="*.lean" backtest-proofs/lean/
grep -rn sorry --include="*.lean" ftap-proofs/
grep -rn sorry --include="*.lean" binomial-proofs/
grep -rn sorry --include="*.lean" mortgage-proofs/lean/

# Expected output: (empty — no output means zero sorry)
```

If any `sorry` is found, the branch is not ready to merge. Remove the `sorry` or move the
incomplete theorem to a feature branch.

---

## Step 2 — lake build

Run from the directory containing `lakefile.toml`.

```bash
# backtest-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/backtest-proofs/lean && lake build

# ftap-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/ftap-proofs && lake build

# binomial-proofs (also builds ftap-proofs as a dependency)
cd /Users/akhilkarra/ode/eigenq/quant-proofs/binomial-proofs && lake build

# mortgage-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/mortgage-proofs && lake build
```

Must exit 0. A non-zero exit means there is a type error, a missing import, or a broken
definition somewhere in the changed files.

**If `binomial-proofs` fails after touching `ftap-proofs`:**
The error is almost certainly in `ftap-proofs` itself. Fix the `ftap-proofs` build first,
then retry `binomial-proofs`.

---

## Step 3 — Downstream dependency check

Only needed when you change `ftap-proofs` interfaces (definitions, theorem signatures,
or namespace exports).

```bash
# After ftap-proofs builds cleanly:
cd /Users/akhilkarra/ode/eigenq/quant-proofs/binomial-proofs && lake build
```

`backtest-proofs` and `mortgage-proofs` have no cross-subdir Lean dependencies, so they
do not need rebuilding when other Lean subdirs change.

---

## Step 4 — Python tests

Run from the subdir that has a Python layer.

```bash
# backtest-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/backtest-proofs/python
uv run pytest -q

# mortgage-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/mortgage-proofs
pytest
```

All tests must pass. A test failure that predates your changes is still a blocking issue —
do not merge with pre-existing failures.

For `backtest-proofs`, the Cython FFI must be compiled before the tests run:
```bash
cd backtest-proofs/python && uv run python setup.py build_ext --inplace
uv run pytest -q
```

---

## Step 5 — mypy --strict

All Python in `src/` directories must be type-clean.

```bash
# backtest-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/backtest-proofs/python
uv run mypy src/ --strict

# mortgage-proofs
cd /Users/akhilkarra/ode/eigenq/quant-proofs/mortgage-proofs
mypy src/ --strict
```

Must exit 0 with no errors. Warnings are not errors, but `error:` lines are blocking.

Common mypy --strict failures and fixes:

| Error | Fix |
|-------|-----|
| `Missing return type annotation` | Add `-> ReturnType` to the function signature |
| `Untyped function declaration` | Add parameter types |
| `Cannot determine type of ...` | Add an explicit type annotation |
| `error: Item "None" of "Optional[X]" has no attribute "y"` | Add a `None` guard |

---

## Step 6 — Trace verification (mortgage-proofs only)

The mortgage pipeline emits `DecisionRecord` JSON traces. The Lean-side trace checker
validates that agent routing satisfies the formal invariants.

```bash
cd /Users/akhilkarra/ode/eigenq/quant-proofs/mortgage-proofs
lake exe verify-trace traces/latest.json
```

Must exit 0. A non-zero exit means a `DecisionRecord` in the trace violates at least
one invariant (e.g., `compliance_before_underwriter`, `risk_score_nonneg`).

To run against all traces in the directory:
```bash
for f in traces/*.json; do
  lake exe verify-trace "$f" || echo "FAILED: $f"
done
```

---

## Pre-commit hooks

Pre-commit hooks run automatically on `git commit`. They enforce:

- `ruff` — Python linting and formatting
- `mypy src/ --strict` — Python type checking
- `lake build` — Lean compilation in each changed subdir
- `pytest` — Python tests in each changed subdir

If a hook fails, the commit is aborted. Fix the issue, re-stage with `git add`, and retry
`git commit`. Do not use `--no-verify` to bypass hooks.

To run hooks manually without committing:
```bash
pre-commit run --all-files
```

---

## Pre-merge checklist

Before opening a PR or merging to `main`:

- [ ] Zero `sorry` in all changed `.lean` files (`grep -rn sorry --include="*.lean" <subdir>/`)
- [ ] `lake build` exits 0 in every changed subdir
- [ ] `lake build` exits 0 in `binomial-proofs` (if `ftap-proofs` changed)
- [ ] `uv run pytest -q` passes (if `backtest-proofs/python/` changed)
- [ ] `pytest` passes (if `mortgage-proofs/` Python changed)
- [ ] `mypy src/ --strict` exits 0 (if any Python in `src/` changed)
- [ ] `lake exe verify-trace` passes on all traces (if `mortgage-proofs/` Lean changed)
- [ ] Pre-commit hooks pass (`pre-commit run --all-files`)
- [ ] No licensed data committed (check with `git diff --name-only HEAD`)
- [ ] No private content in commit message or diff

