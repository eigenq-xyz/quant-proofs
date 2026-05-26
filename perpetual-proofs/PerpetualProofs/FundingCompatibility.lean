import PerpetualProofs.CashFlow
import StoppedTimeProofs.GeomExpectation

/-!
# Funding Compatibility

This module contains the `FundingCompatibility` result: the Ackerer-Hugonnier-Jermann
cash flow specification satisfies costless entry, while the original
He-Manela-Ross-von Wachter specification does not.

## Contents

- **F3.1** `ackerer_pv_eq` — the Ackerer cash flow present value equals `F₀ − E^Q[S_τ]`
- **F3.2** `ackerer_cashflow_satisfies_costless_entry` — **Theorem 1a**
- **F3.3** `he_manela_pv_eq` — the He et al. cash flow present value equals `S₀ − F₀`
- **F3.4** `he_manela_violates_costless_entry` — **Theorem 1b** (explicit counterexample)

## The He et al. error

The original He et al. specification has a constant payment `S₀ − F₀` at every
funding date. By `geometricExpectation_const`, this stream has present value `S₀ − F₀`.
Setting this to zero requires `S₀ = F₀`, which is not a consequence of the no-arbitrage
condition in general. The counterexample in Theorem 1b takes `S₀ = 1`, `F₀ = 2`,
`κ = 1/10`, `r = 1/20`, and verifies that `1 − 2 = −1 ≠ 0`.

## Reference

Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing." *Mathematical
Finance*, 2025. DOI: 10.1111/mafi.70018. The error is documented on p. 1 of the
Introduction.
-/

namespace PerpetualProofs

open StoppedTimeProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### F3.1 — Ackerer present value computation -/

-- TODO: F3.1
-- lemma ackerer_pv_eq (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
--     (F₀ : ℝ) :
--     geometricExpectation (p := market.κ / (1 + market.r))
--       (fun k => ∑ ω : Ω, Q.density ω * ackererCashFlow.cashflow k market F₀ ω) =
--     F₀ - geometricExpectation (p := market.κ / (1 + market.r))
--              (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) := by
--   -- ackererCashFlow.cashflow k market F₀ ω = F₀ - market.spot k ω
--   -- So ∑ ω, Q.density ω * (F₀ - spot k ω) = F₀ * ∑ ω, Q.density ω - ∑ ω, Q.density ω * spot k ω
--   --                                         = F₀ - ∑ ω, Q.density ω * spot k ω
--   -- (using Q.density_sum_eq_one)
--   -- Then geometricExpectation_const gives geometricExpectation p (fun _ => F₀) = F₀
--   sorry

/-! ### F3.2 — Theorem 1a -/

-- TODO: F3.2
-- theorem ackerer_cashflow_satisfies_costless_entry
--     (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r) :
--     let p := market.κ / (1 + market.r)
--     let F₀ := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
--     CostlessEntry ackererCashFlow market Q F₀ := by
--   -- CostlessEntry unfolds to: geometricExpectation p (...) = 0
--   -- By ackerer_pv_eq this equals F₀ - geometricExpectation p (...) = F₀ - F₀ = 0
--   sorry

/-! ### F3.3 — He et al. present value computation -/

-- TODO: F3.3
-- lemma he_manela_pv_eq (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
--     (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
--     (F₀ : ℝ) :
--     geometricExpectation (p := market.κ / (1 + market.r))
--       (fun k => ∑ ω : Ω, Q.density ω * heManelaCashFlow.cashflow k market F₀ ω) =
--     (∑ ω : Ω, market.spot 0 ω) / Fintype.card Ω - F₀ := by
--   -- heManelaCashFlow.cashflow is constant in k and ω
--   -- So the geometric expectation of a constant = the constant (by geometricExpectation_const)
--   sorry

/-! ### F3.4 — Theorem 1b: explicit counterexample -/

-- TODO: F3.4
-- theorem he_manela_violates_costless_entry :
--     ∃ (Ω : Type) [Fintype Ω] [MeasurableSpace Ω] [MeasurableSingletonClass Ω]
--       (market : @OnePeriodMarket Ω _ _ _) (Q : @OnePeriodEMM Ω _ _ _ market) (F₀ : ℝ),
--       ¬ @CostlessEntry Ω _ _ _ heManelaCashFlow market Q F₀ := by
--   -- Construct: Ω = Fin 2 (two states: up / down)
--   -- market.spot 0 _ = 1 (constant spot price = 1)
--   -- F₀ = 2
--   -- κ = 1/10, r = 1/20
--   -- Q.density _ = 1/2
--   -- Then S₀ − F₀ = 1 − 2 = −1 ≠ 0
--   -- Closed by norm_num
--   sorry

end PerpetualProofs
