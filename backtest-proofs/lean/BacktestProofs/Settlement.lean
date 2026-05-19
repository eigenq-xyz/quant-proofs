/-
Copyright (c) 2026 Option Hedge Engine Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

import BacktestProofs.Basic
import QuantCore.Option

/-!
# European Option Settlement

Functions for settling European options into a portfolio.

This module defines:
- `Trade.settlementITM`: Closing trade for in-the-money expiry
- `Portfolio.abandonPosition`: Erase a worthless position (OTM expiry)
- `SettlementResult`, `EuropeanOption.settle`, `applySettlement`: Unified settlement

Option types and payoff functions live in `QuantCore.Option`.
Settlement invariants (including `settlement_value_formula`) live in
`BacktestProofs.SettlementInvariants`.

## Design Notes

`executionPrice_pos` on `Trade` requires `executionPrice > 0`.  OTM options have payoff 0,
which would violate this constraint, so OTM settlement uses `Portfolio.abandonPosition`
(erase the position via `Portfolio.mk'`) rather than `applyTrade`.  The crown-jewel theorem
`settlement_value_formula` in `SettlementInvariants.lean` unifies both branches.
-/

namespace BacktestProofs

open QuantCore

/-- Build the settlement trade for an ITM option.

    Semantics: close the entire position at `payoff` basis points per share.
    Requires `payoff > 0` (i.e., the option is strictly in-the-money) to satisfy
    `Trade.executionPrice_pos`. -/
def Trade.settlementITM (opt : EuropeanOption) (currentQty payoff : Int)
    (h : payoff > 0) : Trade :=
  Trade.mk' opt.assetId (-currentQty) payoff 0 h (by omega)

/-- Remove a worthless (OTM) position from the portfolio.

    Erases the position and recomputes `portfolioValue` via `Portfolio.mk'`,
    so the portfolio value drops by exactly `pos.value`. -/
def Portfolio.abandonPosition (p : Portfolio) (id : AssetId) : Portfolio :=
  Portfolio.mk' p.cash (p.positions.erase id)

/-- Result of option settlement: either ITM (with a closing trade) or OTM. -/
inductive SettlementResult where
  | ITM (t : Trade)
  | OTM

/-- Determine settlement outcome given spot price and current quantity.

    - ITM: payoff > 0 → close with a `settlementITM` trade
    - OTM: payoff = 0 → abandon the position (no cash impact) -/
def settleEuropeanOption (opt : EuropeanOption) (spot currentQty : Int) :
    SettlementResult :=
  let payoff := optionPayoff opt spot
  if h : payoff > 0 then
    .ITM (Trade.settlementITM opt currentQty payoff h)
  else
    .OTM

/-- Apply a settlement result to a portfolio.

    - ITM: call `applyTrade` with the closing trade
    - OTM: call `abandonPosition` to erase the worthless position -/
def applySettlement (p : Portfolio) (opt : EuropeanOption)
    (sr : SettlementResult) : Portfolio :=
  match sr with
  | .ITM t => applyTrade p t
  | .OTM   => p.abandonPosition opt.assetId

end BacktestProofs
