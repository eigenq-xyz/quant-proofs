# quant-core

> The shared pricing primitives the rest of the monorepo builds on: option payoff types and theorems proved in Lean 4, plus a pure Python pricing and simulation layer (Black-Scholes, Greeks, GBM). The payoff identities Python computes are the same ones Lean proves hold for every input. Zero `sorry`.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/black_scholes_gbm.ipynb)

## What's here

This is the foundation layer: types and results that are independent of any backtester or pipeline, so every other project can depend on it without pulling in execution code.

**Lean 4** (`lean/`) proves properties of European option payoffs.

- `QuantCore.Option`: `AssetId`, `OptionKind`, `EuropeanOption`, and the `callPayoff` / `putPayoff` / `optionPayoff` functions.
- `QuantCore.OptionInvariants`: 8 payoff theorems (payoff non-negativity, in-the-money and out-of-the-money characterization, and the put-call payoff identity), all with zero `sorry`.

**Python** (`python/`) implements the runtime pricing and simulation, with no backtester dependencies.

- `quant_core.pricer`: Black-Scholes price and Greeks (delta, gamma, vega, theta, rho), plus basis-point conventions for the FFI boundary.
- `quant_core.simulator`: a source-agnostic `PricePath` type and a seeded GBM path generator.

## Why a verified core matters

The same facts live on both sides of the FFI boundary, but for different reasons. Python computes a put-call payoff identity for a specific set of inputs at runtime; Lean proves that identity holds for *every* admissible input. The split is deliberate: all floating-point computation stays in Python, while Lean reasons in exact arithmetic and never touches a float. The basis-point conventions (`to_bp` / `from_bp`) are the contract that lets a price computed in Python cross into the Lean kernel as an integer.

## Try it (no install)

The [Black-Scholes and GBM notebook](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/black_scholes_gbm.ipynb) prices European options, plots the Greeks, simulates GBM paths, and checks the put-call payoff identity numerically. The Lean theorems in `lean/` are what guarantee that identity for all inputs at once.

## Build and test

```bash
# Lean
cd lean && lake exe cache get && lake build

# Python
cd python && uv sync --extra dev && uv run pytest
```

## Dependencies

- Lean: `mathlib` only.
- Python: `numpy`, `scipy`.

## Used by

Every other project in the monorepo that needs option types or pricing primitives, including [`options-proofs`](../options-proofs/) (shared payoff theorems).

## License

Apache License 2.0.
