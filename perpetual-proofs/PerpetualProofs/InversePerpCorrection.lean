import PerpetualProofs.PerpFuturesNoArb
import StoppedTimeProofs.Jensen

/-!
# Inverse Perpetual Convexity Adjustment

The no-arbitrage price of a coin-settled (inverse) perpetual future satisfies
`G₀ < F₀`, where `F₀` is the price of the corresponding linear perpetual.

The gap arises from Jensen's inequality: since `φ(x) = 1/x` is strictly convex
on `ℝ_{>0}`, the geometric expectation of `1/S_τ` strictly exceeds `1/E^Q[S_τ] = 1/F₀`,
giving `G₀ = 1/E^Q[1/S_τ] < F₀`.

## Contents

- **I4.1** `inversePerp_noArb_price` — definition of `G₀`
- **I4.2** `geom_exp_inv_gt` — `E^Q[1/S_τ] > 1/F₀` via `jensen_geom_strict_convex`
- **I4.3** `inverse_perp_convexity_discount` — **Theorem 3**: `G₀ < F₀`

## Key hypothesis

The strict inequality requires `hS_nondegen : ∃ k ω₁ ω₂, market.spot k ω₁ ≠ market.spot k ω₂`.
Without non-degeneracy (all spot prices identical across states), Jensen's inequality
is an equality and `G₀ = F₀`. The non-degeneracy condition is a hypothesis on the market,
not derived from other assumptions.
-/

namespace PerpetualProofs

open StoppedTimeProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### I4.1 — Inverse perpetual price definition -/

/-- **I4.1** The no-arbitrage price of a coin-settled (inverse) perpetual future.

The inverse perpetual has margin denominated in the base asset (e.g., BTC) rather
than the quote currency (USD). Its no-arbitrage price is the reciprocal of the
geometric expectation of the reciprocal spot:

`G₀ = (geometricExpectation p (E^Q[1/S_·]))⁻¹`

This follows from the same costless-entry argument as for the linear perpetual,
applied to coin-denominated cash flows. -/
noncomputable def inversePerp_noArb_price (market : OnePeriodMarket Ω)
    (Q : OnePeriodEMM Ω market) : ℝ :=
  let p := market.κ / (1 + market.r)
  (geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω))⁻¹

/-! ### I4.2 — E^Q[1/S_τ] > 1/F₀ -/

-- TODO: I4.2
-- lemma geom_exp_inv_gt (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
--     (hS_nondegen : ∃ k ω₁ ω₂, market.spot k ω₁ ≠ market.spot k ω₂) :
--     let p  := market.κ / (1 + market.r)
--     let F₀ := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
--     geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω) >
--     F₀⁻¹ := by
--   -- Apply jensen_geom_strict_convex with φ(x) = 1/x
--   -- φ is strictly convex on ℝ_{>0} by Real.strictConvexOn_inv (or similar)
--   -- The non-degeneracy hypothesis provides k₁ ≠ k₂ with f k₁ ≠ f k₂
--   sorry

/-! ### I4.3 — Theorem 3 -/

-- TODO: I4.3
-- theorem inverse_perp_convexity_discount
--     (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
--     (hS_nondegen : ∃ k ω₁ ω₂, market.spot k ω₁ ≠ market.spot k ω₂) :
--     let p  := market.κ / (1 + market.r)
--     inversePerp_noArb_price market Q <
--       geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) := by
--   -- From geom_exp_inv_gt: E^Q[1/S_τ] > 1/F₀
--   -- Take reciprocals (both positive): 1/E^Q[1/S_τ] < F₀
--   -- G₀ = 1/E^Q[1/S_τ] by definition
--   -- Rearrange using inv_lt_inv_of_lt
--   sorry

end PerpetualProofs
