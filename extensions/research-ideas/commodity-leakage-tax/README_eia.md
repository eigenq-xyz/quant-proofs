# Leakage-tax study (data revision): EIA natural-gas storage

Sibling of [`README.md`](README.md). That study (CFTC COT) tested only **release timing**: a
report's snapshot is public with a fixed lag. This study tests the harder, more genuine form of
look-ahead, the one that lives in the **data itself**: the EIA Weekly Natural Gas Storage Report
figure is **revised after its first release**. The number you could actually trade on Thursday
morning is the first-release estimate; the number sitting in today's database is the revised one.
Backtesting off the database snapshot silently leaks the future.

## The strategy

- **Universe / instrument:** Total Lower-48 working-gas storage as the signal, the UNG ETF as
  the tradable (daily adjusted via `yfinance`; `auto_adjust` handles the 2020 1:4 reverse split).
- **Signal:** storage **surprise** = reported weekly change in working gas minus a transparent,
  point-in-time-computable seasonal expectation. The expectation is the trailing same-ISO-week
  average change over the prior 5 years (`seasonal_expectation`), using only weeks strictly
  before the week being scored. No external consensus feed, so nothing fragile to scrape.
- **Rule:** the surprise is standardized by a trailing 104-week z-score (window ending at w-1,
  so it never sees week w) and the position is `-z`, clipped to [-3, 3]. A larger-than-expected
  **build** (positive surprise) is bearish natural gas, so short UNG; a larger-than-expected
  **draw** is bullish, so long UNG. Continuous tilt, weekly holding, UNG open-to-open returns.

## The leakage

Two variants run on **identical code**, differing only in which storage vintage feeds the signal:

- **NAIVE** uses the **final/revised** levels (`ngshistory.xls`, the live database) as if they
  were known at release. Both the reported change and the trailing seasonal expectation are
  computed from the revised series. This is the standard (wrong) way these signals are
  backtested off a snapshot.
- **PIT (point-in-time honest)** uses the **first-release** levels (`revisions.xls`, the original
  estimate published Thursday 10:30am ET) for every week that appears in the revisions file; for
  un-revised weeks first-release equals the database value. Both the change and the expectation
  use only first-release figures.

Crucially, **release timing is held identical** across the two arms: under both, the position
may act only from the first UNG open on/after the Thursday 10:30am ET release (week-ending Friday
+ 6 days). This isolates the pure **data-revision** effect from the release-timing effect the
COT study already covered.

The **leakage tax** is `SR_naive - SR_pit` (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat (automatic Bartlett bandwidth) on the weekly return **difference**
`r_naive - r_pit`.

## Data sources

- **First-release (PIT) levels:** `https://ir.eia.gov/ngs/revisions.xls`, sheet `original_data`.
  Despite the name, this file is a continuous weekly series of the **original** estimate for each
  week ending, with an `Explanation` column flagging the weeks later revised. Free, no key.
- **Revised (naive) levels:** `https://ir.eia.gov/ngs/ngshistory.xls`, sheet
  `html_report_history` (the live EIA database). Free, no key.
- **Price:** UNG daily via `yfinance`. (FRED Henry Hub `DHHNGSP` is available via the project's
  `fredapi` key as a cross-check but is not traded here.)

## No-look-ahead and backtester reuse

The seasonal expectation and the z-score are trailing-only and the z-score window explicitly
ends at w-1, so the signal at week w never sees week w. A weekly return is earned only by a
signal whose entry day starts that week, so decision information and the return never overlap.
Enforced by construction in `build_signal` / `assemble`. As in the COT study, this reuses the
verified `research_pipeline.data.PricePanel` for point-in-time price access (whose `as_of` is the
runtime witness of the Lean `NonAnticipating` spec) and `research_pipeline.evaluation.sharpe` /
`max_drawdown` for the metrics.

## Result (real data, 2015-2026)

565 first-release weeks (2015-06-19 to 2026-04-10); UNG daily 2010-01-04 to 2026-06-26; 405
common trade weeks. **Of the 565 weeks, 69 were later revised**, but the revisions are tiny:
**mean absolute revision 0.90 Bcf, max 14 Bcf**, against weekly storage changes that routinely
run tens to over 100 Bcf.

| period    | variant | ann ret  | Sharpe | hit  | IC     | maxDD   | tax (SR) | tax (bps) | NW t  |
|-----------|---------|----------|--------|------|--------|---------|----------|-----------|-------|
| full      | naive   | -40.1%   | -0.13  | 0.52 | +0.029 | -98.9%  | +0.00    | -10       | +0.15 |
| full      | pit     | -40.0%   | -0.13  | 0.49 | +0.027 | -98.8%  |          |           |       |
| 2015-2020 | naive   | -15.4%   | -0.07  | 0.50 | +0.016 | -42.7%  | +0.13    | +1262     | +0.71 |
| 2015-2020 | pit     | -28.0%   | -0.20  | 0.42 | +0.029 | -53.6%  |          |           |       |
| 2020-2026 | naive   | -44.8%   | -0.14  | 0.52 | +0.032 | -98.7%  | -0.02    | -229      | -1.04 |
| 2020-2026 | pit     | -42.5%   | -0.12  | 0.51 | +0.039 | -98.3%  |          |           |       |

Newey-West lag = 4 in every window.

## Verdict

**The data-revision leakage tax is statistically zero, and there is no honest signal to tax.**
The full-sample tax is `+0.00` Sharpe / `-10` bps with NW t = +0.15: completely indistinguishable
from zero, and in fact slightly negative in bps. More fundamentally, the PIT strategy **fails the
flat-book null**: its Sharpe is -0.13 over the full sample and negative in every sub-period. A
seasonal-surprise contrarian fade of EIA storage, honestly lagged, loses money relative to
holding cash, so there is no real edge that honesty could be eroding.

This is exactly the result the mechanics predict. EIA storage revisions are **small and rare**
(mean 0.90 Bcf, 12% of weeks), so the difference between trading the first-release figure and the
final figure is negligible relative to the noise in weekly UNG returns. Unlike a release-timing
lag (which moves the *entry day*), a small level revision barely moves the *standardized
surprise* at all. The 2015-2020 sub-period shows a superficially large `+1262` bps tax, but it
rides entirely on a PIT strategy that is itself losing 28% a year, so it is not "alpha lost to
honesty", just two different ways of losing money, and it is not statistically significant
(NW t = +0.71).

**A small/zero tax is a valid result, and it is the honest one here.** The thesis test, can
ignoring data revision manufacture fake alpha, comes back negative for EIA gas storage: the
revisions are too small to matter, and the underlying signal has no edge to inflate.

### Scope limitation

The revisions file begins November 2015 (that is when EIA started publishing its revision
history), so the honest first-release series exists only from week-ending 2015-06-19. Weeks
before that cannot be made point-in-time from this source, so the study is confined to ~2015-2026.

## Run it

```bash
python3.12 run_study_eia.py          # downloads EIA + UNG, prints the table, writes results JSON
python3.12 -m pytest test_leakage_tax_eia.py -q
```

The load-bearing test (`test_pit_uses_first_release_not_revised`) plants a known +50 Bcf revision
and asserts the PIT signal uses the first-release change while the NAIVE signal uses the revised
change. Downloaded EIA workbooks and UNG prices are cached under `data_cache/` (git-ignored). EIA
data is free public-domain government data; UNG prices come from `yfinance`.
