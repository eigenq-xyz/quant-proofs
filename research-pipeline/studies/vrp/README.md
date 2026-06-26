# Variance Risk Premium (VRP) delta-hedged short-volatility study

**EigenQ Research Series.** Stage 1: simulated, free-data study of a short-volatility
strategy on the S&P 500 index. Routing the P&L through the verified delta-hedge accounting
engine (`extensions/hedge-proofs/`) is reserved for Stage 2b; pricing and hedging P&L here
are computed inline with Black-Scholes.

## Hypothesis

Index implied variance (VIX squared) systematically exceeds subsequently realized variance.
This gap is the **variance risk premium** (Bollerslev, Tauchen, and Zhou 2009; Carr and Wu
2009). A seller of index volatility who hedges the directional exposure should harvest the
premium, at the cost of severe negative skew: the short-vol payoff is short the tail, and
tails arrive in crises (Coval and Shumway 2001).

## Signal

Following Bollerslev, Tauchen, and Zhou (2009):

```
VRP(t) = VIX(t)^2 * (30/365) - realized_variance(t)
```

where `VIX(t)` is annualized implied volatility (squared to get implied variance) and
`realized_variance(t)` is the annualized sum of squared daily log returns over the prior
21 trading days. The signal uses only information observed up to and including time `t`, so
it is `F_t`-measurable (no look-ahead).

This non-anticipation property is machine-checked, sorry-free, in
`research-pipeline/lean/ResearchPipeline/Measurability.lean`. The theorem `vrpSignal_adapted`
proves that the VRP signal process is **adapted**: its value at `t` is measurable with respect
to the information available at `t`. Because the signal reads two observable processes, the
price process (through the trailing realized variance) and an implied-variance process (the
squared VIX), the honest scope is that it is adapted to any filtration carrying **both**, the
joint market-information filtration, rather than the price-only natural filtration that suffices
for a pure price signal like `momentumSignal_adapted`. The proof reads each windowed price
`price (t - i)` (every index `≤ t`) and the contemporaneous `impliedVar t` through their
adaptedness and combines them through the measurable signal rule. The statistical and P&L layers
below are empirical and unverified; the non-anticipation of the signal is the part that is
formally proved.

## Strategy

Each trading month (every 21 trading days), sell a 30-day at-the-money straddle on the index,
priced with Black-Scholes using `VIX(t)` as the implied-volatility input, then delta-hedge on
a configurable schedule. An ATM straddle has delta approximately zero at inception, so the
residual delta hedged with the index is small; the position is short gamma and short vega. We
implement the standard discrete delta-hedging P&L (rebalance the stock hedge on schedule,
accrue cash at the risk-free rate, settle at intrinsic value at expiry) rather than relying on
the closed-form implied-minus-realized-variance approximation. P&L is normalized to one dollar
of index exposure per straddle.

The Black-Scholes price and delta are an inline re-implementation of the verified primitives
in `foundations/quant-core/python/src/quant_core/pricer/black_scholes.py` (`bs_price`,
`bs_greeks`); the study is kept to a single dependency-light file and cites quant-core as the
verified reference.

## Data (all free, no API key)

| Series | Source |
|--------|--------|
| S&P 500 spot (`^GSPC`, auto-adjusted) | Yahoo Finance via `yfinance` |
| VIX (`VIXCLS`) | FRED public CSV |
| 3-month T-bill (`DTB3`) | FRED public CSV |

VIX history starts 1990, which sets the sample.

## Methodology

- **In-sample (IS): 1990 to 2009. Out-of-sample (OOS): 2010 to 2025. Declared upfront.**
- **Realistic frictions (this revision).** The original Stage-1 engine charged cost only on
  the option premium (0.5% round-trip) and left the roughly 21 daily stock rebalances
  frictionless, which inflated the net Sharpe to about 2.9. Three configurable frictions are
  now charged (`HedgeConfig`):
  1. **Per-rebalance hedge cost.** Every stock-hedge trade (initial hedge, each rebalance,
     final liquidation) pays `tc_hedge_bps / 1e4 * |d_shares| * S`. Swept over 1, 2, 5, 10 bps.
  2. **Entry half-spread.** The straddle is sold below the Black-Scholes mid:
     `premium_received = mid * (1 - entry_half_spread)`, with the matching closing leg charged
     as a round-trip option spread. Swept over 0 to 3% of premium.
  3. **Hedge frequency.** Daily, every two days, or weekly. Less frequent hedging lowers
     turnover cost but raises hedging error; the tradeoff is reported.
- **Headline assumption: 2 bps per rebalance, 1% entry half-spread, daily hedging.**
- Benchmarks: long index (buy and hold) and a static short straddle **without** delta hedging,
  to isolate the contribution of hedging.
- Per sample: annualized mean return, Sharpe, max drawdown, skew, excess kurtosis,
  Newey-West HAC t-stat (3 lags), and the correlation of the VRP signal with forward realized
  variance.

## Results (actual run, this study)

P&L is per one dollar of index exposure; "return" is the monthly P&L, annualized by 12. Net
figures use the **headline** friction assumption: 2 bps per rebalance, 1% entry half-spread,
daily hedging.

### In-sample 1990 to 2009 (headline frictions)

| Strategy | Ann. return | Sharpe | Max DD | Skew | Exc. kurt | NW t-stat |
|----------|------------:|-------:|-------:|-----:|----------:|----------:|
| Hedged short-vol (net) | 10.7% | 2.56 | -11.7% | -0.87 | 9.27 | 10.2 |
| Hedged short-vol (gross) | 11.7% | 2.82 | -11.4% | -0.84 | 9.28 | 11.3 |
| Static short straddle (no hedge) | 14.6% | 1.61 | -24.4% | -1.61 | 4.47 | 7.4 |
| Long index (buy and hold) | 7.5% | 0.47 | -55.7% | -0.02 | 3.73 | 2.1 |

VRP signal vs forward realized variance correlation: -0.50. Mean monthly VRP: +0.00101.
VRP positive in 90% of months. Mean hedge cost per trade: 0.00068; mean option cost: 0.00023.

### Out-of-sample 2010 to 2025 (headline frictions)

| Strategy | Ann. return | Sharpe | Max DD | Skew | Exc. kurt | NW t-stat |
|----------|------------:|-------:|-------:|-----:|----------:|----------:|
| Hedged short-vol (net) | 8.3% | 1.81 | -10.9% | -2.03 | 8.15 | 6.8 |
| Hedged short-vol (gross) | 9.4% | 2.04 | -10.6% | -2.01 | 8.07 | 7.7 |
| Static short straddle (no hedge) | 11.5% | 1.52 | -10.4% | -0.81 | 2.68 | 6.7 |
| Long index (buy and hold) | 12.5% | 0.92 | -22.5% | -0.70 | 0.96 | 4.3 |

VRP signal vs forward realized variance correlation: -0.07. Mean monthly VRP: +0.00066.
VRP positive in 84% of months. Mean hedge cost per trade: 0.00066; mean option cost: 0.00021.

### Cost sensitivity: net Sharpe vs per-rebalance bps (1% half-spread, daily)

| bps / rebalance | IS Sharpe | OOS Sharpe | IS ann. | OOS ann. | hedge cost / trade |
|----------------:|----------:|-----------:|--------:|---------:|-------------------:|
| 0 (option spread only) | 2.76 | 1.99 | 11.5% | 9.1% | 0.00000 |
| 1 | 2.66 | 1.90 | 11.1% | 8.7% | 0.00034 |
| 2 (headline) | 2.56 | 1.81 | 10.7% | 8.3% | 0.00067 |
| 5 | 2.27 | 1.55 | 9.4% | 7.1% | 0.00168 |
| 10 | 1.78 | 1.11 | 7.4% | 5.1% | 0.00335 |

### Hedge-frequency sensitivity (2 bps/rebalance, 1% half-spread)

| Schedule | IS Sharpe | OOS Sharpe | IS ann. | OOS ann. | hedge cost / trade |
|----------|----------:|-----------:|--------:|---------:|-------------------:|
| Daily | 2.56 | 1.81 | 10.7% | 8.3% | 0.00067 |
| Every 2 days | 2.20 | 1.73 | 10.2% | 8.5% | 0.00055 |
| Weekly | 2.09 | 1.81 | 11.2% | 9.8% | 0.00044 |

Less frequent hedging cuts turnover cost (0.00067 to 0.00044 per trade) but adds hedging
error: the IS Sharpe falls from 2.56 (daily) to 2.09 (weekly) because the residual gamma P&L
between rebalances is larger. OOS the two effects roughly cancel. The hedging error, not the
cost saving, is the binding constraint on the index, where daily closes are cheap and gaps are
modest.

### Entry half-spread sensitivity (2 bps/rebalance, daily)

| Half-spread | IS Sharpe | OOS Sharpe | IS ann. | OOS ann. |
|------------:|----------:|-----------:|--------:|---------:|
| 0% | 2.75 | 1.97 | 11.5% | 9.1% |
| 1% (headline) | 2.37 | 1.65 | 9.8% | 7.6% |
| 2% | 1.98 | 1.32 | 8.2% | 6.0% |
| 3% | 1.59 | 0.99 | 6.5% | 4.5% |

(The half-spread sweep charges a symmetric round-trip option spread of twice the half-spread,
so it is more punitive than the headline's fixed 0.5% closing leg; this isolates the
option-spread sensitivity.)

### Combined friction (higher hedge cost AND wide option spread, daily)

The bps and half-spread sweeps above each hold the other friction light. The realistic case
charges both at once. These rows compute that directly (the round-trip option spread is twice
the entry half-spread).

| Config | IS Sharpe | OOS Sharpe | IS ann. | OOS ann. |
|--------|----------:|-----------:|--------:|---------:|
| 5 bps/reb, 3% half-spread | 1.29 | 0.73 | 5.3% | 3.3% |
| 10 bps/reb, 5% half-spread | -0.01 | -0.37 | -0.1% | -1.7% |

The 5 bps + 3% combination lands the OOS Sharpe at 0.73, inside the literature's 0.7 to 1.0 band
and the number that should be cited as a realistic estimate. At 10 bps + 5% the premium is fully
consumed and the strategy turns negative, so the result is genuinely contingent on the option
execution an investor can achieve.

### Worst hedged months (net P&L per dollar of exposure, headline)

| Entry | Hedged P&L | Index return |
|-------|-----------:|-------------:|
| 2020-03-10 (COVID crash) | -7.4% | -4.6% |
| 2008-09-03 (Lehman) | -6.7% | -12.6% |
| 2025-03-14 | -4.3% | -4.1% |
| 2018-01-05 (Volmageddon) | -4.3% | -1.8% |
| 2008-10-02 (Lehman aftermath) | -3.9% | -13.1% |

## Verdict

**Does the premium survive realistic frictions? Yes, but the Sharpe is lower and cost-dependent.**
Under the headline assumption (2 bps per rebalance, 1% entry half-spread, daily hedging), the
hedged short-vol strategy earns 10.7% annualized in-sample (Sharpe 2.56, Newey-West t of 10.2)
and 8.3% out-of-sample (Sharpe 1.81, t of 6.8). The premium is real and significant after costs,
and hedging still adds value over the unhedged static straddle (Sharpe 1.81 vs 1.52 OOS) while
cutting the in-sample drawdown from -24% to -12%.

**The headline Sharpe is still above the literature range (about 0.5 to 1.0), and the sensitivity
tables show why.** For a delta-flat ATM straddle the stock-hedge turnover is genuinely small, so
even 10 bps per rebalance only knocks the OOS Sharpe from 2.0 to 1.1. The friction that dominates
in practice is the **bid-ask on the option itself**: index-option round-trip spreads are wide
(commonly several percent of the option mid), far above the 0.5% modeled at the headline. The
half-spread sweep makes this explicit: at a 3% entry half-spread (6% round-trip) the OOS Sharpe
falls to **0.99** with hedge cost held at the light 2 bps. Charging both frictions together (the
combined-friction table below) is the realistic case: 5 bps per rebalance plus a 3% half-spread
lands the OOS Sharpe at **0.73**, squarely inside the literature range, and a punitive 10 bps
plus a 5% half-spread fully consumes the premium (OOS Sharpe **-0.37**).

**The honest bottom line:** the variance risk premium clears realistic *hedging* frictions
comfortably; whether it clears realistic *option-execution* frictions depends on the spread an
investor actually pays. With tradeable index-option spreads, the defensible net Sharpe is on the
order of **0.7 to 1.0**, not 2 to 3. The 2 to 3 figures reported under the lightest assumptions
reflect frictionless option execution and should not be taken as live performance.

**What it costs is tail risk, shown honestly.** Every strategy variant has negative skew and
fat tails: the OOS hedged skew is -2.03 with excess kurtosis of 8.1, and the five worst months
are precisely the known volatility events (September 2008 Lehman, March 2020 COVID, January
2018 Volmageddon, March 2025). The premium is compensation for selling insurance against exactly
these episodes. The result is also **weaker out of sample than in sample** (Sharpe 1.81 vs 2.56,
skew worse at -2.03 vs -0.87), reported faithfully.

## Honest caveats

- **The headline Sharpe still overstates live performance**, for one dominant reason: option
  execution. The model charges a 1% entry half-spread and a 0.5% closing leg, but real index-
  option round-trip spreads run several percent of the option mid. The half-spread sweep above
  shows the OOS Sharpe falling to about 0.7 to 1.0 once that spread is set realistically, which
  is the number that should be cited.
- VIX is a 30-day model-free implied-variance proxy, not a tradable straddle IV; using it as the
  BS sigma is a standard simplification, not a quote. The option is priced *at* VIX, so the
  entry mid is "fair" relative to the same VIX that drives realized vol, understating the
  slippage between quoted and transactable prices.
- Delta hedging is at the daily (or schedule) close with no intraday gaps and no gamma slippage
  within a rebalance interval beyond what the frequency sweep captures.
- No historical option chains are used. Stage 2 would replace the simulated premium with real
  index-option mid and bid-ask prices (OptionMetrics or CBOE) and route position sizing through
  the verified portfolio solver.

## References

- Bollerslev, Tauchen, and Zhou (2009), "Expected Stock Returns and Variance Risk Premia,"
  *Review of Financial Studies*.
- Carr and Wu (2009), "Variance Risk Premiums," *Review of Financial Studies*.
- Coval and Shumway (2001), "Expected Option Returns," *Journal of Finance*.

## Run

```bash
python3.12 research-pipeline/studies/vrp/run_study.py
```

Outputs `results/results_vrp.json` (summary statistics) and `results/vrp_trades.csv`
(per-trade panel).
