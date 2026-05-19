---
name: sourcing-financial-data
description: >
  Source hierarchy, licensing rules, and key decisions for financial data used in
  quant-proofs. Use when adding a new data dependency, writing a download script,
  or reviewing a data pipeline for compliance and quality.
paths:
  - "**/scripts/download_*.py"
  - "**/data/**"
  - "**/*.gitignore"
---

# Sourcing Financial Data — quant-proofs

See REFERENCE.md for per-source details (URL patterns, file formats, Python library
usage, API key setup). See QUALITY_NOTES.md for data quality idiosyncrasies — read
that file before merging any data pipeline change.

---

## Source hierarchy

Use sources in this order of preference. Move down the list only when the higher
source cannot satisfy the requirement.

| Priority | Category | Examples |
|----------|----------|---------|
| 1 | Public / free academic | AQR library, Ken French data library, FRED, CBOE |
| 2 | Institutional (requires login) | WRDS: OptionMetrics, CRSP, Compustat |
| 3 | Paid commercial | Polygon.io, Bloomberg |

**Decision rule:** if a free academic source covers your time range and resolution,
use it. Do not reach for WRDS or Polygon.io for something you can get from French
or FRED — institutional licenses are shared resources.

---

## Licensing rules

**Never commit licensed data to the repository.** This is a hard rule with no exceptions.

Licensed data includes:
- OptionMetrics (WRDS)
- CRSP stock prices (WRDS)
- Compustat fundamentals (WRDS)
- Polygon.io historical data (paid tier)
- Bloomberg extracts

Freely distributable data (OK to commit in small amounts for test fixtures):
- AQR dataset files, if the AQR license permits redistribution (check per-file)
- Ken French factor returns
- FRED series (public domain)
- CBOE VIX history (public)

When in doubt, do not commit. Use a download script and add the data path to
`.gitignore`.

---

## gitignore patterns for data directories

Add these patterns to the `.gitignore` at the root of each subproject:

```gitignore
# Data directories — never commit raw or licensed data
data/raw/
data/processed/
data/cache/
*.parquet
*.h5
*.feather

# Keep download scripts and schema files
!data/schemas/
!scripts/download_*.py
```

For test fixtures using small public-domain data samples, place them under
`tests/fixtures/` and explicitly allowlist in `.gitignore`:
```gitignore
!tests/fixtures/*.csv
```

---

## Free academic sources

### AQR Data Library (aqr.com/Insights/Datasets)

Available datasets include: quality-minus-junk (QMJ), betting-against-beta (BAB),
time series momentum (TSMOM), value and momentum everywhere.

Key loading quirk: AQR Excel files use a multi-row header. Always inspect a new
file before writing a loader. The standard is `skiprows=18`, but this varies.
See QUALITY_NOTES.md for date format details.

Download script: `scripts/download_aqr.py`

### Ken French Data Library (mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html)

Primary use: Fama-French factor returns (3-factor, 5-factor), industry portfolios.
Available as zip archives containing CSVs.

Download script: `scripts/download_french.py`

### FRED (Federal Reserve Bank of St. Louis)

Use the `fredapi` Python library. Key series:
- `SP500` — S&P 500 level (has a gap at 2018-01-02; see QUALITY_NOTES.md)
- `VIXCLS` — CBOE VIX closing level
- `TB3MS` — 3-Month Treasury Bill (risk-free proxy)
- `DGS10` — 10-Year Treasury yield

### CBOE

VIX history: available as CSV download from CBOE website.
Historical options data: limited free availability; full chains require institutional access.

---

## Institutional sources (WRDS)

Requires an active institutional login. Do not hardcode credentials; use the
`wrds` library's built-in credential management, which stores a session token.

Key databases:
- **OptionMetrics** — standardized options prices, implied vols, greeks. Primary
  source for options backtesting. See QUALITY_NOTES.md for the 15:59 timestamp issue.
- **CRSP** — stock prices and returns, adjusted for splits/dividends. The authoritative
  source for US equity prices in academic research.
- **Compustat** — company fundamentals (earnings, book value, etc.) for factor construction.

WRDS requires MFA. See QUALITY_NOTES.md for session caching behavior.

---

## Paid commercial sources

### Polygon.io

Historical options data with full chain depth requires the paid Options tier.
Use for high-frequency or recent options data not available through WRDS.
Rate limits on the paid tier: 100 calls/minute for most endpoints. Implement
exponential backoff in all Polygon.io clients.

API key: stored in environment variable `POLYGON_API_KEY`. Never hardcode.

---

## Key decisions summary

| Situation | Source to use |
|-----------|---------------|
| Fama-French factors | Ken French library |
| VIX level (daily) | FRED (VIXCLS) |
| Risk-free rate | FRED (TB3MS) |
| S&P 500 index level | FRED (SP500) — mind the 2018-01-02 gap |
| Options prices for backtesting | OptionMetrics via WRDS |
| Equity prices for backtesting | CRSP via WRDS |
| Real-time / recent options chains | Polygon.io (paid) |
| Alternative factor data | AQR library |
