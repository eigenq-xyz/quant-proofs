# WRDS OptionMetrics Data Download

Target: `data/portfolio_atm_options.parquet`
Tickers: SPY, QQQ, AAPL, MSFT, JPM
Date range: 2019-01-01 to 2024-12-31

---

## Step 1: Log in

Go to **wrds.wharton.upenn.edu** and sign in.

---

## Step 2: Find the secids

1. Left sidebar: **OptionMetrics → Ivy DB US → Security Names**
2. Date range: 2019-01-01 to 2024-12-31
3. Ticker field: `SPY QQQ AAPL MSFT JPM`
4. Variables: check `secid` and `ticker` (ignore `expire_date` if not available)
5. Submit → download as **CSV**
6. Open the CSV and write down the `secid` for each ticker.
   Each ticker may have a few rows; use the secid that appears most often
   (they are almost certainly all the same value per ticker).

**Tell Akhil / Claude the five secids before running Step 3** so the script
can be verified before the large download.

---

## Step 3: Download option prices

1. Sidebar: **OptionMetrics → Ivy DB US → Option Price**
2. Date range: **2019-01-01 to 2024-12-31**
3. Security ID: paste the five secids from Step 2, one per line
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
   (expect several hundred MB; this is normal for 5 tickers × 6 years)

---

## Step 3b: Download underlying spot prices

1. Sidebar: **OptionMetrics → Ivy DB US → Security Prices**
2. Date range: **2019-01-01 to 2024-12-31**
3. Security ID: paste the same five secids, one per line
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

## Step 5: Convert to parquet

The script `scripts/wrds_csv_to_parquet.py` handles column renaming,
secid→ticker mapping, spot-price join, ATM ±3% filter, 20 to 40 day expiry
filter, and a strike×1000 sanity check.

```bash
cd /path/to/backtest-proofs
uv run python scripts/wrds_csv_to_parquet.py
```

Expected output:

```text
underlying_ticker  rows   date_min    date_max    iv_median
AAPL               ~3200  2019-01-02  2024-12-31  ~0.248
JPM                ~2900  2019-01-02  2024-12-31  ~0.218
MSFT               ~3100  2019-01-02  2024-12-31  ~0.225
QQQ                ~3300  2019-01-02  2024-12-31  ~0.195
SPY                ~3800  2019-01-02  2024-12-31  ~0.141
```

Output file: `data/portfolio_atm_options.parquet`

---

## Step 6: Run the real-data tests

```bash
cd python
uv run pytest tests/test_backtest.py -v -k "RealData or Holdout"
```

These two test classes activate automatically once the parquet file exists:

| Test class | What it checks |
| --- | --- |
| `TestRealDataBacktest` | cost/premium ~1.0 +/-10%, all tickers, in-sample sigma |
| `TestHoldoutValidation` | cost/premium ~1.0 +/-15% on 2024, sigma from 2019-2023 |

A passing holdout test means the engine generalises across vol regimes
(2020 COVID crash, 2022 bear market, 2023 to 2024 normalization).

---

## Stress regime downloads

Three historical stress windows fall outside the 2019–2024 range of
`portfolio_atm_options.parquet` and require separate downloads.  Follow
Steps 1–5 above for each, using the date ranges and output filenames below.
The COVID 2020 window is already covered by the main parquet file.

| Period | Date range | Output file |
|---|---|---|
| Sep–Nov 2008 GFC | 2008-09-01 to 2008-12-31 | `data/stress_gfc_2008.parquet` |
| Jan–Feb 2018 Volmageddon | 2017-12-01 to 2018-04-30 | `data/stress_volm_2018.parquet` |
| Aug 2015 flash crash | 2015-07-01 to 2015-10-31 | `data/stress_flash_2015.parquet` |

Use the same five tickers (SPY, QQQ, AAPL, MSFT, JPM) and the same eight
variables as the main download.  Pass the output filename to
`scripts/wrds_csv_to_parquet.py` via `--output`:

```bash
uv run python scripts/wrds_csv_to_parquet.py \
    --options ~/Downloads/opprcd_gfc.csv \
    --spots  ~/Downloads/secprd_gfc.csv \
    --output data/stress_gfc_2008.parquet
```

Once each file is present, `TestStressGFC2008`, `TestStressVolmageddon2018`,
and `TestStressFlashCrash2015` activate automatically.

---

## Notes

- `strike_price` in OptionMetrics is in dollars. If the script prints
  `WARNING: strike appears to be stored × 1000`, it divides automatically.
- `secprd.close` is the daily closing price of the underlying, which is the true
  spot price used for delta computation and ATM filtering.
- The parquet schema expected by the engine:
  `underlying_ticker, date, expiry, strike, option_type, best_bid,
   best_offer, impl_volatility, underlying_price`
