# quant-core

Shared pricing primitives for the quant-proofs monorepo.

## What's here

**Lean 4** (`lean/`): formally verified properties of European option payoffs — zero `sorry`.

| Module | Content |
|---|---|
| `QuantCore.Option` | `AssetId`, `OptionKind`, `EuropeanOption`, `callPayoff`, `putPayoff`, `optionPayoff` |
| `QuantCore.OptionInvariants` | 8 payoff theorems: non-negativity, ITM/OTM characterization, `integerPayoffDifference` |

**Python** (`python/`): pricing and simulation with no backtester dependencies.

| Module | Content |
|---|---|
| `quant_core.pricer.black_scholes` | `bs_price`, `bs_greeks` (Black-Scholes via scipy) |
| `quant_core.pricer.conventions` | `to_bp`, `from_bp` (float ↔ basis-point conversion) |
| `quant_core.simulator.data_types` | `PricePath` (source-agnostic price path type) |
| `quant_core.simulator.gbm` | `simulate_gbm` (seeded GBM path generator) |

## Dependents

Both `backtest-proofs` and `options-proofs` depend on `quant-core`.
`ftap-proofs` and `mortgage-proofs` are independent.
