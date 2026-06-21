# WRDS data request — research-pipeline

A precise, copy-pasteable spec for a **Day Pass Web** session on WRDS (manual query forms,
CSV download, no programmatic `wrds` connection). Take this to the session and execute it
without guessing.

---

## 0. Verdict first: do we actually need WRDS?

**No — not for the critical path.** The headline study runs entirely on **free** data:

- **Cross-sectional momentum** on the Ken French portfolio cross-section (49 industries, or the
  25/100 size-B/M portfolios) — each portfolio is treated as an asset, ranked by 12-1 momentum.
  The Ken French loader (`data_sources.load_ken_french_factors`) already fetches these directly
  from Dartmouth, no credentials.
- **Factor attribution** against Mkt-RF / SMB / HML / RMW / CMA / Mom — free Ken French factors.
- **Cross-asset breadth** — AQR's free "Value and Momentum Everywhere" / "Time Series Momentum"
  datasets (equities, bonds, currencies, commodities).

So we can produce honest IC, IC decay, decile monotonicity, net-of-cost Sharpe, deflated Sharpe,
and a cross-asset table **today**, with zero licensed data. This matches the ROADMAP's explicit
guardrail: *do not block the study on WRDS/CRSP creds.*

**What WRDS *upgrades* (optional, strictly nice-to-have):**

| Capability | Free (Ken French) | With CRSP individual stocks |
|---|---|---|
| Cross-section breadth | ~49–100 portfolios | ~1,000–3,000 single names |
| Rank IC | across portfolios | across individual stocks (the real QR metric) |
| Decile-spread monotonicity | coarse (few buckets) | genuine deciles of single names |
| Transaction costs / turnover | proxied | realistic per-name turnover; capacity in $ |
| Survivorship bias | not an issue (portfolios) | must be handled (delisting returns) |
| Verified **daily** backtester on real data | French daily portfolios work | real single-stock daily prices |

If you want the study to read "cross-sectional momentum on the US single-stock universe" rather
than "on industry/size portfolios," that is the only reason to pull CRSP. Both are defensible; the
portfolio version is faster and fully free.

---

## 1. Day Pass Web constraints (read before querying)

- **No `wrds` Python connection.** You download CSVs by hand from the web query forms; we then
  point the loader at the local file. Nothing licensed is ever committed (the loaders write only
  under `research-pipeline/data/`, which is gitignored).
- **Download size matters.** The CRSP *daily* file for the whole universe over 20 years is tens of
  millions of rows — do **not** pull "entire database, daily." Scope every daily pull by universe
  **and** period. The *monthly* file for the whole universe is ~3–4M rows and is fine as gzipped CSV.
- **Use gzip output.** Each web query form has an output-format step; choose `*.csv` with gzip
  compression to keep the download tractable.
- **One pass.** A day pass is time-boxed; pull everything below in a single session.

---

## 2. PULL #1 (recommended) — CRSP Monthly Stock File: the cross-sectional momentum universe

Monthly is the canonical frequency for 12-1 cross-sectional momentum (Jegadeesh-Titman / Carhart):
form on the last 12 months skipping the most recent, rebalance monthly. This is the primary pull.

**Navigate:** `Get Data → CRSP → Annual Update → Stock / Security Files → Monthly Stock File`

**Step 1 — Date range:** `2000-01` to the latest available (e.g. `2024-12`).
(Pre-2000 is fine too if you want a longer sample; 2000+ keeps the file smaller and the costs/liquidity regime modern.)

**Step 2 — Search / universe:** entire database (we filter by share/exchange code in Step 4).

**Step 3 — Variables (check exactly these):**

| Variable | Why we need it |
|---|---|
| `PERMNO` | permanent security id — the cross-section key |
| `date` | observation month-end |
| `RET` | **holding-period return, dividends included** — the clean total return; use this, not price math |
| `PRC` | price (for a price filter / sanity; can be negative = bid/ask average, take abs) |
| `SHROUT` | shares outstanding → market cap for universe screen / value-weighting |
| `VOL` | volume → liquidity screen |
| `SHRCD` | share code — filter to common stock |
| `EXCHCD` | exchange code — filter to major exchanges |
| `CFACPR` | price adjustment factor (only needed if you reconstruct prices; RET makes this optional) |

**Step 4 — Conditional statements (universe filter — this is the survivorship/quality screen):**

```
SHRCD in (10, 11)        # US common stock only (drop ADRs, REITs, closed-end funds, etc.)
EXCHCD in (1, 2, 3)      # NYSE, AMEX, NASDAQ
```

**Step 5 — Output:** CSV, gzip, date format `YYYY-MM-DD`.

**Save as:** `research-pipeline/data/crsp_msf_2000_2024.csv.gz`

---

## 3. PULL #2 (required if you pull #1) — CRSP Monthly Delisting Returns: survivorship-bias honesty

Without delisting returns, dead stocks silently vanish and momentum looks better than it is. This
is the single most important honesty control for a single-stock study.

**Navigate:** `Get Data → CRSP → Annual Update → Stock / Security Files → Monthly Stock File - CRSP Delisting`
(a.k.a. `msedelist`)

**Step 1 — Date range:** same as Pull #1 (`2000-01` to `2024-12`).

**Step 3 — Variables:** `PERMNO`, `DLSTDT` (delisting date), `DLRET` (delisting return), `DLSTCD` (delisting code).

**Output:** CSV, gzip. **Save as:** `research-pipeline/data/crsp_delist_2000_2024.csv.gz`

We merge `DLRET` into `RET` on the delisting month so a name that goes to zero is counted as a loss,
not a missing row.

---

## 4. PULL #3 (optional) — CRSP Daily, constrained: run the *verified* daily backtester on real single-stock data

Only if you want the no-look-ahead daily backtester to run on real individual stocks (rather than
French daily portfolios). **Constrain hard** or the download is unmanageable.

**Navigate:** `Get Data → CRSP → Annual Update → Stock / Security Files → Daily Stock File`

**Step 1 — Date range:** a single recent window, e.g. `2018-01-01` to `2023-12-31` (6 years).

**Step 2 — Universe:** **do not use entire database.** Either:
- paste a fixed list of ~100–500 PERMNOs (a liquid large-cap set), **or**
- restrict by the same `SHRCD in (10,11)` / `EXCHCD in (1,2,3)` filter and accept a large file.
Recommended: a fixed liquid universe (e.g. current S&P 500 PERMNOs) over 6 years — a few hundred MB gzipped.

**Step 3 — Variables:** `PERMNO`, `date`, `RET`, `PRC`, `CFACPR`, `VOL`, `BID`, `ASK`
(`BID`/`ASK` let us build a realistic spread-based cost model instead of a flat bps proxy).

**Output:** CSV, gzip. **Save as:** `research-pipeline/data/crsp_dsf_sp500_2018_2023.csv.gz`

---

## 5. PULL #4 (skip unless going multi-factor) — Compustat fundamentals

Only needed if we add a *value* or *quality* signal as a second alpha (a stretch goal). For pure
momentum, **skip this.** If pursued: `Get Data → Compustat → CRSP/Compustat Merged → Fundamentals Annual`,
variables `GVKEY, LPERMNO, datadate, at, ceq, ni, sale`, linked via CCM linktable. Out of scope for
the momentum study.

---

## 6. How the files map to the code (and one alignment note)

The current loader `data_sources.load_crsp_daily` (research-pipeline/src/research_pipeline/data_sources.py)
expects either a live `wrds` connection or a `local_parquet` of **prices** and reconstructs
`adj_price = abs(PRC)/CFACPR`. Two things to know:

1. **Point it at the local file**, e.g. `load_crsp_daily(local_parquet="data/crsp_dsf_...parquet")`.
   Convert the downloaded `.csv.gz` to parquet once (`pd.read_csv(...).to_parquet(...)`).
2. **`prc/cfacpr` is split-adjusted but NOT dividend-adjusted** — it understates total return and
   therefore momentum. For a rigorous study we should consume **`RET`** (which includes dividends)
   directly. This is a small loader change I will make when wiring the real study: add a
   `load_crsp_returns(local_csv)` path that pivots `RET` to a returns panel and merges `DLRET`,
   rather than going through prices. The variable list above already includes `RET` and the
   delisting file so the data is ready for that path.

A short converter script (`scripts/ingest_crsp.py`) will: read the gzipped CSV, apply the screens,
merge delisting returns, pivot to a (date × PERMNO) returns panel, and write a gitignored parquet.
I will add it alongside the loader change.

---

## 7. One-session checklist

- [ ] Pull #1 — Monthly Stock File, 2000–2024, `SHRCD∈{10,11}`, `EXCHCD∈{1,2,3}`, vars per §2, gzip CSV
- [ ] Pull #2 — Monthly Delisting, same dates, vars per §3, gzip CSV
- [ ] (optional) Pull #3 — Daily, constrained universe + 6-yr window, vars per §4, gzip CSV
- [ ] Drop all files under `research-pipeline/data/` (gitignored — confirm with `git status` that they do NOT appear)
- [ ] Tell me the filenames; I wire the ingest + run the single-stock study

Until then, the free-data study proceeds and produces the headline numbers.
