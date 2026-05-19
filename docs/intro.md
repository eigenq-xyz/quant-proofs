# quant-proofs

Formally verified quantitative finance — Lean 4 machine-checked proofs paired with production-quality Python execution.

The organizing principle: before trusting a numerical result, prove the accounting correct. Every project here pairs a formal proof with the code that runs in production.

## Projects

### backtest-proofs

Options delta-hedging backtester with a Lean 4 accounting kernel. The kernel (26 theorems, zero `sorry`) proves portfolio value identity, self-financing, and settlement-value formulae. Python calls the kernel via Cython FFI; the accounting layer cannot silently mis-report results regardless of strategy complexity.

See the [full documentation](backtest-proofs).

### ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (Harrison and Pliska, 1981): a finite-state, discrete-time market is arbitrage-free if and only if an equivalent martingale measure exists. Targeting a mathlib PR.

Status: in progress (Summer 2026).

### binomial-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model. The CRR model is a finite-state market where the FTAP from `ftap-proofs` applies, giving an explicit risk-neutral measure; put-call parity is a corollary.

Status: in progress (Summer 2026), depends on `ftap-proofs`.

### mortgage-proofs

LangGraph multi-agent mortgage pipeline (intake, risk, compliance, underwriter agents) with formally verified routing invariants. Agent decisions are recorded as `DecisionRecord` JSON and validated against Lean 4 invariants via `lake exe verify-trace`.

## Repository

- **GitHub:** [eigenq-xyz/quant-proofs](https://github.com/eigenq-xyz/quant-proofs)
- **License:** Apache 2.0
