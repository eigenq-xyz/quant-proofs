# quant-proofs

Formally verified quantitative finance — machine-checked Lean 4 proofs paired with production Python.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What this is

The durable skill in quantitative research is not running backtests — it is knowing whether to trust them. Each project here takes a named result from financial theory or a computational procedure from quantitative research, and makes it formally verifiable: theorem statement as spec, Lean 4 proof as test, zero `sorry` on main.

## Active projects

Status legend: **Complete** = builds with zero `sorry` and `#print axioms` reports only `[propext, Classical.choice, Quot.sound]`. **In progress** = at least one open `sorry` or not yet building cleanly against its dependencies.

| Module | What it proves | Status |
|--------|----------------|--------|
| [`ftap-proofs/`](ftap-proofs/) | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no arbitrage iff an equivalent martingale measure exists | **Complete** — 16 theorems, zero `sorry`, axioms verified |
| [`options-proofs/`](options-proofs/) | Put-call parity `C − P = S₀ − K/(1+r)^T` via the Cox-Ross-Rubinstein binomial model (builds the CRR market, proves it is an EMM and arbitrage-free, then derives parity); depends on `ftap-proofs` | **Complete** — 31 theorems, zero `sorry`, axioms verified |
| [`quant-core/`](quant-core/) | Shared pricing primitives: option type invariants, payoff bounds, Black-Scholes, GBM | **Complete** — 8 theorems |
| [`mortgage-proofs/`](mortgage-proofs/) | LangGraph multi-agent routing invariants, Lean 4-checked trace verification | **Complete** — 13 theorems, zero `sorry` |
| [`optimization-proofs/`](optimization-proofs/) | Projected Gradient Descent for convex QP with an analytical simplex ∩ L₁-ball projection; convergence and projection correctness | **Complete** — 10 theorems, zero `sorry` |
| [`stopped-time-proofs/`](stopped-time-proofs/) | Geometric stopping-time expectations; mathlib-candidate (no finance content) | **In progress** — Jensen (G2.2) is an open `sorry` |
| [`perpetual-proofs/`](perpetual-proofs/) | Perpetual-futures no-arbitrage pricing and the inverse-perp convexity correction | **Complete** — 10 theorems, zero `sorry`; both headline theorems verified (axioms clean). Builds under v4.30.0; depends on `stopped-time-proofs`, whose Jensen (G2.2) is an *unused* open `sorry` |
| [`portfolio-proofs/`](portfolio-proofs/) | Mean-variance allocation with Ledoit-Wolf shrinkage built on `optimization-proofs` (Lean + Python/Cython); stressed-solver scenarios | Applied / empirical |

## Planned

**Formally verified backtester** — an event-driven backtesting engine where the central formal claim is $\mathcal{F}_t$-measurability of signals: provably no look-ahead bias, enforced by the Lean 4 type system. Correctness proofs will cite `ftap-proofs` (now complete).

## Archive

[`archive/position-ledger/`](archive/) — earlier work on a verified position ledger (26 theorems on P&L accounting). Preserved but superseded. See [`archive/README.md`](archive/README.md) for context.

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs/ftap-proofs && lake build   # primary active project
cd quant-proofs/quant-core/lean && lake build
```

## Documentation

Full documentation: [eigenq-xyz.github.io/quant-proofs](https://eigenq-xyz.github.io/quant-proofs)

## License

Apache 2.0 — compatible with mathlib for upstream contribution.
