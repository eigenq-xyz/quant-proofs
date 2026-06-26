# quant-core

Shared pricing primitives for the quant-proofs monorepo: option-type invariants proved in Lean 4, plus a Python pricing and simulation layer (Black-Scholes, Greeks, GBM).

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

**Lean 4** (`lean/QuantCore/`) proves eight theorems about European option payoffs in exact integer arithmetic:

- `callPayoff_nonneg`, `putPayoff_nonneg`, `optionPayoff_nonneg`: a holder never owes money at expiry.
- `callPayoff_itm` / `callPayoff_otm`, `putPayoff_itm` / `putPayoff_otm`: ITM and OTM payoff characterizations.
- `integerPayoffDifference`: `callPayoff − putPayoff = spot − strike` (pure integer identity; not the continuous-time put-call parity relation, which is in `options-proofs`).

All monetary values use basis points (×10,000) as `Int`, enabling exact arithmetic and direct proof via `omega`.

**Python** (`python/`) implements runtime pricing and simulation with no backtester dependencies:

- `quant_core.pricer`: `bs_price` and `bs_greeks` (Black-Scholes via scipy); `to_bp` / `from_bp` basis-point conversion.
- `quant_core.simulator`: `PricePath` type and `simulate_gbm` (seeded exact-discretization GBM).

The basis-point convention (`to_bp` / `from_bp`) is the contract that lets a price computed in Python cross into the Lean kernel as an integer. All floating-point computation stays in Python; Lean reasons in exact arithmetic.

## Who consumes it

Every subproject that needs option types or pricing primitives. Direct dependents:

- [`foundations/options-proofs/`](../options-proofs/) uses the payoff theorems.
- [`extensions/hedge-proofs/`](../../extensions/hedge-proofs/) uses `quant-core` types for the delta-hedge accounting engine.

## Build and test

```bash
# Lean (from foundations/quant-core/lean/)
lake exe cache get
lake build

# Zero-sorry check
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

An empty result from the `grep` means zero `sorry`.

```bash
# Python (from foundations/quant-core/python/)
uv sync --extra dev
uv run pytest
uv run mypy --strict src/
uv run ruff check src/ tests/
```

## Project structure

```
lean/QuantCore/
  Option.lean            - AssetId, OptionKind, EuropeanOption, payoff functions
  OptionInvariants.lean  - 8 payoff theorems (omega-based)
  Tests/UnitTests.lean   - concrete payoff tests via native_decide

python/src/quant_core/
  pricer/
    conventions.py       - to_bp / from_bp (float to basis-point conversion)
    black_scholes.py     - bs_price, bs_greeks (scipy-based)
  simulator/
    data_types.py        - PricePath (source-agnostic price path type)
    gbm.py               - simulate_gbm (seeded exact-discretization GBM)
```

## Dependencies

- Lean: `mathlib` only.
- Python: `numpy`, `scipy`.

## License

Apache 2.0, compatible with mathlib for upstream contribution.
