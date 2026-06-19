"""Track 2 — real point-in-time data loaders.

Two sources:
- **Ken French** (free) — daily factor / portfolio returns. Downloadable; may be cached
  under ``research-pipeline/data/`` (gitignored).
- **WRDS / CRSP** (licensed) — the real equity cross-section. Read via the ``wrds`` package
  using YOUR credentials, or a local gitignored parquet extract.

HARD RULE (repo-wide): **licensed data is NEVER committed.** All cached/extracted data lives
under ``data/`` which is gitignored. These loaders never write to a tracked path.
"""

from __future__ import annotations

import pathlib

import pandas as pd

from .data import PricePanel

# research-pipeline/data — gitignored; never tracked.
DATA_DIR = pathlib.Path(__file__).resolve().parents[2] / "data"


def load_ken_french_factors(
    dataset: str = "F-F_Research_Data_Factors_daily",
    start: str | None = None,
    end: str | None = None,
) -> pd.DataFrame:
    """Daily Fama-French factor returns (decimal). Requires network (``pandas_datareader``).

    Used for the factor-attribution stage and as a cross-asset 'asset class' of factor returns.
    """
    try:
        from pandas_datareader import data as pdr  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise ImportError("pip install pandas-datareader to load Ken French data") from exc
    raw = pdr.DataReader(dataset, "famafrench", start=start, end=end)
    return raw[0] / 100.0  # French returns are in percent


def load_crsp_daily(
    permnos_or_tickers: list[str] | None = None,
    start: str = "2005-01-01",
    end: str = "2023-12-31",
    wrds_username: str | None = None,
    local_parquet: str | pathlib.Path | None = None,
) -> PricePanel:
    """Daily CRSP adjusted-price panel as a ``PricePanel``.

    LICENSED — never commit the output. Two paths:
    1. ``local_parquet`` — a gitignored extract you already pulled (preferred for reuse).
    2. live ``wrds`` connection (``pip install wrds``; needs your WRDS login).

    Builds total-return-adjusted prices (``prc / cfacpr``) pivoted to dates x permno.
    """
    if local_parquet is not None:
        df = pd.read_parquet(local_parquet)
    else:
        try:
            import wrds  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise ImportError(
                "pip install wrds and provide credentials, or pass local_parquet"
            ) from exc
        db = wrds.Connection(wrds_username=wrds_username)
        query = (
            "select date, permno, abs(prc)/cfacpr as adj_price "
            "from crsp.dsf "
            f"where date between '{start}' and '{end}'"
        )
        df = db.raw_sql(query, date_cols=["date"])
        db.close()
    prices = df.pivot(index="date", columns="permno", values="adj_price").sort_index()
    prices.columns = [str(c) for c in prices.columns]
    return PricePanel(prices)
