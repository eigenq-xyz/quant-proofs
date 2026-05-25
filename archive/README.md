# archive/

This directory preserves earlier work that has been superseded or retired. Nothing here is deleted — the proofs are real and the code ran — but the projects are no longer active or representative of the current research direction.

## Contents

### `position-ledger/`

Originally called `backtest-proofs`. Contains 26 Lean 4 theorems proving correctness of a position ledger: mark-to-market identity, cash flow tracking, self-financing constraints. A delta-hedging simulation ran on top of it as a demo.

**Why archived:** The project was framed as a backtester, which it was not. A real backtester requires a historical event loop, formally constrained signal generation (measurability), realistic execution modeling, and statistically correct performance attribution. None of that existed here. The accounting theorems are correct but narrow in scope; calling them a backtester was inaccurate.

**What comes next:** A real event-driven backtester is planned, with the central formal claim being $\mathcal{F}_t$-measurability of signals — provable no-look-ahead bias enforced by the Lean 4 type system. That work will live in `backtest-proofs/` once built, and will cite results from `ftap-proofs/`.
