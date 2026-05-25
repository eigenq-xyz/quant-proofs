# archive/

This directory preserves earlier work that has been superseded. Nothing here is deleted — the proofs are real and the code ran — but these projects are no longer active.

## Contents

### `position-ledger/`

Originally called `backtest-proofs`. Contains 26 Lean 4 theorems proving correctness of a position ledger: mark-to-market identity, cash flow tracking, self-financing constraints. A delta-hedging simulation ran on top of it as a demo.

**Why archived:** Pivoting to build a proper backtester from first principles, starting with the Discrete FTAP (Harrison-Pliska 1981) as the theoretical foundation, then put-call parity via the CRR binomial model, then a real event-driven backtesting engine. The position ledger work is preserved here as a reference.
