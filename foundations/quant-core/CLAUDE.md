# CLAUDE.md: foundations/quant-core

Shared pricing primitives for quant-proofs. Lean 4 proves option payoff invariants; Python implements Black-Scholes pricing and GBM simulation. Both layers are pure: no FFI between Lean and Python, no pipeline orchestration, no data loading.

## Build and test

### Lean (run from `foundations/quant-core/lean/`)

```bash
lake exe cache get          # fetch mathlib build cache after lake update
lake build                  # build the library
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # zero-sorry check
```

To run Lean unit tests:

```bash
lake build QuantCore.Tests.UnitTests
```

### Python (run from `foundations/quant-core/python/`)

```bash
uv sync --extra dev
uv run pytest
uv run mypy --strict src/
uv run ruff check src/ tests/
```

## Architecture

```
lean/QuantCore/
  Option.lean            - AssetId, OptionKind, EuropeanOption, callPayoff/putPayoff/optionPayoff
  OptionInvariants.lean  - 8 payoff theorems: non-negativity, ITM/OTM characterization, integer payoff difference
  Tests/UnitTests.lean   - concrete payoff tests via native_decide

python/src/quant_core/
  pricer/
    conventions.py       - to_bp / from_bp (the only float-to-int conversion point)
    black_scholes.py     - bs_price (BSPrice with value + value_bp), bs_greeks (BSGreeks)
  simulator/
    data_types.py        - PricePath (source-agnostic price path)
    gbm.py               - simulate_gbm (exact-discretization GBM, seeded)
```

## The basis-point contract

All monetary values in Lean use basis points (×10,000) as `Int`. Python computes in floats and converts at the boundary via `to_bp` / `from_bp` in `conventions.py`. This is the only place conversion happens. Do not convert to basis points inside pricing or simulation logic; convert only at the explicit boundary.

## Hard rules

- No FFI between Lean and Python in this module. No Cython. No ctypes. No pipeline orchestration.
- Lean depends only on `mathlib`.
- Python depends only on `numpy` and `scipy`.
- `mypy --strict` must pass on all Python in `src/`.
- Zero `sorry` on `main`. No exceptions.
- Apache 2.0 license: do not add dependencies with incompatible licenses.
