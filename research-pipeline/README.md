# research-pipeline

**A full quant-research-desk workflow, end to end** — with the load-bearing step formally
verified. This is the integrative flagship: it takes a signal idea from hypothesis to an
auditable, net-of-cost verdict, exercising every stage a research desk runs. The repo
thesis in one module: *the durable skill is knowing whether to trust a backtest.*

The engine is alpha-agnostic (cross-sectional and time-series strategies through one interface),
driven by a command-line tool (`rp`), and the load-bearing stages carry verification contracts that
build `sorry`-free. A real, honest study is run and reported in
[`studies/REPORT.md`](studies/REPORT.md); the measure-theoretic `𝓕ₜ`-measurability upgrade is proved.
Remaining work (default verified-solver routing, the dollar-neutral verified projection) is tracked
in the open GitHub issues under the **research-pipeline completion sprint** milestone.

**Headline study** — 12-1 momentum on the 49 Ken French industry portfolios, daily, 1926–2026,
reproducible from free data (`python -m scripts.run_study`): IC t-stat (Newey-West) **14.3**, strict
decile-spread monotonicity, IC positive in **5 of 5** subperiods, net Sharpe **0.28** in-sample /
**0.38** out-of-sample, deflated Sharpe **0.72** (50 trials), max drawdown **−53%**. The verdict is
honest: a real, significant, stable effect whose net edge is modest and has decayed. The signal is a
*known* alpha used as a control; the research object is the pipeline's correctness. Cross-asset
breadth (AQR time-series momentum) in §7 of the report.

## The pipeline (each stage is its own module)

| # | Stage | Module | Verified? |
|---|-------|--------|-----------|
| 1 | **Data** — point-in-time panel | `src/research_pipeline/data.py` | structural (no future accessor as a feature) |
| 2 | **Signals + strategies** — non-anticipating alphas, name-keyed registry | `signals.py`, `strategy.py` | runtime witness of the Lean spec |
| 3 | **Statistical testing** — IC, HAC significance, decay, PSR/DSR | `stats.py` | unverified, **rigorous** (numpy/pandas/scipy) + property tests |
| 4 | **Combination / incrementality** — overlap + orthogonalised incremental IC | `combination.py` | unverified, rigorous |
| 5 | **Portfolio construction** — pluggable constructors + verified PGD bridge | `portfolio.py` | bridges the **verified PGD** solver (`optimization-proofs`); **no silent fallback** (raises if the verified solver is unavailable) |
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
- **`𝓕ₜ`-measurability** — [`lean/ResearchPipeline/Measurability.lean`](lean/ResearchPipeline/Measurability.lean):
  the momentum signal map is `Adapted` to the natural filtration `𝓕ₜ = σ(price s : s ≤ t)` of the
  price process (`momentumSignal_adapted`), the measure-theoretic form of non-anticipation. Cites
  `ftap-proofs` (consumes its market filtration). `sorry`-free; axioms clean.
- **Estimator sanity / accounting integrity** — property tests (`tests/test_properties.py`): IC
  bounds, deflated-Sharpe monotonicity in the trial count, non-negative costs.

`NoLookahead.lean` and `NoLeakage.lean` are dependency-free; `Measurability.lean` depends on mathlib +
`ftap-proofs`. All are `sorry`-free. Run `rp validate` to see the no-look-ahead and no-leakage guards
catch an injected leak.

## Quick start

```bash
cd research-pipeline/lean && lake build          # verification contracts (sorry-free; pulls mathlib for Measurability.lean)
cd research-pipeline && pip install -e ".[dev]"

rp list                                           # registered strategies + portfolios
rp run momentum --cost-bps 10 --oos --out results/   # full study, writes results/<id>/
rp validate                                       # no-look-ahead + no-leakage gates
pytest -q                                         # unit + property contracts
```

## Drop-in points

1. ✅ **Real data** — Ken French loaders work (`data_sources.py`); CRSP single-stock upgrade specced in [`studies/WRDS_DATA_REQUEST.md`](studies/WRDS_DATA_REQUEST.md). Keep the `as_of` guard; never commit licensed data.
2. **Real alpha** — keep a known signal as a control; develop the conditional / multi-period twist.
3. **Verified solver** — `verified_pgd_weights` now refuses a silent fallback. Remaining: route it through `pgd_solve` by default in the study and extend the verified projection to the dollar-neutral simplex (`sum w = 0`).
4. ✅ **Measure-theoretic proof** — `Measurability.lean` proves signal `𝓕ₜ`-measurability against the natural filtration, citing `ftap-proofs`.

Active work is tracked in the open GitHub issues under the **research-pipeline completion sprint** milestone.
