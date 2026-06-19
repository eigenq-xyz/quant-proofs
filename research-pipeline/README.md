# research-pipeline

**A full quant-research-desk workflow, end to end** — with the load-bearing step formally
verified. This is the integrative flagship: it takes a signal idea from hypothesis to an
auditable, net-of-cost verdict, exercising every stage a research desk runs. The repo
thesis in one module: *the durable skill is knowing whether to trust a backtest.*

**Status: In progress.** The no-look-ahead core builds `sorry`-free; the Python pipeline
runs offline on synthetic data. Real data, verified-solver wiring, and the measure-theoretic
proof upgrade are tracked in [`ROADMAP.md`](ROADMAP.md).

## The pipeline (each stage is its own module)

| # | Stage | Module | Verified? |
|---|-------|--------|-----------|
| 1 | **Data** — point-in-time panel | `src/research_pipeline/data.py` | structural (no future accessor as a feature) |
| 2 | **Signals** — non-anticipating alphas | `signals.py` | runtime witness of the Lean spec |
| 3 | **Statistical testing** — IC, HAC significance, decay, factor overlap, PSR/DSR | `stats.py` | unverified, **rigorous** (numpy/pandas/scipy) |
| 4 | **Portfolio construction** | `portfolio.py` | bridges the **verified PGD** solver (`optimization-proofs`) |
| 5 | **Backtest** — event-driven, net-of-cost | `backtest.py` | **formally verified no look-ahead** (Lean) |
| 6 | **Evaluation & attribution** | `evaluation.py` | unverified, rigorous (drawdowns, OLS attribution) |
| — | **Cross-asset generalisation** | `crossasset.py` | robustness study |
| — | **Desk orchestration** | `study.py` | runs 1→6 into one `StudyReport` |

The backtester is one verified stage — not the whole product. Stage 3 (statistical testing)
is deliberately prominent: significance done right (autocorrelation-robust t-stats, deflated
Sharpe for multiple testing) is what separates an edge from a lucky backtest, and it is where
numpy/pandas/scipy discipline is on display even though it carries no Lean proof.

## The verified stage

[`lean/ResearchPipeline/NoLookahead.lean`](lean/ResearchPipeline/NoLookahead.lean) (dependency-free, `sorry`-free):

- `NonAnticipating f` — `f`'s value at time `t` depends only on the path up to `t` (the
  finite, pointwise analogue of 𝓕ₜ-measurability).
- `decision_uses_no_future` — **proved**: positions built from a non-anticipating signal are
  identical on any two paths that agree up to `t`, so a decision cannot use the future.

Runtime witness: [`tests/test_no_lookahead.py`](tests/test_no_lookahead.py).

## Quick start

```bash
cd research-pipeline/lean && lake build          # no-look-ahead proof (sorry-free, no mathlib)
cd research-pipeline && pip install -e ".[dev]"
python -m scripts.run_demo                        # full study + cross-asset, offline
pytest -q                                         # no-look-ahead, backtest, and stats checks
```

## Drop-in points

1. **Real data** — point-in-time loaders (Ken French / yfinance); keep the `as_of` guard; never commit licensed data.
2. **Real alpha** — keep a known signal as a control; develop the conditional / multi-period twist.
3. **Verified solver** — build `pgd_solve` and route `verified_pgd_weights` through it; extend the verified projection to the dollar-neutral simplex (`sum w = 0`).
4. **Measure-theoretic proof** — upgrade `NonAnticipating` to genuine 𝓕ₜ-measurability citing `ftap-proofs`.

See [`ROADMAP.md`](ROADMAP.md).
