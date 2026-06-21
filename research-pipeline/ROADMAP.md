# research-pipeline — ROADMAP

Taking the scaffold to a complete research desk. Each item is issue-sized; open a GitHub
issue and close it in the same PR cycle. Develop on a branch; **never merge a `sorry` to main.**

## Near-term focus (Jun–Jul 2026) — certify → validate → extend

The active sprint, as three technical briefs:

- **W1 — Validate by reproduction.** Wire the AQR TSMOM/VME loaders (`data_sources.py`, free) into a
  per-sleeve Sharpe-vs-published table (equities/FI/FX/commodities), matching sign and rough magnitude
  of each paper's reported figure. `crossasset.py` already ingests the streams and builds the
  correlation matrix; extend rather than rebuild. Add a one-line verification-status line (Lean build
  green ⇒ invariants proven) the study can print. Deliverable: the reproduction table in `REPORT.md`.
- **W2 — Extend: verified total-portfolio combine.** Feed the reproduced sleeve return streams into the
  verified solver (μ = trailing sleeve means, Σ = Ledoit-Wolf-shrunk sleeve covariance, the proven-PSD
  target) through `verified_pgd_weights` (budget simplex `sum w = 1`, `sum|w| ≤ cap`). This reuses the
  existing projection/convergence proof verbatim — **no new theorem** (the dollar-neutral `sum w = 0`
  theorem stays parked). Compare vs 1/N-across-sleeves OOS, net of costs, with deflated/probabilistic
  Sharpe. This is the regime where mean-variance is supposed to help (few diversifying sleeves, decades
  of monthly data, estimable stable Σ). The single-name 49-industry MV result (net Sharpe 0.60, −95% DD,
  loses to 1/N) stays as the contrast: the same optimizer destroys value on noisy single names.
- **W3 — Package: one-command reproduction.** A single `make reproduce` that downloads data, prints
  reproduced-vs-published Sharpes, prints the Lean verification status, runs the verified combine, and
  prints the deflated-Sharpe verdict, plus a one-page `REPORT.md` summary on the certify→validate→extend
  arc.

**Out of scope for this sprint:** dollar-neutral verified projection (new theorem), perpetual-futures
proofs, capacity/impact models, multi-period optimization, CRSP single-name upgrade. Parked to keep focus.

## Priority order (status: most items complete as of Jun 2026)

The completion path that turns the scaffold into a defensible end-to-end research artifact: a
backtested signal with an honest Sharpe and real signal diagnostics, with the load-bearing steps
formally verified. Perpetual-futures proofs are **parked** as an extension, off this critical path.

1. ✅ **Real study on FREE data first (Ken French daily), not CRSP.** Ran the OOS study and filled
   `studies/REPORT.md` with honest net-of-cost / deflated-Sharpe / walk-forward results. The Ken French
   loaders work with no credentials; CRSP is an optional single-stock upgrade (`studies/WRDS_DATA_REQUEST.md`).
2. ✅ **Signal-diagnostics report panel.** `REPORT.md` now reports rank IC, IC IR, Newey-West HAC t-stat,
   IC decay by horizon, **decile-spread monotonicity**, **rolling / subperiod IC stability**, and incremental
   IC vs. known factors (`combination.py`). The Track 1 validation harness (planted-alpha detection, noise
   rejection, injected-leak red-team) is the defensibility backbone for using a known alpha as a control.
3. ✅ **Measure-theoretic 𝓕ₜ upgrade** (Phase 1, item 3 below): genuine 𝓕ₜ-measurability against the natural
   filtration, citing `ftap-proofs`, proved `sorry`-free in `lean/ResearchPipeline/Measurability.lean`
   (`momentumSignal_adapted`). The shipped guarantee is now both the pointwise non-anticipation predicate and
   adapted-process 𝓕ₜ-measurability.
4. **Live verified-PGD wiring** (Phase 3, item 7 below — DONE for the budget simplex): `verified_pgd_weights`
   raises instead of silently substituting an unverified baseline (no silent fallback), and is wired live via
   `make_verified_pgd_weight_fn`. **Finding:** on single-name 49-industry cross-sectional momentum the verified
   MV book amplifies estimation error (net Sharpe 0.60, −95% DD, loses to 1/N) — the textbook Michaud/DeMiguel
   result, kept as the honest *contrast*. The optimizer's real home is the **verified total-portfolio combine**
   across diversifying sleeves — see brief W2 in "Near-term focus" above (reuses the existing budget-simplex
   proof; the dollar-neutral `sum w = 0` theorem stays parked).
5. ✅ **Bounded cross-asset study on FREE published data** (Phase 4, item 10 below): uses AQR's free
   "Time Series Momentum" / "Value and Momentum Everywhere" datasets (equities, bonds, currencies,
   commodities), same momentum signal, no per-asset tuning. `REPORT.md` §7 reports per-asset deflated Sharpe
   plus a cross-asset correlation table, scoped as breadth evidence (not routed through the verified backtester).

**Verification-scope honesty guardrail:** the no-look-ahead theorem covers the daily event-driven backtester.
Either route the cross-asset runs through that same verified backtester, or scope the "verified" claim to the
daily equity backtest and present cross-asset as breadth/generalization evidence. Never let "verified" stretch
silently over runs it did not touch.

## Phase 1 — Formal core (Lean)

- ✅ **Strategy-agnostic engine.** `Strategy` protocol + registry; cross-sectional and
  time-series alphas through one interface; pluggable portfolio constructors; engine hands
  each strategy only `as_of(t)`, so non-anticipation is inherited (issue #153).
- ✅ **No-leakage contract.** `embargo_blocks_label_leakage` (`NoLeakage.lean`, `sorry`-free):
  OOS embargo ≥ horizon ⇒ no training label leaks into the test window; runtime witness
  `oos.leakage_gap` + property test (issue #156).
- ✅ **CLI + artifacts.** `rp list / run / validate`; `results/<id>/` (issue #154).
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
