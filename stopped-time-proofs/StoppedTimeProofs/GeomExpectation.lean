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
- `tsum_mul_left` / `tsum_mul_right` — factor constants out of tsum
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

/-- **G1.5** The geometric expectation series converges when `f` is bounded.

Proof: bound `‖geomPMF p k * f k‖ ≤ geomPMF p k * C` using `geomPMF_nonneg`,
then dominate by the convergent series `∑ geomPMF p k * C = C` via
`summable_geometric_of_lt_one`. -/
lemma geometricExpectation_summable {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
    {f : ℕ → ℝ} (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) :
    Summable (fun k => geomPMF p k * f k) := by
  obtain ⟨C, hC⟩ := hf
  refine Summable.of_norm_bounded (fun k => geomPMF p k * C) ?_ (fun k => ?_)
  · -- Bounding series ∑ geomPMF p k * C converges: it's C · ∑ (1-p)^k · p
    have hs : Summable (fun k : ℕ => (1 - p) ^ k) :=
      summable_geometric_of_lt_one (by linarith) (by linarith)
    simpa only [geomPMF] using (hs.mul_right p).mul_right C
  · -- ‖geomPMF p k * f k‖ ≤ geomPMF p k * C
    have hg : 0 ≤ geomPMF p k := geomPMF_nonneg hp0 hp1 k
    rw [norm_mul, Real.norm_of_nonneg hg]
    exact mul_le_mul_of_nonneg_left (hC k) hg

/-! ### G1.6 — One-step unrolling -/

/-- **G1.6** One-step recursion for `geometricExpectation`.

`geometricExpectation p f = p * f 0 + (1 - p) * geometricExpectation p (fun k => f (k+1))`

Proof: split the tsum at k = 0 using `tsum_eq_zero_add`, then factor `(1-p)` out of the
tail using `tsum_mul_left` and `pow_succ`. -/
lemma geometricExpectation_unroll {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
    {f : ℕ → ℝ} (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) :
    geometricExpectation p f =
      p * f 0 + (1 - p) * geometricExpectation p (fun k => f (k + 1)) := by
  simp only [geometricExpectation]
  rw [tsum_eq_zero_add (geometricExpectation_summable hp0 hp1 hf)]
  simp only [geomPMF, pow_zero, one_mul]
  congr 1
  rw [← tsum_mul_left]
  congr 1
  ext k
  simp only [geomPMF, pow_succ]
  ring

/-! ### G1.7 — Constant function -/

/-- **G1.7** `geometricExpectation p (fun _ => c) = c`.

Since the geometric weights sum to 1 (`geomPMF_tsum_eq_one`), the weighted sum of a
constant equals the constant: `∑' k, geomPMF p k * c = (∑' k, geomPMF p k) * c = c`. -/
lemma geometricExpectation_const {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1) (c : ℝ) :
    geometricExpectation p (fun _ => c) = c := by
  simp only [geometricExpectation]
  rw [tsum_mul_right, geomPMF_tsum_eq_one hp0 hp1, one_mul]

/-! ### G1.8 — Monotonicity -/

/-- **G1.8** `geometricExpectation p f ≤ geometricExpectation p g` when `f ≤ g` pointwise.

Since all weights `geomPMF p k ≥ 0`, pointwise inequality of functions implies
inequality of geometric expectations. Follows from `tsum_le_tsum`. -/
lemma geometricExpectation_mono {p : ℝ} (hp0 : 0 < p) (hp1 : p < 1)
    {f g : ℕ → ℝ} (hf : ∃ C, ∀ k, ‖f k‖ ≤ C) (hg : ∃ C, ∀ k, ‖g k‖ ≤ C)
    (hle : ∀ k, f k ≤ g k) :
    geometricExpectation p f ≤ geometricExpectation p g := by
  simp only [geometricExpectation]
  apply tsum_le_tsum
  · intro k
    exact mul_le_mul_of_nonneg_left (hle k) (geomPMF_nonneg hp0 hp1 k)
  · exact geometricExpectation_summable hp0 hp1 hf
  · exact geometricExpectation_summable hp0 hp1 hg

end StoppedTimeProofs
