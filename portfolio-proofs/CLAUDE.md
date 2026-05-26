# CLAUDE.md — portfolio-proofs

Python scenarios and the persistent-subprocess wrapper that connects them to
the formally verified Lean 4 PGD solver in `optimization-proofs/`.

## What this project is

Six failure scenarios that demonstrate where standard solvers (SLSQP, Gurobi,
trust_constr) break on real portfolio-optimization edge cases, and where the
Lean PGD either holds or fails differently.  Each scenario is a standalone
Quarto document (`scenarios/<name>/<name>.qmd`) with Python solver modules
(`scenarios/<name>/solvers/`) and a rendered Markdown output committed to the
repo.

The `lean_pgd.py` module is the production bridge: it wraps the compiled
`pgd_solve` binary from `optimization-proofs/` in a persistent subprocess so
Python callers pay the ~35 ms process-spawn cost once per session, not per
solve.

## Architecture

```
portfolio-proofs/
  lean_pgd.py           — persistent subprocess wrapper (PRIMARY)
  lean_pgd_direct.py    — single-shot subprocess fallback (reference only)
  tests/
    test_lean_pgd.py         — 21 deterministic unit + integration tests
    test_lean_pgd_properties.py  — Hypothesis property-based tests
  scenarios/
    precision_bleed/    — SLSQP acc=1e-8 constraint drift
    cholesky_crash/     — rank-deficient covariance + Ledoit-Wolf recovery
    boundary_trap/      — L1 kink cycling in SLSQP
    step_divergence/    — step-size Lipschitz violation post-Volmageddon
    phantom_positions/  — interior-point phantom near-zero weights
    vix_shock/          — volatility regime change breaks uncertified GD
    sp500_factor/       — N-scaling benchmark
  data/                 — DVC-managed French 10-industry daily returns
```

## Build & test commands

```bash
# Install dev dependencies (from portfolio-proofs/)
uv sync --extra dev

# Unit tests only (no binary required — runs in CI)
uv run pytest tests/test_lean_pgd.py -v -k "not integration"

# Full test suite including property tests (requires pgd_solve binary)
uv run pytest tests/ -v

# Type check
uv run mypy lean_pgd.py lean_pgd_direct.py tests/ --strict

# Lint
uv run ruff check lean_pgd.py lean_pgd_direct.py tests/

# Docstring coverage
uv run interrogate lean_pgd.py lean_pgd_direct.py

# Theorem cross-reference check (run from monorepo root)
python3 ../.github/scripts/check_theorem_refs.py lean_pgd.py
```

## Wire protocol (lean_pgd.py ↔ pgd_solve)

One space-separated line per problem on stdin:

```
N  sigma_00 sigma_01 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap
```

One space-separated line of N float64 weights on stdout.  An empty line
signals EOF and terminates the Lean process.  All float values use Python
`repr(v)` (shortest round-trip form); the Lean parser handles both decimal
and scientific-notation strings.

## Hard rules

- **Do not edit `scenarios/` or `.lean` files** unless specifically tasked;
  those tracks are developed independently.
- `lean_pgd.py` public API (`solve`, `LEAN_NATIVE_NS`) is frozen — scenarios
  import it directly.  Changes must remain backward-compatible.
- Never claim a theorem is "guaranteed" unless it appears in a Lean file;
  say "planned" or "targeted" for proof obligations not yet formalized.
- `mypy --strict` and `ruff` must pass before any commit.

## Known solver characteristics

- N=3 / identity sigma / uniform mu: budget error ~1e-6 (degenerate input,
  not a bug; documented in `test_solve_degenerate_n3_uniform`).
- `cholesky_crash` scenario: Lean PGD takes 580+ iterations on LW-shrunk
  covariance (cond=87.6), taking ~3.8 s.  Other solvers are faster but
  produce incorrect results on the raw rank-deficient input.
- `phantom_positions` and `vix_shock` currently use `lean_pgd_direct`
  (single-shot); updating them to the persistent wrapper is a tracked TODO.
