# quant-proofs — EigenQ Research Series

Formally verified quantitative finance — machine-checked Lean 4 proofs paired with production Python.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What this is

Before trusting a numerical result, prove the accounting correct. Each project here pairs a formal Lean 4 proof — zero `sorry`, machine-checked on every commit — with the Python code that calls into it at runtime via Cython FFI. The theorem statement is the spec; the proof is the test — and neither can drift silently from the other.

## Modules

| Module | What it proves | Status |
|--------|----------------|--------|
| [`quant-core/`](quant-core/) | Option type invariants, payoff non-negativity, ITM/OTM characterization | v1.0 — 8 theorems |
| [`backtest-proofs/`](backtest-proofs/) | Delta-hedging accounting: NAV identity, self-financing, settlement value formula | v0.5 — 19 theorems |
| [`ftap-proofs/`](ftap-proofs/) | Discrete FTAP (Harrison-Pliska 1981): arbitrage-free iff equivalent martingale measure exists | Skeleton |
| [`options-proofs/`](options-proofs/) | Put-call parity via Cox-Ross-Rubinstein binomial model | Skeleton |
| [`mortgage-proofs/`](mortgage-proofs/) | LangGraph multi-agent routing invariants, Lean 4-checked trace verification | Active |

## Research Paper

The paper proves 11 accounting theorems zero-sorry and validates them on 491,390 WRDS OptionMetrics observations across four historical stress regimes.

- PDF: [eigenq-xyz.github.io/quant-proofs/paper/backtest-proofs.pdf](https://eigenq-xyz.github.io/quant-proofs/paper/backtest-proofs.pdf)

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs/backtest-proofs
make setup   # install Lean (elan) + Python (uv)
make test    # Lean proofs + Python tests
make paper   # render research paper (requires uv sync --group research)
```

For modules without a root Makefile (`ftap-proofs`, `options-proofs`, `mortgage-proofs`), build with:

```bash
cd <module> && lake build
```

## Documentation

Full documentation: [eigenq-xyz.github.io/quant-proofs](https://eigenq-xyz.github.io/quant-proofs)

## License

Apache 2.0 — compatible with mathlib for upstream contribution.
