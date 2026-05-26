import StoppedTimeProofs.GeomExpectation
import Mathlib.Analysis.Convex.Function
import Mathlib.Analysis.MeanInequalities

/-!
# Jensen's Inequality for Geometric Weights

Jensen's inequality for the `geometricExpectation` operator.

Since `geomPMF p` defines a probability measure on `ℕ` (by `geomPMF_tsum_eq_one`),
Jensen's inequality applies: for any convex `φ`,

`φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f)`

The strict version holds when `φ` is strictly convex and `f` is not constant
on the support of `geomPMF p`.

## Contents

- **G2.1** `jensen_geom_convex` — Jensen for convex `φ`
- **G2.2** `jensen_geom_strict_convex` — strict Jensen for strictly convex `φ`
  under a non-degeneracy hypothesis on `f`

## Proof strategy

`geomPMF_tsum_eq_one` establishes that the weights sum to 1. The convex Jensen
inequality follows from the definition of convexity applied to finite partial sums,
then passage to the limit using `geometricExpectation_summable` and monotone
convergence. If a Mathlib lemma for Jensen over `tsum` with a PMF is available
(check `MeasureTheory.inner_le_iff` or discrete integral Jensen), use it; otherwise
prove directly (~25 lines).
-/

namespace StoppedTimeProofs

/-! ### G2.1 — Jensen for convex φ -/

-- TODO: G2.1
-- lemma jensen_geom_convex (hp0 : 0 < p) (hp1 : p < 1)
--     (hf : ∃ C, ∀ k, ‖f k‖ ≤ C)
--     (hφ : ConvexOn ℝ Set.univ φ) :
--     φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f) := by
--   sorry

/-! ### G2.2 — Strict Jensen for strictly convex φ -/

-- TODO: G2.2
-- lemma jensen_geom_strict_convex (hp0 : 0 < p) (hp1 : p < 1)
--     (hf : ∃ C, ∀ k, ‖f k‖ ≤ C)
--     (hφ : StrictConvexOn ℝ Set.univ φ)
--     (hnondegen : ∃ k₁ k₂, f k₁ ≠ f k₂) :
--     φ (geometricExpectation p f) < geometricExpectation p (φ ∘ f) := by
--   sorry

end StoppedTimeProofs
