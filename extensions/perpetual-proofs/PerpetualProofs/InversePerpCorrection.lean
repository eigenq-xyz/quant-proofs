import PerpetualProofs.PerpFuturesNoArb
import StoppedTimeProofs.Jensen
import Mathlib.Analysis.Convex.SpecificFunctions.Deriv

/-!
# Inverse Perpetual Convexity Adjustment

The no-arbitrage price of a coin-settled (inverse) perpetual future satisfies
`G₀ < F₀`, where `F₀` is the price of the corresponding linear perpetual.

The gap arises from Jensen's inequality: since `φ(x) = 1/x` is strictly convex
on `ℝ_{>0}`, the Q-expected inverse spot exceeds the inverse of the Q-expected spot,
giving `G₀ = 1/E^Q[1/S_τ] < F₀`.

## Contents

- **I4.1** `inversePerp_noArb_price` — definition of `G₀`
- **I4.2** `geom_exp_inv_gt` — `E^Q[1/S_τ] > 1/F₀` (main inequality)
- **I4.3** `inverse_perp_convexity_discount` — **Theorem 3**: `G₀ < F₀`

## Key hypotheses

- `hspot_bdd_below`: spot prices are uniformly bounded below by `ε > 0`. Required for
  `E^Q[1/S_k]` to be uniformly bounded (ensuring `geometricExpectation p (E^Q[1/S_·])`
  converges). Without this, Lean's `tsum` convention (returns 0 for non-summable series)
  makes the theorem degenerate.
- `hS_nondegen`: spot price at some date `k₀` is not constant across states. Required for
  the strict Jensen inequality on `Ω`.

## Proof structure

By `spot_expectation_const`, `E^Q[S_k] = F₀` is constant in `k`. For each `k`:
  `F₀ * E^Q[1/S_k] ≥ 1`  (Cauchy-Schwarz on finite `Ω`)
with strict inequality at `k₀` (strict Jensen via `StrictConvexOn.map_sum_lt`
applied to `φ(x) = 1/x` which is strictly convex on `ℝ_{>0}` by `strictConvexOn_zpow`).

Then `geometricExpectation p (E^Q[1/S_·]) > 1/F₀` by `geometricExpectation_strict_mono`
(G2.1 in `Jensen.lean`), and taking reciprocals gives `G₀ < F₀`.
-/

namespace PerpetualProofs

open StoppedTimeProofs Finset

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### I4.1 — Inverse perpetual price definition -/

omit [MeasurableSpace Ω] [MeasurableSingletonClass Ω] in
/-- **I4.1** The no-arbitrage price of an inverse (coin-settled) perpetual future.

`G₀ = 1 / geometricExpectation p (E^Q[1/S_·])` where `p = κ/(1+r)`.

This is the reciprocal of the geometric expectation of the inverse spot price.
By `inverse_perp_convexity_discount` (I4.3), `G₀ < F₀` whenever the spot price
is not constant across states. -/
noncomputable def inversePerp_noArb_price
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market) : ℝ :=
  (geometricExpectation (market.κ / (1 + market.r))
    (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω))⁻¹

/-! ### I4.2 — Main inequality: E^Q[1/S_τ] > 1/F₀ -/

omit [MeasurableSpace Ω] [MeasurableSingletonClass Ω] in
/-- **I4.2** The geometric expectation of the inverse spot exceeds `1/F₀`.

For each `k`, Cauchy-Schwarz on `Ω` gives `E^Q[S_k] * E^Q[1/S_k] ≥ 1`.
At `k₀` (from non-degeneracy), strict Jensen (`StrictConvexOn.map_sum_lt` with
`φ(x) = 1/x`) gives `E^Q[S_{k₀}] * E^Q[1/S_{k₀}] > 1`.
Since `E^Q[S_k] = F₀` (constant, by `spot_expectation_const`):
  `E^Q[1/S_k] ≥ 1/F₀` for all `k`, strict at `k₀`.
By `geometricExpectation_strict_mono`: `geometricExpectation p (E^Q[1/S_·]) > 1/F₀`. -/
lemma geom_exp_inv_gt (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (hspot_bdd_below : ∃ ε : ℝ, 0 < ε ∧ ∀ k : ℕ, ∀ ω : Ω, ε ≤ market.spot k ω)
    (hS_nondegen : ∃ k : ℕ, ∃ ω₁ ω₂ : Ω, market.spot k ω₁ ≠ market.spot k ω₂) :
    (1 : ℝ) / geometricExpectation (market.κ / (1 + market.r))
        (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) <
      geometricExpectation (market.κ / (1 + market.r))
        (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω) := by
  -- Destructure early to get Nonempty Ω
  obtain ⟨k₀, ω₁, ω₂, hω_ne⟩ := hS_nondegen
  obtain ⟨ε, hε, hε_le⟩ := hspot_bdd_below
  haveI hΩ_ne : Nonempty Ω := ⟨ω₁⟩
  -- Parameters
  have hp0 : 0 < market.κ / (1 + market.r) :=
    div_pos market.κ_pos (by linarith [market.r_pos])
  have hp1 : market.κ / (1 + market.r) < 1 := by
    rw [div_lt_one (by linarith [market.r_pos])]; exact market.κ_lt
  set p := market.κ / (1 + market.r) with hp_def
  -- Function abbreviations
  set a := fun k => ∑ ω : Ω, Q.density ω * market.spot k ω
  set b := fun k => ∑ ω : Ω, Q.density ω / market.spot k ω
  -- F₀ := geometricExpectation p a = a 0 (by spot_expectation_const)
  have hF₀_eq : geometricExpectation p a = a 0 := by
    have hconst : geometricExpectation p a = geometricExpectation p (fun _ => a 0) := by
      congr 1; exact funext (fun k => Q.spot_expectation_const k 0)
    rw [hconst, geometricExpectation_const hp0 hp1]
  -- a k > 0 for all k
  have ha_pos : ∀ k, 0 < a k := fun k =>
    sum_pos (fun ω _ => mul_pos (Q.density_pos ω) (market.spot_pos k ω)) univ_nonempty
  -- geometricExpectation p a > 0
  have hF₀_pos : 0 < geometricExpectation p a := hF₀_eq ▸ ha_pos 0
  -- Strict convexity of 1/x on ℝ_{>0} (via strictConvexOn_zpow with m = -1)
  have hscx : StrictConvexOn ℝ (Set.Ioi 0) (fun x : ℝ => x⁻¹) := by
    have h := strictConvexOn_zpow (m := -1) (by norm_num : (-1 : ℤ) ≠ 0)
                                              (by norm_num : (-1 : ℤ) ≠ 1)
    simp only [zpow_neg_one] at h
    exact h
  -- Per-k non-strict inequality: 1 ≤ (a k) * (b k) (Cauchy-Schwarz on Ω)
  have hFb_ge : ∀ k, 1 ≤ a k * b k := by
    intro k
    -- (∑ Q.density ω)^2 ≤ (∑ Q.density ω * spot k ω) * (∑ Q.density ω / spot k ω)
    have hCS := Finset.sum_sq_le_sum_mul_sum_of_sq_le_mul (s := univ)
      (r := fun ω => Q.density ω)
      (f := fun ω => Q.density ω * market.spot k ω)
      (g := fun ω => Q.density ω / market.spot k ω)
      (fun ω _ => mul_nonneg (Q.density_pos ω).le (market.spot_pos k ω).le)
      (fun ω _ => div_nonneg (Q.density_pos ω).le (market.spot_pos k ω).le)
      (fun ω _ => le_of_eq (by
        have hs : (0 : ℝ) < market.spot k ω := market.spot_pos k ω
        field_simp [hs.ne']))
    rw [Q.density_sum_eq_one, one_pow] at hCS
    exact hCS
  -- Strict per-k inequality at k₀ (strict Jensen on Ω)
  have hFb_gt : 1 < a k₀ * b k₀ := by
    -- Strict Jensen: (a k₀)⁻¹ < b k₀
    have hJensen := hscx.map_sum_lt
      (t := univ) (w := Q.density) (p := market.spot k₀)
      (fun ω _ => Q.density_pos ω)
      (by simpa using Q.density_sum_eq_one)
      (fun ω _ => Set.mem_Ioi.mpr (market.spot_pos k₀ ω))
      ⟨ω₁, mem_univ _, ω₂, mem_univ _, hω_ne⟩
    simp only [smul_eq_mul] at hJensen
    -- hJensen : (a k₀)⁻¹ < b k₀  (after rewriting lhs/rhs)
    have hlhs : (∑ ω : Ω, Q.density ω * market.spot k₀ ω)⁻¹ = (a k₀)⁻¹ := rfl
    have hrhs : ∑ ω : Ω, Q.density ω * (market.spot k₀ ω)⁻¹ = b k₀ := by
      simp only [b, div_eq_mul_inv]
    rw [hlhs, hrhs] at hJensen
    -- 1 < a k₀ * b k₀
    calc 1 = a k₀ * (a k₀)⁻¹ := (mul_inv_cancel₀ (ha_pos k₀).ne').symm
      _ < a k₀ * b k₀ := mul_lt_mul_of_pos_left hJensen (ha_pos k₀)
  -- b is bounded (from hspot_bdd_below)
  have hb_bdd : ∃ C, ∀ k : ℕ, ‖b k‖ ≤ C := by
    refine ⟨1 / ε, fun k => ?_⟩
    simp only [b]
    rw [Real.norm_of_nonneg (sum_nonneg fun ω _ =>
          div_nonneg (Q.density_pos ω).le (market.spot_pos k ω).le)]
    calc ∑ ω : Ω, Q.density ω / market.spot k ω
        ≤ ∑ ω : Ω, Q.density ω / ε :=
          sum_le_sum fun ω _ =>
            div_le_div_of_nonneg_left (Q.density_pos ω).le hε (hε_le k ω)
      _ = (∑ ω : Ω, Q.density ω) / ε := (Finset.sum_div _ _ _).symm
      _ = 1 / ε := by rw [Q.density_sum_eq_one]
  -- b k ≥ 1/(geometricExpectation p a) for all k
  have hb_ge : ∀ k, 1 / geometricExpectation p a ≤ b k := fun k => by
    rw [hF₀_eq, div_le_iff₀ (ha_pos 0),
        show a 0 = a k from Q.spot_expectation_const 0 k]
    linarith [hFb_ge k, mul_comm (a k) (b k)]
  -- b k₀ > 1/(geometricExpectation p a) (strict)
  have hb_gt : 1 / geometricExpectation p a < b k₀ := by
    rw [hF₀_eq, div_lt_iff₀ (ha_pos 0),
        show a 0 = a k₀ from Q.spot_expectation_const 0 k₀]
    linarith [hFb_gt, mul_comm (a k₀) (b k₀)]
  -- Constant-bounded witness for the constant lower bound function
  have hcbdd : ∃ C, ∀ k : ℕ, ‖(1 : ℝ) / geometricExpectation p a‖ ≤ C :=
    ⟨‖1 / geometricExpectation p a‖, fun _ => le_refl _⟩
  -- Apply strict monotonicity: geometricExpectation p (fun _ => 1/F₀) < geometricExpectation p b
  have hGeB_gt : geometricExpectation p (fun _ => 1 / geometricExpectation p a) <
      geometricExpectation p b :=
    geometricExpectation_strict_mono hp0 hp1 hb_ge k₀ hb_gt hcbdd hb_bdd
  -- Simplify geometricExpectation p (fun _ => 1/F₀) = 1/F₀ and conclude
  rwa [geometricExpectation_const hp0 hp1] at hGeB_gt

/-! ### I4.3 — Theorem 3 -/

omit [MeasurableSpace Ω] [MeasurableSingletonClass Ω] in
/-- **I4.3 (Theorem 3)** The inverse perpetual price `G₀` is strictly less than the linear
perpetual price `F₀`.

**Proof:** By `geom_exp_inv_gt`, `geometricExpectation p (E^Q[1/S_·]) > 1/F₀ > 0`.
Taking reciprocals (both sides positive, inequality reverses): `G₀ < F₀`. -/
theorem inverse_perp_convexity_discount
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (hspot_bdd_below : ∃ ε : ℝ, 0 < ε ∧ ∀ k : ℕ, ∀ ω : Ω, ε ≤ market.spot k ω)
    (hS_nondegen : ∃ k : ℕ, ∃ ω₁ ω₂ : Ω, market.spot k ω₁ ≠ market.spot k ω₂) :
    inversePerp_noArb_price market Q <
      geometricExpectation (market.κ / (1 + market.r))
        (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) := by
  -- Parameters
  have hp0 : 0 < market.κ / (1 + market.r) :=
    div_pos market.κ_pos (by linarith [market.r_pos])
  have hp1 : market.κ / (1 + market.r) < 1 := by
    rw [div_lt_one (by linarith [market.r_pos])]; exact market.κ_lt
  set p := market.κ / (1 + market.r) with hp_def
  -- Extract ω₁ for Nonempty Ω; keep components to reconstitute hS_nondegen
  obtain ⟨k_nd, ω₁, ω₂, hω_ne⟩ := hS_nondegen
  haveI : Nonempty Ω := ⟨ω₁⟩
  set F₀ := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
  set B := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω)
  -- G₀ = B⁻¹ by definition
  have hG₀ : inversePerp_noArb_price market Q = B⁻¹ := rfl
  -- F₀ > 0
  have hF₀_pos : 0 < F₀ := by
    simp only [F₀]
    have hconst : geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) =
        ∑ ω : Ω, Q.density ω * market.spot 0 ω :=
      (show (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) =
           fun _ => ∑ ω : Ω, Q.density ω * market.spot 0 ω from
        funext (fun k => Q.spot_expectation_const k 0)) ▸
      geometricExpectation_const hp0 hp1 _
    rw [hconst]
    exact Finset.sum_pos (fun ω _ => mul_pos (Q.density_pos ω) (market.spot_pos 0 ω))
      Finset.univ_nonempty
  -- Apply geom_exp_inv_gt: 1/F₀ < B
  have hInvLtB : (1 : ℝ) / F₀ < B :=
    geom_exp_inv_gt market Q hspot_bdd_below ⟨k_nd, ω₁, ω₂, hω_ne⟩
  -- 0 < 1/F₀ < B
  have h1F₀_pos : (0 : ℝ) < 1 / F₀ := one_div_pos.mpr hF₀_pos
  have hB_pos : 0 < B := lt_trans h1F₀_pos hInvLtB
  -- G₀ = B⁻¹ < (1/F₀)⁻¹ = F₀
  rw [hG₀]
  have hlt : B⁻¹ < (1 / F₀)⁻¹ := (inv_lt_inv₀ hB_pos h1F₀_pos).mpr hInvLtB
  simp only [one_div, inv_inv] at hlt
  exact hlt

end PerpetualProofs
