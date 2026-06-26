# Verified Optimization

A portfolio optimizer is only as trustworthy as its solver. Standard solvers (interior-point,
sequential quadratic programming) carry convergence guarantees that hold under ideal conditions
but can silently fail when the problem data is ill-conditioned, volatile, or at a constraint
boundary. This pillar addresses that gap: the mathematical properties of a projected gradient
descent (PGD) solver are proved in Lean 4, and those proofs are paired with stress scenarios
that show the failure modes exist and that the verified solver avoids them.

The Lean proofs establish what the solver is guaranteed to do. The stress scenarios show why
that guarantee is worth having.

---

## `optimization-proofs`: A Formally Verified PGD Core

Projected gradient descent minimizes a convex quadratic objective by alternating gradient
steps with projection onto the feasible set (here, the budget simplex intersected with an L1
leverage ball). Ten theorems are proved in Lean 4, all zero sorry. Four are load-bearing:

- **`shrinkage_isSymmetric`** and **`shrinkage_psd`**: the Ledoit-Wolf shrinkage estimator
  produces a matrix that is symmetric and strictly positive definite. The proof writes the
  shrinkage as a scaled identity plus a scaled PSD matrix, then applies Weyl's monotonicity
  inequality: the smallest eigenvalue of the sum is bounded below by the smallest eigenvalue
  of the strictly PD term, which is positive. This ensures the quadratic objective is convex,
  which PGD requires, and it rules out Cholesky crashes caused by floating-point
  near-singularity.

- **`projection_feasibility`** and **`projection_correctness`**: the dual-bisection simplex
  and L1-ball projection produces a point that is exactly feasible (in the constraint set)
  and exactly optimal (the closest feasible point to the pre-projection iterate). The
  correctness proof uses KKT conditions: budget-cancellation, a pointwise subgradient bound,
  and complementary slackness. The projection's O(N log N) dual-bisection complexity is a
  property of the implementation, not part of the formal claim, which is feasibility and
  optimality.

- **`pgd_descent_lemma`** and **`pgd_convergence`**: each PGD step strictly decreases the
  objective when the step size is set to the reciprocal of the Lipschitz constant of the
  gradient. The descent lemma combines four quadratic lemmas, the Lipschitz bound, and the
  projection inequality via `nlinarith`. The convergence theorem telescopes the descent lemma
  to an O(1/k) bound, with an explicit witness for the required number of iterations.

These are not implementation tests. They are proofs about the mathematical structure of the
algorithm, independent of floating-point arithmetic.

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/foundations/optimization-proofs)

---

## `portfolio-proofs`: The Verified Solver in Production

This project wires the verified PGD core into a mean-variance portfolio solver. The
Markowitz objective,

$$\min_w \; \frac{\gamma}{2} w^\top \Sigma w - \mu^\top w \quad \text{subject to} \quad \sum_i w_i = 1, \; \sum_i |w_i| \leq L$$

is a convex QP on the simplex intersected with an L1 ball. The solver accepts the Ledoit-Wolf
shrinkage of the sample covariance as input, proved positive definite by `shrinkage_psd`, so
the feasible set always admits the analytical projection whose correctness is guaranteed by
`projection_correctness`. Iterates stay exactly feasible at every step with no slack variables
and no constraint drift.

The research-pipeline routes its portfolio construction stage through this verified solver.
A result counts as verified only if the allocation was computed through the verified path; the
pipeline raises rather than silently substituting an unverified baseline. See
[Research Integrity](pillar-research-integrity.md) for how the pipeline uses and enforces
this.

[Read the solver](https://github.com/eigenq-xyz/quant-proofs/tree/main/foundations/portfolio-proofs)

---

## Stress Scenarios

The `portfolio-proofs` project subjects the verified PGD solver and three standard
alternatives (SciPy SLSQP, SciPy trust-constr, and Gurobi) to seven constructed stress
scenarios. Each scenario targets a known failure mode and is paired with an analytically
certified KKT optimum. The Lean proofs from `optimization-proofs` explain why the verified
solver holds in each case; the scenarios show that the abstract guarantees correspond to real
behavioral differences.

| Scenario | Failure mode | Result |
|---|---|---|
| [Boundary Trap](portfolio/boundary_trap) | L1 kink cycling; solver stalls at boundary | SLSQP suboptimal; Lean PGD exact |
| [Phantom Positions](portfolio/phantom_positions) | Log-barrier prevents exact zeros | Interior-point: phantom weights; Lean PGD: exact zeros |
| [VIX Shock](portfolio/vix_shock) | Stale step size violates Lipschitz bound | Gradient descent oscillates; Lean PGD certified convergence |
| [S&P 500 Factor](portfolio/sp500_factor) | Dominant factor: near-rank-deficient covariance | Gurobi impractical at N >= 300; Lean PGD O(N) gradient |
| [Cholesky Crash](portfolio/cholesky_crash) | Floating-point indefinite covariance | SLSQP and Gurobi crash; Lean PGD LW shrinkage holds |
| [Precision Bleed](portfolio/precision_bleed) | IEEE 754 constraint drift in dot products | SLSQP triggers production halt; Lean PGD exact |
| [Step Divergence](portfolio/step_divergence) | Stale calibration after volatility shift | Gradient descent diverges to NaN; Lean PGD certified |

[Full scenario documentation and solver comparison matrix](portfolio/index.md)

---

## What is proved versus what is demonstrated

The Lean 4 proofs in `optimization-proofs` are mathematical theorems: they hold for all
inputs satisfying the stated preconditions, with no reliance on specific data.

The stress scenarios in `portfolio-proofs` are empirical: they show specific constructed
cases where standard solvers fail and the verified solver does not. They are evidence, not
proofs of general superiority.

The combination is the point: the Lean proofs explain why the solver holds in the stress
scenarios (the monotonicity and projection guarantees apply), and the stress scenarios
show that the abstract guarantees correspond to real behavioral differences.
