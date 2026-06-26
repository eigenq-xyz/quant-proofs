# CLAUDE.md: hedge-proofs

Formally verified delta-hedge accounting engine. Namespace: `BacktestProofs` (historical name from the archived engine; kept for continuity).

## Build

```bash
cd extensions/hedge-proofs
lake exe cache get   # fetch mathlib cache before first build
lake build
```

## Test

Zero-sorry check (empty output = clean):

```bash
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake extensions/hedge-proofs/
```

Unit tests compile with `lake build` via `BacktestProofs/Tests/UnitTests.lean`.

## Architecture

| Module | Role |
|--------|------|
| `BacktestProofs/Basic.lean` | Core types: `Position` (price proved positive at construction), `Portfolio` (value proved equal to cash + positions at construction), `Trade` (fee proved non-negative); `applyTrade` |
| `BacktestProofs/Invariants.lean` | All trade invariants: `valueIdentity`, `cashUpdateCorrect`, `quantityConservation`, `valueUpdateFormula`, `selfFinancing`, `selfFinancingWithCost`; well-formedness preservation under `applyTrade` |
| `BacktestProofs/Settlement.lean` | `settleEuropeanOption` (ITM/OTM dispatch), `applySettlement`; OTM uses `abandonPosition`, ITM uses `applyTrade` via `Trade.settlementITM` |
| `BacktestProofs/SettlementInvariants.lean` | `settlement_value_formula` (crown jewel: value change = qty * (payoff - mark), both branches); supporting lemmas for abandonment and ITM cash credit |
| `BacktestProofs/Accounting.lean` | `@[export hedge_*]` C-callable FFI wrappers; no new theorems |
| `BacktestProofs/Tests/UnitTests.lean` | `native_decide` unit tests; basis-point convention (all prices x10,000) |

## Dependencies

- `mathlib` pinned at commit `5719ef278ac6921b1a68b558d9282377f93d0b80`
- `quant-core` (local, `../../foundations/quant-core/lean`): provides `EuropeanOption`, `optionPayoff`, `optionPayoff_nonneg`

## Numeric convention

All monetary values in basis points (x10,000). $50.00 = 500,000 bp. This is enforced throughout and required by the FFI contract.

## Hard rules

- Zero `sorry` on main. No exceptions.
- Do not extend `archive/` or reference it as active code.
- Do not commit licensed data (WRDS, OptionMetrics, Polygon paid tiers).
- No private content: no GPA, no target firm names, no personal timelines.
- `lake build` must stay clean before any PR. Run the sorry grep to confirm.
