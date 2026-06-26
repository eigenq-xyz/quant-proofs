import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Algebra.BigOperators.Group.Finset.Basic

/-!
# Abstract Portfolio Optimization: Problem Definitions

Typed mathematical objects for the mean-variance portfolio optimization problem.
These are the abstract specifications that the Lean 4 proof theorems operate on.

The numerical implementations in `PGD.lean` and `PGDFlat.lean` are
`Float`-arithmetic instantiations of these abstract objects.  Connecting the
`Float` code to these definitions (a "bridge" verification) is a separate step
beyond the scope of this module.

## Contents

- **C1.1** `IsInConstraintSet` — budget hyperplane and L₁ leverage ball
- **C1.2** `quadObj` / `gradObj` — Markowitz quadratic objective and its gradient
- **C1.3** `ledoitWolfShrinkage` — Ledoit-Wolf covariance regularization
-/

open scoped Matrix BigOperators

namespace OptimizationProofs

variable {N : ℕ}

/-! ### C1.1 — Constraint set -/

/-- **C1.1** The feasible constraint set `𝒞(B, L)` for leveraged portfolios.

    A weight vector `w : Fin N → ℝ` is *feasible* when it satisfies:
    - **Budget constraint**: `∑ᵢ wᵢ = B` (weights sum to the budget; usually `B = 1`)
    - **Leverage constraint**: `∑ᵢ |wᵢ| ≤ L` (gross exposure bounded by `L`)

    Together these define the intersection of a hyperplane and an L₁-ball, which
    is convex, closed, and bounded — hence compact in `ℝᴺ`. -/
def IsInConstraintSet (B L : ℝ) (w : Fin N → ℝ) : Prop :=
  (∑ i, w i) = B ∧ (∑ i, |w i|) ≤ L

/-! ### C1.2 — Mean-variance objective and gradient -/

/-- **C1.2** The mean-variance quadratic objective.

    `f(w) = ½ wᵀCov·w − ret·w`

    where `Cov : Matrix (Fin N) (Fin N) ℝ` is the covariance matrix and
    `ret : Fin N → ℝ` is the vector of expected returns.

    Minimizing `f` over `𝒞(B, L)` is the Markowitz mean-variance problem. -/
noncomputable def quadObj
    (Cov : Matrix (Fin N) (Fin N) ℝ) (ret w : Fin N → ℝ) : ℝ :=
  (1 / 2) * (w ⬝ᵥ Cov *ᵥ w) - (ret ⬝ᵥ w)

/-- **C1.3** The gradient of the objective: `∇f(w) = Cov·w − ret`.

    Computed component-wise: `(∇f(w))ᵢ = (Cov·w)ᵢ − retᵢ`.

    PGD uses this to form the gradient step `w − η ∇f(w)` before projecting
    back onto the constraint set. -/
noncomputable def gradObj
    (Cov : Matrix (Fin N) (Fin N) ℝ) (ret w : Fin N → ℝ) : Fin N → ℝ :=
  fun i => (Cov *ᵥ w) i - ret i

/-! ### C1.3 — Ledoit-Wolf shrinkage -/

/-- **C1.4** The Ledoit-Wolf shrinkage estimator.

    Given a (possibly rank-deficient) sample covariance `S` and intensity `δ ∈ (0, 1]`:

        `Σ*(δ) = δ · (Tr(S)/N) · I + (1 − δ) · S`

    The scaled identity `(Tr(S)/N) · I` is the shrinkage target.  When the
    lookback window is shorter than the number of assets (`T < N`), the sample
    covariance `S` is singular (rank-deficient).  Ledoit-Wolf shrinkage guarantees
    `Σ*(δ)` is strictly positive definite regardless of the rank of `S` — see
    `Shrinkage.shrinkage_psd` for the formal proof. -/
noncomputable def ledoitWolfShrinkage
    (S : Matrix (Fin N) (Fin N) ℝ) (δ : ℝ) : Matrix (Fin N) (Fin N) ℝ :=
  δ • ((Matrix.trace S / ↑N) • (1 : Matrix (Fin N) (Fin N) ℝ)) + (1 - δ) • S

end OptimizationProofs
