# research-pipeline

A full quant-research-desk workflow, data through cross-asset generalization, with its
load-bearing correctness properties proved in Lean 4: backtest non-anticipation, out-of-sample
no-leakage, and signal measurability. The statistical and P&L layers are rigorous but not
formally verified; the table below marks the boundary.

The engine is alpha-agnostic (cross-sectional and time-series strategies through one interface)
and driven by a command-line tool, `rp`.

## What it proves

| Property | Where | Status |
|----------|-------|--------|
| Backtest non-anticipation | `lean/ResearchPipeline/NoLookahead.lean` | Proved, zero `sorry` |
| Out-of-sample no-leakage (embargo ≥ label horizon) | `lean/ResearchPipeline/NoLeakage.lean` | Proved, zero `sorry` |
| Signal `𝓕ₜ`-measurability, momentum signal | `lean/ResearchPipeline/Measurability.lean` (`momentumSignal_adapted`) | Proved, zero `sorry`, cites `ftap-proofs` |
| Signal `𝓕ₜ`-measurability, variance-risk-premium signal | `lean/ResearchPipeline/Measurability.lean` (`vrpSignal_adapted`) | Proved, zero `sorry` |
| Portfolio construction | `portfolio.py` | Routed through the verified PGD solver; raises rather than silently using an unverified baseline |
| Statistical layer (IC, Newey-West HAC, PSR/DSR) | `stats.py` | Rigorous, cross-checked against `statsmodels`/`scipy`; not formally verified |

`Measurability.lean` is the measure-theoretic form of non-anticipation: the signal map is adapted
to the natural filtration `σ(price s : s ≤ t)`. The VRP signal additionally reads an
implied-variance process, so it is proved adapted to the joint price-and-implied-vol filtration.

## What it doesn't claim

Alpha is never proved. The momentum and VRP studies below are empirical results that live in the
statistics layer (`stats.py`), not in Lean: a real, significant backtest result is not the same
claim as a machine-checked proof, and this README does not blur the two. Portfolio construction is
routed through the verified PGD solver, but it raises rather than silently falling back to an
unverified baseline if that routing fails; it does not prove the resulting portfolio is optimal in
any sense beyond what the solver's own proofs (in `optimization-proofs/`) establish.

## The pipeline (one module per desk stage)

| # | Stage | Module |
|---|-------|--------|
| 1 | Data: point-in-time panel (`as_of(t)` witnesses the information set) | `data.py` |
| 2 | Signals and strategies: non-anticipating alphas, name-keyed registry | `signals.py`, `strategy.py` |
| 3 | Statistical testing: IC, Newey-West HAC, decay, PSR/DSR | `stats.py` |
| 4 | Combination: signal overlap and orthogonalized incremental IC | `combination.py` |
| 5 | Portfolio construction: pluggable constructors, verified-solver bridge | `portfolio.py` |
| 6 | Backtest: event-driven, net of cost | `backtest.py` |
| 7 | Evaluation and attribution | `evaluation.py` |
| 8 | Out-of-sample: walk-forward with embargo | `oos.py` |
| — | Cross-asset generalization | `crossasset.py` |
| — | Desk orchestration into one `StudyReport` | `study.py` |

A `Strategy` maps the information set up to `t` to a target portfolio, so cross-sectional and
time-series alphas share one interface and portfolio construction is a pluggable choice. Stage 3 is
deliberately prominent: significance done right, autocorrelation-robust t-stats and a deflated Sharpe
for multiple testing, is what separates an edge from a lucky backtest.

## Studies

[`studies/`](studies/) holds the runnable studies, each with its own writeup.

- **[Headline momentum study](studies/REPORT.md):** cross-sectional 12-1 momentum on the 49 Ken
  French industry portfolios, daily, 1926-2026, from free data (`python -m scripts.run_study`).
  IC Newey-West t-stat 14.3, strict quintile monotonicity, net Sharpe 0.28 in-sample / 0.38
  out-of-sample, deflated Sharpe 0.72 over 50 trials, max drawdown −53%. The verdict is honest: a
  real, significant, stable effect whose net edge is modest and has decayed over decades. A known
  alpha is used as a control; the research object is the pipeline's correctness. Cross-asset breadth
  (AQR time-series momentum) is in the report.
- **[Leakage-tax map](studies/LEAKAGE_MAP.md):** across CFTC positioning, EIA gas storage, and
  nonfarm payrolls, how much apparent backtest alpha is a data look-ahead artifact. The finding is a
  map, not an alpha: what decides whether revised-data look-ahead matters is the signal's functional
  form, not how heavily the series is revised.
- **[Variance-risk-premium study](studies/vrp/README.md):** a delta-hedged short-volatility strategy
  on the S&P 500. The premium survives realistic hedging frictions; the defensible net Sharpe is
  around 0.7 to 1.0 once realistic index-option spreads are charged. Its signal's non-anticipation is
  machine-checked (`vrpSignal_adapted`).

## Two tracks

- **Validate the pipeline** (`validation.py`, `tests/`): the pipeline detects planted alpha (over 90%
  power), holds a roughly 5% false-positive rate on noise, catches an injected one-day look-ahead, and
  matches `statsmodels`/`scipy` on the estimators.
- **Use the pipeline** (`scripts/run_study.py`, `studies/`): real out-of-sample studies. A report from
  an unvalidated pipeline is not written.

## Build and verify

```bash
cd research-pipeline/lean && lake exe cache get && lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
cd research-pipeline && pip install -e ".[dev]" && pytest -q
rp validate                              # no-look-ahead and no-leakage gates
```

Full build/test/lint matrix and study-running commands: see `CLAUDE.md`.

Licensed data (WRDS/CRSP, paid feeds) is never committed; the Ken French and AQR loaders use free
data. Keep the `as_of` guard on any new data source.

## Dependencies

Cites [`foundations/ftap-proofs/`](../foundations/ftap-proofs/) at one point:
`market_price_natural_le_filtration` feeds `FtapProofs.FinancialMarket.S_adapted` into the
adaptedness proof. Load-bearing, single point of contact; see `DEPENDENCY_GRAPH.md` at the repo
root.

## License

Apache 2.0.
