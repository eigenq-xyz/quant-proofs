import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Data.Real.StarOrdered
import OptimizationProofs.ProblemDefs

/-!
# Quadratic Lemmas for PGD Convergence (Milestone 4 prerequisites)

Three bespoke lemmas needed for `pgd_descent_lemma` that are not directly
available in mathlib for the `Matrix.dotProduct` / `Matrix.mulVec` API:

- **Q1** `symmetric_bilin_form` — bilinear form symmetry for real symmetric matrices:
      `x ⬝ᵥ A *ᵥ y = y ⬝ᵥ A *ᵥ x` when `symmetric matrix `A`

- **Q2** `quadratic_identity` — exact second-order Taylor expansion of `quadObj`:
      `f(v) − f(u) = ⟨∇f(u), v−u⟩ + ½(v−u)ᵀCov(v−u)`

- **Q3** `polarization_identity` — dot-product polarization:
      `2 * (a ⬝ᵥ b) = (a ⬝ᵥ a) + (b ⬝ᵥ b) − ((a−b) ⬝ᵥ (a−b))`

All proofs are closed (0 sorry).  Mathlib provides the building blocks:
`Matrix.conjTranspose_eq_transpose_of_trivial`, `Matrix.dotProduct_transpose_mulVec`,
`Matrix.sub_dotProduct`, `Matrix.dotProduct_sub`, `Matrix.mulVec_sub`.
-/

open scoped BigOperators
open Matrix

namespace OptimizationProofs

variable {N : ℕ}

/-! ### Q1 — Bilinear form symmetry for real symmetric matrices -/

/-- **Q1** For a real symmetric matrix `A`, the bilinear form is symmetric:
    `x ⬝ᵥ A *ᵥ y = y ⬝ᵥ A *ᵥ x`.

    Proof: the symmetry hypothesis (mathlib calls it `A.IsHermitian`, meaning Aᵀ = A
    for real matrices) gives `Aᴴ = A`; since `Aᴴ = Aᵀ` over ℝ, we get `Aᵀ = A`.
    Then `dotProduct_transpose_mulVec : x ⬝ᵥ Aᵀ *ᵥ y = y ⬝ᵥ A *ᵥ x` gives the result. -/
theorem symmetric_bilin_form {A : Matrix (Fin N) (Fin N) ℝ} (hA : A.IsHermitian)
    (x y : Fin N → ℝ) : x ⬝ᵥ A *ᵥ y = y ⬝ᵥ A *ᵥ x := by
  -- For ℝ: Aᴴ = Aᵀ, so hA.eq (Aᴴ = A) gives Aᵀ = A
  conv_lhs => rw [show A = Aᵀ from by
    rw [← conjTranspose_eq_transpose_of_trivial A]; exact hA.eq.symm]
  exact dotProduct_transpose_mulVec A x y

/-! ### Q2 — Exact quadratic expansion of `quadObj` -/

-- Helper: gradient sum as dotProduct
private theorem grad_sum_eq_dotProduct {Cov : Matrix (Fin N) (Fin N) ℝ} (hCov : Cov.IsHermitian)
    (ret u v : Fin N → ℝ) :
    ∑ i, ((Cov *ᵥ u) i - ret i) * (v i - u i) =
    u ⬝ᵥ Cov *ᵥ v - u ⬝ᵥ Cov *ᵥ u - (ret ⬝ᵥ v - ret ⬝ᵥ u) := by
  -- Rewrite the sum as a single dotProduct (Cov *ᵥ u - ret) ⬝ᵥ (v - u)
  have hform : ∑ i : Fin N, ((Cov *ᵥ u) i - ret i) * (v i - u i) =
      (Cov *ᵥ u - ret) ⬝ᵥ (v - u) := by
    simp [dotProduct, Pi.sub_apply]
  rw [hform, sub_dotProduct, dotProduct_sub, dotProduct_sub]
  -- (Cov *ᵥ u) ⬝ᵥ v = u ⬝ᵥ Cov *ᵥ v  (by dotProduct_comm + symmetric_bilin_form)
  rw [show (Cov *ᵥ u) ⬝ᵥ v = u ⬝ᵥ Cov *ᵥ v from by
    rw [dotProduct_comm, symmetric_bilin_form hCov v u]]
  rw [show (Cov *ᵥ u) ⬝ᵥ u = u ⬝ᵥ Cov *ᵥ u from by
    rw [dotProduct_comm, symmetric_bilin_form hCov u u]]

-- Helper: quadratic term expansion
private theorem quad_term_eq {Cov : Matrix (Fin N) (Fin N) ℝ} (hCov : Cov.IsHermitian)
    (u v : Fin N → ℝ) :
    (fun i => v i - u i) ⬝ᵥ Cov *ᵥ (fun i => v i - u i) =
    v ⬝ᵥ Cov *ᵥ v - 2 * (v ⬝ᵥ Cov *ᵥ u) + u ⬝ᵥ Cov *ᵥ u := by
  -- (v - u)ᵀCov(v - u) = vᵀCov v - 2 vᵀCov u + uᵀCov u  (by linearity + symmetry)
  rw [show (fun i => v i - u i) = v - u from rfl,
      mulVec_sub, dotProduct_sub, sub_dotProduct, sub_dotProduct]
  linarith [symmetric_bilin_form hCov v u]

/-- **Q2** Exact second-order Taylor identity for the quadratic objective:

    `quadObj Cov ret v − quadObj Cov ret u = ⟨∇f(u), v−u⟩ + ½(v−u)ᵀCov(v−u)`

    where `⟨∇f(u), d⟩ = ∑ i, gradObj Cov ret u i * d i`.

    This is an **equality** (not an inequality) — it holds exactly for all quadratic `f`,
    because `f` has no terms of degree ≥ 3.

    **Consequence**: since `Cov.PosSemidef` implies `(v−u)ᵀCov(v−u) ≥ 0`, we get the
    convexity bound `f(u) − f(v) ≤ ⟨∇f(u), u−v⟩` (see `quadratic_convexity`). -/
theorem quadratic_identity {Cov : Matrix (Fin N) (Fin N) ℝ} (hCov : Cov.IsHermitian)
    (ret u v : Fin N → ℝ) :
    quadObj Cov ret v - quadObj Cov ret u =
      (∑ i, gradObj Cov ret u i * (v i - u i)) +
      (1 / 2) * ((fun i => v i - u i) ⬝ᵥ Cov *ᵥ (fun i => v i - u i)) := by
  simp only [quadObj, gradObj]
  rw [quad_term_eq hCov u v, grad_sum_eq_dotProduct hCov ret u v]
  -- After rewrites: 1/2·A - R - (1/2·B - S) = (C - B - (R-S)) + 1/2·(A - 2D + B)
  -- where A=v⬝Cov·v, B=u⬝Cov·u, C=u⬝Cov·v, D=v⬝Cov·u, R=ret⬝v, S=ret⬝u
  -- Symmetry C = D closes by linarith
  linarith [symmetric_bilin_form hCov v u]

/-- **Q2b** Convexity bound for the quadratic objective:

    `quadObj Cov ret u − quadObj Cov ret v ≤ ∑ i, gradObj Cov ret u i * (u i − v i)`

    Follows from `quadratic_identity` plus `Cov.PosSemidef` (the quadratic
    remainder term `½(u−v)ᵀCov(u−v) ≥ 0` is non-positive and can be dropped). -/
theorem quadratic_convexity {Cov : Matrix (Fin N) (Fin N) ℝ} (hCov : Cov.PosSemidef)
    (ret u v : Fin N → ℝ) :
    quadObj Cov ret u - quadObj Cov ret v ≤
      ∑ i, gradObj Cov ret u i * (u i - v i) := by
  -- From quadratic_identity (applied to v, u):
  -- f(v) - f(u) = ⟨∇f(u), v-u⟩ + ½(v-u)ᵀCov(v-u)
  have hid := quadratic_identity hCov.1 ret u v
  -- ½(v-u)ᵀCov(v-u) ≥ 0 since Cov is PSD
  have hquad_nn : 0 ≤ (fun i => v i - u i) ⬝ᵥ Cov *ᵥ (fun i => v i - u i) :=
    hCov.dotProduct_mulVec_nonneg _
  -- ⟨∇f(u), v-u⟩ = -⟨∇f(u), u-v⟩
  have hflip : ∑ i, gradObj Cov ret u i * (u i - v i) =
      -(∑ i, gradObj Cov ret u i * (v i - u i)) := by
    rw [← Finset.sum_neg_distrib]
    apply Finset.sum_congr rfl; intro i _; ring
  linarith [hid, hquad_nn]

/-! ### Q3 — Dot-product polarization -/

/-- **Q3** The polarization identity for `Matrix.dotProduct`:

    `2 * (a ⬝ᵥ b) = (a ⬝ᵥ a) + (b ⬝ᵥ b) − ((a − b) ⬝ᵥ (a − b))`

    This is pure algebra: `aᵢ² + bᵢ² − (aᵢ−bᵢ)² = 2aᵢbᵢ`, summed over `i`.

    Used in `pgd_descent_lemma` to convert the inner product `⟨w₊−w*, w₊−w⟩`
    into squared-norm differences for the telescoping bound. -/
theorem polarization_identity (a b : Fin N → ℝ) :
    2 * (a ⬝ᵥ b) = (a ⬝ᵥ a) + (b ⬝ᵥ b) - ((fun i => a i - b i) ⬝ᵥ (fun i => a i - b i)) := by
  simp only [dotProduct]
  -- LHS: 2 * ∑ aᵢbᵢ = ∑ 2aᵢbᵢ  (Finset.mul_sum)
  rw [Finset.mul_sum]
  -- RHS: combine three sums into one: ∑ A + ∑ B - ∑ C = ∑ (A + B - C)
  rw [← Finset.sum_add_distrib, ← Finset.sum_sub_distrib]
  -- Now LHS = RHS = ∑ 2aᵢbᵢ pointwise via ring
  apply Finset.sum_congr rfl; intro i _; ring

end OptimizationProofs
