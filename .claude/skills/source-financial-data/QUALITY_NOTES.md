# Data Quality Notes

Critical idiosyncrasies and known issues with each data source. Read this file
before writing any data pipeline that touches these sources.

---

## OptionMetrics (via WRDS)

- **Timestamp:** OptionMetrics prices are recorded at **15:59** Eastern, not 16:00.
  Merging with equity close prices (16:00) creates a 1-minute mismatch. Align by
  date, not timestamp. (Wallmeier 2024 documents this; treat closing prices as
  same-day end-of-day.)

- **Volume:** OptionMetrics volume is often 0 for illiquid strikes even when trades
  occurred. Use open interest changes as a proxy for activity.

- **Implied volatility:** OptionMetrics implied vols (`impl_volatility`) are
  annualized and expressed as decimals (0.25 = 25%). Confirm the convention before
  converting to basis points.

- **Greeks sign conventions:** Delta for puts is negative in OptionMetrics. Check
  `cp_flag` ('C' or 'P') before using raw `delta` in a position-level aggregation.

- **Zero bid/ask:** Some records have `best_bid = 0` and `best_offer = 0` for
  illiquid far out-of-the-money options. Filter these before computing bid/ask
  midpoints — a midpoint of 0 is almost always a data artifact.

---

## WRDS General

- **MFA:** WRDS requires MFA on login. The `wrds` Python library caches a session
  token (~30-day expiry). IP address changes reset the session and trigger MFA
  again. Plan bulk downloads for a single session on a stable connection.

- **Access:** Institutional access required. Data cannot be redistributed.
  Never commit WRDS data to the repository (see `.gitignore` rules in SKILL.md).

- **Query timeout:** Long queries (e.g., full OptionMetrics year) can time out.
  Break queries into quarterly chunks and concatenate results.

- **Column names:** WRDS column names are lowercase in query results but may differ
  from the OptionMetrics documentation (which uses mixed case). Always inspect
  `df.columns` after the first query on a new table.

---

## FRED

- **SP500 gap:** The SP500 series (ticker: `SP500`) has a gap at **2018-01-02** —
  the value is missing. Forward-fill with `max 1 business day` gap to handle it:
  ```python
  sp500 = fred.get_series("SP500").ffill(limit=1)
  ```
  Do not forward-fill with a larger limit — this can mask genuine data issues.

- **Date alignment:** FRED series use end-of-period dating; align carefully with
  daily returns. A monthly FRED series dated `2023-01-31` corresponds to January
  2023; do not merge it with daily data as if it is a January 1 observation.

- **Rate units:** `TB3MS` and `FEDFUNDS` are annualized percentages (e.g., 5.25,
  not 0.0525). Convert before using in return calculations:
  ```python
  rf_daily = tb3ms / 100 / 252   # approximate daily risk-free rate
  ```

- **Revision history:** FRED series are sometimes revised. If reproducibility over
  time is required, snapshot the series at download time with a dated filename.

---

## yfinance

- **Illiquid strikes:** yfinance returns the last trade price for options, which
  may be days old for illiquid strikes. Prefer bid/ask midpoint
  (`(bid + ask) / 2`) for current value. Verify that both `bid > 0` and `ask > 0`
  before computing the midpoint (see OptionMetrics zero bid/ask note above).

- **Adjusted prices:** Always use `.history(auto_adjust=True)` or the `Adj Close`
  column for backtesting; raw `Close` does not account for splits or dividends.
  Using raw `Close` in a backtest will produce incorrect returns around split dates.

- **Rate limiting:** yfinance is not an official API and has no SLA. Requests may
  be throttled or blocked without notice. Do not use yfinance as a primary data
  source for production pipelines; use WRDS or Polygon.io instead.

---

## AQR Data Library

- **File format:** AQR Excel files use a header that spans multiple rows. Load with
  `pd.read_excel(..., skiprows=18)` (the exact number may vary by dataset — always
  inspect the file to confirm before writing the loader).

- **Date format:** Dates are in `YYYYMM` integer format in some files; convert with:
  ```python
  pd.to_datetime(df["date"].astype(str), format="%Y%m")
  ```
  Other AQR files use `YYYY-MM-DD` string format. Check which format a given file
  uses before applying a parser.

- **Factor returns:** AQR factor returns are expressed as decimals (0.01 = 1%), not
  percentages. This differs from the Ken French library convention (which uses
  percentages). Confirm the convention per file before mixing sources.

- **Missing values:** Some AQR files use `#N/A` or blank cells for missing data.
  Pass `na_values=["#N/A", " "]` to `pd.read_excel()`.

---

## Polygon.io

- **Options depth:** Historical options data with full chain depth requires the paid
  Options tier. The free tier only provides current-day snapshots. Attempting to
  query historical data on the free tier returns an empty result set without an
  error — validate that your result is non-empty after each query.

- **Rate limits:** Paid tier: 100 calls/minute for most endpoints. Use exponential
  backoff (see REFERENCE.md). Log retry attempts — silent backoff can make a stuck
  pipeline hard to diagnose.

- **Ticker format for options:** Polygon.io uses the OCC option symbol format:
  `{underlying}{expiry}{cp}{strike}` (e.g., `SPY230120C00400000`). Parse carefully
  when joining with other data sources that use different strike formatting.

- **Adjusted vs. unadjusted:** Polygon.io equity prices include an `adjusted` flag.
  Always use adjusted prices for backtesting. The options data references the
  unadjusted underlying price in the strike; account for this when computing
  moneyness around dividend or split dates.

---

## Volatility / VRP Data

- **VOLARE:** The Oxford-Man Institute's VOLARE dataset (realized volatility) was
  discontinued mid-2022. Do not reference or attempt to download it. Use CBOE's
  official realized volatility product or compute realized volatility from
  5-minute intraday returns directly.

- **VRP computation:** Variance risk premium is conventionally computed as:
  ```
  VRP = implied_vol^2 - realized_vol^2
  ```
  where `implied_vol` comes from VIX (annualized, expressed as a decimal: VIX/100)
  and `realized_vol` is the annualized realized volatility from 21-day rolling
  daily returns:
  ```python
  realized_vol = returns.rolling(21).std() * (252 ** 0.5)
  vrp = (vix / 100) ** 2 - realized_vol ** 2
  ```
  VRP is typically negative (the variance risk premium is a negative expected return
  to variance sellers) — a consistently positive VRP signals a data error.

- **VIX as implied vol:** VIX measures 30-day implied variance of the S&P 500.
  When using VIX to proxy implied vol at other maturities, the term-structure
  mismatch introduces bias. For maturities other than ~30 days, use
  OptionMetrics implied vols directly.
