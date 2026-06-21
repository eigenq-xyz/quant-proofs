"""Cross-asset analysis + AQR parser tests.

Deterministic and offline: a tiny synthetic returns fixture exercises ``analyze_return_streams``
and an inline AQR-shaped row list exercises ``parse_aqr_sheet``. No network access.
"""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd

from research_pipeline import analyze_return_streams
from research_pipeline.data_sources import parse_aqr_sheet


def _synthetic_streams() -> dict[str, pd.Series]:
    """Three monthly return streams: a strong, a weak, and a near-zero asset class."""
    idx = pd.date_range("2000-01-31", periods=120, freq="ME")
    rng = np.random.default_rng(0)
    return {
        "strong": pd.Series(0.012 + rng.normal(0.0, 0.03, len(idx)), index=idx),
        "weak": pd.Series(0.004 + rng.normal(0.0, 0.03, len(idx)), index=idx),
        "flat": pd.Series(rng.normal(0.0, 0.03, len(idx)), index=idx),
    }


def test_analyze_return_streams_shapes_and_columns() -> None:
    streams = _synthetic_streams()
    summary, corr = analyze_return_streams(streams, periods_per_year=12)
    assert set(summary.index) == set(streams)
    assert "sharpe" in summary.columns
    assert "deflated_sharpe" in summary.columns
    assert list(corr.index) == list(corr.columns) == list(streams)
    # Correlation matrix is square with unit diagonal.
    assert corr.shape == (3, 3)
    assert np.allclose(np.diag(corr.to_numpy()), 1.0)


def test_analyze_return_streams_ranks_strong_above_flat() -> None:
    streams = _synthetic_streams()
    summary, _ = analyze_return_streams(streams, periods_per_year=12)
    assert summary.loc["strong", "sharpe"] > summary.loc["flat", "sharpe"]
    # Deflated Sharpe stays a probability in [0, 1] and ranks consistently with Sharpe.
    for cls in streams:
        assert 0.0 <= summary.loc[cls, "deflated_sharpe"] <= 1.0
    assert summary.loc["strong", "deflated_sharpe"] >= summary.loc["flat", "deflated_sharpe"]


def test_analyze_return_streams_deflation_uses_n_trials() -> None:
    # With more asset classes searched, the deflated Sharpe of a fixed stream can only fall
    # (the multiple-testing hurdle rises). Compare n_trials=1 vs n_trials=4 for the same series.
    base = _synthetic_streams()["strong"]
    one, _ = analyze_return_streams({"a": base}, periods_per_year=12)
    four, _ = analyze_return_streams(
        {"a": base, "b": base, "c": base, "d": base}, periods_per_year=12
    )
    assert four.loc["a", "deflated_sharpe"] <= one.loc["a", "deflated_sharpe"] + 1e-9


def _aqr_fixture_rows() -> list[tuple[object, ...]]:
    """A tiny AQR-shaped sheet: text preamble, a padded header row, then dated decimal returns.

    Mirrors the real files: a leading blank date column, a gap column in the header (AQR pads
    with blanks), mixed datetime/string date cells, a blank return cell, then a footnote row.
    """
    return [
        ("AQR Capital Management, LLC",) + ("",) * 4,
        ("This file contains ...",) + ("",) * 4,
        ("",) * 5,
        ("", "FAC_EQ", "FAC_FI", "", "FAC_FX"),  # header: gap at position 3
        (datetime.datetime(1990, 1, 31), 0.01, -0.02, "", 0.03),
        ("02/28/1990", 0.04, 0.05, "", None),  # blank/None return -> NaN
        (datetime.datetime(1990, 3, 31), -0.01, 0.02, "", 0.00),
        ("Please see disclosures.",) + ("",) * 4,  # footnote ends the block
    ]


def test_parse_aqr_sheet_basic_structure() -> None:
    df = parse_aqr_sheet(_aqr_fixture_rows())
    # Header gap is dropped; only labelled factor columns survive, in order.
    assert list(df.columns) == ["FAC_EQ", "FAC_FI", "FAC_FX"]
    assert len(df) == 3
    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index[0] == pd.Timestamp("1990-01-31")
    assert df.index[1] == pd.Timestamp("1990-02-28")  # MM/DD/YYYY string parsed
    # Values are passed through as decimals; the blank cell became NaN.
    assert df.loc[pd.Timestamp("1990-01-31"), "FAC_EQ"] == 0.01
    assert np.isnan(df.loc[pd.Timestamp("1990-02-28"), "FAC_FX"])


def test_parse_aqr_sheet_stops_at_footnote() -> None:
    rows = _aqr_fixture_rows()
    df = parse_aqr_sheet(rows)
    # The trailing "Please see disclosures." row must not leak in as data.
    assert pd.Timestamp("1990-03-31") in df.index
    assert df.shape[0] == 3


def test_analyze_return_streams_end_to_end_with_parsed_fixture() -> None:
    # Wire the parser output into the analysis to prove the full offline path works.
    df = parse_aqr_sheet(_aqr_fixture_rows())
    streams = {c: df[c].dropna() for c in df.columns}
    summary, corr = analyze_return_streams(streams, periods_per_year=12)
    assert set(summary.index) == {"FAC_EQ", "FAC_FI", "FAC_FX"}
    assert corr.shape == (3, 3)
