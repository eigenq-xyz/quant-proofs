# perpetual-proofs

Lean 4 formalization of no-arbitrage pricing for perpetual futures, following Ackerer,
Hugonnier, and Jermann (2025), with a machine-checked counterexample to a cash-flow
specification from an earlier draft by He, Manela, Ross, and von Wachter. Zero `sorry`,
axioms verified.

## What it proves

A perpetual future has no fixed expiration; a periodic funding rate pins its price to
the underlying spot. Ackerer, Hugonnier, and Jermann (2025) show that in a finite-state,
discrete-time market with funding rate `k` and risk-free rate `r`, the unique
no-arbitrage price is:

```
F₀ = geometricExpectation (k/(1+r)) (E^Q[S_·])
```

The price is the risk-neutral expectation of spot, weighted by a geometric distribution
whose parameter is set by the funding mechanism. This module states and proves that
result, derives the convexity correction for inverse (coin-margined) perpetuals, and
provides a concrete counterexample showing where an earlier cash-flow specification
fails.

| Theorem | Statement |
|---------|-----------|
| `ackerer_cashflow_satisfies_costless_entry` | The Ackerer-Hugonnier-Jermann cash-flow specification satisfies costless entry |
| `he_manela_violates_costless_entry` | An earlier specification provably fails costless entry: an explicit two-state counterexample reduces the obligation to `-1 != 0`, closed by `norm_num` |
| `perp_futures_no_arb_price` | The geometric-expectation price is the unique no-arbitrage price (existence and uniqueness) |
| `inverse_perp_convexity_discount` | The inverse perpetual price `G₀` satisfies `G₀ < F₀` by Jensen's inequality applied to `1/x` on `R_{>0}` |

10 theorems total. `#print axioms` on the headline theorems reports only
`[propext, Classical.choice, Quot.sound]`.

## Dependencies

- [`extensions/stopped-time-proofs/`](../stopped-time-proofs/): the
  `GeometricExpectation` operator, its convergence lemmas, and the strict Jensen
  inequality (`geom_exp_inv_gt` uses `geometricExpectation_strict_mono` from there).
- [`foundations/ftap-proofs/`](../../foundations/ftap-proofs/): the Harrison-Pliska
  finite market model and self-financing strategy machinery. `ftap-proofs` is complete,
  zero `sorry`.
- `mathlib`: measure theory, convex analysis (`strictConvexOn_zpow` for `1/x`),
  `tsum_geometric_of_lt_one`.

## Build and test

```bash
cd extensions/perpetual-proofs
lake exe cache get          # fetch prebuilt mathlib (first run only)
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

## Project structure

```
extensions/perpetual-proofs/
  PerpetualProofs.lean             root module, re-exports submodules
  PerpetualProofs/
    Market.lean                    OnePeriodMarket, OnePeriodEMM
    CashFlow.lean                  CashFlowSpec, ackererCashFlow, heManelaCashFlow,
                                   CostlessEntry, NoBuyAndHoldArbitrage
    FundingCompatibility.lean      Theorems 1a and 1b (costless entry proof + counterexample)
    PerpFuturesNoArb.lean          Theorem 2 (existence and uniqueness of no-arb price)
    InversePerpCorrection.lean     Theorem 3 (convexity discount G₀ < F₀)
  lakefile.lean                    requires mathlib + stopped-time-proofs + ftap-proofs
  lean-toolchain                   pinned toolchain (same as ftap-proofs)
```

## Reference

Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing." *Mathematical
Finance*, 2025. DOI: 10.1111/mafi.70018.

## License

Apache 2.0, compatible with mathlib for upstream contribution.
