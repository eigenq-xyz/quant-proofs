# CLAUDE.md: portfolio-proofs

Applied allocation and hedging on top of the verified PGD solver from
`foundations/optimization-proofs/`. This project is **not** a Lean proof project; it
routes production portfolio problems through the verified core and documents solver
behavior on stressed inputs.

## Architecture

```
foundations/portfolio-proofs/
  lean_pgd.py              persistent-subprocess bridge to pgd_solve (primary API)
  lean_pgd_direct.py       single-shot subprocess fallback (reference only)
  lean_pgd_ffi.py          Cython FFI wrapper; dispatches flat/boxed by condition number
  hedging/
    variance_optimal_hedge.py  variance-optimal QP hedge (Monte Carlo, no licensed data)
  scenarios/               stressed-solver scenarios (Quarto source + solver modules)
    cholesky_crash/        rank-deficient covariance
    precision_bleed/       SLSQP constraint drift
    boundary_trap/         L₁-kink cycling
    step_divergence/       Lipschitz violation post-volatility shift
    phantom_positions/     interior-point phantom weights
    vix_shock/             volatility regime change
    sp500_factor/          N-scaling benchmark
  tests/
    test_lean_pgd.py           21 deterministic unit + integration tests
    test_lean_pgd_properties.py  Hypothesis property-based tests
    test_hedge.py              hedging tests
  data/                    DVC-managed Ken French 10-industry daily returns
  reports/                 Quarto performance report (generated; do not edit by hand)
  results/                 committed benchmark JSON
```

## Dependencies

- **`optimization-proofs`**: provides `pgd_solve` binary and Cython FFI target; must be built
  before integration tests or the FFI extension run. Zero `sorry`, four theorems.
- **`quant-core`**: no direct import; hedging module uses Black-Scholes conventions consistent
  with `quant-core`'s `OptionKind` and payoff definitions.

## Build and test

```bash
# Install Python dependencies
cd foundations/portfolio-proofs
uv sync --extra dev

# Unit tests only (no binary required; used in CI)
uv run pytest tests/test_lean_pgd.py -v -k "not integration"

# Full test suite (requires pgd_solve binary)
uv run pytest tests/ -v

# Type check
uv run mypy lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/ --strict

# Lint
uv run ruff check lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/

# Build the Cython FFI extension (from optimization-proofs/)
cd ../optimization-proofs && python ffi/setup_ffi.py build_ext --inplace

# Build pgd_solve binary (from optimization-proofs/)
cd ../optimization-proofs && lake exe cache get && lake build pgd_solve
```

## Wire protocol (lean_pgd.py to pgd_solve)

One space-separated line per problem on stdin:

```
N  sigma_00 sigma_01 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap
```

One space-separated line of N float64 weights on stdout. An empty line signals EOF and
terminates the Lean process. All float values use Python `repr(v)` (shortest round-trip
form); the Lean parser handles both decimal and scientific-notation strings.

## Known solver characteristics

- N=3, identity sigma, uniform mu: budget error ~1e-6 (degenerate input, documented in
  `test_solve_degenerate_n3_uniform`).
- `cholesky_crash`: PGD takes 580+ iterations on Ledoit-Wolf-shrunk covariance (cond=87.6),
  approximately 3.8 s. Other solvers are faster but produce incorrect results on the raw
  rank-deficient input.
- `lean_pgd_ffi.py`: FFI-boxed path is approximately 1.5x faster than subprocess for
  condition number ≥ 150 (e.g., `boundary_trap` random sigma, cond approximately 204).

## Hard rules

- Do not edit `scenarios/**/*.qmd`, `scenarios/**/*.md`, or `reports/` files; those are
  Quarto content maintained separately.
- Do not edit `data/README.md`.
- `lean_pgd.py` public API (`solve`, `LEAN_NATIVE_NS`) is frozen; scenarios import it
  directly. Changes must remain backward-compatible.
- Never claim a theorem is "guaranteed" or "verified" unless it appears, zero `sorry`, in a
  Lean file. The statistical layer (covariance estimation, expected-return inputs) is
  rigorous but not formally verified; say so if it comes up.
- `mypy --strict` and `ruff` must pass before any commit.
- Licensed data (WRDS, OptionMetrics, paid) is never committed; describe it as
  licensed-not-included if referenced.
