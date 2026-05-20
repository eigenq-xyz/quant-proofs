"""Download SPX stress-regime option panels from WRDS OptionMetrics IvyDB.

Produces three parquets in ``data/`` matching the schema expected by
``run_stress_window`` (backtest_proofs.backtest.stress).

The COVID-2020 window (Feb 19 – Mar 23, 2020) is already covered by
``data/portfolio_atm_options.parquet`` (the main multi-ticker dataset) and is
not re-downloaded here.  The three new files are:

  data/stress_gfc_2008.parquet       — GFC-2008 (Sep 15 – Nov 21, 2008)
  data/stress_volm_2018.parquet      — Volmageddon-2018 (Jan 22 – Feb 16, 2018)
  data/stress_flash_2015.parquet     — Flash Crash-2015 (Aug 17 – Aug 28, 2015)

These three plus the existing ``portfolio_atm_options.parquet`` satisfy the
``WRDS_PRESENT`` gate in ``reports/backtest-proofs.qmd``.

Prerequisites
-------------
- WRDS institutional subscription with OptionMetrics access.
- ``wrds`` Python package installed (``uv sync --group research`` includes it,
  or ``pip install wrds``).
- WRDS credentials stored in ~/.pgpass or supplied interactively on first run.

Usage
-----
From the backtest-proofs directory:

    uv run python scripts/download_stress_windows.py

Each parquet is saved to data/<name>.parquet.  These files are .gitignored
and must never be committed — they contain licensed OptionMetrics data.

Output schema (columns saved to parquet)
-----------------------------------------
underlying_ticker : str    "SPX"
date              : str    "YYYY-MM-DD"
expiry            : str    "YYYY-MM-DD"
strike            : float  dollars (OM stores strike*1000 as int; divided here)
option_type       : str    "call" or "put"
best_bid          : float  dollars
best_offer        : float  dollars
impl_volatility   : float  fraction (e.g. 0.80 for 80%)
underlying_price  : float  dollars (spotprice from opprcd at 15:59 ET)
delta             : float  Black-Scholes delta from OM
volume            : int    contracts traded
open_interest     : int    open interest
optionid          : int    OM permanent option ID

Data quality notes
------------------
- GFC-2008: ~20-40% of would-be ATM rows are dropped on peak-stress days
  (Oct 6-10 2008) due to best_bid=0 filter.  End-of-day snapshots only.
- Volmageddon-2018: end-of-day (15:59 ET) snapshot.  The intraday Feb 5 VIX
  peak (~50) is not captured; closing-day IV (~37) is.
- Flash Crash-2015: Aug 24 end-of-day snapshot reflects recovery.  Intraday
  opening-session quote gaps are not visible in end-of-day data.
- COVID-2020 (already downloaded as portfolio_atm_options.parquet, but
  re-downloadable here): Wallmeier (2024) documents a 15:59 vs 16:00
  timestamp mismatch that inflates apparent IV spreads.  Disclosed in paper.

Reference: Wallmeier (2024), J. Futures Markets, doi:10.1002/fut.22495
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_DATA = Path(__file__).parent.parent / "data"


@dataclass(frozen=True)
class _StressWindow:
    name: str  # output filename stem, e.g. "stress_gfc_2008"
    label: str  # human-readable label
    start_date: str
    end_date: str
    min_dte: int = 14
    max_dte: int = 90
    moneyness_lo: float = 0.95
    moneyness_hi: float = 1.05


# COVID-2020 is covered by portfolio_atm_options.parquet — not re-downloaded.
_WINDOWS: list[_StressWindow] = [
    _StressWindow(
        name="stress_gfc_2008",
        label="GFC-2008",
        start_date="2008-09-15",
        end_date="2008-11-21",
    ),
    _StressWindow(
        name="stress_volm_2018",
        label="Volmageddon-2018",
        start_date="2018-01-22",
        end_date="2018-02-16",
    ),
    _StressWindow(
        name="stress_flash_2015",
        label="FlashCrash-2015",
        start_date="2015-08-17",
        end_date="2015-08-28",
    ),
]


def resolve_spx_secid(db: object) -> int:  # type: ignore[type-arg]
    """Return the OptionMetrics secid for the S&P 500 index (SPX).

    Verifies at runtime that exactly one secid resolves.  Never hardcode.
    """
    spx_meta = db.raw_sql(  # type: ignore[union-attr]
        """
        SELECT secid, ticker, issuer
        FROM optionm.secnmd
        WHERE ticker = 'SPX'
        """
    )
    if len(spx_meta) != 1:
        raise RuntimeError(
            f"Expected 1 SPX secid, got {len(spx_meta)} rows:\n{spx_meta}"
        )
    secid = int(spx_meta.iloc[0]["secid"])
    print(f"Resolved SPX secid: {secid}  (issuer: {spx_meta.iloc[0]['issuer']})")
    return secid


def pull_window(
    db: object,  # type: ignore[type-arg]
    secid: int,
    window: _StressWindow,
) -> pd.DataFrame:
    """Pull ATM SPX call options from opprcd for one stress window.

    Filters applied at query time:
      - calls only (cp_flag = 'C')
      - DTE between min_dte and max_dte
      - moneyness between moneyness_lo and moneyness_hi
      - positive best_bid
      - impl_volatility between 0.05 and 2.0

    Strike encoding: opprcd stores strike_price as integer strike × 1000
    (e.g. $1,500 strike → 1,500,000).  Divided by 1000.0 in this query.
    """
    sql = f"""
        SELECT
            o.secid,
            o.date,
            o.exdate                     AS expiry,
            o.cp_flag,
            o.strike_price / 1000.0      AS strike,
            o.best_bid,
            o.best_offer,
            o.impl_volatility,
            o.delta,
            o.volume,
            o.open_interest,
            o.optionid,
            o.spotprice                  AS underlying_price
        FROM optionm.opprcd AS o
        WHERE o.secid        = {secid}
          AND o.date         BETWEEN '{window.start_date}' AND '{window.end_date}'
          AND o.cp_flag      = 'C'
          AND o.exdate - o.date BETWEEN {window.min_dte} AND {window.max_dte}
          AND o.best_bid     > 0
          AND o.impl_volatility BETWEEN 0.05 AND 2.0
          AND (o.strike_price / 1000.0)
              BETWEEN (o.spotprice * {window.moneyness_lo})
                  AND (o.spotprice * {window.moneyness_hi})
        ORDER BY o.date, o.exdate, o.strike_price
    """
    df: pd.DataFrame = db.raw_sql(sql, date_cols=["date", "expiry"])  # type: ignore[union-attr]
    return df


def _to_engine_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Rename/recode raw query output to the schema run_stress_window expects."""
    df = df.copy()

    # underlying_ticker: SPX index has no ticker column in opprcd
    df["underlying_ticker"] = "SPX"

    # option_type: "C" → "call"
    df["option_type"] = df["cp_flag"].str.upper().map({"C": "call", "P": "put"})
    df = df.drop(columns=["cp_flag", "secid"])

    # Normalise dates to ISO strings (in case raw_sql returns Timestamp objects)
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["expiry"] = pd.to_datetime(df["expiry"]).dt.strftime("%Y-%m-%d")

    return df


def main() -> None:
    """Download all four stress windows and save as parquets."""
    try:
        import wrds  # type: ignore[import]
    except ImportError as exc:
        raise SystemExit(
            "wrds package not found.  Install with: uv sync --group research"
        ) from exc

    print("Connecting to WRDS ...")
    db = wrds.Connection()

    spx_secid = resolve_spx_secid(db)

    _DATA.mkdir(parents=True, exist_ok=True)

    for window in _WINDOWS:
        out_path = _DATA / f"{window.name}.parquet"
        print(f"\n[{window.label}] {window.start_date} — {window.end_date}")
        df = pull_window(db, spx_secid, window)
        if df.empty:
            print(f"  WARNING: zero rows returned — check secid or date range")
            continue
        df = _to_engine_schema(df)
        print(f"  rows       : {len(df):,}")
        print(f"  dates      : {df['date'].min()} — {df['date'].max()}")
        print(f"  strike range: ${df['strike'].min():.0f} — ${df['strike'].max():.0f}")
        print(f"  iv range   : {df['impl_volatility'].min():.2f} — {df['impl_volatility'].max():.2f}")
        zero_bid_drop = (df["best_bid"] == 0).sum()
        if zero_bid_drop > 0:
            print(f"  NOTE: {zero_bid_drop} rows with best_bid=0 (already excluded by filter)")
        df.to_parquet(out_path, index=False)
        print(f"  saved      : {out_path}")

    db.close()
    print(
        "\nDone.  All three stress parquets are in data/."
        "\nOnce portfolio_atm_options.parquet is also present, WRDS_PRESENT will"
        "\ntrigger in reports/backtest-proofs.qmd and all four stress panels will render."
        "\nNever commit these files — they contain licensed OptionMetrics data."
    )


if __name__ == "__main__":
    main()
