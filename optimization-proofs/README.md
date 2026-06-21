# optimization-proofs

> A convex quadratic-program solver whose convergence and constraint-feasibility are **proved in Lean 4**, not just tested. Where SLSQP and Gurobi can silently return an infeasible or suboptimal answer under stress, this solver carries a machine-checked guarantee that it cannot. General-purpose, zero finance dependencies, 10 theorems, zero `sorry`.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## The result

The engine solves convex quadratic programs

$$\min_{x \in \mathcal{C}} \tfrac{1}{2} x^T Q x + c^T x, \qquad \mathcal{C} = \Big\{ x : \sum_i x_i = B,\ \sum_i |x_i| \le L \Big\}$$

with $Q$ symmetric positive definite, over the intersection of a budget hyperplane and a gross-exposure $L_1$ ball. It uses Projected Gradient Descent: alternate an unconstrained gradient step with a Euclidean projection back onto $\mathcal{C}$.

Two things about that loop are proved correct in Lean, rather than assumed:

- **Convergence.** For any step size satisfying $\eta < 2/\lambda_{\max}(Q)$, the iterates converge to the unique global minimum. The Lipschitz bound is the largest eigenvalue of $Q$, so the admissible step size is known at compile time.
- **Projection correctness.** The analytical $O(N \log N)$ dual-bisection projection returns the exact Euclidean projection onto $\mathcal{C}$, so every iterate satisfies the budget and leverage constraints exactly.

## Why prove it formally

General-purpose QP solvers handle the non-differentiable $L_1$ constraint by introducing $2N$ slack variables and $2N$ inequalities. Under ill-conditioned inputs that machinery fails in characteristic ways: active-set solvers (SLSQP) cycle on the non-smooth boundary and hit their iteration limit, interior-point solvers terminate early in flat penalty valleys, and a non-PSD covariance makes Gurobi refuse the problem outright. The failures are documented, with data, in [`portfolio-proofs/scenarios/`](../portfolio-proofs/).

This solver sidesteps all of it by projecting analytically (no slack variables) and proving the two properties that matter. A solver that *reports* optimality is not the same as a solver that is *proved* to reach it. This one is the latter, which is the whole point: the answer can be trusted without re-checking it.

## Run the benchmark

```bash
cd optimization-proofs
lake exe cache get          # fetch prebuilt mathlib (first run only)
lake build                  # build both binaries and machine-check every proof
lake exe pgd_bench          # time 1000 solves at N = 10
grep -rn '^[[:space:]]*sorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

`lake build` produces two binaries: `pgd_solve` (a stdin/stdout server that Python drives as a persistent subprocess) and `pgd_bench` (the embedded benchmark). The wire protocol is documented in `CLI.lean`. For the applied side, see the [portfolio stress-test notebook](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/portfolio_solver_stress.ipynb).

## What's inside

| Module | Role |
| ------ | ---- |
| `PGDFlat.lean` | Production PGD loop and projection (unboxed `FloatArray`); drives the CLI |
| `PGD.lean` | Reference PGD loop and projection (`Array Float`) |
| `Projection.lean` | Dual-bisection projection: feasibility and optimality proofs |
| `Convergence.lean` | Descent lemma and the convergence theorem |
| `Shrinkage.lean` | Ledoit-Wolf shrinkage: symmetry and positive-definiteness proofs |
| `QuadraticLemmas.lean` | Supporting algebra (convexity, polarization identity) |
| `CLI.lean` / `Main.lean` | `pgd_solve` server and `pgd_bench` entry points |
| `FFI.lean` | `@[export]` bindings for the Cython path (latency hedge; subprocess is default) |

Headline theorems (all complete, zero `sorry`):

| Theorem | What it states |
| ------- | -------------- |
| `pgd_convergence` | PGD iterates converge to the global minimum for $\eta < 2/\lambda_{\max}(Q)$ |
| `projection_correctness` | The analytical projection is the exact Euclidean projection onto $\mathcal{C}$ |
| `projection_feasibility` | Every projected point satisfies the budget and leverage constraints |
| `shrinkage_psd` | The Ledoit-Wolf shrinkage estimator is positive definite for any input |

10 theorems total.

## Dependencies

- `mathlib` (linear algebra, analysis, spectral bounds)

## Used by

This engine is finance-agnostic by design. Two distinct finance problems reduce to its QP and are demonstrated in [`portfolio-proofs`](../portfolio-proofs/): mean-variance **allocation** (instance `(Q, c) = (Σ, μ)`) and variance-optimal **hedging** (instance `(Q, c) = (C, b)`). Neither reduces to the other; the QP is their shared form.

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
