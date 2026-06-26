# quant-core (Python)

The Python layer of `foundations/quant-core`: Black-Scholes pricing, Greeks, and GBM simulation. No backtester dependencies.

## Modules

- `quant_core.pricer.black_scholes`: `bs_price` returns a `BSPrice` with a float `value` and an integer `value_bp` (basis points). `bs_greeks` returns a `BSGreeks` with delta, gamma, vega, theta, rho.
- `quant_core.pricer.conventions`: `to_bp` / `from_bp` convert between dollar floats and basis-point integers. These are the only conversion functions; use them at any boundary where a float must cross into the Lean kernel.
- `quant_core.simulator.gbm`: `simulate_gbm` produces a `PricePath` via exact GBM discretization (no Euler bias), seeded for reproducibility.
- `quant_core.simulator.data_types`: `PricePath` is a source-agnostic price path type accepted by any consumer regardless of whether the path came from GBM, historical data, or a test fixture.

## Install and test

From `foundations/quant-core/python/`:

```bash
uv sync --extra dev
uv run pytest
uv run mypy --strict src/
```

## What the Lean side proves about this layer

The payoff functions in Python compute the same identities that the Lean theorems in `lean/QuantCore/OptionInvariants.lean` prove hold for every admissible integer input. Python computes at runtime for specific inputs; Lean proves for all inputs at once. The basis-point representation is the bridge.

See [`../README.md`](../README.md) for the full module overview and the Lean build instructions.
