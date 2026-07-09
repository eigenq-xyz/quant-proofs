# backtest-proofs (archived)

**Archived.** Superseded by the FTAP-first rebuild (`foundations/ftap-proofs/` →
`foundations/options-proofs/` → `research-pipeline/`). Nothing here is deleted or wrong — the
proofs are real and the code ran — but this project is frozen history, not active code. See
`archive/README.md` for why. Full design rationale (ADRs, risk register, dev process) lives in
this directory's own `CONTRIBUTING.md`, `DECISIONS.md`, `DEVELOPMENT.md`, and `RISKS.md` files
in git history as of the archival commit — not reproduced here.

## What it was

Options portfolio delta-hedging backtester. Lean 4 proved the accounting layer (portfolio
value, trades, option settlement); Python handled data engineering, Black-Scholes pricing,
GBM simulation, and backtest orchestration. A Cython FFI bridged the two — Lean compiled to C
via Lake (`@[export]`), wrapped by Cython, called from Python. Basis-point integers were the
only numeric type crossing the FFI boundary; Lean never touched floats.

## What was proved

27 theorems, zero `sorry`, zero `axiom`:

| Layer | Count | Key theorems |
|---|---|---|
| Option payoffs (`QuantCore.OptionInvariants`) | 8 | `callPayoff_nonneg`, `putPayoff_nonneg`, `optionPayoff_nonneg`, ITM/OTM exactness |
| Accounting kernel (`Invariants.lean`) | 12 | `valueIdentity`, `cashUpdateCorrect`, `quantityConservation`, `valueUpdateFormula`, `selfFinancing` |
| Settlement (`SettlementInvariants.lean`) | 6 | `abandonPosition_portfolioValue`, `settlement_cash_itm`, **`settlement_value_formula`** |
| **Total** | **26 code theorems** (27 counting `integerPayoffDifference`, a pure-integer identity not classified above) | |

**Crown jewel — `settlement_value_formula`:** one theorem statement unifies both settlement
branches (ITM and OTM):

```lean
theorem settlement_value_formula (p : Portfolio) (opt : EuropeanOption)
    (pos : Position) (hPos : p.getPosition opt.assetId = some pos)
    (spot : Int) :
    (applySettlement p opt (settleEuropeanOption opt spot pos.quantity)).portfolioValue =
      p.portfolioValue + pos.quantity * (optionPayoff opt spot - pos.markPrice)
```

ΔPV = qty × (payoff − mark) holds identically whether the option expires ITM (settles at the
payoff price) or OTM (payoff = 0, position written off). Impossible-by-construction states this
type system ruled out: negative-price positions, negative fees, ghost zero-quantity positions
after a trade, wrong cash after any trade sequence.

## What was not verified

Pricing (Black-Scholes, Greeks), the delta-hedging strategy, the simulator, ETL, and backtest
orchestration were conventional Python — not formally verified. Proofs covered the accounting
layer only: invariants that must hold regardless of which strategy or pricing model sits on top.

## Numerical validation (not formal proof)

- Black-Scholes pricer matched Hull/DerivaGem reference vectors within `abs=0.01` (price),
  `abs=0.001` (delta).
- 500 seeded GBM paths × 20 weekly steps: mean discrete-hedge cost within ±3% of the BS price;
  all 10,000 step certificates passed `valueUpdateFormula`.
- BKL (2000) variance scaling and Carr-Madan (1998) P&L decomposition both replicated.

## Repository structure (as archived)

```text
lean/BacktestProofs/       # Basic, Accounting (FFI exports), Invariants, Settlement,
                           # SettlementInvariants, Tests/UnitTests
python/src/backtest_proofs/  # pricer/, etl/ (WRDS), simulator/ (GBM), backtest/, ffi/
docs/                      # JupyterBook source (archived, not built)
data/                      # WRDS OptionMetrics + FRED, git-crypt encrypted
```

## Disclaimer

Educational and research use only. Not intended for live trading or real financial
decision-making. No warranty, no financial advice. Formal verification does not guarantee
correctness for real-world trading — it eliminates one class of bug (accounting errors), not
all classes. Submitting this code as your own academic coursework is plagiarism under most
institutions' policies.

Apache 2.0. Research software, not production trading infrastructure.

## References

Hull, *Options, Futures, and Other Derivatives*, 9th ed. (2014), Tables 19.2–19.3 · Leland
(1985), *JF* 40(4) · Bertsimas, Kogan & Lo (2000), *JFE* 55(2) · Carr & Madan (1998)
