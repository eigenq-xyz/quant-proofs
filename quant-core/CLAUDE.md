# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Shared pricing primitives for the quant-proofs monorepo. Provides types and
theorems that are independent of any specific backtester or pipeline.

Lean 4 proves properties of option payoffs. Python implements pricing (Black-Scholes)
and simulation (GBM). Both are pure — no FFI, no pipeline orchestration, no data loading.

## Build & Test Commands

### Lean (from `lean/`)

- `lake exe cache get` — fetch mathlib build cache (run after `lake update`)
- `lake build` — build the library
- `lake build QuantCore.Tests.UnitTests` — run Lean tests
- `lake build --watch` — rebuild on file changes

### Python (from `python/`)

- `uv sync --extra dev` — install dependencies
- `uv run pytest -v` — run tests
- `uv run mypy src/ --strict` — type check
- `uv run ruff check src/ tests/` — lint

## Architecture

```
lean/QuantCore/
  Option.lean            — AssetId, OptionKind, EuropeanOption, payoff functions
  OptionInvariants.lean  — 8 pure payoff theorems (omega-based)
  Tests/UnitTests.lean   — concrete payoff tests via native_decide

python/src/quant_core/
  pricer/
    conventions.py       — to_bp / from_bp (float ↔ basis-point conversion)
    black_scholes.py     — bs_price, bs_greeks (scipy-based)
  simulator/
    data_types.py        — PricePath (source-agnostic price path type)
    gbm.py               — simulate_gbm (seeded GBM path generator)
```

## Constraints

- No FFI. No Cython. No pipeline orchestration. No data loading.
- Lean depends only on mathlib.
- Python depends only on numpy and scipy.
- Apache 2.0 license matches mathlib so Lean content can flow upstream.
