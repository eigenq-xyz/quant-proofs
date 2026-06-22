"""Download Ken French 10 Industry Portfolio daily returns and save as parquet.

Source: Kenneth R. French Data Library (public domain)
URL: https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html

Usage
-----
    uv run python scripts/ingest_french_10ind.py

Output
------
    data/french_10ind_daily_vw.parquet   Value-weighted daily returns, 1926-present

The file is tracked by DVC (see data/french_10ind_daily_vw.parquet.dvc).
Run `dvc push` after regenerating to update the MinIO remote.
"""

from __future__ import annotations

import io
import pathlib
import urllib.request
import zipfile

import pandas as pd

URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "10_Industry_Portfolios_daily_CSV.zip"
)
OUT = (
    pathlib.Path(__file__).parent.parent
    / "data"
    / "french_10ind_daily_vw.parquet"
)

MISSING_CODES = {-99.99 / 100.0, -999.0 / 100.0}


def _parse_vw_block(raw: str) -> pd.DataFrame:
    """Extract the value-weighted returns block from the raw CSV text."""
    lines = raw.replace("\r", "").split("\n")
    title = "Average Value Weighted Returns -- Daily"
    ti = next(i for i, line in enumerate(lines) if title in line)

    # Column header is the next non-blank line after the title
    hi = ti + 1
    while not lines[hi].strip():
        hi += 1
    cols = [c.strip() for c in lines[hi].split(",") if c.strip()]

    rows: list[list[str]] = []
    for line in lines[hi + 1 :]:
        line = line.strip()
        if not line:
            break
        parts = [p.strip() for p in line.split(",")]
        parts = [p for p in parts if p]  # drop empty leading field
        if not parts[0].isdigit():
            break
        rows.append(parts)

    df = pd.DataFrame(rows, columns=["date"] + cols)
    df["date"] = pd.to_datetime(df["date"], format="%Y%m%d")
    for col in cols:
        df[col] = pd.to_numeric(df[col], errors="coerce") / 100.0
    df = df.set_index("date")

    # Replace missing-value sentinels
    for code in MISSING_CODES:
        df = df.replace(code, float("nan"))

    return df


def main() -> None:
    print(f"Downloading: {URL}")
    with urllib.request.urlopen(URL) as response:
        with zipfile.ZipFile(io.BytesIO(response.read())) as zf:
            raw = zf.read(zf.namelist()[0]).decode("latin-1")

    vw = _parse_vw_block(raw)

    print(f"Parsed {len(vw):,} rows, {len(vw.columns)} industries")
    print(f"Date range: {vw.index.min().date()} to {vw.index.max().date()}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    vw.to_parquet(OUT, compression="snappy")
    print(f"Saved: {OUT}  ({OUT.stat().st_size / 1024:.1f} KB)")
    print("Run `dvc push` to upload to the MinIO remote.")


if __name__ == "__main__":
    main()
