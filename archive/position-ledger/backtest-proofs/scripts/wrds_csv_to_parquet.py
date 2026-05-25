"""Convert WRDS OptionMetrics CSV exports to the engine's parquet schema.

Usage — single wide-window download (2007–2024, all tickers)
-------------------------------------------------------------
Place the three WRDS CSV downloads in the data/ directory and run:

    cd /path/to/backtest-proofs
    uv run python scripts/wrds_csv_to_parquet.py

The script builds a full joined parquet (data/portfolio_all.parquet) and
automatically writes four sub-window parquets:

    data/portfolio_atm_options.parquet  — 2019-01-01 to 2024-12-31
    data/stress_gfc_2008.parquet        — 2008-09-01 to 2008-12-31
    data/stress_volm_2018.parquet       — 2017-12-01 to 2018-04-30
    data/stress_dec2018.parquet         — 2018-10-01 to 2019-01-31

Custom output directory
-----------------------
Pass --output-dir to write all parquets to a different location:

    uv run python scripts/wrds_csv_to_parquet.py --output-dir /tmp/data
"""

import argparse
from pathlib import Path

import pandas as pd

_DATA = Path(__file__).parent.parent / "data"

# ── Default input files (WRDS CSV exports, wide 2007–2024 dataset) ──────
SECNMD_CSV = _DATA / "optionmetrics_secid_ticker_cusip.csv"
OPPRCD_CSV = _DATA / "optionmetrics_tickers_options_data.csv"
SECPRD_CSV = _DATA / "optionmetrics_asset_prices.csv"

TARGET_TICKERS = {"SPY", "QQQ", "AAPL", "MSFT", "JPM", "IWM"}

# ── Sub-window date ranges ───────────────────────────────────────────────
_WINDOWS: list[tuple[str, str, str]] = [
    # (output_filename, date_start, date_end)
    ("portfolio_atm_options.parquet", "2019-01-01", "2024-12-31"),
    ("stress_gfc_2008.parquet", "2008-09-01", "2008-12-31"),
    ("stress_volm_2018.parquet", "2017-12-01", "2018-04-30"),
    ("stress_dec2018.parquet", "2018-10-01", "2019-01-31"),
]
# ───────────────────────────────────────────────────────────────────────────


def build_secid_map(secnmd_csv: Path) -> dict[int, str]:
    """Return {secid: ticker} for the target tickers."""
    df = pd.read_csv(secnmd_csv, low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]

    # Keep only the most-recent active row per secid
    df["effect_date"] = pd.to_datetime(df["effect_date"])
    df = df.sort_values("effect_date").drop_duplicates("secid", keep="last")

    df = df[df["ticker"].str.upper().isin(TARGET_TICKERS)]
    mapping = dict(zip(df["secid"].astype(int), df["ticker"].str.upper()))
    print("secid map:", mapping)
    return mapping


def load_security_prices(secprd_csv: Path, secid_map: dict[int, str]) -> pd.DataFrame:
    """Return DataFrame with (secid, date, underlying_price) from daily closes."""
    df = pd.read_csv(secprd_csv, low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]

    df["secid"] = df["secid"].astype(int)
    df = df[df["secid"].isin(secid_map)]
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")

    return df[["secid", "date", "close"]].rename(columns={"close": "underlying_price"})


def load_and_clean(
    opprcd_csv: Path,
    secid_map: dict[int, str],
    spot_df: pd.DataFrame,
) -> pd.DataFrame:
    """Load option prices, join spot prices, and apply ATM/expiry filters."""
    df = pd.read_csv(opprcd_csv, low_memory=False)
    df.columns = [c.lower().strip() for c in df.columns]

    # Map secid → ticker
    df["secid"] = df["secid"].astype(int)
    df["underlying_ticker"] = df["secid"].map(secid_map)
    df = df[df["underlying_ticker"].notna()]

    # Rename to engine schema
    df = df.rename(
        columns={
            "exdate": "expiry",
            "strike_price": "strike",
            "cp_flag": "option_type",
        }
    )

    # Normalise date strings
    df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    df["expiry"] = pd.to_datetime(df["expiry"]).dt.strftime("%Y-%m-%d")
    # Normalise option_type to "call"/"put" (OptionMetrics uses "C"/"P")
    df["option_type"] = df["option_type"].str.upper().map({"C": "call", "P": "put"})

    # Join underlying spot prices from Security Prices table
    df = df.merge(spot_df, on=["secid", "date"], how="inner")
    df = df.drop(columns=["secid"])

    # Filter: calls only, valid quotes, non-null IV, valid spot
    df = df[
        (df["option_type"] == "call")
        & (df["best_bid"] > 0)
        & (df["best_offer"].notna())
        & (df["impl_volatility"].notna())
        & (df["underlying_price"] > 0)
    ]

    # Sanity check: OptionMetrics stores strike × 1000 — fix BEFORE ATM filter
    median_ratio = (df["strike"] / df["underlying_price"]).median()
    if median_ratio > 100:
        print("NOTE: strike stored x1000 — dividing by 1000")
        df["strike"] = df["strike"] / 1000.0

    # Filter: 20–40 calendar days to expiry
    days = (pd.to_datetime(df["expiry"]) - pd.to_datetime(df["date"])).dt.days
    df = df[(days >= 20) & (days <= 40)]

    # Filter: ATM ±3%
    moneyness = (df["strike"] / df["underlying_price"] - 1).abs()
    df = df[moneyness <= 0.03]

    return df.reset_index(drop=True)


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--secnmd",
        type=Path,
        default=SECNMD_CSV,
        help="Security Names CSV (default: data/optionmetrics_secid_ticker_cusip.csv)",
    )
    p.add_argument(
        "--options",
        type=Path,
        default=OPPRCD_CSV,
        help="Option Price CSV (default: data/optionmetrics_tickers_options_data.csv)",
    )
    p.add_argument(
        "--spots",
        type=Path,
        default=SECPRD_CSV,
        help="Security Prices CSV (default: data/optionmetrics_asset_prices.csv)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=_DATA,
        help="Output directory for all parquet files (default: data/)",
    )
    return p.parse_args()


def main() -> None:
    """Build parquet files from WRDS OptionMetrics CSV exports."""
    args = _parse_args()
    secnmd, opprcd, secprd = args.secnmd, args.options, args.spots
    out_dir: Path = args.output_dir

    for path in (secnmd, opprcd, secprd):
        if not path.exists():
            raise FileNotFoundError(f"Required file not found: {path}")

    print("Building secid map ...")
    secid_map = build_secid_map(secnmd)
    missing = TARGET_TICKERS - set(secid_map.values())
    if missing:
        print(f"WARNING: these tickers were not found in secnmd: {missing}")

    print("Loading security prices ...")
    spot_df = load_security_prices(secprd, secid_map)

    print("Loading and filtering option data ...")
    df = load_and_clean(opprcd, secid_map, spot_df)

    summary = df.groupby("underlying_ticker").agg(
        rows=("date", "count"),
        date_min=("date", "min"),
        date_max=("date", "max"),
        iv_median=("impl_volatility", "median"),
    )
    print("\nSummary by ticker (full window):")
    print(summary.to_string())
    print(f"\nTotal rows: {len(df):,}")

    out_dir.mkdir(exist_ok=True)

    # Write the full wide-window parquet
    all_out = out_dir / "portfolio_all.parquet"
    df.to_parquet(all_out, index=False)

    # Write sub-window parquets
    print("\nWriting sub-window parquets ...")
    print(f"\n{'Output file':<45}  {'Rows':>7}  {'Date min':<12}  {'Date max'}")
    print("-" * 85)

    # Full window first
    _fmt_row(all_out, df)

    for fname, date_start, date_end in _WINDOWS:
        mask = (df["date"] >= date_start) & (df["date"] <= date_end)
        sub = df[mask].reset_index(drop=True)
        out_path = out_dir / fname
        sub.to_parquet(out_path, index=False)
        _fmt_row(out_path, sub)


def _fmt_row(path: Path, df: pd.DataFrame) -> None:
    """Print a one-line summary row for a parquet output."""
    n = len(df)
    if n > 0:
        d_min = df["date"].min()
        d_max = df["date"].max()
    else:
        d_min = d_max = "—"
    print(f"  {str(path.name):<43}  {n:>7,}  {d_min:<12}  {d_max}")


if __name__ == "__main__":
    main()
