# CLAUDE.md — research-pipeline

Full quant-research-desk workflow (data → signals → **statistical testing** → portfolio →
backtest → evaluation → cross-asset), orchestrated by `study.run_research_study`. The
**backtesting stage** carries a formal no-look-ahead guarantee (Lean
`ResearchPipeline.NonAnticipating`); the statistical/evaluation layers are unverified but
rigorous. **Status: In progress.** Read [`ROADMAP.md`](ROADMAP.md) before working here.

## Architecture (one module per desk stage)

| Stage | Where | Role |
|-------|-------|------|
| Formal core | `lean/ResearchPipeline/NoLookahead.lean` | `NonAnticipating` + `decision_uses_no_future` (proved, `sorry`-free) |
| Formal core | `lean/ResearchPipeline/NoLeakage.lean` | `embargo_blocks_label_leakage`: OOS embargo >= horizon => no label leak (proved, `sorry`-free) |
| 1 Data | `src/research_pipeline/data.py` | point-in-time `PricePanel`; `as_of(t)` witnesses the info set |
| 2 Signals + strategy | `signals.py`, `strategy.py` | non-anticipating alphas; `Strategy` protocol + name-keyed registry (alpha-agnostic) |
| 3 Stats | `stats.py` | IC + HAC (Newey-West) t-stat, decay, bootstrap, PSR/DSR |
| 4 Combination | `combination.py` | signal overlap + orthogonalised incremental IC ("disguised beta?") |
| 5 Portfolio | `portfolio.py` | pluggable constructors (registry) + bridge to the verified PGD solver |
| 6 Backtest | `backtest.py` | `𝓕ₜ`-aligned, net-of-cost event loop; configurable horizon |
| 7 Evaluation | `evaluation.py` | performance, drawdowns, OLS factor attribution |
| 8 OOS | `oos.py` | expanding walk-forward + embargo; `leakage_gap` runtime witness |
| — Orchestration | `study.py` | runs the stages into a `StudyReport` (opt-in X-sec metrics, optional combination) |
| — CLI | `cli.py` | `rp list / run / validate`; flags + JSON config replay; `results/<id>/` artifacts |
| — Cross-asset | `crossasset.py` | same pipeline across asset classes |
| Real data | `data_sources.py` | Ken French (free) + WRDS/CRSP (**licensed — never committed**) |
| Validation (Track 1) | `validation.py`, `tests/test_properties.py` | synthetic-truth + property contracts: detection power, false-positive rate, planted-leak red-team, estimator/accounting invariants |
| Study (Track 2) | `scripts/run_study.py`, `studies/REPORT.md` | real study driver + report template |

**Two tracks.** *Track 1 (validate the pipeline)* — `validation.py` + `tests/test_validation.py`/`test_reference.py` prove the pipeline detects planted alpha, stays null on noise, catches injected look-ahead, and matches `statsmodels`/`scipy`. *Track 2 (use the pipeline)* — `run_study.py` runs a real OOS study (Ken French now; CRSP via your WRDS creds) into `studies/REPORT.md`, which cites Track 1. A report from an unvalidated pipeline is not written.

## Build / test

```bash
cd research-pipeline/lean && lake build
grep -rn '^\s*sorry\b' --include="*.lean" lean/      # must be empty on main (strips docstrings)
cd research-pipeline && pip install -e ".[dev]"
pytest -q                                             # unit + hypothesis property contracts
rp list && rp validate                                # registry + no-look-ahead/no-leakage gates
rp run momentum --oos --out results/                  # full study -> results/<id>/
mypy --strict src/                                    # scipy is import-ignored; pandas needs pandas-stubs
ruff check .
```

## Hard rules (inherited from repo root)

- **Zero `sorry` on main.** In progress — develop on a branch; do not merge until any new
  `sorry` is discharged. Current Lean is `sorry`-free.
- `mypy --strict` clean on `src/` (scipy `ignore_missing_imports`; pandas via `pandas-stubs`).
- **Never commit licensed data.** Synthetic generator only, in-repo.
- No private content: no grades, no target-firm names in strategy context, no resume paths,
  no application timelines. Described purely as a research/verification artifact.

## How to proceed

Ordered, issue-sized plan in [`ROADMAP.md`](ROADMAP.md). Open a GitHub issue per task; close
it in the same PR cycle.
