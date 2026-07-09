# hedge-proofs

A formally verified delta-hedge accounting engine: Lean 4 proofs of self-financing,
settlement-value, and portfolio value-update invariants over a discrete rebalancing schedule.

Cites [`foundations/quant-core/`](../../foundations/quant-core/) for option types and payoff bounds.

## What it proves

The engine tracks a portfolio of positions and cash through a sequence of trades and
expiries. 19 theorems, zero `sorry` (`grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .`
returns empty). `#print axioms` on each reports only `[propext, Classical.choice, Quot.sound]`.

| Guarantee | Theorem |
|---|---|
| Portfolio value = cash + sum of mark-to-market position values | `valueIdentity` |
| Mark prices are structurally positive | `pricesPositive` |
| Fees are non-negative | `feeNonNegative` |
| Cash is debited by exactly `deltaQuantity * executionPrice + fee` | `cashUpdateCorrect` |
| Post-trade quantity = pre-trade quantity + `deltaQuantity` | `quantityConservation` |
| Portfolio value change = pre-trade quantity * price improvement, minus fee | `valueUpdateFormula` |
| A trade at the existing mark price changes portfolio value only by the fee | `selfFinancing` (named-fee variant: `selfFinancingWithCost`) |
| Settling an option changes portfolio value by `quantity * (payoff - mark)`, covering both the in-the-money (close via trade) and out-of-the-money (abandon worthless position) paths | `settlement_value_formula` |

This engine covers the accounting layer only: that each rebalance is self-financing, that
settlement credit flows through cash correctly, and that the portfolio value identity holds
at every step. The statistical and execution layers above this engine — signal generation,
P&L attribution, backtest economics — are not formally verified.

## Build and verify

```bash
cd extensions/hedge-proofs
lake exe cache get
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

Unit tests are in `BacktestProofs/Tests/UnitTests.lean` and run as part of `lake build`.
Full build/test matrix: see CLAUDE.md.

## Dependencies

Cites `foundations/quant-core/` for `EuropeanOption`, `optionPayoff`, `optionPayoff_nonneg`.

## License

Apache License 2.0.
