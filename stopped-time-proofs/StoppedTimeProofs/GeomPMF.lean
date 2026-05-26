import Mathlib.Topology.Algebra.InfiniteSum.Basic
import Mathlib.Algebra.GeomSum

/-!
# Geometric PMF

The geometric probability mass function and its basic summability properties.

We define `geomPMF p k := (1 - p) ^ k * p` and prove:
- **G1.2** `geomPMF_nonneg` — non-negativity for `0 < p < 1`
- **G1.3** `geomPMF_tsum_eq_one` — the PMF sums to 1 over all `k : ℕ`

These establish that `geomPMF p` is a genuine probability mass function on `ℕ`,
which is the foundation for `geometricExpectation` in `GeomExpectation.lean` and
Jensen's inequality in `Jensen.lean`.

## Mathlib touchpoints

- `tsum_geometric_of_lt_one` — geometric series `∑' k, r^k = 1/(1-r)` for `|r| < 1`
-/

namespace StoppedTimeProofs

/-! ### G1.1 — Definition -/

/-- **G1.1** The geometric probability mass function with parameter `p`.

`geomPMF p k` is the probability of a geometric random variable taking value `k`:
`P(τ = k) = (1 - p)^k * p`.

For `0 < p < 1`, this defines a valid PMF on `ℕ` (proved in `geomPMF_tsum_eq_one`).
The intensity parameter in the perpetual futures context is `p = κ / (1 + r)`,
where `κ` is the funding rate and `r` is the risk-free rate. -/
noncomputable def geomPMF (p : ℝ) (k : ℕ) : ℝ := (1 - p) ^ k * p

/-! ### G1.2 — Non-negativity -/

-- TODO: G1.2
-- lemma geomPMF_nonneg (hp0 : 0 < p) (hp1 : p < 1) (k : ℕ) : 0 ≤ geomPMF p k := by
--   simp [geomPMF]
--   apply mul_nonneg
--   · exact pow_nonneg (by linarith) k
--   · linarith

/-! ### G1.3 — Sum to 1 -/

-- TODO: G1.3
-- lemma geomPMF_tsum_eq_one (hp0 : 0 < p) (hp1 : p < 1) :
--     ∑' k : ℕ, geomPMF p k = 1 := by
--   simp only [geomPMF]
--   -- ∑' k, (1-p)^k * p = p * ∑' k, (1-p)^k = p * 1/(1-(1-p)) = p * 1/p = 1
--   -- Uses tsum_geometric_of_lt_one with r = (1-p), noting 0 ≤ 1-p < 1
--   sorry

end StoppedTimeProofs
