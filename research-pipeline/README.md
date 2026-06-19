# research-pipeline

**A full quant-research-desk workflow, end to end** — with the load-bearing step formally
verified. This is the integrative flagship: it takes a signal idea from hypothesis to an
auditable, net-of-cost verdict, exercising every stage a research desk runs. The repo
thesis in one module: *the durable skill is knowing whether to trust a backtest.*

**Status: In progress.** The engine is alpha-agnostic (cross-sectional and time-series
strategies through one interface), driven by a command-line tool (`rp`), and the load-bearing
stages carry verification contracts that build `sorry`-free. It runs offline on synthetic data.
Real-data studies, verified-solver wiring, and the measure-theoretic proof upgrade are tracked
in [`ROADMAP.md`](ROADMAP.md).

## The pipeline (each stage is its own module)

| # | Stage | Module | Verified? |
|---|-------|--------|-----------|
| 1 | **Data** — point-in-time panel | `src/research_pipeline/data.py` | structural (no future accessor as a feature) |
| 2 | **Signals + strategies** — non-anticipating alphas, name-keyed registry | `signals.py`, `strategy.py` | runtime witness of the Lean spec |
| 3 | **Statistical testing** — IC, HAC significance, decay, PSR/DSR | `stats.py` | unverified, **rigorous** (numpy/pandas/scipy) + property tests |
| 4 | **Combination / incrementality** — overlap + orthogonalised incremental IC | `combination.py` | unverified, rigorous |
| 5 | **Portfolio construction** — pluggable constructors + verified PGD bridge | `portfolio.py` | bridges the **verified PGD** solver (`optimization-proofs`) |
| 6 | **Backtest** — event-driven, net-of-cost | `backtest.py` | **formally verified no look-ahead** (Lean) |
| 7 | **Evaluation & attribution** | `evaluation.py` | unverified, rigorous (drawdowns, OLS attribution) |
| 8 | **Out-of-sample** — walk-forward with embargo | `oos.py` | **formally verified no leakage** (Lean) |
| — | **Cross-asset generalisation** | `crossasset.py` | robustness study |
| — | **Desk orchestration** | `study.py` | runs the stages into one `StudyReport` |

The engine is **alpha-agnostic**: a `Strategy` maps the information set up to `t` to a target
portfolio, so cross-sectional and time-series alphas share one interface, and portfolio
construction is a pluggable choice (`dollar_neutral`, `long_only`, `long_short_quantile`,
`directional`). Stage 3 is deliberately prominent: significance done right (autocorrelation-robust
t-stats, deflated Sharpe for multiple testing) is what separates an edge from a lucky backtest.

## Verification contracts

The pipeline does not just assert its load-bearing properties, it checks them. Each contract is
a small Lean theorem (where there is a genuine theorem) plus a runtime / property witness that
ties it to the executable code. Alpha is never "proved": it is empirical, and lives in the
honest statistics, not in Lean.

- **No look-ahead** — [`lean/ResearchPipeline/NoLookahead.lean`](lean/ResearchPipeline/NoLookahead.lean):
  positions built from a non-anticipating signal cannot depend on the future. Witness:
  [`tests/test_no_lookahead.py`](tests/test_no_lookahead.py).
- **No leakage** — [`lean/ResearchPipeline/NoLeakage.lean`](lean/ResearchPipeline/NoLeakage.lean):
  an out-of-sample split with embargo at least the label horizon cannot leak a training label
  into the test window. Witness: `oos.leakage_gap` + a property test that agrees with the theorem.
- **Estimator sanity / accounting integrity** — property tests (`tests/test_properties.py`): IC
  bounds, deflated-Sharpe monotonicity in the trial count, non-negative costs.

Both Lean modules are dependency-free and `sorry`-free. Run `rp validate` to see the
no-look-ahead and no-leakage guards catch an injected leak.

## Quick start

```bash
cd research-pipeline/lean && lake build          # verification contracts (sorry-free, no mathlib)
cd research-pipeline && pip install -e ".[dev]"

rp list                                           # registered strategies + portfolios
rp run momentum --cost-bps 10 --oos --out results/   # full study, writes results/<id>/
rp validate                                       # no-look-ahead + no-leakage gates
pytest -q                                         # unit + property contracts
```

## Drop-in points

1. **Real data** — point-in-time loaders (Ken French / yfinance); keep the `as_of` guard; never commit licensed data.
2. **Real alpha** — keep a known signal as a control; develop the conditional / multi-period twist.
3. **Verified solver** — build `pgd_solve` and route `verified_pgd_weights` through it; extend the verified projection to the dollar-neutral simplex (`sum w = 0`).
4. **Measure-theoretic proof** — upgrade `NonAnticipating` to genuine 𝓕ₜ-measurability citing `ftap-proofs`.

See [`ROADMAP.md`](ROADMAP.md).
