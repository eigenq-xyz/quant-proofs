/-
Copyright (c) 2026 eigenq-xyz Contributors. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Akhil Karra
-/

import QuantCore.Option

/-!
# Unit Tests

Concrete tests for option payoff functions.
All prices in basis points (×10,000).
-/

namespace QuantCore.Tests

/-! ## Option payoffs -/

-- Call ITM: spot=$55, strike=$50 → payoff = $5.00 (50,000 bp)
example : callPayoff 550000 500000 = 50000 := by native_decide

-- Call OTM: spot=$45, strike=$50 → payoff = $0
example : callPayoff 450000 500000 = 0 := by native_decide

-- Call ATM: spot=$50, strike=$50 → payoff = $0
example : callPayoff 500000 500000 = 0 := by native_decide

-- Put ITM: spot=$45, strike=$50 → payoff = $5.00 (50,000 bp)
example : putPayoff 450000 500000 = 50000 := by native_decide

-- Put OTM: spot=$55, strike=$50 → payoff = $0
example : putPayoff 550000 500000 = 0 := by native_decide

-- Integer put-call parity: call - put = spot - strike
example : callPayoff 550000 500000 - putPayoff 550000 500000 = 550000 - 500000 := by native_decide
example : callPayoff 450000 500000 - putPayoff 450000 500000 = 450000 - 500000 := by native_decide

end QuantCore.Tests
