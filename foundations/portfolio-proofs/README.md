# portfolio-proofs

Mean-variance allocation with Ledoit-Wolf shrinkage, routed through the verified PGD solver from
[`optimization-proofs`](../optimization-proofs/), with stressed-solver scenarios that document
where standard solvers break and why.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What this project is and is not

This is an **applied / empirical** project. It does not contain new Lean 4 proofs. The convergence
and projection-correctness guarantees reside in `optimization-proofs` (zero `sorry`); this project
routes production allocation problems through that verified core and documents the solver's behavior
on stressed inputs.

The verified guarantees (from `optimization-proofs`):

| Guarantee | Theorem |
|-----------|---------|
| Ledoit-Wolf shrinkage produces a positive-definite covariance | `shrinkage_psd` |
| The analytical projection is the exact Euclidean projection onto the feasible set | `projection_correctness` |
| Every iterate satisfies the budget and leverage constraints exactly | `projection_feasibility` |
| PGD iterates converge to the global optimum for step size `η < 2/λ_max(Q)` | `pgd_convergence` |

The statistical layer (covariance estimation, expected-return inputs) is rigorous but not formally
verified, and the results say so.

## The solver

`lean_pgd.py` is a persistent-subprocess bridge to the compiled `pgd_solve` binary from
`optimization-proofs`. The Markowitz objective,

    min_w  (γ/2) w'Σw − μ'w   subject to  Σwᵢ = 1,  Σ|wᵢ| ≤ L

reduces to a convex QP on the simplex ∩ L₁ ball. The feasible set admits an exact O(N log N)
analytical projection (dual-bisection), so iterates stay exactly feasible with no slack variables
and no constraint drift.

`lean_pgd_ffi.py` is a Cython FFI wrapper that dispatches to a flat or boxed call path based on
the covariance condition number; it is approximately 1.5x faster than the subprocess bridge for
ill-conditioned inputs (condition number ≥ 150).

## Stressed-solver scenarios

Seven scenarios in [`scenarios/`](scenarios/) each isolate one solver failure mode, provide a
KKT-certified analytical optimum as ground truth, and compare the verified PGD against SLSQP,
CVXPY/OSQP, and Gurobi.

| Scenario | What it tests |
|----------|---------------|
| [`cholesky_crash/`](scenarios/cholesky_crash/) | Rank-deficient sample covariance; Gurobi refuses, SLSQP crashes; Ledoit-Wolf shrinkage + PGD recovers |
| [`precision_bleed/`](scenarios/precision_bleed/) | SLSQP constraint drift at `acc=1e-8` accumulates across solves |
| [`boundary_trap/`](scenarios/boundary_trap/) | L₁-kink cycling in SLSQP on a corner-constrained portfolio |
| [`step_divergence/`](scenarios/step_divergence/) | Lipschitz constant violation in unverified GD after a volatility regime shift |
| [`phantom_positions/`](scenarios/phantom_positions/) | Interior-point phantom near-zero weights from barrier relaxation |
| [`vix_shock/`](scenarios/vix_shock/) | Volatility regime change breaks uncertified gradient descent |
| [`sp500_factor/`](scenarios/sp500_factor/) | N-scaling benchmark across asset universes |

## Build and test

```bash
# Install Python dependencies (from foundations/portfolio-proofs/)
cd foundations/portfolio-proofs
uv sync --extra dev

# Unit tests (no binary required; runs in CI)
uv run pytest tests/test_lean_pgd.py -v -k "not integration"

# Full test suite including property tests (requires pgd_solve binary)
uv run pytest tests/ -v

# Type check
uv run mypy lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/ --strict

# Lint
uv run ruff check lean_pgd.py lean_pgd_direct.py lean_pgd_ffi.py tests/

# Build the Cython FFI extension (from foundations/optimization-proofs/)
cd ../optimization-proofs && python ffi/setup_ffi.py build_ext --inplace

# Reproduce a stress scenario
python3 foundations/portfolio-proofs/scenarios/cholesky_crash/scipy_slsqp.py
```

The `pgd_solve` binary is built in `optimization-proofs`:

```bash
cd foundations/optimization-proofs && lake exe cache get && lake build pgd_solve
```

## Project structure

```
foundations/portfolio-proofs/
  lean_pgd.py              persistent-subprocess bridge to pgd_solve (primary)
  lean_pgd_direct.py       single-shot subprocess fallback (reference)
  lean_pgd_ffi.py          Cython FFI wrapper; dispatches flat/boxed by condition number
  hedging/
    variance_optimal_hedge.py  variance-optimal hedge via the same QP (Monte Carlo, no licensed data)
  scenarios/               seven stressed-solver scenarios (Quarto source + solver modules)
  tests/
    test_lean_pgd.py           deterministic unit + integration tests
    test_lean_pgd_properties.py  Hypothesis property-based tests
    test_hedge.py              hedging tests
  data/                    DVC-managed Ken French 10-industry daily returns (free data)
  reports/                 Quarto performance report (do not edit by hand)
  results/                 committed benchmark JSON outputs
```

## References

- Markowitz, H. (1952). "Portfolio Selection." *Journal of Finance* 7(1): 77-91.
- Ledoit, O., and M. Wolf (2004). "A Well-Conditioned Estimator for Large-Dimensional Covariance
  Matrices." *Journal of Multivariate Analysis* 88(2): 365-411.
- Schweizer, M. (1995). "Variance-Optimal Hedging in Discrete Time." *Mathematics of Operations
  Research* 20(1): 1-32.

## License

Apache License 2.0.
