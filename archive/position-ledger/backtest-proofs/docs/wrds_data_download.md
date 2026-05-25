# WRDS OptionMetrics Data Download

Target: `data/portfolio_all.parquet` (wide window — split automatically)
Tickers: SPY, QQQ, AAPL, MSFT, JPM, IWM
Date range: **2007-01-01 to 2024-12-31** (single portal visit)

---

## Overview

Download one wide date window covering all tickers in **a single portal visit**,
then let `scripts/wrds_csv_to_parquet.py` split it into the required sub-windows
automatically.  This replaces the previous workflow of four separate downloads.

The script produces four output files:

| Output file | Date range | Purpose |
|---|---|---|
| `data/portfolio_atm_options.parquet` | 2019-01-01 to 2024-12-31 | Main backtest |
| `data/stress_gfc_2008.parquet` | 2008-09-01 to 2008-12-31 | GFC stress |
| `data/stress_volm_2018.parquet` | 2017-12-01 to 2018-04-30 | Volmageddon |
| `data/stress_dec2018.parquet` | 2018-10-01 to 2019-01-31 | Q4 2018 selloff |

> **Note:** COVID-2020 is already covered by `portfolio_atm_options.parquet`
> (2019–2024 window).  The August 2015 "flash crash" was an intraday event and
> is invisible in daily OptionMetrics closing prices — it has been replaced by
> the December 2018 Q4 selloff (S&P −20 % peak-to-trough), which is fully
> visible at daily frequency.

---

## Step 1: Log in

Go to **wrds.wharton.upenn.edu** and sign in.

---

## Step 2: Find the secids

1. Left sidebar: **OptionMetrics → Ivy DB US → Security Names**
2. Date range: **2007-01-01 to 2024-12-31**
3. Ticker field: `SPY QQQ AAPL MSFT JPM IWM`
4. Variables: check `secid` and `ticker` (ignore `expire_date` if not available)
5. Submit → download as **CSV**
6. Open the CSV and write down the `secid` for each ticker.
   Each ticker may have a few rows; use the secid that appears most often
   (they are almost certainly all the same value per ticker).

**Tell Akhil / Claude the six secids before running Step 3** so the script
can be verified before the large download.

---

## Step 3: Download option prices

1. Sidebar: **OptionMetrics → Ivy DB US → Option Price**
2. Date range: **2007-01-01 to 2024-12-31**
3. Security ID: paste the six secids from Step 2, one per line
4. Variables: check exactly these eight:
   - `secid`
   - `date`
   - `exdate`
   - `strike_price`
   - `cp_flag`
   - `best_bid`
   - `best_offer`
   - `impl_volatility`
5. Submit → download as **CSV**
   (expect 1–2 GB; this is normal for 6 tickers × 18 years)

---

## Step 3b: Download underlying spot prices

1. Sidebar: **OptionMetrics → Ivy DB US → Security Prices**
2. Date range: **2007-01-01 to 2024-12-31**
3. Security ID: paste the same six secids, one per line
4. Variables: check exactly these three:
   - `secid`
   - `date`
   - `close`
5. Submit → download as **CSV**
   (small file containing only daily closing prices)

---

## Step 4: Save the files

| File                | Save as                  |
|---------------------|--------------------------|
| Security Names CSV  | `~/Downloads/secnmd.csv` |
| Option Price CSV    | `~/Downloads/opprcd.csv` |
| Security Prices CSV | `~/Downloads/secprd.csv` |

---

## Step 5: Convert to parquet (one command, all outputs)

The script `scripts/wrds_csv_to_parquet.py` handles column renaming,
secid→ticker mapping, spot-price join, ATM ±3% filter, 20 to 40 day expiry
filter, and a strike×1000 sanity check.  After building the full joined
parquet, it automatically splits into the four sub-window files.

```bash
cd /path/to/backtest-proofs
uv run python scripts/wrds_csv_to_parquet.py
```

Expected output:

```text
Building secid map ...
Loading security prices ...
Loading and filtering option data ...

Summary by ticker (full window):
underlying_ticker  rows   date_min    date_max    iv_median
AAPL               ~8500  2007-01-03  2024-12-31  ~0.260
IWM                ~7200  2007-01-03  2024-12-31  ~0.200
JPM                ~7800  2007-01-03  2024-12-31  ~0.240
MSFT               ~8200  2007-01-03  2024-12-31  ~0.235
QQQ                ~8800  2007-01-03  2024-12-31  ~0.210
SPY               ~10000  2007-01-03  2024-12-31  ~0.155

Writing sub-window parquets ...

Output files:
  data/portfolio_all.parquet           ~50500 rows  (2007-01-03 to 2024-12-31)
  data/portfolio_atm_options.parquet   ~20000 rows  (2019-01-02 to 2024-12-31)
  data/stress_gfc_2008.parquet          ~1200 rows  (2008-09-01 to 2008-12-31)
  data/stress_volm_2018.parquet         ~2800 rows  (2017-12-01 to 2018-04-30)
  data/stress_dec2018.parquet           ~2400 rows  (2018-10-01 to 2019-01-31)
```

---

## Step 6: Run the real-data tests

```bash
cd python
uv run pytest tests/test_backtest.py -v -k "RealData or Holdout or Stress"
```

These test classes activate automatically once the relevant parquet file exists:

| Test class | Data file | What it checks |
| --- | --- | --- |
| `TestRealDataBacktest` | `portfolio_atm_options.parquet` | cost/premium ~1.0 ±10%, all tickers |
| `TestHoldoutValidation` | `portfolio_atm_options.parquet` | cost/premium ~1.0 ±15% on 2024 holdout |
| `TestStressCovid2020` | `portfolio_atm_options.parquet` | cost/premium > 1.0 during COVID crash |
| `TestStressGFC2008` | `stress_gfc_2008.parquet` | cost/premium > 1.0 during GFC |
| `TestStressVolmageddon2018` | `stress_volm_2018.parquet` | cost/premium in [0.8, 5.0] |
| `TestStressDecember2018` | `stress_dec2018.parquet` | cost/premium > 1.0 during Q4 selloff |

A passing holdout test means the engine generalises across vol regimes
(2020 COVID crash, 2022 bear market, 2023 to 2024 normalization).

---

## Notes

- `strike_price` in OptionMetrics is in dollars. If the script prints
  `NOTE: strike stored x1000 — dividing by 1000`, it divides automatically.
- `secprd.close` is the daily closing price of the underlying, which is the true
  spot price used for delta computation and ATM filtering.
- The parquet schema expected by the engine:
  `underlying_ticker, date, expiry, strike, option_type, best_bid,
   best_offer, impl_volatility, underlying_price`
- `data/portfolio_all.parquet` is the intermediate wide-window file; it is
  gitignored (along with all `*.parquet`) and should never be committed.
