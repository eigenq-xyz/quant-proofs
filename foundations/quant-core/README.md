# quant-core

Shared pricing primitives for the quant-proofs monorepo: option-type invariants proved in Lean 4, plus a Python pricing and simulation layer (Black-Scholes, Greeks, GBM).

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

**Lean 4** (`lean/QuantCore/`) proves eight theorems about European option payoffs in exact integer arithmetic.

| Guarantee | Theorem |
| --------- | ------- |
| A holder never owes money at expiry | `callPayoff_nonneg`, `putPayoff_nonneg`, `optionPayoff_nonneg` |
| ITM/OTM payoff characterization, call | `callPayoff_itm`, `callPayoff_otm` |
| ITM/OTM payoff characterization, put | `putPayoff_itm`, `putPayoff_otm` |
| `callPayoff − putPayoff = spot − strike` (integer identity; not the continuous-time put-call parity relation, which is in `options-proofs`) | `integerPayoffDifference` |

All monetary values use basis points (×10,000) as `Int`, enabling exact arithmetic and direct proof via `omega`. Zero `sorry` (Lean's placeholder tactic for "trust me, no proof yet"; none remain, so no unproven steps).

**Python** (`python/`) implements runtime pricing and simulation with no backtester dependencies:

- `quant_core.pricer`: `bs_price` and `bs_greeks` (Black-Scholes via scipy); `to_bp` / `from_bp` basis-point conversion.
- `quant_core.simulator`: `PricePath` type and `simulate_gbm` (seeded exact-discretization GBM).

The basis-point convention (`to_bp` / `from_bp`) is the contract that lets a price computed in Python cross into the Lean kernel as an integer. All floating-point computation stays in Python; Lean reasons in exact arithmetic.

## What it doesn't claim

The basis-point contract is enforced by code convention, not proved correct in Lean. Nothing in Lean verifies that the Python conversion is called correctly, and there is no FFI between the two layers in this module. The Python pricing and simulation layer (Black-Scholes, GBM) is rigorous but not formally verified: it is ordinary numerical code, checked by `pytest`, not by Lean.

## Build and verify

```bash
# Lean (from foundations/quant-core/lean/)
lake exe cache get
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty output = clean

# Python (from foundations/quant-core/python/)
uv sync --extra dev
uv run pytest
```

Full build/test/lint/type-check matrix: see `CLAUDE.md`.

## Who consumes it

- [`foundations/options-proofs/`](../options-proofs/) uses the payoff theorems.
- [`extensions/hedge-proofs/`](../../extensions/hedge-proofs/) uses `quant-core` types for the delta-hedge accounting engine.

## Dependencies

- Lean: `mathlib` only.
- Python: `numpy`, `scipy`.

## License

Apache License 2.0.
