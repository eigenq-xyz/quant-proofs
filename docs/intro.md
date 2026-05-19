# quant-proofs

Formally verified quantitative finance — Lean 4 machine-checked proofs paired with production-quality Python execution.

The organizing principle: before trusting a numerical result, prove the accounting correct. Every project here pairs a formal proof with the code that runs in production.

## Projects

### quant-core

Shared pricing primitives used by `backtest-proofs` and `options-proofs`. Provides the canonical `EuropeanOption` type (with `strike_pos` invariant), payoff functions, and 8 machine-checked theorems covering payoff non-negativity, ITM/OTM characterization, and the integer payoff identity `callPayoff − putPayoff = spot − strike`. The Python side provides Black-Scholes pricing, Greeks, and the `PricePath` / GBM simulator — all without any backtester dependency.

### backtest-proofs

Options delta-hedging backtester with a Lean 4 accounting kernel. 18 BacktestProofs theorems plus 8 from QuantCore, zero `sorry`. Proves portfolio value identity, self-financing, and `settlement_value_formula` (ΔPV = qty × (payoff − mark), unifying ITM and OTM expiry). Python calls the kernel via Cython FFI; the accounting layer cannot silently mis-report results regardless of strategy complexity.

See the [full documentation](https://eigenq-xyz.github.io/quant-proofs/backtest-proofs/intro.html) including formal guarantees, validation, and architecture.

### ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (Harrison and Pliska, 1981): a finite-state, discrete-time market is arbitrage-free if and only if an equivalent martingale measure exists. Targeting a mathlib PR.

Status: in progress (Summer 2026).

### options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model. Imports `quant-core` for shared option types and payoff theorems; the CRR pricing theorems build directly on `QuantCore.Option` and `QuantCore.OptionInvariants`. The FTAP connection (risk-neutral measure → put-call parity) depends on `ftap-proofs`.

Status: in progress (Summer 2026), depends on `quant-core` (active) and `ftap-proofs` (planned).

### mortgage-proofs

LangGraph multi-agent mortgage pipeline (intake, risk, compliance, underwriter agents) with formally verified routing invariants. Agent decisions are recorded as `DecisionRecord` JSON and validated against Lean 4 invariants via `lake exe verify-trace`.

## Repository

- **GitHub:** [eigenq-xyz/quant-proofs](https://github.com/eigenq-xyz/quant-proofs)
- **License:** Apache 2.0
