# Verified Optimization

A portfolio optimizer is only as trustworthy as its solver. Standard solvers (interior-point,
sequential quadratic programming) carry convergence guarantees that hold under ideal
conditions but can silently fail when the problem data is ill-conditioned, volatile, or at a
constraint boundary. This pillar addresses that gap: it proves the mathematical properties of
a projected gradient descent (PGD) solver in Lean 4, then empirically demonstrates that those
properties matter in exactly the stress regimes where standard solvers fail.

The Lean proofs establish what the solver is guaranteed to do. The stress scenarios show why
that guarantee is worth having.

---

## `optimization-proofs`: A Formally Verified PGD Core

Projected gradient descent minimizes a convex quadratic objective by alternating gradient
steps with projection onto the feasible set (here, the probability simplex or a box
constraint). Nine theorems are proved in Lean 4, all zero sorry:

- **`shrinkage_psd`**: covariance shrinkage produces a matrix that is symmetric and positive
  semidefinite. This ensures the quadratic objective is convex, which PGD requires.
- **`projection_correctness`**: the simplex/box projection is feasible (the projected point
  is in the constraint set) and correct (it is the closest feasible point to the
  pre-projection iterate). The projection uses an O(N log N) dual-bisection method.
- **`pgd_descent_lemma`**: each PGD step strictly decreases the objective when the step
  size is set to the reciprocal of the Lipschitz constant of the gradient. This is the
  key monotonicity property that makes the algorithm converge.

These are not implementation tests. They are proofs about the mathematical structure of the
algorithm, independent of floating-point arithmetic.

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/optimization-proofs)

---

## `portfolio-proofs`: Stress Scenarios Against Standard Solvers

This project wires the verified PGD core into a portfolio solver and then subjects it and
three standard solvers (SciPy SLSQP, SciPy trust-constr, and Gurobi) to seven constructed
stress scenarios. Each scenario targets a known failure mode.

The Lean proofs from `optimization-proofs` establish the solver's mathematical properties.
The scenarios below are empirical demonstrations on constructed data: they show that the
failure modes exist and that the verified solver avoids them, but they are not formal proofs
of solver dominance across all possible inputs.

### The seven scenarios

**Boundary trap.** Weights concentrate on a single asset. Non-differentiable L1 kinks in the
objective cause SQP-type solvers to stall at the boundary rather than converging to the
interior optimum. PGD handles L1 structure directly via the projection step.

**Phantom positions.** Interior-point slack variables inflate near the constraint boundary,
producing small positive weights that should be exactly zero. The verified projection enforces
feasibility exactly.

**VIX shock.** A sudden volatility spike changes the curvature of the objective between
iterations. A solver that caches its step size or Hessian approximation may use a stale value
and diverge. PGD recomputes the Lipschitz step size at each iteration.

**S&P 500 factor.** A rank-deficient covariance matrix (a dominant common factor makes assets
nearly collinear) causes condition-number problems for methods that require a full-rank
Hessian. Shrinkage, proved positive semidefinite by `shrinkage_psd`, restores full rank.

**Cholesky crash.** The covariance matrix is slightly indefinite due to floating-point
accumulation, causing Cholesky factorization to fail entirely. The shrinkage step, proved
to produce a positive semidefinite matrix, prevents the failure.

**Precision bleed.** Accumulated floating-point error in dot-product accumulation causes
the constraint $\sum w_i = 1$ to drift. The verified projection re-enforces the constraint
at every step, so drift does not compound.

**Step divergence.** An aggressive initial step size causes oscillation rather than descent.
The `pgd_descent_lemma` proof prescribes the correct step-size bound; the solver enforces it
by construction.

Each scenario is documented on its own page under the `portfolio/` section of this site.

[Read the solver and scenarios](https://github.com/eigenq-xyz/quant-proofs/tree/main/portfolio-proofs)

---

## What is proved versus what is demonstrated

To be precise about the claims in this pillar:

The Lean 4 proofs in `optimization-proofs` are mathematical theorems: they hold for all
inputs satisfying the stated preconditions, with no reliance on specific data.

The stress scenarios in `portfolio-proofs` are empirical: they show specific constructed
cases where standard solvers fail and the verified solver does not. They are evidence, not
proofs of general superiority.

The combination is the point: the Lean proofs explain why the solver holds in the stress
scenarios (the monotonicity and projection guarantees apply), and the stress scenarios
show that the abstract guarantees correspond to real behavioral differences.
