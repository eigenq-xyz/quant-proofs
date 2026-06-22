/-
Copyright (c) 2026 eigenq-xyz Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

/-!
# Options Primitives

Shared types and payoff functions for European options.

This module defines:
- `AssetId`: string identifier for a tradeable asset
- `OptionKind`: Call or Put
- `EuropeanOption`: option contract with type-level strike positivity
- `callPayoff`, `putPayoff`, `optionPayoff`: payoff functions (non-negative, exact integer)

## Design Notes

All monetary values use **basis points** (×10,000) as `Int`.
Example: $50.25 = 502,500 basis points.

Payoff functions operate on integers to enable exact arithmetic and
direct use in formal proofs via `omega`.
-/

namespace QuantCore

/-- String identifier for a tradeable asset. -/
abbrev AssetId := String

/-- Call or Put -/
inductive OptionKind where
  | Call
  | Put
  deriving DecidableEq, Repr, BEq

/-- A European option contract.

The `strike_pos` field is a proof that `strike > 0`,
making it impossible to construct an option with a non-positive strike. -/
structure EuropeanOption where
  assetId   : AssetId
  kind      : OptionKind
  strike    : Int
  strike_pos : strike > 0
  deriving DecidableEq

instance : BEq EuropeanOption := ⟨fun a b => decide (a = b)⟩

instance : Repr EuropeanOption where
  reprPrec o _ :=
    s!"EuropeanOption(assetId := {repr o.assetId}, kind := {repr o.kind}, strike := {repr o.strike})"

/-- Smart constructor: builds a EuropeanOption with strike proved positive.
    The proof is auto-discharged by `omega` for concrete positive literals. -/
def EuropeanOption.mk' (assetId : AssetId) (kind : OptionKind) (strike : Int)
    (h : strike > 0 := by omega) : EuropeanOption :=
  ⟨assetId, kind, strike, h⟩

/-- Call payoff: max(spot − strike, 0) -/
@[inline]
def callPayoff (spot strike : Int) : Int := max 0 (spot - strike)

/-- Put payoff: max(strike − spot, 0) -/
@[inline]
def putPayoff (spot strike : Int) : Int := max 0 (strike - spot)

/-- Option payoff dispatched by kind -/
def optionPayoff (opt : EuropeanOption) (spot : Int) : Int :=
  match opt.kind with
  | .Call => callPayoff spot opt.strike
  | .Put  => putPayoff  spot opt.strike

end QuantCore
