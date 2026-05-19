# quant-core

Shared pricing primitives for the [quant-proofs](https://github.com/eigenq-xyz/quant-proofs) monorepo.

## What's here

**Lean 4** (`lean/`): formally verified properties of European option payoffs.
- `QuantCore.Option` — `AssetId`, `OptionKind`, `EuropeanOption`, `callPayoff`, `putPayoff`, `optionPayoff`
- `QuantCore.OptionInvariants` — 8 payoff theorems (non-negativity, ITM/OTM characterization, integer put-call identity), all zero `sorry`

**Python** (`python/`): pricing and simulation utilities with no backtester dependencies.
- `quant_core.pricer` — Black-Scholes price and Greeks (scipy), basis-point conventions
- `quant_core.simulator` — `PricePath` type, seeded GBM path generator

## Build

```bash
# Lean
cd lean && lake exe cache get && lake build

# Python
cd python && uv sync --extra dev && uv run pytest
```

## Dependencies

- **Lean**: mathlib only
- **Python**: numpy, scipy

## License

Apache License 2.0
