import PerpetualProofs.Market
import PerpetualProofs.CashFlow
import PerpetualProofs.FundingCompatibility
import PerpetualProofs.PerpFuturesNoArb
import PerpetualProofs.InversePerpCorrection

/-!
# PerpetualProofs

Lean 4 formalization of the no-arbitrage pricing theorem for perpetual futures,
building on the discrete Harrison-Pliska framework from `ftap-proofs` and the
geometric stopping time infrastructure from `stopped-time-proofs`.

**Primary reference:** Ackerer, D., J. Hugonnier, and U. Jermann.
"Perpetual Futures Pricing." *Mathematical Finance*, 2025. DOI: 10.1111/mafi.70018.

## Main theorems

- `FundingCompatibility` (split across two theorems):
  - `ackerer_cashflow_satisfies_costless_entry` — the Ackerer-Hugonnier-Jermann
    cash flow specification satisfies costless entry.
  - `he_manela_violates_costless_entry` — an explicit counterexample showing the
    original He-Manela-Ross-von Wachter specification does not.

- `perp_futures_no_arb_price` — the unique no-arbitrage price is
  `F₀ = geometricExpectation (κ/(1+r)) (E^Q[S_·])`.

- `inverse_perp_convexity_discount` — the inverse perpetual price satisfies
  `G₀ < F₀` (strict Jensen inequality from convexity of `1/x`).

## Module structure

- `PerpetualProofs.Market` — `OnePeriodMarket`, `OnePeriodEMM`
- `PerpetualProofs.CashFlow` — `CashFlowSpec`, `ackererCashFlow`,
  `heManelaCashFlow`, `CostlessEntry`, `NoBuyAndHoldArbitrage`
- `PerpetualProofs.FundingCompatibility` — Theorems 1a and 1b
- `PerpetualProofs.PerpFuturesNoArb` — Theorem 2
- `PerpetualProofs.InversePerpCorrection` — Theorem 3

## Dependencies

- `stopped-time-proofs` — `geometricExpectation` and Jensen's inequality
- `ftap-proofs` — `FtapProofs.Market` (market model), `FtapProofs.Strategy`
  (trading strategies, self-financing)
- `mathlib` — measure theory, probability

## Status

Work in progress. See `SPEC.md` for the proof roadmap.
-/
