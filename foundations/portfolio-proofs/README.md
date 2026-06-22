# portfolio-proofs

> Two distinct problems in quantitative finance, optimal **allocation** and optimal **hedging**, each reduce to the same convex quadratic program. This project solves that program with a projected-gradient solver whose convergence and constraint-feasibility are **proved in Lean 4** (see [`optimization-proofs`](../optimization-proofs/)), and demonstrates it on both.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/portfolio_solver_stress.ipynb)

## Two finance problems, one optimization core

### Optimal allocation

An investor spreads capital across `N` assets with random returns, expected excess returns `μ`, and return covariance `Σ`. The Markowitz objective trades expected return against variance: for risk aversion `γ`,

$$\max_w\ \mu^\top w - \tfrac{\gamma}{2}\, w^\top \Sigma w \quad\Longleftrightarrow\quad \min_w\ \tfrac{\gamma}{2}\, w^\top \Sigma w - \mu^\top w$$

subject to a budget `Σwᵢ = 1` (fully invested) and a gross-leverage cap `Σ|wᵢ| ≤ L` (a long-short or regulatory limit). With a positive-definite `Σ`, this is a convex quadratic program in the weights `w`.

### Optimal hedging

A desk holds a liability with random payoff `H` at horizon `T`, for example an index option, and offsets it by trading `n` instruments whose price changes are `ΔS`. The residual after hedging is `H − ξᵀΔS`. Minimizing the mean-square hedging error,

$$\min_\xi\ \mathbb{E}\big[(H - \xi^\top \Delta S)^2\big] \;=\; \min_\xi\ \tfrac{1}{2}\,\xi^\top C\,\xi - b^\top \xi \;+\; \text{const},$$

where `C = E[ΔS·ΔSᵀ]` is the instruments' second-moment matrix and `b = E[H·ΔS]` is the claim's cross-moment with each instrument. Under a hedge-budget normalization `Σξⱼ = B` and a gross-leverage cap `Σ|ξⱼ| ≤ L`, this is again a convex quadratic program, now in the hedge positions `ξ`. This is the variance-optimal (quadratic) hedge of Schweizer (1995).

### How the two are related, honestly

They are distinct problems. Allocation prices an *appetite for return*: its linear term `μ` is a preference, scaled by risk aversion, and there is no liability to replicate. Hedging prices the *cost of tracking error against a fixed liability*: its linear term `b = E[H·ΔS]` is a projection coefficient forced by the claim's correlation with the instruments, not a return. Substituting one into the other yields nothing economically meaningful (`E[H·ΔS]` is not an expected return). The two touch only in the degenerate minimum-variance corner (allocation with `μ = 0` and a pinned position behaves like a hedge), which is a shared special case rather than a reduction. What they genuinely share is their reduced form: the convex quadratic program below.

## The general convex QP

$$\min_x\ \tfrac{1}{2}\, x^\top Q\, x - c^\top x \qquad \text{s.t.}\qquad \sum_i x_i = B,\quad \sum_i |x_i| \le L,$$

with `Q` symmetric positive definite. The feasible set is the intersection of a budget hyperplane and a gross-exposure `L₁` ball: convex, compact, with a unique minimizer. Allocation is the instance `(Q, c) = (Σ, μ)`; hedging is the instance `(Q, c) = (C, b)`.

## Why projected gradient descent

The feasible set admits an exact analytical `O(N log N)` projection (dual-bisection onto the simplex ∩ `L₁` ball), so projected-gradient iterates stay *exactly* feasible with no slack variables and no constraint drift. The alternatives fail in characteristic ways on stressed inputs, documented with data in [`scenarios/`](scenarios/):

- Active-set solvers (SciPy SLSQP) introduce `2N` slack variables for the `L₁` kink and cycle on the non-differentiable boundary until they hit the iteration limit.
- Interior-point and commercial solvers (Gurobi) require a positive-definite `Q`, refuse a rank-deficient sample covariance outright, and stop early in flat penalty valleys.

Projected gradient descent needs none of that, and its convergence rate is governed by a single explicit constant, the largest eigenvalue of `Q`. That is exactly what makes the method tractable to verify formally.

## What is proven (in `optimization-proofs`, zero `sorry`)

| Guarantee | Theorem |
| --------- | ------- |
| The covariance is positive definite for any sample (Ledoit-Wolf shrinkage) | `shrinkage_psd` |
| The analytical projection is the exact Euclidean projection onto the feasible set | `projection_correctness` |
| Every iterate satisfies the budget and leverage constraints exactly | `projection_feasibility` |
| The iterates converge to the global optimum for `η < 2/λ_max(Q)` | `pgd_convergence` |

Because both finance problems reduce to the same QP, these guarantees apply to both. The hedging second-moment matrix `C` is a Gram matrix and hence symmetric positive semidefinite, so `shrinkage_psd` applies to it directly.

## Results

### Allocation: stressed-solver scenarios

Seven scenarios in [`scenarios/`](scenarios/) each target one solver failure mode (rank-deficient covariance, `L₁` boundary cycling, floating-point constraint drift, step-size divergence, interior-point phantom positions, volatility-regime change, and `N`-scaling). Each has a KKT-certified analytical optimum as ground truth. The verified PGD is the only solver that passes all seven. Run the stress demo: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/portfolio_solver_stress.ipynb)

### Hedging: variance-optimal index-option hedge

[`hedging/`](hedging/) builds `C` and `b` from Monte Carlo option scenarios under Black-Scholes (no licensed data), solves for the variance-optimal hedge with the verified solver, and benchmarks the out-of-sample hedging-error variance against the Black-Scholes delta hedge. Minimum-variance hedging is known to reduce hedged-PnL variance out of sample relative to the practitioner delta (Hull and White, 2017). The framing is deliberate: this is the verifiable convex counterpart to black-box deep hedging (Bühler et al., 2019), trading some empirical hedging performance for a machine-checked global-optimality and feasibility guarantee. Run it: [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/variance_optimal_hedge.ipynb)

## Build and run

```bash
# Build the verified solver binary (from the repo root)
cd foundations/optimization-proofs && lake exe cache get && lake build pgd_solve

# Install Python deps and run the test suite (from foundations/portfolio-proofs/)
cd ../portfolio-proofs && uv sync --extra dev
uv run pytest tests/test_lean_pgd.py -v -k "not integration"

# Reproduce a stress scenario (allocation)
python3 scenarios/cholesky_crash/scipy_slsqp.py

# Run the variance-optimal hedge (hedging)
uv run python hedging/variance_optimal_hedge.py
```

## Architecture

```text
foundations/portfolio-proofs/
  lean_pgd.py            persistent-subprocess bridge to the verified pgd_solve binary
  hedging/               variance-optimal hedge: Monte Carlo -> C, b -> verified solve, vs BS delta
  scenarios/             seven allocation stress scenarios (Quarto + solver modules)
  tests/                 deterministic unit tests + Hypothesis property tests
  data/                  DVC-managed French 10-industry daily returns
```

## References

- Markowitz, H. (1952). "Portfolio Selection." *Journal of Finance* 7(1): 77-91.
- Schweizer, M. (1995). "Variance-Optimal Hedging in Discrete Time." *Mathematics of Operations Research* 20(1): 1-32.
- Ledoit, O., and M. Wolf (2004). "A Well-Conditioned Estimator for Large-Dimensional Covariance Matrices." *Journal of Multivariate Analysis* 88(2): 365-411.
- Hull, J., and A. White (2017). "Optimal Delta Hedging for Options." *Journal of Banking and Finance* 82: 180-190.
- Bühler, H., L. Gonon, J. Teichmann, and B. Wood (2019). "Deep Hedging." *Quantitative Finance* 19(8): 1271-1291.

## License

Apache License 2.0.
