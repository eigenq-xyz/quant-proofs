# research-pipeline — ROADMAP

Taking the scaffold to a complete research desk. Each item is issue-sized; open a GitHub
issue and close it in the same PR cycle. Develop on a branch; **never merge a `sorry` to main.**

## Phase 1 — Formal core (Lean)

1. **Concrete signal is non-anticipating.** Model a discrete momentum map in Lean and prove
   it satisfies `NonAnticipating` (instantiating `decision_uses_no_future`). No `sorry`.
2. **Backtester PnL invariance.** Prove cumulative PnL through `t` is a function of the path
   up to `t+1` only (positions ≤ `t`, one realised step).
3. **Measure-theoretic upgrade.** Replace pointwise non-anticipation with genuine
   𝓕ₜ-measurability against the natural filtration; wire `require «ftap-proofs»` + the pinned
   mathlib rev in `lean/lakefile.lean`; cite `ftap-proofs`.

## Track 1 — validate the pipeline (DONE, ongoing)

- ✅ A/B synthetic-truth harness (`validation.py`): detection-power, false-positive rate,
  planted-leak red-team of the no-look-ahead guard.
- ✅ Placebo/permutation IC test (`stats.permutation_ic_test`).
- ✅ Ground-truth reference tests vs `statsmodels`/`scipy` (`tests/test_reference.py`).
- ✅ Out-of-sample walk-forward with embargo (`oos.py`).
- TODO: White/Hansen SPA (reality check) for multi-signal data-snooping; ADF stationarity;
  `hypothesis` property tests; silence zero-variance-cross-section RuntimeWarnings; mark slow tests.

## Track 2 — use the pipeline for a real study + report

- ✅ Real-data loaders scaffolded (`data_sources.py`): Ken French (free) + WRDS/CRSP
  (licensed, gitignored, never committed) + `scripts/run_study.py` + `studies/REPORT.md`.
- TODO: pull the CRSP daily universe (your WRDS creds) to a gitignored parquet; run the OOS
  cross-asset study; fill `studies/REPORT.md` with honest net-of-cost / deflated / OOS results,
  citing Track 1's validation.

## Phase 2 — Statistical / attribution depth

5. **Attribution depth.** Extend `evaluation.factor_attribution` to a real factor set
   (market / size / value / momentum), with Newey-West standard errors on the alpha.

## Phase 3 — Real pipeline

6. **Point-in-time data.** Replace `make_synthetic_panel` with Ken French / yfinance loaders;
   test the loader is itself non-anticipating. Never commit licensed data.
7. **Verified portfolio construction.** Build `pgd_solve`; route `verified_pgd_weights`
   through it; extend the verified projection to the **dollar-neutral simplex (`sum w = 0`)**
   for cross-sectional L/S — a new `optimization-proofs` theorem.
8. **Conditional / multi-period signal.** Promote `conditional_scale` to a real regime model;
   add multi-period optimisation with transaction costs.
9. **Capacity model.** Replace proportional costs with spread + square-root impact; report $ capacity.

## Phase 4 — Breadth & integration

10. **Cross-asset study.** Equities → futures → FX → commodities; analyse common-factor
    structure; report deflated Sharpe (multiple testing across asset classes).
11. **CI + docs.** Add to `lean-ci` / `python-ci`; `mypy --strict` + `ruff` green; docs page.
12. **Promote status.** Once Phase 1 lands `sorry`-free and CI is green, flip the status in
    the repo-root `README.md` / `CLAUDE.md` from *In progress*.
