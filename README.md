# quant-proofs: EigenQ Research Series

Formally verified quantitative finance: machine-checked Lean 4 proofs paired with production Python.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What this is

The durable skill in quantitative research is not running backtests: it is knowing whether to trust them. Each project here takes a named result from financial theory or a computational procedure from quantitative research, and makes it formally verifiable: theorem statement as spec, Lean 4 proof as test, zero `sorry` on main.

## Active projects

| Module | What it proves | Status |
|--------|----------------|--------|
| [`ftap-proofs/`](ftap-proofs/) | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no arbitrage iff equivalent martingale measure exists | Complete: zero sorry |
| [`options-proofs/`](options-proofs/) | Put-call parity via Cox-Ross-Rubinstein binomial model; imports `ftap-proofs` and `quant-core` | Complete: zero sorry |
| [`stopped-time-proofs/`](stopped-time-proofs/) | Geometric PMF and `GeometricExpectation` operator; Mathlib PR candidate, no finance content | Complete: zero sorry |
| [`perpetual-proofs/`](perpetual-proofs/) | No-arbitrage pricing for perpetual futures (Ackerer-Hugonnier-Jermann 2025); 8 theorems proved | Complete: zero sorry |
| [`quant-core/`](quant-core/) | Shared pricing primitives: option type invariants, payoff bounds, Black-Scholes, GBM | Stable: 8 theorems |
| [`mortgage-proofs/`](mortgage-proofs/) | LangGraph multi-agent routing invariants, Lean 4-checked trace verification | Active |
| [`optimization-proofs/`](optimization-proofs/) | Formally verified abstract PGD and simplex/L1 projection core | Verified PGD core |
| [`portfolio-proofs/`](portfolio-proofs/) | Formally verified PGD simplex portfolio solver | Verified core + scenarios |

## Planned

**Formally verified backtester**: an event-driven backtesting engine where the central formal claim is $\mathcal{F}_t$-measurability of signals: provably no look-ahead bias, enforced by the Lean 4 type system. Correctness proofs will cite `ftap-proofs`.

## Archive

[`archive/position-ledger/`](archive/): earlier work on a verified position ledger (26 theorems on P&L accounting). Preserved but superseded. See [`archive/README.md`](archive/README.md) for context.

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs/ftap-proofs && lake exe cache get && lake build
cd quant-proofs/options-proofs && lake exe cache get && lake build
cd quant-proofs/quant-core/lean && lake build
```

## Documentation

Full documentation: [eigenq-xyz.github.io/quant-proofs](https://eigenq-xyz.github.io/quant-proofs)

## License

Apache 2.0: compatible with mathlib for upstream contribution.
