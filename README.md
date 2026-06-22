# quant-proofs

Formally verified quantitative finance — machine-checked Lean 4 proofs paired with production Python.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

> **New here?** Read [`START_HERE.md`](START_HERE.md) — a two-minute orientation.

The durable skill in quantitative research is not running backtests, it is knowing whether to trust
them. Each project here takes a named result from financial theory or a load-bearing step of quant
research and makes it formally verifiable: the theorem statement is the spec, the Lean 4 proof is the
test, with zero `sorry` on main.

## The flagship: `research-pipeline/`

A full quant-research-desk workflow — **data → signals → statistical testing → portfolio → backtest →
evaluation → cross-asset** — that unifies the verified modules end to end. The load-bearing steps are
formally verified; the statistical layer is unverified but rigorous (the numpy/pandas/scipy showcase).

- **No look-ahead:** the backtester is proved non-anticipating, and the signal map is proved
  `𝓕ₜ`-measurable against the natural filtration of the price process (citing `ftap-proofs`).
- **No leakage:** out-of-sample splits with an embargo ≥ the label horizon are proved leak-free.
- **Verified portfolio construction** that refuses to silently substitute an unverified baseline.
- **Self-validating:** detects planted alpha (> 90% power), holds a ~5% false-positive rate on noise,
  and catches an injected one-day look-ahead.

**Headline study** ([`research-pipeline/studies/REPORT.md`](research-pipeline/studies/REPORT.md)) —
12-1 momentum on the 49 Ken French industry portfolios, daily, 1926–2026, fully reproducible from free
data via `python -m scripts.run_study`:

| IC t-stat (Newey-West) | Decile monotonicity | Net Sharpe (IS / OOS) | Deflated Sharpe (50 trials) | Max drawdown |
|---|---|---|---|---|
| 14.3 | strict (Q1→Q5) | 0.28 / 0.38 | 0.72 | −53% |

The honest verdict, stated in the report: the effect is real, significant, and stable, but modest net
of costs and decaying over decades. A known alpha is used deliberately as a control — the research
object is the pipeline's correctness. Cross-asset (AQR time-series momentum): a positive,
multiple-testing-significant Sharpe in equities, bonds, currencies, and commodities, with low
cross-asset correlation (breadth evidence; see §7 of the report).

→ [`research-pipeline/README.md`](research-pipeline/README.md) · [`ROADMAP.md`](research-pipeline/ROADMAP.md)

## Verified foundations

The theorems the flagship rests on. Status legend: **Complete** = builds with zero `sorry` and
`#print axioms` reports only `[propext, Classical.choice, Quot.sound]`.

| Module | What it proves | Status |
|--------|----------------|--------|
| [`foundations/ftap-proofs/`](foundations/ftap-proofs/) | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no arbitrage iff an equivalent martingale measure exists | **Complete** — 16 theorems, zero `sorry` |
| [`foundations/options-proofs/`](foundations/options-proofs/) | Put-call parity `C − P = S₀ − K/(1+r)^T` via the Cox-Ross-Rubinstein binomial model (builds the CRR market, proves it is an EMM and arbitrage-free, then derives parity); cites `ftap-proofs` | **Complete** — 31 theorems, zero `sorry` |
| [`foundations/quant-core/`](foundations/quant-core/) | Shared pricing primitives: option-type invariants, payoff bounds, Black-Scholes, GBM | **Complete** — 8 theorems |
| [`foundations/optimization-proofs/`](foundations/optimization-proofs/) | Projected gradient descent for convex QP with an analytical simplex ∩ L₁-ball projection; convergence and projection correctness | **Complete** — 10 theorems, zero `sorry` |
| [`foundations/portfolio-proofs/`](foundations/portfolio-proofs/) | Mean-variance allocation with Ledoit-Wolf shrinkage on the verified PGD solver (Lean + Python/Cython); stressed-solver scenarios | Applied / empirical |

## Extensions

Self-contained results that branch off the core. Not on the flagship's critical path.

| Module | What it proves | Status |
|--------|----------------|--------|
| [`extensions/perpetual-proofs/`](extensions/perpetual-proofs/) | Perpetual-futures no-arbitrage pricing and the inverse-perp convexity correction; cites `stopped-time-proofs` + `ftap-proofs` | **Complete** — 10 theorems, zero `sorry` |
| [`extensions/stopped-time-proofs/`](extensions/stopped-time-proofs/) | Geometric stopping-time expectations; a mathlib-candidate library (no finance content) | **In progress** — Jensen (G2.2) is an open, *unused* `sorry` |
| [`extensions/mortgage-proofs/`](extensions/mortgage-proofs/) | LangGraph multi-agent routing invariants with Lean 4-checked trace verification (auditable AI for high-stakes decisions) | **Complete** — 13 theorems, zero `sorry` |

## Archive

[`archive/position-ledger/`](archive/) — earlier work on a verified position ledger (26 theorems on
P&L accounting). Preserved but superseded; do not build or extend. See
[`archive/README.md`](archive/README.md).

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs/research-pipeline && pip install -e ".[dev]" && pytest -q   # the flagship
python -m scripts.run_study                                                 # reproduce the headline study
cd ../ftap-proofs && lake build                                             # a verified foundation
```

## Documentation

Full documentation: [eigenq-xyz.github.io/quant-proofs](https://eigenq-xyz.github.io/quant-proofs)

## License

Apache 2.0 — compatible with mathlib for upstream contribution.
