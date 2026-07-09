# portfolio-proofs

Mean-variance allocation with Ledoit-Wolf shrinkage, routed through the correct-by-construction
PGD (projected gradient descent) solver from [`optimization-proofs`](../optimization-proofs/):
convergence and projection correctness are proved in Lean 4, not just tested. Seven adversarial
scenarios document concrete cases where SciPy SLSQP, CVXPY/OSQP, and Gurobi fail to converge or
silently violate constraints, and where the Lean-verified solver matches the KKT-certified
(the standard first-order optimality conditions for a constrained convex program) analytical
optimum instead.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

This is an applied/empirical project. It contains no new Lean 4 proofs. The convergence and
projection-correctness guarantees are proved in `optimization-proofs` (zero `sorry`, Lean's
placeholder tactic for an unproven step; none remain there); this project routes production
allocation problems through that correct-by-construction core and documents the solver's behavior
on stressed inputs.

The guarantees this project relies on, each proved correct in Lean 4 in `optimization-proofs`:

| Guarantee | Theorem |
|-----------|---------|
| Ledoit-Wolf shrinkage produces a positive-definite covariance | `shrinkage_psd` |
| The analytical projection is the exact Euclidean projection onto the feasible set | `projection_correctness` |
| Every iterate satisfies the budget and leverage constraints exactly | `projection_feasibility` |
| PGD iterates converge to the global optimum for step size `η · λ_max(Q) ≤ 1` | `pgd_convergence` |

## What it doesn't claim

- The statistical layer (covariance estimation, expected-return inputs) is rigorous but not
  formally verified. Results here inherit that boundary.
- The seven scenarios are built around each competitor solver's known weak point (rank-deficient
  covariance, tight numerical tolerance, L1-ball corners, and so on); they document specific,
  concrete failure modes (SLSQP non-convergence, silent constraint violation, Gurobi refusal), not
  a general claim that PGD dominates these solvers on arbitrary inputs.

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
