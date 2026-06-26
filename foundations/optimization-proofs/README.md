# optimization-proofs

Projected gradient descent for convex quadratic programs, with machine-checked convergence and projection correctness. General-purpose, zero finance dependencies. 10 theorems, zero `sorry`.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it proves

The module solves convex quadratic programs of the form

$$\min_{x \in \mathcal{C}} \tfrac{1}{2} x^T Q x + c^T x, \qquad \mathcal{C} = \Big\{ x \in \mathbb{R}^N : \textstyle\sum_i x_i = B,\ \sum_i |x_i| \le L \Big\}$$

with Q symmetric positive definite, via Projected Gradient Descent: alternate an unconstrained gradient step with an analytical Euclidean projection back onto the constraint set. Two properties of that loop are proved correct in Lean 4:

**Convergence** (`pgd_convergence`). For any step size satisfying `η * lMax(Q) ≤ 1`, the PGD iterates satisfy the O(1/k) bound

$$f(w_k) - f(w^*) \le \frac{\|w_0 - w^*\|^2}{2\eta k}$$

and converge to the unique global minimum.

**Projection correctness** (`projection_correctness`). The analytical O(N log N) dual-bisection projection returns the exact Euclidean projection onto the constraint set: for any feasible point x and the projected point p, the projection inequality `sum_i (p_i - y_i)(x_i - p_i) >= 0` holds. Combined with `projection_feasibility`, every iterate satisfies the budget and leverage constraints exactly.

**Shrinkage positive definiteness** (`shrinkage_psd`). The Ledoit-Wolf shrinkage estimator is positive definite for any input covariance, so the step-size bound is always finite.

## Why it matters

General-purpose QP solvers handle the non-differentiable L1 constraint by introducing 2N slack variables and 2N inequalities. Under ill-conditioned inputs, that machinery fails in characteristic ways: active-set solvers cycle on the non-smooth boundary, interior-point solvers terminate early in flat penalty valleys, and a non-PSD covariance matrix causes some solvers to refuse the problem. The failures are documented with data in [`foundations/portfolio-proofs/scenarios/`](../portfolio-proofs/).

This module sidesteps those issues by projecting analytically and carrying a machine-checked proof that every iterate is feasible and that the sequence converges. [`foundations/portfolio-proofs/`](../portfolio-proofs/) uses this solver for mean-variance allocation and variance-optimal hedging.

## Build

```bash
cd foundations/optimization-proofs
lake exe cache get    # fetch prebuilt mathlib (first run only)
lake build
```

`lake build` produces two binaries: `pgd_solve` (a stdin/stdout server that Python drives as a persistent subprocess) and `pgd_bench` (an embedded benchmark timing 1000 solves at N=10).

## Test

```bash
# Confirm zero sorry (empty output = clean)
grep -rn '^\s*sorry\b' --include="*.lean" --exclude-dir=.lake .

# Run the benchmark
lake exe pgd_bench
```

## Project structure

```
foundations/optimization-proofs/
  OptimizationProofs/
    ProblemDefs.lean       abstract problem types: IsInConstraintSet, quadObj, gradObj
    QuadraticLemmas.lean   supporting algebra: convexity, polarization identity (4 thms)
    Shrinkage.lean         Ledoit-Wolf shrinkage: symmetry and PD (2 thms)
    Projection.lean        dual-bisection projection: feasibility and correctness (2 thms)
    Convergence.lean       descent lemma and O(1/k) convergence theorem (2 thms)
    PGD.lean               reference PGD loop and projection (Array Float)
    PGDFlat.lean           production PGD loop and projection (FloatArray); drives the CLI
    FFI.lean               @[export] bindings for the Cython path (latency hedge)
  CLI.lean                 pgd_solve stdin/stdout server
  Main.lean                pgd_bench entry point
  ffi/
    pgd_ffi.pyx            Cython bindings (not the default integration path)
    setup_ffi.py           setuptools build for the Cython extension
```

## License

Apache 2.0, compatible with mathlib for upstream contribution.
