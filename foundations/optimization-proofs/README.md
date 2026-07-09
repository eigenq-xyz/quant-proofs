# optimization-proofs

Correct-by-construction projected gradient descent (PGD) for convex quadratic programs on a
budget/leverage constraint set: convergence and projection correctness are proved in Lean 4, not
just tested. General-purpose, zero finance dependencies. 10 theorems, zero `sorry` (Lean's
placeholder tactic for an unproven step; none remain here).

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it proves

The module solves convex quadratic programs of the form

$$\min_{x \in \mathcal{C}} \tfrac{1}{2} x^T Q x + c^T x, \qquad \mathcal{C} = \Big\{ x \in \mathbb{R}^N : \textstyle\sum_i x_i = B,\ \sum_i |x_i| \le L \Big\}$$

with Q symmetric positive definite, via Projected Gradient Descent: an unconstrained gradient step
followed by an analytical Euclidean projection back onto the constraint set (the simplex/L1-ball
feasible region defined above). The projection is solved by dual bisection: search over a single
dual variable until the KKT conditions (the standard first-order optimality conditions for a
constrained convex program) hold exactly, closed-form and non-iterative once the dual variable is
found.

| Guarantee | Theorem |
|-----------|---------|
| For step size `η * lMax(Q) ≤ 1`, PGD iterates satisfy `f(w_k) - f(w*) ≤ ‖w_0 - w*‖² / (2ηk)` and converge to the unique global minimum | `pgd_convergence` |
| One PGD step reduces the objective by at least `(1/2η)(D_k - D_{k+1})` | `pgd_descent_lemma` |
| The dual-bisection projection returns the exact Euclidean projection onto the constraint set (`sum_i (p_i - y_i)(x_i - p_i) ≥ 0`) | `projection_correctness` |
| Valid dual variables exist for any feasible `(B, L)` with `|B| ≤ L`; every iterate satisfies the budget and leverage constraints exactly | `projection_feasibility` |
| The Ledoit-Wolf shrinkage estimator is positive definite for any input covariance, so the step-size bound stays finite | `shrinkage_psd` |
| The shrinkage estimator is symmetric | `shrinkage_isSymmetric` |
| Q is a symmetric bilinear form | `symmetric_bilin_form` |
| Algebraic identity underlying the convexity and descent proofs | `quadratic_identity` |
| The quadratic objective is convex under `Cov.PosSemidef` | `quadratic_convexity` |
| Polarization identity used in the descent-lemma algebra | `polarization_identity` |

## What it doesn't claim

- No finance-specific claim: the QP form and PGD proof are generic. `foundations/portfolio-proofs/`
  applies this solver to mean-variance allocation and variance-optimal hedging, and documents
  concrete cases where SciPy SLSQP, CVXPY/OSQP, and Gurobi fail on stressed inputs (non-convergence,
  silent constraint violation, solver refusal). That comparison is empirical, not part of this
  module's proofs.
- `PGD.lean` (Array Float) and `PGDFlat.lean` (FloatArray, used by the CLI) are separate
  implementations of the same algorithm; only the algorithm is proved correct, not bit-identical
  output between the two.
- `pgd_convergence` is conditional, not unconditional: it takes monotone per-step descent
  (`hdesc_obj`), projection feasibility and correctness, and `Cov.PosDef` as hypotheses rather than
  deriving them inline. The hypotheses are themselves proved elsewhere in this module
  (`pgd_descent_lemma`, `projection_feasibility`, `projection_correctness`) and wired together in
  the compiled `pgd_solve` binary, but the convergence theorem's statement is only as strong as the
  hypotheses it's given. It also reasons over real-valued arithmetic; the compiled binary runs on
  `Float64`, and no theorem here bridges that gap.

## Build and verify

```bash
cd foundations/optimization-proofs
lake exe cache get   # fetch prebuilt mathlib (first run only)
lake build           # builds pgd_solve, pgd_bench, and type-checks all proofs (Lean's proof
                     # checking is mechanical: the compiler rejects any gap in the logic)

# Zero-sorry check (empty output = clean)
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

Full build/test/FFI command list: see [CLAUDE.md](CLAUDE.md).

## Dependencies

No dependencies on other subprojects. `foundations/portfolio-proofs/` depends on this project's compiled `pgd_solve` binary.

## License

Apache License 2.0.
