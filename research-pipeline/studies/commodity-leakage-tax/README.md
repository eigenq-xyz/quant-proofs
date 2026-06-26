# Commodity leakage-tax study: CFTC COT crude-oil positioning

How much of the apparent alpha in a commodity systematic strategy is an artifact of
look-ahead in the **data** (not the code)? This study isolates one clean, mechanical source
of data look-ahead: the release lag of the CFTC Commitments-of-Traders report.

## The strategy

- **Universe / instrument:** WTI crude positioning as the signal, the USO ETF as the
  tradable (daily adjusted prices via `yfinance`; `auto_adjust` handles the April-2020 1:8
  reverse split).
- **Signal:** the trailing 52-week percentile of Managed-Money **net** long positioning
  (`M_Money_Positions_Long_All - M_Money_Positions_Short_All`) in NYMEX Light Sweet Crude Oil
  (CFTC contract market code `067651`, Disaggregated Futures-Only report).
- **Rule:** contrarian fade. Position = `-(2 * percentile - 1)`, so a crowded-long extreme
  (percentile near 1) gives a short and a crowded-short extreme gives a long. Continuous tilt,
  weekly holding, USO open-to-open returns. No magic threshold.

## The leakage

A COT report is **as-of Tuesday** but is **released the following Friday 3:30pm ET**, a
3.5-day lag. Two variants run on identical code:

- **NAIVE** treats Tuesday's positioning as tradeable at/after that Tuesday's close. This is
  the standard (wrong) way these signals are backtested: it assumes you knew Tuesday's
  positioning on Tuesday.
- **PIT (point-in-time honest)** lets the signal act only from the following **Monday's open**,
  strictly after the Friday 3:30pm release. We set `release_date = as_of + 3 days` (Tuesday to
  Friday) and require the entry day to be the first trading day on/after the next Monday.

The **leakage tax** is `SR_naive - SR_pit` (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat (automatic Bartlett bandwidth) on the weekly return **difference**
`r_naive - r_pit`.

## No-look-ahead and backtester reuse

The percentile signal is trailing-only (`min_periods` guards the warm-up), and a weekly
return is earned only by a signal whose entry day precedes that week, so decision information
and the return it earns never overlap. This is enforced by construction in `assemble`.

The verified engine `research_pipeline.backtest.run_backtest` is a cross-sectional,
daily-rebalanced, IC-scored panel engine and does not model a single-asset weekly directional
timing strategy, so this study uses a clean standalone weekly backtest. It **reuses** the
verified primitives: `research_pipeline.data.PricePanel` for point-in-time price access (whose
`as_of` is the runtime witness of the Lean `NonAnticipating` spec) and
`research_pipeline.evaluation.sharpe` / `max_drawdown` for the metrics.

## Result (real data, 2010-2025)

835 weekly COT reports (2010-01-05 to 2025-12-30); USO daily prices 2006-04-10 to 2026-06-26.
The Disaggregated COT report begins in 2010, so the sample starts there even though USO trades
from 2006.

| period    | variant | ann ret  | Sharpe | hit  | IC     | maxDD  | tax (SR) | tax (bps) | NW t |
|-----------|---------|----------|--------|------|--------|--------|----------|-----------|------|
| full      | naive   | -0.53%   | +0.04  | 0.39 | -0.032 | -14.3% | +0.10    | +151      | +0.22|
| full      | pit     | -2.04%   | -0.06  | 0.45 | +0.033 | -20.1% |          |           |      |
| pre-2020  | naive   | -0.30%   | +0.06  | 0.42 | -0.031 | -14.3% | +0.55    | +954      | +1.30|
| pre-2020  | pit     | -9.84%   | -0.49  | 0.40 | -0.060 | -20.1% |          |           |      |
| 2020-2025 | naive   | -0.86%   | +0.02  | 0.34 | -0.047 | -10.0% | -0.93    | -1114     | -0.77|
| 2020-2025 | pit     | +10.28%  | +0.95  | 0.51 | +0.245 | -4.0%  |          |           |      |

Newey-West lag = 3 in every window.

## Verdict

**The release-timing leakage tax is statistically indistinguishable from zero, and there is no
real PIT alpha to tax.** Every window has `|NW t| < 1.96`. More importantly, the PIT strategy
**fails the null** in the full sample (Sharpe -0.06) and pre-2020 (Sharpe -0.49): a contrarian
fade of crowd positioning in WTI, honestly lagged, does not beat a flat book. The one window
where PIT looks good (2020-2025, Sharpe +0.95) is a single COVID-era regime, the tax there is
negative (PIT beats naive), and it is not statistically significant. The positive pre-2020 tax
rides entirely on a strategy that is itself losing money, so it is not a meaningful "alpha lost
to honesty."

This is a valid, publishable null: for a weekly-held COT positioning signal, the 3.5-day
COT release lag is **mechanically small** relative to the noise of weekly crude returns, and
the apparent edge in the naive backtest is not a robust release-timing artifact. The honest
takeaway is that you cannot establish a leakage tax here because there is no honest signal to
begin with.

## Run it

```bash
python3.12 run_study.py        # downloads CFTC + USO, prints the table, writes results JSON
python3.12 -m pytest test_leakage_tax.py -q
```

Downloaded CFTC year files are cached under `data_cache/` (git-ignored). The CFTC data is
free public-domain government data; USO prices come from `yfinance`.
