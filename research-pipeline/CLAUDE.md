# CLAUDE.md: research-pipeline

The flagship. A full quant-research-desk workflow (data → signals → statistical testing → portfolio
→ backtest → evaluation → cross-asset), orchestrated by `study.run_research_study`. The
correctness-critical stages are proved in Lean 4; the statistical and evaluation layers are rigorous
but not formally verified. This file orients an AI agent working here.

## Architecture (one module per desk stage)

| Stage | Where | Role |
|-------|-------|------|
| Formal core | `lean/ResearchPipeline/NoLookahead.lean` | `NonAnticipating` + `decision_uses_no_future` (proved, zero `sorry`) |
| Formal core | `lean/ResearchPipeline/NoLeakage.lean` | `embargo_blocks_label_leakage`: OOS embargo ≥ horizon implies no label leak (proved, zero `sorry`) |
| Formal core | `lean/ResearchPipeline/Measurability.lean` | `momentumSignal_adapted` and `vrpSignal_adapted`: signals are `Adapted` to the relevant filtration (proved, zero `sorry`; cites `ftap-proofs`, needs mathlib) |
| 1 Data | `src/research_pipeline/data.py` | point-in-time `PricePanel`; `as_of(t)` witnesses the information set |
| 2 Signals + strategy | `signals.py`, `strategy.py` | non-anticipating alphas; `Strategy` protocol + name-keyed registry (alpha-agnostic) |
| 3 Stats | `stats.py` | IC + Newey-West HAC t-stat, decay, bootstrap, PSR/DSR |
| 4 Combination | `combination.py` | signal overlap + orthogonalized incremental IC |
| 5 Portfolio | `portfolio.py` | pluggable constructors + bridge to the verified PGD solver; `verified_pgd_weights` raises rather than silently using an unverified baseline |
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

- `REPORT.md`: headline 12-1 momentum study (49 Ken French industries, daily, 1926-2026) plus
  cross-asset AQR time-series-momentum breadth.
- `LEAKAGE_MAP.md` + `commodity-leakage-tax/` + `macro-leakage/`: the data-revision leakage map.
  Raw data is fetched at runtime into git-ignored `data_cache/`; only source and small summary JSON
  are tracked. The FRED key is read from the environment, never committed.
- `vrp/`: the variance-risk-premium delta-hedged short-vol study; free data, no key.

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

## Hard rules

- Zero `sorry` on main. Develop on a branch; discharge before merge.
- `mypy --strict` clean on `src/` (scipy import-ignored; pandas via `pandas-stubs`); `ruff` clean.
- Never commit licensed data; the in-repo synthetic generator and free loaders only.
- Public-neutral: no grades, no target-firm names in strategy context, no resume paths, no
  application timelines. Describe the work as a research and verification artifact.

## Planning

GitHub issues are the planning system; open an issue per task and close it in the same PR cycle.
