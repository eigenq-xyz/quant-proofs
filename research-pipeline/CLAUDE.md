# CLAUDE.md: research-pipeline

The flagship. Full quant-research-desk workflow (data → signals → statistical testing → portfolio
→ backtest → evaluation → cross-asset), orchestrated by `study.run_research_study`.
Correctness-critical stages are proved in Lean 4; statistical and evaluation layers are rigorous
but not formally verified (see root `CLAUDE.md` for the verified/unverified boundary).

## Architecture (one module per desk stage)

| Stage | Where | Role |
|-------|-------|------|
| Formal core | `lean/ResearchPipeline/NoLookahead.lean` | `NonAnticipating` + `decision_uses_no_future` (proved, zero `sorry`) |
| Formal core | `lean/ResearchPipeline/NoLeakage.lean` | `embargo_blocks_label_leakage`: OOS embargo ≥ horizon implies no label leak (proved, zero `sorry`) |
| Formal core | `lean/ResearchPipeline/Measurability.lean` | `momentumSignal_adapted` and `vrpSignal_adapted`: signals are `Adapted` to the relevant filtration (proved, zero `sorry`; cites `ftap-proofs`, needs mathlib) |
| 1 Data | `src/research_pipeline/data.py` | point-in-time `PricePanel`; `as_of(t)` witnesses the information set |
| 2 Signals + strategy | `signals.py`, `strategy.py` | alphas free of implementation look-ahead; `Strategy` protocol + name-keyed registry (alpha-agnostic) |
| 3 Stats | `stats.py` | IC + Newey-West HAC t-stat, decay, bootstrap, PSR/DSR |
| 4 Combination | `combination.py` | signal overlap + orthogonalized incremental IC |
| 5 Portfolio | `portfolio.py` | pluggable constructors + bridge to the correct-by-construction PGD solver; `verified_pgd_weights` raises rather than silently using an unverified baseline |
| 6 Backtest | `backtest.py` | `𝓕ₜ`-aligned, net-of-cost event loop; configurable horizon |
| 7 Evaluation | `evaluation.py` | performance, drawdowns, OLS factor attribution |
| 8 OOS | `oos.py` | expanding walk-forward + embargo; `leakage_gap` runtime witness |
| Orchestration | `study.py` | runs the stages into a `StudyReport` |
| CLI | `cli.py` | `rp list / run / validate`; `results/<id>/` artifacts |
| Cross-asset | `crossasset.py` | same pipeline across asset classes |
| Real data | `data_sources.py` | Ken French and AQR (free); WRDS/CRSP (licensed, never committed) |

## Two tracks

- **Validate the pipeline:** `validation.py` + `tests/` prove the pipeline detects planted alpha,
  stays null on noise, catches an injected look-ahead, and matches `statsmodels`/`scipy`.
- **Use the pipeline:** `scripts/run_study.py` runs real out-of-sample studies into `studies/`. A
  report from an unvalidated pipeline is not written.

## Studies (`studies/`)

- `REPORT.md`: headline 12-1 momentum study (49 Ken French industries, daily, 1926-2026).
- `vrp/`: the variance-risk-premium delta-hedged short-vol study; free data, no key.

The data-revision leakage map (CFTC/EIA/payrolls) and cross-asset breadth on pre-built AQR factor
returns moved to [`extensions/research-ideas/`](../extensions/research-ideas/CLAUDE.md): exploratory,
not yet a load-bearing result. `crossasset.py` in this package is unaffected: it runs raw prices
through the backtester proved free of implementation look-ahead, and stays here.

## Build / test

```bash
cd research-pipeline/lean && lake exe cache get && lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake lean/      # must be empty on main
cd research-pipeline && pip install -e ".[dev]"
pytest -q                                             # unit + property contracts
rp list && rp validate                                # registry + no-look-ahead/no-leakage gates
rp run momentum --oos --out results/                  # full study into results/<id>/
mypy --strict src/ && ruff check .
```

## Local notes

- `mypy --strict` on `src/`: scipy import-ignored, pandas typed via `pandas-stubs`.
- No licensed data here either: synthetic generator and free loaders only (see root `CLAUDE.md`
  for the repo-wide rule).
