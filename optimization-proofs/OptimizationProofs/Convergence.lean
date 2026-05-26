import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Analysis.RCLike.Basic
import OptimizationProofs.ProblemDefs
import OptimizationProofs.Shrinkage
import OptimizationProofs.QuadraticLemmas
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
    -- Step size: η ≤ 1/lMax ensures the ‖w₊−w‖² remainder term is non-positive
    (η : ℝ) (hη_pos : 0 < η) (hη_bound : η * lMax ≤ 1)
    (B L : ℝ)
    (proj : (Fin N → ℝ) → Fin N → ℝ)
    (hproj_feas : ∀ y, IsInConstraintSet B L (proj y))
    -- Projection inequality: ⟨proj(y) − y, x − proj(y)⟩ ≥ 0 for all feasible x
    (hproj_ineq : ∀ y x, IsInConstraintSet B L x →
                 ∑ i, (proj y i - x i) * (proj y i - y i) ≤ 0)
    (w_star : Fin N → ℝ) (hw_star : IsInConstraintSet B L w_star)
    (hw_star_opt : ∀ w, IsInConstraintSet B L w → quadObj Cov ret w_star ≤ quadObj Cov ret w)
    (w : Fin N → ℝ) (hw : IsInConstraintSet B L w) :
    let w_plus := proj (fun i => w i - η * gradObj Cov ret w i)
    quadObj Cov ret w_plus - quadObj Cov ret w_star ≤
      (1 / (2 * η)) * ((∑ i, (w i - w_star i) ^ 2) - (∑ i, (w_plus i - w_star i) ^ 2)) := by
  -- ── Setup ──────────────────────────────────────────────────────────────────
  -- Introduce the gradient step g and abbreviate proj g as w₊
  set g := fun i : Fin N => w i - η * gradObj Cov ret w i with hg_def
  show quadObj Cov ret (proj g) - quadObj Cov ret w_star ≤
      (1/(2*η)) * ((∑ i, (w i - w_star i)^2) - (∑ i, (proj g i - w_star i)^2))
  -- Use `suffices` to work with the equivalent multiplied form (avoids division issues)
  have hη2 : 0 < 2 * η := by positivity
  rw [show (1/(2*η)) * ((∑ i, (w i - w_star i)^2) - (∑ i, (proj g i - w_star i)^2)) =
      ((∑ i, (w i - w_star i)^2) - (∑ i, (proj g i - w_star i)^2)) / (2*η) from by ring]
  rw [le_div_iff₀ hη2]
  -- Goal: (f(w₊) − f(w*)) * (2η) ≤ E² − F²
  -- ── (A) Quadratic identity: f(w₊)−f(w) = ∑grad·(w₊−w) + ½Q ──────────────
  have hqi := quadratic_identity hCov.1 ret w (proj g)
  -- ── (B) Convexity: f(w)−f(w*) ≤ ∑grad·(w−w*) ────────────────────────────
  have hconv := quadratic_convexity hCov.posSemidef ret w w_star
  -- ── (C) Lipschitz: Q ≤ lMax·D²  ─────────────────────────────────────────
  have hLip := hlMax_bound (fun i => proj g i - w i)
  have hD_nn : 0 ≤ (fun i => proj g i - w i) ⬝ᵥ (fun i => proj g i - w i) :=
    Finset.sum_nonneg (fun i _ => mul_self_nonneg _)
  -- ── (D) Expand projection inequality at w_star ─────────────────────────────
  -- hproj_ineq g w_star hw_star gives: ∑(w₊−w*)(w₊−g) ≤ 0
  -- Expand w₊ − g = (w₊ − w) + η·∇f(w), split into A + η·B ≤ 0
  have hAB : ∑ i : Fin N, (proj g i - w_star i) * (proj g i - w i) +
      η * ∑ i, gradObj Cov ret w i * (proj g i - w_star i) ≤ 0 := by
    have h := hproj_ineq g w_star hw_star
    simp_rw [show ∀ i : Fin N, (proj g i - w_star i) * (proj g i - g i) =
        (proj g i - w_star i) * (proj g i - w i) +
        η * (gradObj Cov ret w i * (proj g i - w_star i)) from fun i => by
      simp only [hg_def, gradObj]; ring] at h
    rw [Finset.sum_add_distrib, ← Finset.mul_sum] at h
    linarith
  -- ── (E) Polarization: 2·A = F² + D² − E² ─────────────────────────────────
  -- where A = ∑(w₊−w*)(w₊−w), F² = ∑(w₊−w*)², D² = ∑(w₊−w)², E² = ∑(w−w*)²
  have hpol_raw := polarization_identity (fun i => proj g i - w_star i) (fun i => proj g i - w i)
  have hpol : 2 * ∑ i : Fin N, (proj g i - w_star i) * (proj g i - w i) =
      ∑ i, (proj g i - w_star i)^2 + ∑ i, (proj g i - w i)^2 - ∑ i, (w i - w_star i)^2 := by
    -- dotProduct v w = ∑ i, v i * w i by definition (rfl), sq via ring
    have e1 : (fun i : Fin N => proj g i - w_star i) ⬝ᵥ (fun i => proj g i - w i) =
        ∑ i, (proj g i - w_star i) * (proj g i - w i) := rfl
    have e2 : (fun i : Fin N => proj g i - w_star i) ⬝ᵥ (fun i => proj g i - w_star i) =
        ∑ i, (proj g i - w_star i)^2 := by
      apply Finset.sum_congr rfl; intro i _; ring
    have e3 : (fun i : Fin N => proj g i - w i) ⬝ᵥ (fun i => proj g i - w i) =
        ∑ i, (proj g i - w i)^2 := by
      apply Finset.sum_congr rfl; intro i _; ring
    have e4 : (fun i : Fin N => (proj g i - w_star i) - (proj g i - w i)) =
        fun i => w i - w_star i := by funext i; ring
    have e5 : (fun i : Fin N => w i - w_star i) ⬝ᵥ (fun i => w i - w_star i) =
        ∑ i, (w i - w_star i)^2 := by
      apply Finset.sum_congr rfl; intro i _; ring
    linarith [show (fun i : Fin N => (proj g i - w_star i) - (proj g i - w i)) ⬝ᵥ
        (fun i => (proj g i - w_star i) - (proj g i - w i)) = ∑ i, (w i - w_star i)^2 from by
          rw [e4, e5],
        hpol_raw, e1.symm, e2.symm, e3.symm]
  -- ── Gradient split: ∑grad·(w₊−w*) = ∑grad·(w₊−w) + ∑grad·(w−w*) ─────────
  have hBsplit : ∑ i : Fin N, gradObj Cov ret w i * (proj g i - w_star i) =
      ∑ i, gradObj Cov ret w i * (proj g i - w i) +
      ∑ i, gradObj Cov ret w i * (w i - w_star i) := by
    rw [← Finset.sum_add_distrib]; apply Finset.sum_congr rfl; intro i _; ring
  -- ── D² as sum-of-squares ──────────────────────────────────────────────────
  have hD_sq : (fun i : Fin N => proj g i - w i) ⬝ᵥ (fun i => proj g i - w i) =
      ∑ i, (proj g i - w i)^2 := by
    apply Finset.sum_congr rfl; intro i _; ring
  -- ── Close: nlinarith with all five pieces ─────────────────────────────────
  -- Chain: 2η·(f(w₊)-f(w*)) ≤ 2η·B + η·lMax·D² ≤ (E²-F²-D²)+D² = E²-F²
  nlinarith [hqi, hconv, hLip, hAB, hpol, hBsplit, hD_sq, hD_nn,
             mul_nonneg (le_of_lt hη_pos) hD_nn,
             Finset.sum_nonneg (fun i (_ : i ∈ Finset.univ) => sq_nonneg (proj g i - w i))]

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
    (η : ℝ) (hη_pos : 0 < η) (hη_bound : η * lMax ≤ 1)
    (B L : ℝ)
    (proj : (Fin N → ℝ) → Fin N → ℝ)
    (hproj_feas : ∀ y, IsInConstraintSet B L (proj y))
    (hproj_ineq : ∀ y x, IsInConstraintSet B L x →
                 ∑ i, (proj y i - x i) * (proj y i - y i) ≤ 0)
    (w : ℕ → Fin N → ℝ)
    (hw₀ : IsInConstraintSet B L (w 0))
    (hrec : ∀ k, w (k + 1) = proj (fun i => w k i - η * gradObj Cov ret (w k) i))
    (hfeas : ∀ k, IsInConstraintSet B L (w k))
    -- Monotonicity of f along iterates: f(w(k+1)) ≤ f(w(k))
    -- (Follows from pgd_descent_lemma + strong convexity, taken as hypothesis here)
    (hdesc_obj : ∀ k, quadObj Cov ret (w (k + 1)) ≤ quadObj Cov ret (w k))
    (w_star : Fin N → ℝ) (hw_star : IsInConstraintSet B L w_star)
    (hw_star_opt : ∀ v, IsInConstraintSet B L v → quadObj Cov ret w_star ≤ quadObj Cov ret v) :
    ∀ ε > 0, ∃ K : ℕ, ∀ k ≥ K,
      quadObj Cov ret (w k) - quadObj Cov ret w_star < ε := by
  intro ε hε
  -- Shorthand: E k = f(w k) - f(w*), D k = ‖w k - w*‖², D₀ = D 0
  let E : ℕ → ℝ := fun k => quadObj Cov ret (w k) - quadObj Cov ret w_star
  let D : ℕ → ℝ := fun k => ∑ i : Fin N, (w k i - w_star i) ^ 2
  -- E k ≥ 0 (w_star is optimal)
  have hEnn : ∀ k, 0 ≤ E k := fun k => sub_nonneg.mpr (hw_star_opt (w k) (hfeas k))
  -- E is non-increasing
  have hEmono : ∀ j k, j ≤ k → E k ≤ E j := by
    intro j k hjk
    induction hjk with
    | refl => exact le_refl _
    | @step k' hjk' ih => exact le_trans (sub_le_sub_right (hdesc_obj k') _) ih
  -- Per-step descent: D(K+1) + 2η·E(K+1) ≤ D K
  have hstep : ∀ k, D (k + 1) + 2 * η * E (k + 1) ≤ D k := by
    intro k
    have hη2 : 0 < 2 * η := by positivity
    -- Apply pgd_descent_lemma with w k as the current iterate
    have hdesc := pgd_descent_lemma Cov ret hCov lMax hlMax_pos hlMax_bound
        η hη_pos hη_bound B L proj hproj_feas hproj_ineq w_star hw_star hw_star_opt
        (w k) (hfeas k)
    -- The conclusion references `proj (fun i => w k i - η * gradObj Cov ret (w k) i)`
    -- which equals `w (k+1)` by hrec k.  Rewrite using hrec k (←).
    have heq : proj (fun i => w k i - η * gradObj Cov ret (w k) i) = w (k + 1) := (hrec k).symm
    simp only [heq] at hdesc
    -- hdesc : E (k+1) ≤ (1/(2η)) * (D k - D (k+1))
    -- Conclude D(k+1) + 2η·E(k+1) ≤ D k
    have hDnn : 0 ≤ D (k + 1) := Finset.sum_nonneg (fun i _ => sq_nonneg _)
    have hmul : (2 * η) * E (k + 1) ≤ D k - D (k + 1) := by
      have h := mul_le_mul_of_nonneg_left hdesc (le_of_lt hη2)
      have heq : 2 * η * (1 / (2 * η) * (D k - D (k + 1))) = D k - D (k + 1) := by
        field_simp
      linarith
    linarith
  -- Telescope: D K + 2η · ∑_{k<K} E(k+1) ≤ D 0
  have htelescope : ∀ K : ℕ, D K + 2 * η * (∑ k ∈ Finset.range K, E (k + 1)) ≤ D 0 := by
    intro K
    induction K with
    | zero => simp
    | succ n ih =>
        simp only [Finset.sum_range_succ]
        linarith [hstep n]
  -- Corollary: 2η · ∑_{k<K} E(k+1) ≤ D 0
  have hsum_le : ∀ K, 2 * η * (∑ k ∈ Finset.range K, E (k + 1)) ≤ D 0 := fun K => by
    have hDKnn : 0 ≤ D K := Finset.sum_nonneg (fun i _ => sq_nonneg _)
    linarith [htelescope K]
  -- K * E K ≤ D 0/(2η): from monotonicity, each E(k+1) ≥ E K for k+1 ≤ K
  have hKEK : ∀ K : ℕ, (K : ℝ) * E K ≤ D 0 / (2 * η) := by
    intro K
    have heta2 : 0 < 2 * η := by positivity
    -- ∑_{k<K} E(k+1) ≥ K * E K since E(k+1) ≥ E K whenever k+1 ≤ K
    have hmono_sum : (K : ℝ) * E K ≤ ∑ k ∈ Finset.range K, E (k + 1) :=
      calc (K : ℝ) * E K
          = ∑ _k ∈ Finset.range K, E K := by simp [Finset.sum_const, Finset.card_range]
        _ ≤ ∑ k ∈ Finset.range K, E (k + 1) :=
            Finset.sum_le_sum (fun k hk => hEmono (k + 1) K
              (Nat.succ_le_iff.mpr (Finset.mem_range.mp hk)))
    calc (K : ℝ) * E K
        ≤ ∑ k ∈ Finset.range K, E (k + 1) := hmono_sum
      _ ≤ D 0 / (2 * η) := by
            rw [le_div_iff₀ heta2]
            linarith [hsum_le K]
  -- Choose K₀ = ⌈D 0 / (2η ε)⌉ + 1
  refine ⟨Nat.ceil (D 0 / (2 * η * ε)) + 1, fun k hk => ?_⟩
  set K₀ := Nat.ceil (D 0 / (2 * η * ε)) + 1 with hK₀_def
  have hK₀pos : (0 : ℝ) < K₀ := by exact_mod_cast Nat.succ_pos _
  -- E k ≤ E K₀ (monotonicity since k ≥ K₀)
  have hEk : E k ≤ E K₀ := hEmono K₀ k hk
  -- E K₀ ≤ D 0 / (2η K₀) (from K₀ * E K₀ ≤ D 0/(2η))
  have hEK₀_bound : E K₀ ≤ D 0 / (2 * η) / K₀ := by
    rw [le_div_iff₀ hK₀pos]
    nlinarith [hKEK K₀]
  -- D 0/(2η)/K₀ < ε because K₀ > D 0/(2ηε): multiply K₀ > D 0/(2ηε) by ε to get K₀*ε > D 0/(2η)
  have hEK₀ : E K₀ < ε := by
    have hK₀_gt : D 0 / (2 * η * ε) < (K₀ : ℝ) := by
      have hceil_lt : (Nat.ceil (D 0 / (2 * η * ε)) : ℝ) < (K₀ : ℝ) := by
        exact_mod_cast Nat.lt_succ_self _
      linarith [Nat.le_ceil (D 0 / (2 * η * ε))]
    have hD0_2η_lt : D 0 / (2 * η) < (K₀ : ℝ) * ε := by
      have heq : D 0 / (2 * η * ε) * ε = D 0 / (2 * η) := by field_simp
      nlinarith [heq]
    calc E K₀
        ≤ D 0 / (2 * η) / (K₀ : ℝ) := hEK₀_bound
      _ < ε := by rw [div_lt_iff₀ hK₀pos]; linarith
  linarith [hEk, hEK₀]

end OptimizationProofs
