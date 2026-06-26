# hedge-proofs

A formally verified delta-hedge accounting engine: Lean 4 proofs of self-financing,
settlement-value, and portfolio value-update invariants over a discrete rebalancing schedule.

Cites [`foundations/quant-core/`](../../foundations/quant-core/) for option types and payoff bounds.

## What it proves

The engine tracks a portfolio of positions and cash through a sequence of trades and
expiries. Three groups of invariants are proved:

**Portfolio value identity and domain constraints.**
Portfolio value always equals cash plus the sum of mark-to-market position values. Mark
prices are structurally positive (enforced at construction). Fees are non-negative.

**Trade invariants.**
`cashUpdateCorrect`: cash is debited by exactly `deltaQuantity * executionPrice + fee`.
`quantityConservation`: post-trade quantity equals pre-trade quantity plus `deltaQuantity`.
`valueUpdateFormula`: the change in portfolio value equals the pre-trade quantity times
the price improvement minus the fee. No value leaks through rounding or representation.

**Self-financing.**
`selfFinancing`: a trade executed at the existing mark price changes portfolio value only
by the fee. `selfFinancingWithCost` is the named-fee variant.

**Settlement invariants.**
`settlement_value_formula` is the crown-jewel result: settling an option changes portfolio
value by `quantity * (payoff - mark)`, covering both the in-the-money path (close via trade)
and the out-of-the-money path (abandon worthless position) in a single equation.

All 19 theorems build with zero `sorry`. "Verified" means `#print axioms` reports only
`[propext, Classical.choice, Quot.sound]`. The statistical and execution layers above this
engine are not formally verified.

## Relation to a hedging backtest

A delta-hedging strategy rebalances a position in the underlying to offset option exposure.
This engine verifies the accounting layer: that each rebalance is self-financing (no hidden
P&L from the accounting rules themselves), that settlement credit flows through cash
correctly, and that the portfolio value identity holds at every step. These are the
preconditions any honest backtest must satisfy before attributing P&L to the strategy.

## Build

```bash
cd extensions/hedge-proofs
lake exe cache get
lake build
```

## Test

Zero-sorry check:

```bash
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake extensions/hedge-proofs/
```

An empty result means the build is clean. Concrete unit tests are in
`BacktestProofs/Tests/UnitTests.lean` and run as part of `lake build`.

## Project structure

| File | Contents |
|------|----------|
| `BacktestProofs/Basic.lean` | `Position`, `Portfolio`, `Trade` types with type-level invariants; `applyTrade` |
| `BacktestProofs/Invariants.lean` | `valueIdentity`, `cashUpdateCorrect`, `quantityConservation`, `valueUpdateFormula`, `selfFinancing`, `selfFinancingWithCost`, well-formedness theorems |
| `BacktestProofs/Settlement.lean` | `settleEuropeanOption`, `applySettlement`, ITM and OTM settlement paths |
| `BacktestProofs/SettlementInvariants.lean` | `settlement_value_formula` and supporting lemmas |
| `BacktestProofs/Accounting.lean` | C-callable FFI exports (the `hedge_` prefix symbols) |
| `BacktestProofs/Tests/UnitTests.lean` | Concrete `#eval`/`native_decide` unit tests |
| `lakefile.lean` | Package config; depends on `mathlib` and `quant-core` |
