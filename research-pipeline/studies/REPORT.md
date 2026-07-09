# Research Study: Cross-Sectional Momentum on the US Industry Cross-Section

> Reproduce with `python -m scripts.run_study` (free Ken French data, no credentials).
> Numbers below are read directly from `studies/results_ken_french_49ind.json`. This report
> is only as trustworthy as the pipeline that produced it, so read **§4 Pipeline validation**
> before the results.

## 1. Hypothesis

Cross-sectional momentum is a known, widely documented effect: assets that outperformed over
the past year (skipping the most recent month) tend to keep outperforming over the near
horizon. The effect is usually attributed to underreaction to information and to slow
diffusion of news across the cross-section.

We use this **known** alpha deliberately as a scientific control. The signal is not the
research question; the pipeline is. If a clean, leak-free, cost-aware pipeline cannot recover
a documented effect, the pipeline is wrong. If it recovers it but the effect is modest net of
costs and decays out of sample, that is the honest truth a research desk needs before
committing capital. The aim is to show the pipeline can tell a real, capacity-limited edge
from phantom backtest profit.

## 2. Data

- **Source:** Ken French Data Library, `49_Industry_Portfolios_daily` (free, fetched directly
  from Dartmouth by `data_sources.load_ken_french_factors`; no licensed data).
- **Universe:** 49 value-weighted US industry portfolios treated as the cross-section.
- **Period:** full available daily history, July 1926 to April 2026 (25,981 daily observations).
- **Point-in-time:** prices are built from the published returns and consumed only through
  `PricePanel.as_of(t)`; every signal value at date `t` uses prices at dates up to `t` only.
- **Attribution factors:** Fama-French 5 factors plus the momentum factor, daily (also free).

## 3. Method

- **Signal:** 12-1 cross-sectional momentum, defined as the return from `t-252` to `t-21`
  (both at or before `t`), cross-sectionally demeaned so the book is dollar-neutral.
- **Portfolio:** dollar-neutral proportional weights, `sum(w)=0`, `sum(|w|)=1`.
- **Costs:** 10 basis points proportional per unit of one-way turnover.
- **Horizon:** one day.
- **Out-of-sample:** 5-fold expanding walk-forward with a 5-day embargo (purge) between each
  training window and its test window. The realized minimum leakage slack was **5** trading
  days, so no training label bleeds into any test window (the runtime witness of the embargo
  contract; slack >= 1 means clean).

## 4. Pipeline validation (Track 1)

Before any number below is trusted, the pipeline was validated against synthetic ground truth
(`validation.py`, `tests/`, 47 tests passing):

- it **detects planted alpha** at strong signal-to-noise (detection power above 0.9);
- its **false-positive rate on pure noise** sits near the nominal 5%;
- the **no-look-ahead guard catches an injected one-day leak** (the leaky signal trips the
  boundary discrepancy; the clean momentum signal does not);
- the **no-leakage contract** flags an embargo shorter than the label horizon;
- the estimators (rank IC, Newey-West HAC t-stat, PSR/DSR) **match `statsmodels` / `scipy`**
  references.

## 5. Results

### 5.1 Signal quality (information coefficient)

| Metric | Value |
|---|---|
| Mean rank IC | 0.0264 |
| IC standard deviation | 0.2592 |
| Annualized IC information ratio | 1.62 |
| IC t-statistic (Newey-West HAC) | 14.25 |
| IC hit rate (share of days IC > 0) | 55.3% |
| Periods | 25,980 |

The IC is small per day but extremely stable, which is what a real cross-sectional effect over
a long daily sample looks like.

### 5.2 Quintile-spread monotonicity

Sorting the cross-section into quintiles by signal each day and averaging the forward return of
each bucket gives a **strictly monotone** low-to-high pattern:

| Bucket (low signal to high) | Mean forward return |
|---|---|
| Q1 | 0.00029 |
| Q2 | 0.00037 |
| Q3 | 0.00044 |
| Q4 | 0.00050 |
| Q5 | 0.00065 |
| **Top minus bottom** | **0.00036 / day** |

Rank correlation between bucket and mean return is **1.00**; the fraction of adjacent steps
that increase is **1.00**. The effect is not driven by a single extreme bucket.

### 5.3 IC decay by horizon

| Forward horizon (days) | 1 | 5 | 21 | 63 |
|---|---|---|---|---|
| Mean IC | 0.026 | 0.047 | 0.072 | 0.100 |

IC *rises* with horizon: momentum is a slow signal, so a one-day forward target understates it.
Daily rebalancing therefore trades more often than the signal demands, which the net Sharpe
below reflects.

### 5.4 Subperiod IC stability

Splitting the IC series into 5 contiguous subperiods:

| Metric | Value |
|---|---|
| Subperiods with positive mean IC | 5 of 5 (100%) |
| Worst subperiod mean IC | 0.0216 |
| Best subperiod mean IC | 0.0309 |
| Subperiod IC dispersion (std) | 0.0038 |

The edge shows up in every subperiod across nearly a century, not just one lucky regime.

### 5.5 Backtest performance (net of costs)

| Metric | In-sample | Out-of-sample (walk-forward) |
|---|---|---|
| Net Sharpe | 0.28 | **0.38** |
| Gross Sharpe | 0.55 | — |
| Annualized return | 1.95% | — |
| Annualized volatility | 7.97% | — |
| Max drawdown | -53.2% | — |
| Average daily turnover | 0.084 | — |
| Skewness | -0.70 | — |
| Kurtosis | 14.0 | — |
| Probabilistic Sharpe ratio | 0.998 | — |
| **Deflated Sharpe ratio** (n_trials = 50) | **0.72** | — |

Per-fold out-of-sample net Sharpe: 0.63 (1941-1956), 0.95 (1956-1974), 0.30 (1974-1991),
0.24 (1991-2008), 0.17 (2008-2026).

### 5.6 Verified portfolio construction vs. naive baselines

The backtest above uses a fixed, naive weighting scheme. This asks whether routing the same
signal through the correct-by-construction mean-variance solver (`optimization-proofs`) does
better, on this same 49-industry cross-section, monthly rebalance, gross leverage capped at 1.5.
Reproduce with `python -m scripts.compare_pgd` (default `--rebalance monthly`; results in
`studies/results_pgd_comparison_monthly.json`).

| Book | Net Sharpe | Max drawdown |
|---|---|---|
| Verified PGD mean-variance | 0.60 | −94.6% |
| Long-only momentum | 0.80 | −76.8% |
| **Equal weight (1/N)** | **0.70** | −78.5% |
| Dollar-neutral baseline | 0.48 | −45.0% |

Equal weight beats the verified mean-variance book here, and the mean-variance book's drawdown is
the worst of the four: the sample-mean-driven optimizer concentrates on whichever industries look
best in-sample, the same failure mode DeMiguel, Garlappi, and Uppal (2009) document for
mean-variance on noisy single-name universes. The honest reading is that routing through the
correct-by-construction solver buys correctness and auditability of the optimization step, not
outperformance: the solve is proved to land on the constrained optimum, but a mean-variance
objective fed noisy sample-mean inputs does not beat naive diversification on this cross-section.

### 5.7 Factor attribution (net returns on FF5 + momentum)

| Term | Value |
|---|---|
| Daily alpha | 0.00008 |
| Beta to momentum (Mom) | 0.063 |
| Beta to market (Mkt-RF) | 0.005 |
| Beta to SMB / HML / RMW / CMA | -0.011 / 0.005 / -0.017 / 0.003 |
| R-squared | 0.010 |

As designed, the strategy loads positively and predominantly on the momentum factor with
negligible incremental alpha. This is the correct result for a known-alpha control: the signal
*is* momentum, it is not pretending to be something new.

## 6. Conclusion and limitations

The pipeline recovers the momentum effect cleanly and honestly. The signal is strongly
significant (IC t-stat 14.3), strictly monotone across buckets, and stable in every subperiod
of a near-century sample. It survives multiple-testing deflation (deflated Sharpe 0.72 against
50 trials). But the honest verdict is sober:

- **The net edge is modest.** Transaction costs cut the Sharpe roughly in half (0.55 gross to
  0.28 net), and daily rebalancing of a slow signal overtrades relative to the IC decay profile.
- **The edge has decayed.** Out-of-sample fold Sharpe falls monotonically from 0.95 in the
  mid-century to 0.17 in the most recent fold (2008-2026), consistent with the well-documented
  erosion of the simple momentum premium as it became widely traded.
- **The tail is ugly.** A -53% maximum drawdown and a left-skewed, fat-tailed return
  distribution (skew -0.70, kurtosis 14) reflect the periodic momentum crashes.

What would change the conclusion: rebalancing on the signal's natural horizon rather than daily
(the IC decay says the information is strongest at 21 to 63 days), a volatility-managed overlay
to tame the crash risk, and richer transaction-cost and capacity modeling. Those remain future
work.

Two further analyses that used to appear here (cross-asset generalization on AQR's pre-built
factor-return sleeves, and a verified-solver-vs-1/N combine test on those same sleeves) moved to
[`extensions/research-ideas/`](../../extensions/research-ideas/README.md). Neither routes through
the backtester this report's no-look-ahead guarantee covers, and neither has had enough independent
studies run to support a load-bearing claim yet. They are preserved there as exploratory work, not
results this report stands behind.

## 7. Verification status

When the Lean proofs build green, the load-bearing invariants of the pipeline are proved correct:
no look-ahead in the backtester, no train/test leakage (the out-of-sample embargo is at least the
holding horizon), and the signal is measurable against the information set available at each date
(adapted to the natural price filtration, citing the FTAP development). Separately, the projection
and convergence of the PGD portfolio solver are proved sorry-free in Lean (`optimization-proofs`,
where zero `sorry`, Lean's placeholder for an unproven step, means none remain); the running solver
is a Python implementation of that proven algorithm, and these proofs are not yet wired into the
continuous-integration matrix.
