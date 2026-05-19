/-
Copyright (c) 2026 Option Hedge Engine Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

import BacktestProofs.Basic

/-!
# BacktestProofs — Options Portfolio Accounting Kernel

Formally verified options portfolio accounting and hedging system (v0.5).

This library provides:
- Exact decimal arithmetic using scaled integers (basis points × 10,000)
- Portfolio state representation with `value_valid` proof field
- Formally proven accounting invariants: `valueIdentity`, `valueUpdateFormula`,
  `selfFinancing`, `quantityConservation`, `cashUpdateCorrect`
- European option settlement: `settlement_value_formula` (crown jewel)
- FFI exports (C symbols via `@[export hedge_*]`) for Cython bridge

Shared option primitives (types, payoff functions, payoff theorems) live in `QuantCore`.

## Module structure

```
Basic.lean                — Core types: AssetId (alias of QuantCore.AssetId), Position, Portfolio, Trade
Accounting.lean           — FFI exports: hedge_apply_trade, hedge_settle_option, …
Invariants.lean           — Accounting theorems (valueUpdateFormula, selfFinancing, …)
Settlement.lean           — Settlement functions: Trade.settlementITM, Portfolio.abandonPosition, applySettlement
SettlementInvariants.lean — Settlement theorems including settlement_value_formula
Tests/UnitTests.lean      — Concrete computation tests via native_decide
```
-/
