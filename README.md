# quant-proofs

Formally verified quantitative finance — Lean 4 proofs of correctness paired with production-quality Python execution.

## Projects

| Project | Status | What it proves |
|---------|--------|---------------|
| [`quant-core/`](quant-core/) | v1.0 — 8 theorems, zero `sorry` | Shared option primitives: `EuropeanOption` type invariants, payoff non-negativity, ITM/OTM characterization, integer payoff identity |
| [`backtest-proofs/`](backtest-proofs/) | v0.5 — 18 theorems + 8 from QuantCore, zero `sorry` | Options delta-hedging accounting: portfolio value identity, self-financing, settlement value formula |
| [`ftap-proofs/`](ftap-proofs/) | Skeleton — in progress | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): arbitrage-free ↔ equivalent martingale measure exists |
| [`options-proofs/`](options-proofs/) | Skeleton — in progress (imports quant-core; depends on ftap-proofs) | Put-call parity via Cox-Ross-Rubinstein binomial model |
| [`mortgage-proofs/`](mortgage-proofs/) | Active — Lean 4 invariant checking | LangGraph multi-agent mortgage pipeline with formally verified routing invariants |

## Why formal verification for quant finance?

Backtesting bugs, settlement errors, and compliance violations share a common root: the code does something subtly different from what the math says. Lean 4 proofs make that gap impossible — the theorem statement *is* the spec, and the proof *is* the test.

`backtest-proofs` proves the accounting kernel correct once; Python calls into it via Cython FFI. No matter how complex the backtesting strategy gets, the accounting layer cannot silently mis-report portfolio value, misapply a trade, or mis-settle an option.

## Structure

Each subdir is an independent project with its own Lake/Python build and its own CLAUDE.md. Namespaces: `QuantCore`, `BacktestProofs`, `FtapProofs`, `OptionsProofs`, `MortgageProofs`. `quant-core` sits at the base of the dependency graph; `backtest-proofs` and `options-proofs` import it.

## License

Apache 2.0 — compatible with mathlib for upstream contribution.
