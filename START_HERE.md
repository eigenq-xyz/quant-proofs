# Start here

**quant-proofs** is a monorepo of formally verified quantitative finance: named results from
asset-pricing theory and load-bearing steps of quant research, each paired with a machine-checked
Lean 4 proof (zero `sorry` on main) and production Python.

**The thesis:** the durable skill in quantitative research is not running a backtest, it is knowing
whether to trust one. Every project here demonstrates the ability to *verify* a quantitative claim,
not just compute it.

## Read in this order

1. **2 minutes:** this file.
2. **The flagship:** [`research-pipeline/`](research-pipeline/README.md) — a full research-desk
   workflow (data → signals → statistical testing → portfolio → backtest → evaluation → cross-asset)
   whose load-bearing steps are formally verified.
3. **The headline study:** [`research-pipeline/studies/REPORT.md`](research-pipeline/studies/REPORT.md)
   — a real, honest momentum study with the numbers below.
4. **The foundations:** the verified theorems the pipeline rests on (`ftap-proofs`, `options-proofs`,
   `quant-core`, `optimization-proofs`, `portfolio-proofs`).

## The flagship in one screen

A research-desk pipeline that:

- **builds signals from a non-anticipating information set** — proved both as a pointwise
  non-anticipation predicate *and*, in the measure-theoretic upgrade, as genuine
  `𝓕ₜ`-measurability against the natural filtration of the price process (`Measurability.lean`,
  `sorry`-free, citing `ftap-proofs`);
- **backtests without look-ahead and splits out-of-sample without leakage** — both proved in Lean 4,
  zero `sorry`;
- **routes portfolio construction through a verified solver** — and *refuses* to silently substitute
  an unverified baseline (it raises), so a result is "verified" only if it actually was;
- **validates itself** — detects planted alpha (> 90% power), stays near a 5% false-positive rate on
  noise, and a red-team injection of a one-day look-ahead is caught by the guard.

## Headline numbers (real study, free data, reproducible)

Cross-sectional 12-1 momentum on the 49 Ken French industry portfolios, daily, 1926–2026
(`python -m scripts.run_study`):

| | |
|---|---|
| IC t-statistic (Newey-West HAC) | **14.3** |
| Decile-spread monotonicity | **strict (Q1→Q5 increasing)** |
| IC positive across subperiods | **5 of 5** |
| Net Sharpe (in-sample / out-of-sample) | **0.28 / 0.38** |
| Deflated Sharpe (50 trials) | **0.72** |
| Max drawdown | **−53%** |

The honest verdict is in the report: the effect is real, strongly significant, and stable, but the
net edge is modest and has decayed across decades. Using a *known* alpha as a control is deliberate —
the research object is the pipeline's correctness, not the signal.

Cross-asset breadth (AQR time-series-momentum, free): momentum earns a positive, multiple-testing-
significant Sharpe in equities, fixed income, currencies, and commodities, with low cross-asset
correlation (0.12–0.25) — the signature of a structural effect.

## Verification scorecard

| Layer | Status |
|---|---|
| Backtest no-look-ahead | Proved, `sorry`-free |
| OOS no-leakage (embargo ≥ horizon) | Proved, `sorry`-free |
| Signal `𝓕ₜ`-measurability (natural filtration) | Proved, `sorry`-free, cites `ftap-proofs` |
| Portfolio construction | Routes through the verified PGD solver; no silent fallback |
| Statistical layer (IC, HAC, PSR/DSR) | Rigorous, validated vs `statsmodels`/`scipy`; not formally verified |
| Cross-asset generalization | Breadth evidence; not routed through the verified backtester |

`CLAUDE.md` is the developer guide; each subproject has its own README.
License: Apache 2.0 (mathlib-compatible).
