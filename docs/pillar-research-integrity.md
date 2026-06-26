# Research Integrity

The central question in quantitative research is not "what does the backtest say?" It is "should
we trust it?" A backtest can be wrong because the code peeked at the future, because an
out-of-sample split leaked a label, or because the data it read was not knowable at decision time.
This pillar is the EigenQ Research Series flagship: a full research-desk workflow whose
trust-critical steps are machine-checked, paired with honest empirical studies that map where that
trust actually breaks.

The proofs here are the rigor backbone, not the headline. The headline is the research: a pipeline
that is correct by construction, and studies that are reported with their limitations intact.

---

## `research-pipeline`: a verified research desk

`research-pipeline` runs the stages a research desk runs, from data through signals, statistical
testing, portfolio construction, backtesting, evaluation, and a cross-asset robustness check. The
engine is alpha-agnostic: a strategy maps the information set available at time `t` to a target
portfolio, so cross-sectional and time-series ideas share one interface.

What is machine-checked, zero `sorry`:

- **No look-ahead.** The backtester is proved non-anticipating: a position built from a
  non-anticipating signal cannot depend on the future.
- **No leakage.** An out-of-sample split with an embargo at least the label horizon is proved
  unable to leak a training label into the test window.
- **Signal measurability.** The signal map is proved adapted to the natural filtration of the price
  process, the measure-theoretic form of "uses only what was knowable at `t`." This holds for the
  momentum signal and for the variance-risk-premium signal, the latter adapted to the joint
  information of prices and implied volatility.

What is rigorous but not formally verified: the statistical layer (information coefficients,
Newey-West HAC t-statistics, the deflated and probabilistic Sharpe ratios) and all profit-and-loss
and strategy economics. The pipeline cross-checks these against `statsmodels` and `scipy`, and it
validates itself: it detects planted alpha, stays near a five percent false-positive rate on noise,
and a deliberately injected one-day look-ahead is caught by the guard. Portfolio construction is
routed through the verified solver and raises rather than silently substituting an unverified
baseline, so a result counts as verified only when it was.

### The headline study

Cross-sectional 12-1 momentum on the 49 Ken French industry portfolios, daily, 1926 to 2026,
reproducible from free data. The information-coefficient t-statistic (Newey-West) is 14.3, the
quintile spread is strictly monotone, the net Sharpe ratio is 0.28 in sample and 0.38 out of
sample, the deflated Sharpe ratio over 50 trials is 0.72, and the maximum drawdown is 53 percent.

The verdict, stated in the report, is honest: the effect is real, strongly significant, and stable,
but the net edge is modest and has decayed across decades. A known alpha is used deliberately as a
control, because the research object is the pipeline's correctness, not the signal. A cross-asset
check finds a multiple-testing-significant momentum Sharpe in equities, fixed income, currencies,
and commodities, with low cross-asset correlation.

[Read the pipeline](https://github.com/eigenq-xyz/quant-proofs/tree/main/research-pipeline)

---

## The leakage-tax map: where point-in-time discipline matters

A backtest can be perfectly non-anticipating in its logic and still be contaminated if the values it
reads were later revised. This study asks how much apparent alpha is such an artifact, and measures
it on real data across several series: CFTC positioning (a release-timing channel), EIA gas storage
(a barely-revised series), and nonfarm payrolls (revised in essentially every month). Each cell runs
identical code with only the data-timing rule changed, and reports a Newey-West HAC t-statistic on
the difference.

The result is a map, not an alpha claim. The binding axis is the signal's functional form, not how
heavily the series is revised. A standardized, clipped signal is structurally immune to revision
look-ahead even on the most heavily revised series; a hard threshold signal on the same data is
exposed, though the exposed case is modest and regime-dependent. Point-in-time discipline is cheap
insurance whose payoff depends on signal design, a conclusion drawn from a Federal Reserve
forecasting question and made precise here.

[Read the map](https://github.com/eigenq-xyz/quant-proofs/tree/main/research-pipeline/studies)

---

## The variance-risk-premium study

A delta-hedged short-volatility strategy on the S&P 500, harvesting the gap by which index implied
variance exceeds subsequently realized variance (Bollerslev, Tauchen, and Zhou, 2009). The signal's
non-anticipation is machine-checked, and its discrete pricing identities are proved on the
Cox-Ross-Rubinstein tree (see [No-Arbitrage Pricing](pillar-pricing.md)).

The result is reported with its frictions and its tail. The premium survives realistic hedging
costs, but the defensible net Sharpe ratio is on the order of 0.7 to 1.0 once realistic index-option
spreads are charged, not the 2 to 3 seen under frictionless option execution. The payoff is short
the tail: negative skew and fat left tails, with the worst months falling on the known volatility
events. The in-sample and out-of-sample windows are declared in advance.

Reference: Bollerslev, T., G. Tauchen, and H. Zhou. "Expected Stock Returns and Variance Risk
Premia." *Review of Financial Studies* 22, no. 11 (2009): 4463-4492.

[Read the study](https://github.com/eigenq-xyz/quant-proofs/tree/main/research-pipeline/studies/vrp)

---

## Why this is the flagship

Every result in this pillar reflects one discipline: never treat an input as ground truth. A proof
will not compile a false correctness claim; point-in-time data refuses values that were not knowable;
the revision map refuses to assume a knowable value was the right one. The verification is what makes
the research auditable, and the research is the point.
