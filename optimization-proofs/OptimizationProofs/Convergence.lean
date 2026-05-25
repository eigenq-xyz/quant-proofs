import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Analysis.InnerProductSpace.Basic
import OptimizationProofs.ProblemDefs
import OptimizationProofs.Shrinkage
import OptimizationProofs.Projection

/-!
# PGD Convergence under Lipschitz Step-Size Bounds (Milestone 4)

Formally verifies that projected gradient descent converges to the unique global
minimum of the mean-variance objective on the constraint set `𝒞`, provided the
step size `η` satisfies the Lipschitz stability bound `η < 2 / lMax(Σ)`.

## Main theorems

- **V4.1** `pgd_descent_lemma` — one PGD step strictly decreases the objective (TODO: prove)
- **V4.2** `pgd_convergence` — the iterate sequence converges to the optimal portfolio (TODO: prove)

## Mathematical background

The objective `f(w) = ½ wᵀΣw − μᵀw` has Lipschitz-continuous gradient with constant
`lMax(Σ)` (the largest eigenvalue of `Σ`).  Standard PGD convergence theory gives:

    f(wₖ) − f(w*) ≤ ‖w₀ − w*‖² / (2η(1 − ηlMax/2) · k)

under `η < 2/lMax`, yielding O(1/k) convergence.

For **strongly convex** objectives (Σ is PD), the convergence is geometric:

    f(wₖ) − f(w*) ≤ (1 − ηλ_min)^k · (f(w₀) − f(w*))

under `η ≤ 1/lMax`, where `λ_min = λ_min(Σ) > 0` by `shrinkage_psd`.

## Proof strategy (for future completion)

**Step V4.1 (descent lemma)**:
Starting from the Lipschitz smoothness condition:

    f(wₖ₊₁) ≤ f(wₖ) + ⟨∇f(wₖ), wₖ₊₁ − wₖ⟩ + (lMax/2) ‖wₖ₊₁ − wₖ‖²

Use the projection inequality `⟨wₖ₊₁ − (wₖ − η∇f(wₖ)), x − wₖ₊₁⟩ ≥ 0` at `x = w*`
to eliminate the cross-term and obtain:

    f(wₖ₊₁) − f(w*) ≤ (1/2η) (‖wₖ − w*‖² − ‖wₖ₊₁ − w*‖²)

**Step V4.2 (telescoping)**:
Sum the descent inequality from `k = 0` to `K`:

    ∑ (f(wₖ) − f(w*)) ≤ ‖w₀ − w*‖² / (2η)

Since all terms are non-negative and `f(wₖ) − f(w*)` is the minimum in the
partial sum, we get the O(1/K) bound.

**Status**: Proof obligations are stubs.  The structure is correct; individual
steps require `Mathlib.Analysis.Convex.GradientDescent` (or equivalent bespoke
lemmas) and the projection inequality from `Projection.projection_correctness`.
Remove `sorry` after completing Milestones 3 and 4.
-/

open scoped BigOperators Matrix

namespace OptimizationProofs

variable {N : ℕ} [NeZero N]

/-! ### V4.1 — Descent lemma -/

/-- **V4.1** One PGD step strictly decreases the objective.

    Given:
    - `Σ.PosDef` (covariance is PD after Ledoit-Wolf shrinkage)
    - `lMax` is a Lipschitz constant for `∇f`: `‖∇f(w)‖² ≤ lMax · ‖w‖²`
    - `η ∈ (0, 2/lMax)` (stability step size)
    - `Π y` is the projection of `y` onto `𝒞`, satisfying the projection inequality

    The descent lemma states:

        f(w₊) − f(w*) ≤ (1/(2η)) (‖w − w*‖² − ‖w₊ − w*‖²)

    where `w₊ = Π(w − η ∇f(w))` is the PGD update.

    **Status**: `sorry`.  Full proof uses the Lipschitz smoothness inequality and
    the projection inequality from `projection_correctness`. -/
theorem pgd_descent_lemma
    (Cov : Matrix (Fin N) (Fin N) ℝ) (ret : Fin N → ℝ)
    (hCov : Cov.PosDef)
    (lMax : ℝ) (hlMax_pos : 0 < lMax)
    (hlMax_bound : ∀ w : Fin N → ℝ, w ⬝ᵥ (Cov *ᵥ w) ≤ lMax * (w ⬝ᵥ w))
    (η : ℝ) (hη_pos : 0 < η) (hη_bound : η * lMax < 2)
    (B L : ℝ)
    (proj : (Fin N → ℝ) → Fin N → ℝ)
    (hproj_feas : ∀ y, IsInConstraintSet B L (proj y))
    (hproj_ineq : ∀ y x, IsInConstraintSet B L x →
                 ∑ i, (proj y i - x i) * (proj y i - y i) ≤ 0)
    (w_star : Fin N → ℝ) (hw_star : IsInConstraintSet B L w_star)
    (hw_star_opt : ∀ w, IsInConstraintSet B L w → quadObj Cov ret w_star ≤ quadObj Cov ret w)
    (w : Fin N → ℝ) (hw : IsInConstraintSet B L w) :
    let w_plus := proj (fun i => w i - η * gradObj Cov ret w i)
    quadObj Cov ret w_plus - quadObj Cov ret w_star ≤
      (1 / (2 * η)) * ((∑ i, (w i - w_star i) ^ 2) - (∑ i, (w_plus i - w_star i) ^ 2)) := by
  sorry
  -- TODO (Milestone 4, Step V4.1):
  -- 1. Expand `quadObj Σ μ_ret w_plus` using Lipschitz smoothness of ∇f:
  --      f(w₊) ≤ f(w) + ⟨∇f(w), w₊−w⟩ + (lMax/2)‖w₊−w‖²
  -- 2. Apply the projection inequality hproj_ineq at x = w_star to get:
  --      ⟨w₊ − (w − η∇f(w)), w_star − w₊⟩ ≥ 0
  --    which gives:  ⟨∇f(w), w_star−w₊⟩ ≤ (1/η)⟨w₊−w, w_star−w₊⟩
  -- 3. Use the identity  ⟨a−b, c−a⟩ = (‖b−c‖²−‖a−c‖²−‖a−b‖²)/2
  -- 4. Combine with ηlMax < 2 to absorb the ‖w₊−w‖² term.

/-! ### V4.2 — Convergence -/

/-- **V4.2** PGD converges to the unique global minimum `w*` in objective value.

    Given a PD covariance `Σ` and step size `η ∈ (0, 2/lMax)`, the iterates
    `wₖ₊₁ = Π_𝒞(wₖ − η ∇f(wₖ))` satisfy:

        f(wₖ) − f(w*) ≤ ‖w₀ − w*‖² / (2η k)   (O(1/k) convergence)

    In particular, for any `ε > 0` there exists `K` such that for all `k ≥ K`,
    `|f(wₖ) − f(w*)| < ε`.

    **Status**: `sorry`.  Full proof telescopes `pgd_descent_lemma` over `k` steps
    and uses convexity to bound `f(wₖ) − f(w*)` from the minimum in the sum. -/
theorem pgd_convergence
    (Cov : Matrix (Fin N) (Fin N) ℝ) (ret : Fin N → ℝ)
    (hCov : Cov.PosDef)
    (lMax : ℝ) (hlMax_pos : 0 < lMax)
    (hlMax_bound : ∀ w : Fin N → ℝ, w ⬝ᵥ (Cov *ᵥ w) ≤ lMax * (w ⬝ᵥ w))
    (η : ℝ) (hη_pos : 0 < η) (hη_bound : η * lMax < 2)
    (B L : ℝ)
    (proj : (Fin N → ℝ) → Fin N → ℝ)
    (hproj_feas : ∀ y, IsInConstraintSet B L (proj y))
    (hproj_ineq : ∀ y x, IsInConstraintSet B L x →
                 ∑ i, (proj y i - x i) * (proj y i - y i) ≤ 0)
    -- The iterate sequence satisfying the PGD recurrence
    (w : ℕ → Fin N → ℝ)
    (hw₀ : IsInConstraintSet B L (w 0))
    (hrec : ∀ k, w (k + 1) = proj (fun i => w k i - η * gradObj Cov ret (w k) i))
    (hfeas : ∀ k, IsInConstraintSet B L (w k))
    (w_star : Fin N → ℝ) (hw_star : IsInConstraintSet B L w_star)
    (hw_star_opt : ∀ v, IsInConstraintSet B L v → quadObj Cov ret w_star ≤ quadObj Cov ret v) :
    ∀ ε > 0, ∃ K : ℕ, ∀ k ≥ K,
      quadObj Cov ret (w k) - quadObj Cov ret w_star < ε := by
  sorry
  -- TODO (Milestone 4, Step V4.2):
  -- 1. Let D₀ := ∑ i, (w 0 i - w_star i)^2.
  -- 2. Sum pgd_descent_lemma from k = 0 to K-1 (using hrec and hfeas):
  --      K * (f(w_kMin) − f(w*)) ≤ D₀ / (2η)
  --    where w_kMin is the minimiser over the K iterates.
  -- 3. Since f is convex and f(w k) - f(w*) is non-increasing (from descent lemma),
  --      f(w k) - f(w*) ≤ D₀ / (2η k).
  -- 4. For ε > 0, choose K = ⌈D₀ / (2η ε)⌉ + 1.
  -- Key: step (3) uses strict descent from `pgd_descent_lemma`, not just convexity.

end OptimizationProofs
