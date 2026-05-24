# quant-proofs — EigenQ Research Series

Formally verified quantitative finance — Lean 4 machine-checked proofs paired with production-quality Python execution.

The organizing principle: before trusting a numerical result, prove the accounting correct. Every project in the EigenQ Research Series pairs a formal proof with the code that runs in production.

## Projects

### quant-core

Shared pricing primitives used by `backtest-proofs` and `options-proofs`. Provides the canonical `EuropeanOption` type (with `strike_pos` invariant), payoff functions, and 8 machine-checked theorems covering payoff non-negativity, ITM/OTM characterization, and the integer payoff identity `callPayoff − putPayoff = spot − strike`. The Python side provides Black-Scholes pricing, Greeks, and the `PricePath` / GBM simulator — all without any backtester dependency.

### backtest-proofs

Options delta-hedging backtester with a Lean 4 accounting module. 19 BacktestProofs theorems (13 accounting + 6 settlement) plus 8 from QuantCore — 27 total, zero `sorry`. Proves portfolio value identity, self-financing, and `settlement_value_formula` (ΔPV = qty × (payoff − mark), covering ITM and OTM expiry). Python calls the module via Cython FFI; the accounting layer cannot silently mis-report results regardless of strategy complexity.

See the [full documentation](https://eigenq-xyz.github.io/quant-proofs/backtest-proofs/intro.html) including formal guarantees, validation, and architecture.

Read the research paper: [Provably Correct Quantitative Backtesting (PDF)](https://eigenq-xyz.github.io/quant-proofs/paper/backtest-proofs.pdf)

### ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (Harrison and Pliska, 1981): a finite-state, discrete-time market is arbitrage-free if and only if an equivalent martingale measure exists. Targeting a mathlib PR.

Status: skeleton — proof content planned; targeting a mathlib PR.

### options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model. Imports `quant-core` for shared option types and payoff theorems; the CRR pricing theorems build directly on `QuantCore.Option` and `QuantCore.OptionInvariants`. The FTAP connection (risk-neutral measure → put-call parity) depends on `ftap-proofs`.

Status: skeleton — depends on `quant-core` (active) and `ftap-proofs` (planned).

### mortgage-proofs

LangGraph multi-agent mortgage pipeline (intake, risk, compliance, underwriter agents) with formally verified routing invariants. Agent decisions are recorded as `DecisionRecord` JSON and validated against Lean 4 invariants via `lake exe verify-trace`.

## Repository

- **GitHub:** [eigenq-xyz/quant-proofs](https://github.com/eigenq-xyz/quant-proofs)
- **License:** Apache 2.0

## Status

| Project | Theorems | Status | Links |
|---------|----------|--------|-------|
| quant-core | 8 (zero sorry) | v1.0 — stable | [Docs](quant-core.html) |
| backtest-proofs | 27 (zero sorry) | v0.5 — paper published | [Docs](https://eigenq-xyz.github.io/quant-proofs/backtest-proofs/intro.html) · [Paper (PDF)](https://eigenq-xyz.github.io/quant-proofs/paper/backtest-proofs.pdf) |
| ftap-proofs | — | Skeleton | [Docs](ftap-proofs.html) |
| options-proofs | — | Skeleton (depends on ftap-proofs) | [Docs](options-proofs.html) |
| mortgage-proofs | — | Active development | [Docs](mortgage-proofs.html) |
