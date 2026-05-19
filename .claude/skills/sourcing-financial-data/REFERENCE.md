# Financial Data Reference — quant-proofs

Per-source details: URL patterns, file formats, Python library usage, API setup,
and download script conventions.

---

## AQR Data Library

**Base URL:** `https://www.aqr.com/Insights/Datasets`

AQR datasets are delivered as Excel (`.xlsx`) files, with a preamble section before
the actual data. The data rows begin at a row that varies by file — always inspect
a new file manually before writing the loader.

Standard loader pattern:
```python
import pandas as pd

def load_aqr_dataset(path: str, skiprows: int = 18) -> pd.DataFrame:
    """Load an AQR Excel dataset, skipping the preamble rows.

    Args:
        path: Local path to the downloaded .xlsx file.
        skiprows: Number of rows to skip (inspect the file to confirm).

    Returns:
        DataFrame with the factor data, index as datetime.
    """
    df = pd.read_excel(path, skiprows=skiprows, index_col=0)
    # AQR dates are often in YYYYMM integer format
    df.index = pd.to_datetime(df.index.astype(str), format="%Y%m")
    return df
```

Download script: `scripts/download_aqr.py`
- Prompts for the dataset name
- Downloads to `data/raw/aqr/<dataset_name>.xlsx`
- Logs the skiprows used

---

## Ken French Data Library

**Base URL:** `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/`

Datasets are `.zip` archives containing one or more CSV files. The CSVs have a
header section separated from the data by an empty line.

Standard loader using `pandas_datareader`:
```python
import pandas_datareader.data as web
import datetime

def load_french_factors(name: str = "F-F_Research_Data_5_Factors_2x3") -> pd.DataFrame:
    """Download and return Fama-French factors via pandas_datareader.

    Args:
        name: Dataset name as used by pandas_datareader (see FRED/FF library keys).

    Returns:
        Monthly factor returns (Mkt-RF, SMB, HML, RMW, CMA, RF) as percentages.
    """
    factors, _ = web.DataReader(
        name, "famafrench", start="1963-01-01"
    )
    return factors
```

Manual download (for full control):
```python
import zipfile, io, requests

URL = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/{name}_CSV.zip"

def download_french_zip(name: str) -> pd.DataFrame:
    resp = requests.get(URL.format(name=name), timeout=30)
    resp.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
        csv_name = next(n for n in zf.namelist() if n.endswith(".CSV"))
        with zf.open(csv_name) as f:
            # Skip the header description lines
            raw = f.read().decode("utf-8")
    # The data starts after the first blank line
    data_section = raw.split("\r\n\r\n")[1].split("\r\n\r\n")[0]
    return pd.read_csv(io.StringIO(data_section), index_col=0)
```

Download script: `scripts/download_french.py`

---

## FRED (St. Louis Fed)

**Library:** `fredapi` (`uv add fredapi`)
**API key:** stored in environment variable `FRED_API_KEY`. Register at
`https://fred.stlouisfed.org/docs/api/api_key.html` (free).

```python
import os
from fredapi import Fred

def get_fred_series(series_id: str, start: str, end: str) -> pd.Series:
    """Fetch a FRED time series.

    Args:
        series_id: FRED series identifier (e.g., "VIXCLS", "SP500", "TB3MS").
        start: Start date as YYYY-MM-DD string.
        end: End date as YYYY-MM-DD string.

    Returns:
        pandas Series indexed by date.
    """
    fred = Fred(api_key=os.environ["FRED_API_KEY"])
    return fred.get_series(series_id, observation_start=start, observation_end=end)
```

Key series codes:

| Series ID | Description | Frequency |
|-----------|-------------|-----------|
| `SP500` | S&P 500 level | Daily (note 2018-01-02 gap) |
| `VIXCLS` | CBOE VIX closing level | Daily |
| `TB3MS` | 3-Month T-Bill secondary market rate | Monthly |
| `DGS10` | 10-Year Treasury constant maturity | Daily |
| `FEDFUNDS` | Federal funds effective rate | Monthly |
| `CPIAUCSL` | CPI (all urban consumers) | Monthly |

FRED series use end-of-period dating. For daily series, each observation is the
value on that calendar date. Align with equity return data by merging on date
(not timestamp).

---

## CBOE

**VIX history:** `https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv`

Direct download — no authentication required.

```python
import pandas as pd

VIX_URL = "https://cdn.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv"

def load_vix_history() -> pd.DataFrame:
    """Download CBOE VIX history (open, high, low, close)."""
    df = pd.read_csv(VIX_URL, parse_dates=["DATE"], index_col="DATE")
    df.columns = [c.lower() for c in df.columns]
    return df
```

---

## WRDS

**Library:** `wrds` (`uv add wrds`)
**Credentials:** managed by the `wrds` library; stored in `~/.pgpass` after first login.

Login flow:
```python
import wrds

db = wrds.Connection()
# First call opens browser for MFA. Subsequent calls (same IP, <30 days) use cached token.
```

Session caching: the `wrds` library caches a PostgreSQL session token. If your IP
address changes (e.g., switching networks), the session is invalidated and MFA is
required again. Plan bulk downloads for a single session on a stable connection.

OptionMetrics query pattern:
```python
# Get standardized options for SPX on a given date
query = """
    SELECT secid, date, cp_flag, strike_price, best_bid, best_offer,
           impl_volatility, delta, gamma, vega, theta, open_interest, volume
    FROM optionm.opprcd{year}
    WHERE secid = 108105        -- SPX
      AND date BETWEEN '{start}' AND '{end}'
"""
df = db.raw_sql(query.format(year=2023, start="2023-01-01", end="2023-12-31"))
```

Note: OptionMetrics uses `secid` not ticker. SPX secid is `108105`; retrieve the
mapping via `optionm.securd`.

CRSP query pattern:
```python
# Daily stock returns
query = """
    SELECT permno, date, ret, retx, prc, shrout, cfacpr
    FROM crsp.dsf
    WHERE date BETWEEN '{start}' AND '{end}'
      AND permno IN ({permnos})
"""
```

---

## Polygon.io

**API key:** stored in environment variable `POLYGON_API_KEY`.
**Documentation:** `https://polygon.io/docs/options`

```python
import os
import time
import requests

BASE_URL = "https://api.polygon.io/v3"


def get_options_chain(
    underlying: str,
    date: str,
    *,
    max_retries: int = 5,
) -> list[dict[str, object]]:
    """Fetch the options chain for an underlying on a given date.

    Requires the paid Options tier for historical data.

    Args:
        underlying: Ticker symbol (e.g., "SPY").
        date: Date as YYYY-MM-DD string.
        max_retries: Number of retries with exponential backoff.

    Returns:
        List of option contract dicts from the Polygon API.
    """
    url = f"{BASE_URL}/snapshot/options/{underlying}"
    params = {"as_of": date, "apiKey": os.environ["POLYGON_API_KEY"]}
    delay = 1.0
    for attempt in range(max_retries):
        resp = requests.get(url, params=params, timeout=30)
        if resp.status_code == 429:
            time.sleep(delay)
            delay *= 2
            continue
        resp.raise_for_status()
        return resp.json().get("results", [])
    raise RuntimeError(f"Polygon.io rate limit exceeded after {max_retries} retries")
```

Rate limits (paid tier): 100 calls/minute for most endpoints. Use exponential backoff
as shown. Free tier: current-day snapshots only; no historical data.

---

## Download script conventions

All download scripts live in `scripts/` and follow these conventions:

1. Accept `--start` and `--end` date arguments.
2. Write output to `data/raw/<source>/` by default; accept `--output-dir` override.
3. Log what was downloaded and where.
4. Exit with code 1 on failure; do not silently continue.
5. Never overwrite existing files without `--force` flag.

Script naming: `scripts/download_<source>.py`
Examples: `download_aqr.py`, `download_french.py`, `download_fred.py`,
`download_polygon.py`, `download_wrds_optionmetrics.py`
