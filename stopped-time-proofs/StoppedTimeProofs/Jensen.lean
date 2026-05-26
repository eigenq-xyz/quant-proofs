import StoppedTimeProofs.GeomExpectation
import Mathlib.Analysis.Convex.Function
import Mathlib.Analysis.MeanInequalities
import Mathlib.Analysis.SpecificLimits.Basic

/-!
# Jensen's Inequality for Geometric Weights

Jensen's inequality for the `geometricExpectation` operator.

Since `geomPMF p` defines a probability mass function on `ℕ` (by `geomPMF_tsum_eq_one`),
Jensen's inequality applies: for any convex `φ`,

`φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f)`

The strict version holds when `φ` is strictly convex and `f` is non-constant on the
support of `geomPMF p` (which is all of `ℕ` since `geomPMF p k > 0` for all `k`).

## Contents

- **G2.1** `jensen_geom_convex` — Jensen for convex `φ`
- **G2.2** `jensen_geom_strict_convex` — strict Jensen for strictly convex `φ`
  under a non-degeneracy hypothesis on `f`

## Proof strategy for G2.1

Define the N-th partial sum approximation:
  `E_N := (∑ k in Finset.range N, geomPMF p k * f k) / (∑ k in Finset.range N, geomPMF p k)`

For each N, the finite weights `geomPMF p k / S_N` are non-negative and sum to 1,
so `ConvexOn.map_sum_le` gives:
  `φ(E_N) ≤ (∑ k in Finset.range N, (geomPMF p k / S_N) * φ(f k))`
  `       = (∑ k in Finset.range N, geomPMF p k * φ(f k)) / S_N`

As N → ∞:
- `S_N → 1` by `geomPMF_tsum_eq_one`
- `∑ k in Finset.range N, geomPMF p k * f k → geometricExpectation p f` by summability (G1.5)
- `E_N → geometricExpectation p f`
- The RHS converges to `geometricExpectation p (φ ∘ f)`
- Continuity of `φ` (from convexity, via `ConvexOn.continuousOn`) gives `φ(E_N) → φ(...)`.

Alternatively, use `Pmf.toMeasure` to package `geomPMF p` as a `Pmf ℕ` and invoke
`MeasureTheory.inner_le_iff` or a discrete Jensen lemma once one is available in Mathlib.
Both paths are ~25–40 lines; the `Pmf` route is cleaner if the infrastructure exists.

## Proof strategy for G2.2

Strict Jensen follows from G2.1 plus: if `f k₁ ≠ f k₂` and `φ` is strictly convex,
then the finite Jensen inequality at the two indices `k₁, k₂` is strict, which
propagates to the tsum via `tsum_lt_tsum` or a similar monotone limit argument.
-/

namespace StoppedTimeProofs

/-! ### G2.1 — Jensen for convex φ -/

-- TODO: G2.1 — proof strategy outlined in module docstring above.
-- Estimated: ~30 lines using finite truncation + limit, or Pmf.toMeasure route.
-- Depends on: geomPMF_tsum_eq_one (G1.3), geometricExpectation_summable (G1.5),
--             ConvexOn.map_sum_le (Mathlib), continuity of convex functions.
-- lemma jensen_geom_convex {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
--     {f : ℕ → ℝ} (hf : ∃ C, ∀ k, ‖f k‖ ≤ C)
--     {φ : ℝ → ℝ} (hφ : ConvexOn ℝ Set.univ φ) :
--     φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f) := by
--   sorry

/-! ### G2.2 — Strict Jensen for strictly convex φ -/

-- TODO: G2.2 — follows from G2.1 plus strict convexity + non-degeneracy.
-- The non-degeneracy hypothesis `∃ k₁ k₂, f k₁ ≠ f k₂` ensures the finite truncation
-- at some N contains both k₁ and k₂, making the finite Jensen strict.
-- The strict inequality then passes to the limit since geomPMF p kᵢ > 0.
-- Depends on: G2.1, StrictConvexOn API in Mathlib (Mathlib.Analysis.Convex.StrictConvex).
-- lemma jensen_geom_strict_convex {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
--     {f : ℕ → ℝ} (hf : ∃ C, ∀ k, ‖f k‖ ≤ C)
--     {φ : ℝ → ℝ} (hφ : StrictConvexOn ℝ Set.univ φ)
--     (hnondegen : ∃ k₁ k₂, f k₁ ≠ f k₂) :
--     φ (geometricExpectation p f) < geometricExpectation p (φ ∘ f) := by
--   sorry

end StoppedTimeProofs
