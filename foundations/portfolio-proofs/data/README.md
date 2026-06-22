# Data

All files in this directory are tracked by DVC, not committed to git.
Run `dvc pull` after cloning to restore them from the MinIO remote.

---

## `french_10ind_daily_vw.parquet`

| Field | Value |
| :---- | :---- |
| Source | Kenneth R. French Data Library |
| Series | 10 Industry Portfolios — Daily, Value-Weighted Returns |
| URL | https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html |
| File fetched | `10_Industry_Portfolios_daily_CSV.zip` |
| Date range | 1926-07-01 to 2026-03-31 |
| Returns | Percent per day, divided by 100 to decimal (e.g. 1.0% → 0.01) |
| Missing code | `-99.99` and `-999` replaced with `NaN` |
| Industries | NoDur, Durbl, Manuf, Enrgy, HiTec, Telcm, Shops, Hlth, Utils, Other |
| License | Public domain (freely distributed by Prof. French) |

### Industry definitions (GICS approximate mapping)

| French label | Approximate sector |
| :----------- | :----------------- |
| NoDur | Consumer Staples |
| Durbl | Consumer Discretionary (durables) |
| Manuf | Industrials + Materials |
| Enrgy | Energy |
| HiTec | Information Technology |
| Telcm | Communication Services |
| Shops | Consumer Discretionary (retail) |
| Hlth | Health Care |
| Utils | Utilities |
| Other | Financials + Real Estate + other |

### Reproducing the download

```python
import pandas as pd, io, zipfile, urllib.request

url = "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/10_Industry_Portfolios_daily_CSV.zip"
with urllib.request.urlopen(url) as r:
    with zipfile.ZipFile(io.BytesIO(r.read())) as z:
        raw = z.read(z.namelist()[0]).decode("latin-1")
# See foundations/portfolio-proofs/scripts/ingest_french_10ind.py for the full parser.
```
