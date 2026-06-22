# Research Study — Cross-Sectional Momentum on the US Industry Cross-Section

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

### 5.2 Decile-spread monotonicity

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

### 5.6 Factor attribution (net returns on FF5 + momentum)

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
to tame the crash risk, and richer transaction-cost and capacity modeling. Those are tracked in
the ROADMAP. The cross-asset generalization study (does the same effect appear in bonds,
currencies, and commodities) is reported separately in **§7** as breadth evidence.

## 7. Cross-asset generalization

> Breadth / generalization evidence using free AQR factor data (`load_aqr_tsmom`). These are
> AQR's published time-series-momentum return streams and are **not** routed through the
> verified daily backtester, so the formal no-look-ahead guarantee is scoped to the equity
> study in sections 1 to 6. The cross-asset results below are presented as evidence that the
> effect is structural rather than market-specific. Reproduce with
> `python -m scripts.run_cross_asset --dataset tsmom` (writes `studies/results_crossasset.json`).

Time-series momentum, monthly, January 1985 to January 2025 (481 months), deflated against
`n_trials = 4` asset classes:

| Asset class | Sharpe | Annualized return | Deflated Sharpe |
|---|---|---|---|
| Equities | 0.54 | 11.5% | 0.989 |
| Fixed income | 0.62 | 15.2% | 0.998 |
| Currencies | 0.57 | 9.1% | 0.995 |
| Commodities | 0.64 | 8.7% | 0.999 |

Cross-asset correlations of the return streams are low (0.12 to 0.25). Momentum earns a
positive, multiple-testing-significant Sharpe in every asset class with weakly correlated
streams, the common-factor signature one expects from a structural effect rather than a
single-market artifact (Moskowitz, Ooi, Pedersen 2012; Asness, Moskowitz, Pedersen 2013).

### 7.1 Validation by reproduction

A breadth study is only as trustworthy as its agreement with the published record. The check here
places each sleeve's realized Sharpe (computed from the free AQR factor streams) beside the figure
reported in the source paper. The bar is sign and rough magnitude, not exact decimals: the free data
extend each paper's sample by a decade or more, and construction details (rebalance lag, volatility
scaling, universe) differ. A sleeve counts as reproduced when its realized Sharpe shares the
published sign and lands within a factor of two of the published value. Reproduce with
`python -m scripts.run_cross_asset --dataset vme --json studies/results_crossasset_vme.json`.

Value and Momentum Everywhere, per-market momentum factor, realized over January 1972 to March 2026,
against the figures in Asness, Moskowitz, Pedersen (2013), Table I (gross, each market over its own
sample to 2011):

| Market | Realized Sharpe | Published Sharpe | Reproduced |
|---|---|---|---|
| US equities | 0.44 | 0.45 | yes |
| UK equities | 0.51 | 0.88 | yes |
| Europe equities | 0.64 | 1.07 | yes |
| Japan equities | 0.12 | 0.37 | no |
| Equity indices | 0.46 | 1.00 | no |
| Currencies | 0.22 | 1.28 | no |
| Fixed income | 0.13 | 0.20 | yes |
| Commodities | 0.38 | 0.62 | yes |

Momentum is positive in all eight markets, the sign agreement one expects from a structural effect,
and five of eight land within a factor of two of the published Sharpe. Two of those five, UK and
Europe equities, reproduce at the lower end of the band (realized/published ratios near 0.58 and
0.60), so they clear the bar without much room to spare. The three that fall short are informative
rather than embarrassing. Japanese-equity and fixed-income momentum are the two markets
the paper itself reports as statistically insignificant (its own t-statistics near zero), so a weak
realized Sharpe agrees with the paper rather than contradicting it. Currency and equity-index
momentum decayed in the fifteen years of data after the paper's 2011 cutoff: the realized window here
runs to 2026, and the well-documented post-2011 drawdown in currency momentum pulls its full-sample
Sharpe far below the 1979 to 2011 figure. The realized numbers are reported as they come out,
including where they undershoot.

For time-series momentum the source paper (Moskowitz, Ooi, Pedersen 2012) does not tabulate
per-sleeve Sharpe ratios; it reports only the diversified all-asset composite, in prose, as greater
than 1.0 (gross, 1985 to 2009). The realized diversified TSMOM composite over 1985 to 2025 is 0.98,
essentially reproducing that figure (the small shortfall is the post-2009 decay common to the
literature). The four per-sleeve TSMOM Sharpes in the table at the top of this section are therefore
computed from the AQR data, not quoted from the paper.

### 7.2 Verification status

When the Lean proofs build green, the load-bearing invariants of the pipeline are machine-checked: no
look-ahead in the backtester, no train/test leakage (the out-of-sample embargo is at least the
holding horizon), and the signal is measurable against the information set available at each date
(adapted to the natural price filtration, citing the FTAP development). Separately, the projection and
convergence of the PGD portfolio solver are proven sorry-free in Lean (optimization-proofs); the
running solver is a Python implementation of that proven algorithm, and these proofs are not yet wired
into the continuous-integration matrix. The machine-checked no-look-ahead guarantee is scoped to the
daily equity backtester; the cross-asset streams in this section are pre-built factor returns
presented as breadth evidence, not verified runs.
