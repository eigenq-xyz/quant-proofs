import PerpetualProofs.FundingCompatibility
import FtapProofs.Strategy

/-!
# The No-Arbitrage Pricing Theorem for Perpetual Futures

The unique no-arbitrage price for a perpetual future is the geometric expectation
of the risk-neutral spot price:

`F₀ = geometricExpectation (κ/(1+r)) (fun k => E^Q[S_k])`

This is the discrete finite-state version of the main result in Ackerer, Hugonnier,
and Jermann (2025), DOI: 10.1111/mafi.70018.

## Contents

- **PR4.1** `no_arb_uniqueness` — any two no-arbitrage prices must be equal
- **PR4.2** `no_arb_existence` — the geometric-expectation price satisfies
  `NoBuyAndHoldArbitrage`
- **PR4.3** `perp_futures_no_arb_price` — **Theorem 2** combining existence and
  uniqueness

## Proof structure

**Uniqueness (PR4.1):** If `F₀ ≠ F₀'` both satisfy `NoBuyAndHoldArbitrage`, then
a round-trip strategy (enter long at `F₀`, short at `F₀'`) has nonzero expected
payoff under Q, contradicting one of the two hypotheses.

**Existence (PR4.2):** At the geometric-expectation price, `CostlessEntry` holds by
`ackerer_cashflow_satisfies_costless_entry` (Theorem 1a). The risk-neutral pricing
identity then shows no deviation from this price is compatible with zero expected cost.
-/

namespace PerpetualProofs

open StoppedTimeProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### PR4.1 — Uniqueness -/

-- TODO: PR4.1
-- lemma no_arb_uniqueness (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
--     (F₀ F₀' : ℝ)
--     (h : NoBuyAndHoldArbitrage market Q F₀)
--     (h' : NoBuyAndHoldArbitrage market Q F₀') :
--     F₀ = F₀' := by
--   sorry

/-! ### PR4.2 — Existence -/

-- TODO: PR4.2
-- lemma no_arb_existence (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r) :
--     let p := market.κ / (1 + market.r)
--     NoBuyAndHoldArbitrage market Q
--       (geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)) := by
--   sorry

/-! ### PR4.3 — Theorem 2 -/

-- TODO: PR4.3
-- theorem perp_futures_no_arb_price (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r) :
--     let p  := market.κ / (1 + market.r)
--     let F₀ := geometricExpectation p
--                 (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
--     NoBuyAndHoldArbitrage market Q F₀ ∧
--     ∀ F₀' : ℝ, NoBuyAndHoldArbitrage market Q F₀' → F₀' = F₀ := by
--   constructor
--   · exact no_arb_existence market Q hκ hr hκr
--   · intro F₀' h'
--     exact no_arb_uniqueness market Q hκ hr hκr _ F₀' (no_arb_existence market Q hκ hr hκr) h'

end PerpetualProofs
