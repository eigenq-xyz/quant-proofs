# portfolio-proofs

Mean-variance allocation with Ledoit-Wolf shrinkage, routed through the verified PGD solver from
[`optimization-proofs`](../optimization-proofs/), with stressed-solver scenarios that document
where standard solvers break and why.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

This is an applied/empirical project. It contains no new Lean 4 proofs. The convergence and
projection-correctness guarantees reside in `optimization-proofs` (zero `sorry`); this project
routes production allocation problems through that verified core and documents the solver's
behavior on stressed inputs.

The verified guarantees this project relies on (proved in `optimization-proofs`):

| Guarantee | Theorem |
|-----------|---------|
| Ledoit-Wolf shrinkage produces a positive-definite covariance | `shrinkage_psd` |
| The analytical projection is the exact Euclidean projection onto the feasible set | `projection_correctness` |
| Every iterate satisfies the budget and leverage constraints exactly | `projection_feasibility` |
| PGD iterates converge to the global optimum for step size `η < 2/λ_max(Q)` | `pgd_convergence` |

## What it doesn't claim

- The statistical layer (covariance estimation, expected-return inputs) is rigorous but not
  formally verified. Results here inherit that boundary.
- The seven stressed-solver scenarios compare the verified PGD against SLSQP, CVXPY/OSQP, and
  Gurobi on adversarially chosen inputs; they document specific failure modes, not a general claim
  that PGD dominates these solvers.

## The solver

`lean_pgd.py` is a persistent-subprocess bridge to the compiled `pgd_solve` binary from
`optimization-proofs`. It solves the Markowitz objective

    min_w  (γ/2) w'Σw − μ'w   subject to  Σwᵢ = 1,  Σ|wᵢ| ≤ L

as a convex QP on the simplex ∩ L₁ ball, using the exact O(N log N) analytical projection
(dual-bisection) proved in `optimization-proofs`.

`lean_pgd_ffi.py` is a Cython FFI wrapper that dispatches to a flat or boxed call path based on
the covariance condition number; it is approximately 1.5x faster than the subprocess bridge for
ill-conditioned inputs (condition number ≥ 150).

## Stressed-solver scenarios

Seven scenarios in [`scenarios/`](scenarios/), each isolating one solver failure mode with a
KKT-certified analytical optimum as ground truth:

| Scenario | What it tests |
|----------|---------------|
| [`cholesky_crash/`](scenarios/cholesky_crash/) | Rank-deficient sample covariance; Gurobi refuses, SLSQP crashes; Ledoit-Wolf shrinkage + PGD recovers |
| [`precision_bleed/`](scenarios/precision_bleed/) | SLSQP constraint drift at `acc=1e-8` accumulates across solves |
| [`boundary_trap/`](scenarios/boundary_trap/) | L₁-kink cycling in SLSQP on a corner-constrained portfolio |
| [`step_divergence/`](scenarios/step_divergence/) | Lipschitz constant violation in unverified GD after a volatility regime shift |
| [`phantom_positions/`](scenarios/phantom_positions/) | Interior-point phantom near-zero weights from barrier relaxation |
| [`vix_shock/`](scenarios/vix_shock/) | Volatility regime change breaks uncertified gradient descent |
| [`sp500_factor/`](scenarios/sp500_factor/) | N-scaling benchmark across asset universes |

## Build and verify

```bash
cd foundations/portfolio-proofs
uv sync --extra dev

# Unit tests (no binary required; runs in CI)
uv run pytest tests/test_lean_pgd.py -v -k "not integration"
```

The `pgd_solve` binary (required for integration tests and the FFI path) is built in
`optimization-proofs`:

```bash
cd foundations/optimization-proofs && lake exe cache get && lake build pgd_solve
```

Full build/test/typecheck/lint matrix: see [CLAUDE.md](CLAUDE.md).

## Dependencies

- **`optimization-proofs`**: provides the `pgd_solve` binary and Cython FFI target this project
  routes through.
- **`quant-core`**: no direct import; the hedging module uses Black-Scholes conventions consistent
  with `quant-core`'s `OptionKind` and payoff definitions.

## References

- Markowitz, H. (1952). "Portfolio Selection." *Journal of Finance* 7(1): 77-91.
- Ledoit, O., and M. Wolf (2004). "A Well-Conditioned Estimator for Large-Dimensional Covariance
  Matrices." *Journal of Multivariate Analysis* 88(2): 365-411.
- Schweizer, M. (1995). "Variance-Optimal Hedging in Discrete Time." *Mathematics of Operations
  Research* 20(1): 1-32.

## License

Apache License 2.0.
