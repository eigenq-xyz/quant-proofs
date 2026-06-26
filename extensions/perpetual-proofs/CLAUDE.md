# CLAUDE.md: perpetual-proofs

Lean 4 formalization of no-arbitrage pricing for perpetual futures (Ackerer,
Hugonnier, and Jermann 2025). Builds on `stopped-time-proofs` (geometric expectation
infrastructure) and `ftap-proofs` (Harrison-Pliska market model). Complete, 10
theorems, zero `sorry`.

## Build and test

```bash
# From extensions/perpetual-proofs/
lake exe cache get          # first run only
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

## Architecture

```
extensions/perpetual-proofs/
  PerpetualProofs.lean             root: re-exports all submodules
  PerpetualProofs/
    Market.lean                    OnePeriodMarket, OnePeriodEMM
    CashFlow.lean                  CashFlowSpec, ackererCashFlow, heManelaCashFlow,
                                   CostlessEntry, NoBuyAndHoldArbitrage
    FundingCompatibility.lean      Theorems 1a + 1b (F3.1-F3.4)
    PerpFuturesNoArb.lean          Theorem 2 (PR4.1-PR4.3)
    InversePerpCorrection.lean     Theorem 3 (I4.1-I4.3)
  lakefile.lean                    requires mathlib + stopped-time-proofs + ftap-proofs
  lean-toolchain                   pinned toolchain (same as ftap-proofs)
```

## Theorem index

| Theorem | File | Internal label |
|---------|------|---------------|
| `ackerer_cashflow_satisfies_costless_entry` | `FundingCompatibility.lean` | F3.2 |
| `he_manela_violates_costless_entry` | `FundingCompatibility.lean` | F3.4 |
| `no_arb_uniqueness` | `PerpFuturesNoArb.lean` | PR4.1 |
| `no_arb_existence` | `PerpFuturesNoArb.lean` | PR4.2 |
| `perp_futures_no_arb_price` | `PerpFuturesNoArb.lean` | PR4.3 |
| `inversePerp_noArb_price` | `InversePerpCorrection.lean` | I4.1 |
| `geom_exp_inv_gt` | `InversePerpCorrection.lean` | I4.2 |
| `inverse_perp_convexity_discount` | `InversePerpCorrection.lean` | I4.3 |

`no_arb_existence` and `no_arb_uniqueness` are named lemmas; `perp_futures_no_arb_price`
combines them into the headline theorem.

## Key definitions

- `OnePeriodMarket Ω`: fields `spot : N -> Omega -> R`, `k : R` (funding rate),
  `r : R` (risk-free rate), with positivity hypotheses and `k < 1 + r`.
- `OnePeriodEMM Ω market`: risk-neutral density with `density_pos`,
  `density_sum_eq_one`, and `spot_expectation_const` (Q-expectation of spot is
  constant in time, the stationarity hypothesis for Theorem 2).
- `CostlessEntry`: the present value of the cash-flow stream under geometric weighting
  equals zero. A `Prop` that each cash-flow specification must satisfy before any
  pricing theorem can be stated.
- `NoBuyAndHoldArbitrage market Q F₀`: the pair `(CostlessEntry, no-round-trip)`.
- `geometricExpectation p f`: imported from `stopped-time-proofs`. The sum
  `sum_k (1-p)^k * p * f k` for `0 < p < 1`.

## Dependencies

- `stopped-time-proofs`: `GeometricExpectation`, `geometricExpectation_const`,
  `geometricExpectation_strict_mono`, Jensen lemmas. `InversePerpCorrection.lean`
  uses `StrictConvexOn.map_sum_lt` via `jensen_geom_strict_convex`.
- `ftap-proofs`: complete (zero `sorry`). `Market.lean` and `CashFlow.lean` import
  `FtapProofs.Market` and `FtapProofs.Strategy`. `OnePeriodEMM` is a local struct;
  it does not import `FtapProofs.MartingaleMeasure` (that module uses a different
  EMM formulation).

## Hard rules

- Zero `sorry` on main. No exceptions.
- Do not edit `.lean` files to resolve documentation issues; fix documentation only.
- Do not import private context from outside this repository.
- Apache 2.0 license; keep compatible with mathlib for upstream contribution.
