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
| 1 Data | `src/research_pipeline/data.py` | point-in-time `PricePanel`; `as_of(t)` witnesses the info set |
| 2 Signals | `signals.py` | non-anticipating known alphas + conditional hook |
| 3 Stats | `stats.py` | IC + HAC (Newey-West) t-stat, decay, factor overlap, bootstrap, PSR/DSR |
| 4 Portfolio | `portfolio.py` | baseline + bridge to the verified PGD solver (`portfolio-proofs`) |
| 5 Backtest | `backtest.py` | `𝓕ₜ`-aligned, net-of-cost event loop |
| 6 Evaluation | `evaluation.py` | performance, drawdowns, OLS factor attribution |
| — Cross-asset | `crossasset.py` | same pipeline across asset classes |
| — Orchestration | `study.py` | runs 1→6 into a `StudyReport` |
| OOS | `oos.py` | expanding walk-forward + embargo (purge) |
| Real data | `data_sources.py` | Ken French (free) + WRDS/CRSP (**licensed — never committed**) |
| Validation (Track 1) | `validation.py` | A/B synthetic-truth: detection power, false-positive rate, planted-leak red-team |
| Study (Track 2) | `scripts/run_study.py`, `studies/REPORT.md` | real study driver + report template |

**Two tracks.** *Track 1 (validate the pipeline)* — `validation.py` + `tests/test_validation.py`/`test_reference.py` prove the pipeline detects planted alpha, stays null on noise, catches injected look-ahead, and matches `statsmodels`/`scipy`. *Track 2 (use the pipeline)* — `run_study.py` runs a real OOS study (Ken French now; CRSP via your WRDS creds) into `studies/REPORT.md`, which cites Track 1. A report from an unvalidated pipeline is not written.

## Build / test

```bash
cd research-pipeline/lean && lake build
grep -rn '\bsorry\b' --include="*.lean" lean/        # must be empty on main
cd research-pipeline && pip install -e ".[dev]"
pytest -q
python -m scripts.run_demo
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
