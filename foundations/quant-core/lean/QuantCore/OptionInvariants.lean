/-
Copyright (c) 2026 eigenq-xyz Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

import QuantCore.Option

/-!
# Option Payoff Invariants

Formal theorems for European option payoffs (pure integer arithmetic).

This module proves:
- Payoff non-negativity for calls, puts, and any option
- ITM/OTM payoff characterization for calls and puts
- Integer payoff difference identity (discrete analogue of put-call parity)

These theorems depend only on the payoff definitions in `QuantCore.Option`
and have no dependency on portfolios, trades, or settlement logic.
-/

namespace QuantCore

/-! ## Payoff Non-Negativity -/

/-- Call payoff is always non-negative.

    Economic meaning: the holder of a call never owes money at expiry —
    they exercise only when it is profitable to do so. The right but not
    the obligation to buy. -/
theorem callPayoff_nonneg (spot strike : Int) : callPayoff spot strike ≥ 0 := by
  unfold callPayoff; omega

/-- Put payoff is always non-negative.

    Economic meaning: the holder of a put never owes money at expiry —
    they exercise only when it is profitable to do so. The right but not
    the obligation to sell. -/
theorem putPayoff_nonneg (spot strike : Int) : putPayoff spot strike ≥ 0 := by
  unfold putPayoff; omega

/-- Option payoff is always non-negative.

    Economic meaning: a European option can never obligate its holder to
    pay at expiry. This holds for both calls and puts, covering all
    possible spot prices. -/
theorem optionPayoff_nonneg (opt : EuropeanOption) (spot : Int) :
    optionPayoff opt spot ≥ 0 := by
  simp only [optionPayoff]
  cases opt.kind with
  | Call => exact callPayoff_nonneg spot opt.strike
  | Put  => exact putPayoff_nonneg  spot opt.strike

/-! ## Payoff Characterization -/

/-- Call is in-the-money: payoff equals spot minus strike.

    Economic meaning: when the underlying closes above the strike the
    holder receives the intrinsic value (spot − strike) in cash. -/
theorem callPayoff_itm (spot strike : Int) (h : spot > strike) :
    callPayoff spot strike = spot - strike := by
  unfold callPayoff; omega

/-- Call is out-of-the-money (or at-the-money): payoff is zero.

    Economic meaning: when the underlying closes at or below the strike,
    exercising the call is unprofitable and the option expires worthless. -/
theorem callPayoff_otm (spot strike : Int) (h : spot ≤ strike) :
    callPayoff spot strike = 0 := by
  unfold callPayoff; omega

/-- Put is in-the-money: payoff equals strike minus spot.

    Economic meaning: when the underlying closes below the strike the
    holder receives the intrinsic value (strike − spot) in cash. -/
theorem putPayoff_itm (spot strike : Int) (h : spot < strike) :
    putPayoff spot strike = strike - spot := by
  unfold putPayoff; omega

/-- Put is at-the-money or out-of-the-money: payoff is zero.

    Economic meaning: when the underlying closes at or above the strike,
    exercising the put is unprofitable and the option expires worthless. -/
theorem putPayoff_otm (spot strike : Int) (h : spot ≥ strike) :
    putPayoff spot strike = 0 := by
  unfold putPayoff; omega

/-! ## Integer Payoff Difference -/

/-- Integer payoff difference: call payoff minus put payoff equals spot minus strike.

    This is a pure integer identity (max(0,S−K) − max(0,K−S) = S−K), proved by omega.
    It does not model the financial put-call parity relation C − P = S − K·e^{−rT},
    which requires continuous-time pricing and is not expressed here. -/
theorem integerPayoffDifference (spot strike : Int) :
    callPayoff spot strike - putPayoff spot strike = spot - strike := by
  simp only [callPayoff, putPayoff]; omega

end QuantCore
