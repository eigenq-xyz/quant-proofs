# verified-options-backtest — Python package

Python components of the verified-options-backtest engine.

## Modules

- `pricer/` — Black-Scholes pricing + Greeks (scipy), basis-point conventions
- `etl/` — WRDS OptionMetrics loaders + Pydantic data types
- `simulator/` — Seeded GBM path generator
- `backtest/` — Delta-hedging runner, step certificates, Hull 19.2/19.3 scenarios
- `ffi/` — Compiled Cython bridge to the Lean accounting kernel

See the [main README](../README.md) and [docs/architecture/overview.md](../docs/architecture/overview.md) for the bigger picture.
