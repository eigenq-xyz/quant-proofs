# quant-proofs — EigenQ Research Series

Formally verified quantitative finance — Lean 4 machine-checked proofs paired with
production-quality Python execution.

The organizing principle: the durable skill in quantitative research is not running
backtests — it is knowing whether to trust them. Every project here takes a named
result from financial theory and makes it formally verifiable: theorem statement as
spec, Lean 4 proof as test, zero `sorry` on main.

## Active projects

### ftap-proofs

Lean 4 proof of the Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981):
a finite-state, discrete-time market is arbitrage-free if and only if an equivalent
martingale measure exists. This is the foundational result underlying all of derivative
pricing theory. Targeting a mathlib PR.

**Status:** In progress — see [ROADMAP](https://github.com/eigenq-xyz/quant-proofs/blob/main/ftap-proofs/ROADMAP.md) for the 5-phase task breakdown.

### options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model. Imports
`quant-core` for shared option types; the no-arbitrage argument cites `ftap-proofs`.

**Status:** Planned — depends on `ftap-proofs`.

### quant-core

Shared pricing primitives: `EuropeanOption` type, payoff bounds, Black-Scholes, GBM
simulator. 8 theorems, zero `sorry`, stable.

### mortgage-proofs

LangGraph multi-agent mortgage pipeline (intake, risk, compliance, underwriter) with
Lean 4-checked routing invariants. Agent decisions are recorded as `DecisionRecord` JSON
and validated via `lake exe verify-trace`.

**Status:** Active development.

## Status

| Project | Theorems | Status |
|---------|----------|--------|
| `ftap-proofs` | — | In progress |
| `options-proofs` | — | Planned (depends on ftap-proofs) |
| `quant-core` | 8 (zero sorry) | v1.0 stable |
| `mortgage-proofs` | — | Active |

## Repository

- **GitHub:** [eigenq-xyz/quant-proofs](https://github.com/eigenq-xyz/quant-proofs)
- **License:** Apache 2.0
