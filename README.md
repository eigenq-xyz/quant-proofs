# quant-proofs

Formally verified quantitative finance: correct-by-construction Lean 4 proofs paired with
production Python.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

The durable skill in quantitative research is not running a backtest, it is knowing whether to
trust one. Each project here takes a named result from asset-pricing theory, or a load-bearing step
of quant research, and proves it correct in [Lean 4](https://lean-lang.org/), a proof assistant:
the theorem statement is the specification, the proof is machine-checked line by line, and breaking
an assumption fails the build, not the backtest. "Proved" or "zero `sorry`" here means: the module
builds, `sorry` (Lean's placeholder for "trust me, no proof yet") appears nowhere, and `#print
axioms` on the theorem reports only Lean's three standard axioms
(`[propext, Classical.choice, Quot.sound]`), not a project-specific escape hatch.

Full narrative and audience guides: **[eigenq-xyz.github.io/quant-proofs](https://eigenq-xyz.github.io/quant-proofs)**.

## The flagship: `research-pipeline/`

A full research-desk workflow, **data → signals → statistical testing → portfolio → backtest →
evaluation → cross-asset**, that wires the verified modules together end to end. The load-bearing
steps are proved free of implementation look-ahead in Lean 4; the statistical layer is rigorous but
not formally verified, and the README says so where it matters.

| Layer | Guarantee |
|-------|-----------|
| Backtest is free of implementation look-ahead (no future data reaches a past decision) | Proved, zero `sorry` |
| Out-of-sample no-leakage (embargo ≥ label horizon) | Proved, zero `sorry` |
| Signal `𝓕ₜ`-measurability (momentum and variance-risk-premium signals use only information available at each date; `𝓕ₜ` is the standard notation for "everything known up to time `t`") | Proved, zero `sorry`, cites `ftap-proofs` |
| Portfolio construction | Routed through the correct-by-construction solver; raises rather than silently using an unverified baseline |
| Statistical layer (IC, Newey-West HAC, PSR/DSR) | Rigorous, cross-checked against `statsmodels`/`scipy`; not formally verified |

**Headline study** ([`studies/REPORT.md`](research-pipeline/studies/REPORT.md)): cross-sectional
12-1 momentum on the 49 Ken French industry portfolios, daily, 1926-2026, reproducible from free
data with `python -m scripts.run_study`.

| IC t-stat (Newey-West) | Quintile monotonicity | Net Sharpe (IS / OOS) | Deflated Sharpe (50 trials) | Max drawdown |
|---|---|---|---|---|
| 14.3 | strict (Q1→Q5) | 0.28 / 0.38 | 0.72 | −53% |

The report states the honest verdict: the effect is real, significant, and stable, but modest net
of costs and decaying over decades. A known alpha is used deliberately as a control, because the
research object is the pipeline's correctness, not the signal.

A second study lives in [`research-pipeline/studies/`](research-pipeline/studies/):

- **[Variance-risk-premium study](research-pipeline/studies/vrp/README.md):** a delta-hedged
  short-volatility strategy on the S&P 500. The premium survives realistic hedging frictions; the
  defensible net Sharpe is around 0.7 to 1.0 once realistic index-option spreads are charged. Its
  signal is proved free of implementation look-ahead (`vrpSignal_adapted`).

Exploratory work that hasn't cleared this bar (a CFTC/EIA/payrolls data-revision leakage map, and
AQR cross-asset breadth on pre-built factor returns) lives in
[`extensions/research-ideas/`](extensions/research-ideas/README.md): preserved as ideas being
tried, not results being claimed.

→ [`research-pipeline/README.md`](research-pipeline/README.md)

## Verified foundations

The theorems the flagship rests on.

| Module | What it proves | Status |
|--------|----------------|--------|
| [`foundations/ftap-proofs/`](foundations/ftap-proofs/) | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no arbitrage iff an equivalent martingale measure exists | Complete, zero `sorry` |
| [`foundations/options-proofs/`](foundations/options-proofs/) | Put-call parity `C − P = S₀ − K/(1+r)^T` via the Cox-Ross-Rubinstein binomial model; builds the CRR market, proves it is an arbitrage-free EMM, then derives parity. Cites `ftap-proofs` | Complete, zero `sorry` |
| [`foundations/quant-core/`](foundations/quant-core/) | Shared pricing primitives: option-type invariants, payoff bounds, Black-Scholes, GBM (Lean with a Python/Cython port) | Complete, zero `sorry` |
| [`foundations/optimization-proofs/`](foundations/optimization-proofs/) | Projected gradient descent for convex QP with an analytical simplex ∩ L₁-ball projection; convergence and projection correctness | Complete, zero `sorry` |
| [`foundations/portfolio-proofs/`](foundations/portfolio-proofs/) | Mean-variance allocation with Ledoit-Wolf shrinkage on the verified solver (Lean and Python/Cython), with stressed-solver scenarios | Applied / empirical |

## Extensions

Self-contained results that branch off the core, not on the flagship's critical path.

| Module | What it proves | Status |
|--------|----------------|--------|
| [`extensions/vrp-proofs/`](extensions/vrp-proofs/) | Discrete variance-risk-premium identities on the CRR tree: replication of any terminal payoff, and the premium as the gap between risk-neutral and physical expectations. Cites `options-proofs` | Complete, zero `sorry` |
| [`extensions/hedge-proofs/`](extensions/hedge-proofs/) | Delta-hedge accounting engine: self-financing, settlement-value, and value-update invariants over a discrete rebalancing schedule. Cites `quant-core` | Complete, zero `sorry` |
| [`extensions/perpetual-proofs/`](extensions/perpetual-proofs/) | Perpetual-futures no-arbitrage pricing and the inverse-perp convexity correction; builds on `stopped-time-proofs` | Complete, zero `sorry` |
| [`extensions/stopped-time-proofs/`](extensions/stopped-time-proofs/) | Geometric stopping-time expectations and a strict-monotonicity (Jensen) lemma; a mathlib-candidate library with no finance content | Complete, zero `sorry` |
| [`extensions/mortgage-proofs/`](extensions/mortgage-proofs/) | LangGraph multi-agent routing invariants with Lean 4-checked trace verification: auditable AI for high-stakes decisions | Complete, zero `sorry` |
| [`extensions/research-ideas/`](extensions/research-ideas/) | Exploratory studies moved out of the flagship: a data-revision leakage map, AQR cross-asset breadth | No Lean, no verified claim |

## Archive

[`archive/position-ledger/`](archive/) holds earlier work on a verified position ledger. Preserved
as history, superseded, not built or extended.

## Quick start

```bash
git clone https://github.com/eigenq-xyz/quant-proofs
cd quant-proofs

# the flagship
cd research-pipeline && pip install -e ".[dev]" && pytest -q
python -m scripts.run_study          # reproduce the headline study from free data

# a verified foundation
cd ../foundations/ftap-proofs && lake exe cache get && lake build
```

Working in the repo with an AI agent? `CLAUDE.md` is the developer and agent guide; each subproject
has its own.

## License

Apache 2.0, compatible with mathlib for upstream contribution.
