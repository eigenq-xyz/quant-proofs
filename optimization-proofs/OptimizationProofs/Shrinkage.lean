import Mathlib.LinearAlgebra.Matrix.PosDef
-- StarOrderedRing ℝ (for Matrix.PosDef.smul and Matrix.PosSemidef.smul)
import Mathlib.Data.Real.StarOrdered
-- StarModule ℝ ℝ (for Matrix.IsHermitian.smul and Matrix.conjTranspose_smul)
import Mathlib.Analysis.RCLike.Basic
-- PosSMulStrictMono ℝ ℝ (for Matrix.PosDef.smul via PosMulStrictMono.toPosSMulStrictMono)
import Mathlib.Algebra.Order.Module.Defs
import OptimizationProofs.ProblemDefs

/-!
# Ledoit-Wolf Shrinkage: Positive Definiteness (Milestone 2)

Formally verifies that the Ledoit-Wolf shrinkage estimator always produces a
strictly positive definite covariance matrix, eliminating Cholesky crashes in
numerical solvers when the sample covariance is rank-deficient.

## Main theorems

- **S2.1** `shrinkage_isHermitian` — `Σ*(δ)` is symmetric for any symmetric `S`
- **S2.2** `shrinkage_psd` — `Σ*(δ)` is strictly positive definite when:
  - `S.PosSemidef` (sample covariance is PSD)
  - `0 < Tr(S)` (non-degenerate sample; at least one nonzero eigenvalue)
  - `0 < δ ≤ 1` (strictly positive shrinkage intensity)

## Proof strategy

Write `Σ*(δ) = (δc) · I + (1−δ) · S` where `c = Tr(S)/N > 0`.

- `(δc) · I` is **strictly PD**: `I` is PD; scaling by `δc > 0` preserves PD
  (Theorem `Matrix.PosDef.smul`).
- `(1−δ) · S` is **PSD**: `S` is PSD; scaling by `1−δ ≥ 0` preserves PSD
  (Theorem `Matrix.PosSemidef.smul`).
- **PD + PSD = PD** by `Matrix.PosDef.add_posSemidef`.

This is essentially Weyl's monotonicity inequality for eigenvalues:
`λ_min(Σ*) ≥ λ_min((δc)I) + λ_min((1−δ)S) = δc + 0 > 0`.
-/

open Matrix

namespace OptimizationProofs

variable {N : ℕ}

/-! ### S2.1 — Symmetry of the shrinkage estimator -/

/-- **S2.1** The Ledoit-Wolf shrinkage matrix is symmetric (Hermitian).

    The identity matrix `I` is Hermitian; scalar multiples and sums of Hermitian
    matrices are Hermitian.  Hence `Σ*(δ) = δcI + (1−δ)S` is Hermitian whenever
    `S` is, regardless of `δ`. -/
theorem shrinkage_isHermitian {S : Matrix (Fin N) (Fin N) ℝ}
    (hS : S.IsHermitian) (δ : ℝ) :
    (ledoitWolfShrinkage S δ).IsHermitian := by
  unfold ledoitWolfShrinkage
  apply Matrix.IsHermitian.add
  · -- δ • (c • I) is Hermitian: I is Hermitian, preserved under two scalar multiples
    exact (Matrix.isHermitian_one.smul (star_trivial _)).smul (star_trivial _)
  · -- (1-δ) • S is Hermitian: S is Hermitian, preserved under scalar multiple
    exact hS.smul (star_trivial _)

/-! ### S2.2 — Strict positive definiteness -/

/-- **S2.2** The Ledoit-Wolf shrinkage estimator is strictly positive definite.

    Formally: if `S.PosSemidef`, `0 < Matrix.trace S`, and `0 < δ ≤ 1`, then
    `Σ*(δ) = δ(Tr(S)/N)I + (1−δ)S` satisfies `(ledoitWolfShrinkage S δ).PosDef`.

    This theorem is the formal proof that Ledoit-Wolf shrinkage completely eliminates
    Cholesky crashes: the output covariance is always invertible, even when the sample
    covariance `S` is singular from a short lookback window (`T < N` observations). -/
theorem shrinkage_psd [NeZero N] {S : Matrix (Fin N) (Fin N) ℝ}
    (hS : S.PosSemidef)
    (htr : 0 < Matrix.trace S)
    {δ : ℝ} (hδ_pos : 0 < δ) (hδ_le : δ ≤ 1) :
    (ledoitWolfShrinkage S δ).PosDef := by
  unfold ledoitWolfShrinkage
  -- Arithmetic setup
  have hN_pos : (0 : ℝ) < ↑N := Nat.cast_pos.mpr (NeZero.pos N)
  have hc_pos : 0 < Matrix.trace S / ↑N := div_pos htr hN_pos
  have h1δ_nn : 0 ≤ 1 - δ := by linarith
  -- Merge the two scalar multiples: δ • (c • I) = (δ * c) • I
  rw [smul_smul]
  -- (δc)•I is PD and (1-δ)•S is PSD, so their sum is PD
  exact Matrix.PosDef.add_posSemidef
    (Matrix.PosDef.one.smul (mul_pos hδ_pos hc_pos))
    (hS.smul h1δ_nn)

end OptimizationProofs
