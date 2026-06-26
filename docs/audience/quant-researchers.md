# For Quant Researchers and Practitioners

If you build or audit quantitative systems, the most relevant entry point is the
[Research Integrity flagship](../pillar-research-integrity.md): a full research-desk
workflow whose trust-critical steps are machine-checked, paired with empirical studies
that report their limitations intact. The [No-Arbitrage Pricing pillar](../pillar-pricing.md)
covers the derivative pricing results and the variance-risk-premium identities that
underpin the VRP study.

The core concern addressed here is not whether the code ran. It is whether the
pipeline did what it claims: no look-ahead, no out-of-sample leakage, and signals
that provably use only what was knowable at decision time.

## What the research pipeline proves

The `research-pipeline` module runs a complete desk workflow from data ingestion
through signals, statistical testing, portfolio construction, backtesting, evaluation,
and a cross-asset robustness check. What is machine-checked, zero sorry:

- **No look-ahead.** The backtester is proved non-anticipating: a position built from
  a non-anticipating signal cannot depend on the future.
- **No leakage.** An out-of-sample split with an embargo at least the label horizon is
  proved unable to leak a training label into the test window.
- **Signal measurability.** The signal map is proved adapted to the natural filtration
  of the price process, the measure-theoretic form of "uses only what was knowable at
  this time." This holds for the 12-1 momentum signal and for the variance-risk-premium
  signal, the latter adapted to the joint filtration of prices and implied volatility.

What is rigorous but not formally verified: the statistical layer (information
coefficients, Newey-West HAC t-statistics, the deflated and probabilistic Sharpe
ratios) and all profit-and-loss and strategy economics. The pipeline validates itself:
it detects planted alpha, stays near a five percent false-positive rate on noise,
and a deliberately injected one-day look-ahead is caught by the guard.

## The headline study

Cross-sectional 12-1 momentum on the 49 Ken French industry portfolios, daily,
1926 to 2026, reproducible from free data. Information-coefficient t-statistic
(Newey-West): 14.3. Quintile spread: strictly monotone. Net Sharpe ratio: 0.28
in sample and 0.38 out of sample. Deflated Sharpe over 50 trials: 0.72. Maximum
drawdown: 53 percent. A cross-asset check finds a multiple-testing-significant
momentum Sharpe in equities, fixed income, currencies, and commodities, with
low cross-asset correlation.

The verdict, stated in the report: the effect is real, strongly significant, and
stable, but the net edge is modest and has decayed. A known alpha is used
deliberately as a control, because the research object is the pipeline's
correctness, not the signal.

## The leakage-tax map

A backtest can be perfectly non-anticipating in its logic and still be contaminated
if the values it reads were later revised. The leakage-tax map measures this on
real data across several series: CFTC COT release timing, EIA gas storage, and
nonfarm payrolls. Each cell runs identical code with only the data-timing rule
changed, and reports a Newey-West HAC t-statistic on the difference.

The result is a map, not an alpha claim. The binding axis is the signal's functional
form, not how heavily the series is revised. A standardized, clipped signal is
structurally immune to revision look-ahead even on the most heavily revised series.
A hard threshold on the same data is exposed, though the exposed case is modest and
regime-dependent.

## The variance-risk-premium study

A delta-hedged short-volatility strategy on the S&P 500, signal defined as VIX-squared
times 30/365 minus realized variance over the prior 30 days, with the signal's
non-anticipation machine-checked. The premium survives realistic hedging costs, but
the defensible net Sharpe ratio is 0.7 to 1.0 once realistic index-option spreads are
charged, not the 2 to 3 seen under frictionless execution. The payoff is short the
tail: negative skew and fat left tails, with the worst months on the known volatility
events. In-sample and out-of-sample windows are declared in advance.

The discrete pricing identities behind the VRP are proved separately in
`extensions/vrp-proofs/`, see the [No-Arbitrage Pricing pillar](../pillar-pricing.md).

## The FFI contract: why basis-point arithmetic matters

The quant-core library represents all prices and payoffs as integers scaled by 10,000
(basis points). The Lean theorems are proved over integers; the Python and Cython
execution layer uses the same integer representation. The arithmetic in the proof and
the arithmetic in production are identical. There is no rounding gap between the proved
result and the computed result.

This matters because floating-point summation is non-associative: the order of
operations can change the result by small amounts, and those amounts can accumulate
in a portfolio rebalancing loop or a constraint check. The basis-point contract
eliminates that class of discrepancy. Details are in [how-we-verify.md](../how-we-verify.md).

## Optimization guarantees the solver actually satisfies

The [Verified Optimization pillar](../pillar-optimization.md) proves that the simplex
projection always returns a weight vector satisfying the budget constraint (weights sum
to one) and the no-leverage constraint (each weight is nonnegative), for any gradient
input. The portfolio solver raises when the verified solver cannot be applied rather
than silently substituting an unverified baseline, so a result counts as verified only
when it was. Seven empirical stress scenarios compare the verified solver against
SciPy SLSQP, SciPy trust-constr, and Gurobi on inputs designed to expose constraint
violations and numerical drift.

## Entry points

- Research integrity, studies, and signal measurability: [pillar-research-integrity.md](../pillar-research-integrity.md)
- Pricing results and VRP identities: [pillar-pricing.md](../pillar-pricing.md)
- Verification methodology and the FFI contract: [how-we-verify.md](../how-we-verify.md)
- Optimization proofs and stress scenarios: [pillar-optimization.md](../pillar-optimization.md)
- AI decision pipeline invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
