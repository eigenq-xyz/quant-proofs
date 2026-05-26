import StoppedTimeProofs.GeomPMF
import Mathlib.Topology.Algebra.InfiniteSum.Basic

/-!
# Geometric Expectation

`geometricExpectation p f` is the probability-weighted average of `f : ℕ → ℝ`
under the geometric distribution with parameter `p`.

$$\mathrm{geometricExpectation}(p, f) = \sum_{k=0}^\infty (1-p)^k \cdot p \cdot f(k)$$

For `0 < p < 1` and bounded `f`, this series converges (proved in
`geometricExpectation_summable`). By `geomPMF_tsum_eq_one`, the weights sum to 1,
so `geometricExpectation` is a genuine expectation operator.

## Contents

- **G1.4** `geometricExpectation` — definition
- **G1.5** `geometricExpectation_summable` — convergence for bounded `f`
- **G1.6** `geometricExpectation_unroll` — one-step recursion:
  `geometricExpectation p f = p * f 0 + (1-p) * geometricExpectation p (fun k => f (k+1))`
- **G1.7** `geometricExpectation_const` — `geometricExpectation p (fun _ => c) = c`
- **G1.8** `geometricExpectation_mono` — monotonicity in `f`

## Mathlib touchpoints

- `tsum_eq_zero_add` — splits `∑' k, f k` into `f 0 + ∑' k, f (k+1)`
- `Summable.of_norm_bounded` — comparison test for series convergence
-/

namespace StoppedTimeProofs

open BigOperators

/-! ### G1.4 — Definition -/

/-- **G1.4** The geometric expectation of `f : ℕ → ℝ` with parameter `p`.

This is the expectation of `f` under a geometric random variable with success
probability `p`:

`geometricExpectation p f = ∑' k, geomPMF p k * f k`

In the perpetual futures context, `f k` is typically `E^Q[S_k]` — the risk-neutral
expectation of the spot price at funding date `k` — and `p = κ/(1+r)`. -/
noncomputable def geometricExpectation (p : ℝ) (f : ℕ → ℝ) : ℝ :=
  ∑' k, geomPMF p k * f k

/-! ### G1.5 — Summability -/

-- TODO: G1.5
-- lemma geometricExpectation_summable (hp0 : 0 < p) (hp1 : p < 1)
--     (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) : Summable (fun k => geomPMF p k * f k) := by
--   obtain ⟨C, hC⟩ := hf
--   apply Summable.of_norm_bounded (fun k => (1 - p) ^ k * p * C)
--   · -- The bounding series ∑ (1-p)^k * p * C converges: it's C times a geometric series
--     exact (summable_geometric_of_lt_one (by linarith) (by linarith)).mul_right _
--   · intro k
--     simp [geomPMF, norm_mul]
--     calc ‖(1 - p) ^ k‖ * ‖p‖ * ‖f k‖
--         ≤ (1 - p) ^ k * p * C := by
--           sorry
--     sorry

/-! ### G1.6 — One-step unrolling -/

-- TODO: G1.6
-- lemma geometricExpectation_unroll (hp0 : 0 < p) (hp1 : p < 1)
--     (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) :
--     geometricExpectation p f =
--     p * f 0 + (1 - p) * geometricExpectation p (fun k => f (k + 1)) := by
--   simp only [geometricExpectation, geomPMF]
--   -- Split off the k=0 term using tsum_eq_zero_add
--   rw [tsum_eq_zero_add (geometricExpectation_summable hp0 hp1 hf)]
--   simp only [pow_zero, one_mul]
--   congr 1
--   -- Shift the index: ∑' k, (1-p)^(k+1) * p * f(k+1) = (1-p) * ∑' k, (1-p)^k * p * f(k+1)
--   sorry

/-! ### G1.7 — Constant function -/

-- TODO: G1.7
-- lemma geometricExpectation_const (hp0 : 0 < p) (hp1 : p < 1) (c : ℝ) :
--     geometricExpectation p (fun _ => c) = c := by
--   simp only [geometricExpectation, geomPMF]
--   rw [tsum_mul_right]
--   -- ∑' k, (1-p)^k * p = 1 by geomPMF_tsum_eq_one
--   rw [← geomPMF_tsum_eq_one hp0 hp1]
--   simp [geomPMF]

/-! ### G1.8 — Monotonicity -/

-- TODO: G1.8
-- lemma geometricExpectation_mono (hp0 : 0 < p) (hp1 : p < 1)
--     (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) (hg : ∃ C, ∀ k, ‖g k‖ ≤ C)
--     (hle : ∀ k, f k ≤ g k) :
--     geometricExpectation p f ≤ geometricExpectation p g := by
--   apply tsum_le_tsum
--   · intro k
--     apply mul_le_mul_of_nonneg_left (hle k)
--     exact geomPMF_nonneg hp0 hp1 k
--   · exact geometricExpectation_summable hp0 hp1 hf
--   · exact geometricExpectation_summable hp0 hp1 hg

end StoppedTimeProofs
