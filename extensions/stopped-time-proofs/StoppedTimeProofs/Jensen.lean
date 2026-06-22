import StoppedTimeProofs.GeomExpectation
import Mathlib.Analysis.Convex.Function
import Mathlib.Analysis.MeanInequalities
import Mathlib.Analysis.SpecificLimits.Basic
import Mathlib.Topology.Algebra.InfiniteSum.Real

/-!
# Jensen's Inequality for Geometric Weights

Jensen's inequality for the `geometricExpectation` operator.

Since `geomPMF p` defines a probability mass function on `ℕ` (by `geomPMF_tsum_eq_one`),
Jensen's inequality applies: for any convex `φ`,

`φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f)`

The strict version holds when `φ` is strictly convex and `f` is non-constant on the
support of `geomPMF p` (which is all of `ℕ` since `geomPMF p k > 0` for all `k`).

## Contents

- **G2.0** `geomPMF_pos` — strict positivity of `geomPMF p k` for `0 < p < 1`
- **G2.1** `geometricExpectation_strict_mono` — strict monotonicity under pointwise
  strict domination at one index

## Proof strategy for G2.1

`geometricExpectation p g − geometricExpectation p f = ∑' k, geomPMF p k * (g k − f k)`.
The term at `k₀` is `geomPMF p k₀ * (g k₀ − f k₀) > 0` (from `geomPMF_pos` and `hlt`).
All other terms are ≥ 0 (from `hfg` and `geomPMF_nonneg`). So the tsum is positive by
`Summable.tsum_lt_tsum_of_nonneg`.

## Note

G2.2 (abstract Jensen for convex φ) and the original G2.1/G2.2 stubs are superseded
by the targeted `geometricExpectation_strict_mono` which is all that
`InversePerpCorrection.lean` requires.
-/

namespace StoppedTimeProofs

open BigOperators

/-! ### G2.0 — Strict positivity of geomPMF -/

/-- **G2.0** `geomPMF p k > 0` for `0 < p < 1`.

Both factors are strictly positive: `(1 - p) ^ k > 0` since `0 < 1 - p`,
and `p > 0` from `hp0`. -/
lemma geomPMF_pos {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1) (k : ℕ) : 0 < geomPMF p k :=
  mul_pos (pow_pos (by linarith : (0 : ℝ) < 1 - p) k) hp0

/-! ### G2.1 — Strict monotonicity of geometric expectation -/

/-- **G2.1** The geometric expectation is strictly monotone: if `f k ≤ g k` for all `k`
and `f k₀ < g k₀` for some `k₀`, then `geometricExpectation p f < geometricExpectation p g`.

**Proof:** The difference is `∑' k, geomPMF p k * (g k - f k)`. All summands are
non-negative (geomPMF ≥ 0 and g ≥ f pointwise), and the summand at `k₀` is strictly
positive (geomPMF p k₀ > 0 by `geomPMF_pos` and g k₀ > f k₀). The result follows from
`Summable.tsum_lt_tsum_of_nonneg`. -/
lemma geometricExpectation_strict_mono {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
    {f g : ℕ → ℝ}
    (hfg : ∀ k, f k ≤ g k)
    (k₀ : ℕ) (hlt : f k₀ < g k₀)
    (hf : ∃ C, ∀ k, ‖f k‖ ≤ C)
    (hg : ∃ C, ∀ k, ‖g k‖ ≤ C) :
    geometricExpectation p f < geometricExpectation p g := by
  simp only [geometricExpectation]
  have hf_sum := geometricExpectation_summable hp0 hp1 hf
  have hg_sum := geometricExpectation_summable hp0 hp1 hg
  -- Summability of geomPMF p k * (g k - f k)
  have hdiff_bdd : ∃ C, ∀ k, ‖g k - f k‖ ≤ C := by
    obtain ⟨Cf, hCf⟩ := hf; obtain ⟨Cg, hCg⟩ := hg
    exact ⟨Cg + Cf, fun k => (norm_sub_le _ _).trans (add_le_add (hCg k) (hCf k))⟩
  have hdiff_sum : Summable (fun k => geomPMF p k * (g k - f k)) :=
    geometricExpectation_summable hp0 hp1 hdiff_bdd
  -- Rewrite the goal using the difference tsum
  suffices h : 0 < ∑' k, geomPMF p k * g k - ∑' k, geomPMF p k * f k by linarith
  rw [← hg_sum.tsum_sub hf_sum]
  -- Simplify geomPMF p k * g k - geomPMF p k * f k = geomPMF p k * (g k - f k)
  have hrw : ∀ k, geomPMF p k * g k - geomPMF p k * f k = geomPMF p k * (g k - f k) :=
    fun k => by ring
  simp_rw [hrw]
  -- Apply tsum_lt_tsum_of_nonneg with lower bound 0 and strict index k₀
  rw [show (0 : ℝ) = ∑' (_ : ℕ), (0 : ℝ) from tsum_zero.symm]
  exact Summable.tsum_lt_tsum_of_nonneg
    (i := k₀)
    (fun _ => le_refl 0)
    (fun b => mul_nonneg (geomPMF_nonneg hp0 hp1 b) (sub_nonneg.mpr (hfg b)))
    (mul_pos (geomPMF_pos hp0 hp1 k₀) (sub_pos.mpr hlt))
    hdiff_sum

end StoppedTimeProofs
