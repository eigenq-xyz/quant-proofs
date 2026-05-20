"""Convert WRDS web-portal CSV exports of SPX options into stress-window parquets.

This script is the manual-download companion to the WRDS web portal.  It does
NOT require the ``wrds`` Python package; it only needs ``pandas`` and
``pyarrow`` (both installed by ``uv sync --extra dev``).

How to download the three stress windows from WRDS
----------------------------------------------------
For each of the three windows below, repeat these steps on the WRDS web portal
(requires a campus VPN connection):

  1. Go to: https://wrds-www.wharton.upenn.edu/
     Navigate to: Data > OptionMetrics > IvyDB US > Option Price (opprcd)

  2. Date range — set the window dates:
       GFC-2008:          2008-09-15 to 2008-11-21
       Volmageddon-2018:  2018-01-22 to 2018-02-16
       Flash Crash-2015:  2015-08-17 to 2015-08-28

  3. Security filter — search for ticker "SPX" and select it.
     (SPX = S&P 500 index options; not SPY the ETF.)

  4. Variable selection — select ALL of these columns:
       secid, date, exdate, cp_flag, strike_price,
       best_bid, best_offer, impl_volatility, delta,
       volume, open_interest, optionid, spotprice

  5. Output format: CSV (tab or comma-delimited both work).

  6. Download and note the path.  Suggested filenames:
       spx_opprcd_gfc_2008.csv
       spx_opprcd_volm_2018.csv
       spx_opprcd_flash_2015.csv

Usage
-----
From the backtest-proofs directory:

    uv run python scripts/download_stress_windows.py \\
        --gfc   ~/Downloads/spx_opprcd_gfc_2008.csv \\
        --volm  ~/Downloads/spx_opprcd_volm_2018.csv \\
        --flash ~/Downloads/spx_opprcd_flash_2015.csv

Omit any flag to skip that window (useful when re-running after a partial
download).

Output
------
  data/stress_gfc_2008.parquet
  data/stress_volm_2018.parquet
  data/stress_flash_2015.parquet

These three files plus the existing ``data/portfolio_atm_options.parquet``
satisfy the ``WRDS_PRESENT`` gate in ``reports/backtest-proofs.qmd``, causing
``fig-stress`` to render with real data instead of the placeholder.

Licensing
---------
All output parquets are .gitignored (data/*.parquet).  Never commit them —
they contain licensed OptionMetrics data.

Filters applied
---------------
- Calls only (cp_flag = 'C')
- 14–90 calendar days to expiry
- ATM moneyness: strike / spotprice in [0.95, 1.05]
- best_bid > 0 (drops zero-quoted rows, common in GFC peak days)
- impl_volatility in [0.05, 2.0]

Strike encoding note
--------------------
OptionMetrics stores strike_price as an integer = dollar_strike × 1000.
A $1,500 strike is stored as 1500000.  This script divides by 1000.0
automatically.  The heuristic: if the median strike/spot ratio > 100,
the column is still in raw encoding and needs the correction.
"""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

_DATA = Path(__file__).parent.parent / "data"

_MIN_DTE = 14
_MAX_DTE = 90
_MONO_LO = 0.95
_MONO_HI = 1.05
_IV_LO = 0.05
_IV_HI = 2.0


@dataclass(frozen=True)
class _WindowSpec:
    label: str
    start_date: str
    end_date: str
    r: float
    out_stem: str  # parquet filename without .parquet


_SPECS: dict[str, _WindowSpec] = {
    "gfc": _WindowSpec(
        label="GFC-2008",
        start_date="2008-09-15",
        end_date="2008-11-21",
        r=0.01,
        out_stem="stress_gfc_2008",
    ),
    "volm": _WindowSpec(
        label="Volmageddon-2018",
        start_date="2018-01-22",
        end_date="2018-02-16",
        r=0.015,
        out_stem="stress_volm_2018",
    ),
    "flash": _WindowSpec(
        label="FlashCrash-2015",
        start_date="2015-08-17",
        end_date="2015-08-28",
        r=0.005,
        out_stem="stress_flash_2015",
    ),
}


def process_csv(csv_path: Path, spec: _WindowSpec) -> pd.DataFrame:
    """Load, filter, and rename a raw opprcd CSV into the engine schema.

    Returns a DataFrame with columns:
        underlying_ticker, date, expiry, strike, option_type,
        best_bid, best_offer, impl_volatility, underlying_price,
        delta, volume, open_interest, optionid
    """
    raw = pd.read_csv(csv_path, sep=None, engine="python", low_memory=False)
    raw.columns = [c.lower().strip() for c in raw.columns]

    # Verify required columns are present
    required = {
        "date", "exdate", "cp_flag", "strike_price",
        "best_bid", "best_offer", "impl_volatility", "spotprice",
    }
    missing = required - set(raw.columns)
    if missing:
        raise ValueError(
            f"{spec.label}: CSV is missing required columns: {missing}\n"
            f"Found: {sorted(raw.columns)}"
        )

    df = raw.copy()

    # Normalise dates
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["exdate"] = pd.to_datetime(df["exdate"]).dt.strftime("%Y-%m-%d")

    # Filter to the window dates (in case the CSV is wider than one window)
    df = df[
        (df["date"] >= spec.start_date) & (df["date"] <= spec.end_date)
    ]

    # Calls only
    df = df[df["cp_flag"].str.upper() == "C"]

    # DTE filter
    dte = (
        pd.to_datetime(df["exdate"]) - pd.to_datetime(df["date"])
    ).dt.days
    df = df[(dte >= _MIN_DTE) & (dte <= _MAX_DTE)]

    # Coerce numeric columns
    for col in ("strike_price", "best_bid", "best_offer", "impl_volatility", "spotprice"):
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Detect and correct OptionMetrics strike×1000 encoding
    valid_spot = df["spotprice"] > 0
    if valid_spot.sum() > 0:
        median_ratio = (
            df.loc[valid_spot, "strike_price"] / df.loc[valid_spot, "spotprice"]
        ).median()
        if median_ratio > 100:
            print(
                f"  [{spec.label}] strike_price appears to be in OM raw encoding "
                f"(median ratio={median_ratio:.0f}) — dividing by 1000"
            )
            df["strike_price"] = df["strike_price"] / 1000.0

    # Filters that need the corrected strike
    df = df[df["best_bid"] > 0]
    df = df[
        df["impl_volatility"].between(_IV_LO, _IV_HI, inclusive="both")
    ]
    df = df[
        (df["spotprice"] > 0)
        & df["impl_volatility"].notna()
    ]
    moneyness = df["strike_price"] / df["spotprice"]
    df = df[moneyness.between(_MONO_LO, _MONO_HI, inclusive="both")]

    # Rename to engine schema
    df = df.rename(
        columns={
            "exdate": "expiry",
            "strike_price": "strike",
            "spotprice": "underlying_price",
        }
    )
    df["underlying_ticker"] = "SPX"
    df["option_type"] = "call"

    # Keep only the columns run_stress_window + optionmetrics_option_snapshots_from_df need
    keep = [
        "underlying_ticker", "date", "expiry", "strike", "option_type",
        "best_bid", "best_offer", "impl_volatility", "underlying_price",
    ]
    optional = ["delta", "volume", "open_interest", "optionid"]
    keep += [c for c in optional if c in df.columns]

    return df[keep].reset_index(drop=True)


def _print_summary(df: pd.DataFrame, spec: _WindowSpec, out_path: Path) -> None:
    n_days = df["date"].nunique()
    print(f"  rows          : {len(df):,}")
    print(f"  trading days  : {n_days}")
    print(f"  date range    : {df['date'].min()} — {df['date'].max()}")
    print(f"  strike range  : ${df['strike'].min():.0f} — ${df['strike'].max():.0f}")
    print(f"  iv range      : {df['impl_volatility'].min():.2f} — {df['impl_volatility'].max():.2f}")
    print(f"  saved         : {out_path}")


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--gfc",   type=Path, default=None, metavar="CSV",
                   help="opprcd CSV for GFC-2008 (2008-09-15 to 2008-11-21)")
    p.add_argument("--volm",  type=Path, default=None, metavar="CSV",
                   help="opprcd CSV for Volmageddon-2018 (2018-01-22 to 2018-02-16)")
    p.add_argument("--flash", type=Path, default=None, metavar="CSV",
                   help="opprcd CSV for Flash Crash-2015 (2015-08-17 to 2015-08-28)")
    return p.parse_args()


def main() -> None:
    args = _parse_args()

    inputs: dict[str, Path | None] = {
        "gfc": args.gfc,
        "volm": args.volm,
        "flash": args.flash,
    }

    if not any(inputs.values()):
        print(__doc__)
        raise SystemExit(
            "No CSV files specified.  Pass at least one of --gfc, --volm, --flash."
        )

    _DATA.mkdir(exist_ok=True)

    for key, csv_path in inputs.items():
        spec = _SPECS[key]
        if csv_path is None:
            print(f"[{spec.label}] skipped (no --{key} argument)")
            continue
        if not csv_path.exists():
            print(f"[{spec.label}] ERROR: file not found: {csv_path}")
            continue

        print(f"\n[{spec.label}] processing {csv_path.name} ...")
        df = process_csv(csv_path, spec)

        if df.empty:
            print(
                f"  WARNING: zero rows after filtering.  Check that the CSV "
                f"covers {spec.start_date}–{spec.end_date} and includes SPX options."
            )
            continue

        out_path = _DATA / f"{spec.out_stem}.parquet"
        df.to_parquet(out_path, index=False)
        _print_summary(df, spec, out_path)

    print(
        "\nDone.  Once all three stress parquets plus portfolio_atm_options.parquet"
        "\nare in data/, WRDS_PRESENT will be True and fig-stress will render."
        "\nReminder: never commit .parquet files — they are .gitignored."
    )


if __name__ == "__main__":
    main()
