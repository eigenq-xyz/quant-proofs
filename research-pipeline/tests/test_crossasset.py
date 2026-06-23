"""Cross-asset analysis + AQR parser tests.

Deterministic and offline: a tiny synthetic returns fixture exercises ``analyze_return_streams``
and an inline AQR-shaped row list exercises ``parse_aqr_sheet``. No network access.
"""

from __future__ import annotations

import datetime

import numpy as np
import pandas as pd
import pytest

from research_pipeline import (
    analyze_return_streams,
    combine_sleeves_walkforward,
    reproduction_table,
    verification_status_line,
)
from research_pipeline.data_sources import parse_aqr_sheet
from research_pipeline.portfolio import VerifiedSolverUnavailable


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


def test_reproduction_table_flags_sign_and_magnitude() -> None:
    realized = pd.DataFrame(
        {"sharpe": [0.60, 0.55, -0.10, 0.30]},
        index=["match", "low_magnitude", "wrong_sign", "extra_realized"],
    )
    published = {
        "match": 0.50,  # ratio 1.2 -> sign + magnitude -> reproduced
        "low_magnitude": 0.20,  # ratio 2.75 > tol 2.0 -> sign ok, magnitude fails
        "wrong_sign": 0.40,  # realized is negative -> sign fails
        "absent": 0.50,  # not in realized -> dropped from the table
    }
    table = reproduction_table(realized, published, tol_ratio=2.0)
    # Only sleeves present in BOTH realized and published appear; 'extra_realized' has no
    # published anchor and 'absent' was never realized.
    assert set(table.index) == {"match", "low_magnitude", "wrong_sign"}
    assert bool(table.loc["match", "reproduced"]) is True
    assert bool(table.loc["low_magnitude", "sign_match"]) is True
    assert bool(table.loc["low_magnitude", "magnitude_match"]) is False
    assert bool(table.loc["low_magnitude", "reproduced"]) is False
    assert bool(table.loc["wrong_sign", "sign_match"]) is False
    assert bool(table.loc["wrong_sign", "reproduced"]) is False
    assert int(table["reproduced"].sum()) == 1


def test_reproduction_table_tol_ratio_widens_band() -> None:
    realized = pd.DataFrame({"sharpe": [0.55]}, index=["x"])
    published = {"x": 0.20}  # ratio 2.75
    assert (
        bool(reproduction_table(realized, published, tol_ratio=2.0).loc["x", "reproduced"]) is False
    )
    assert (
        bool(reproduction_table(realized, published, tol_ratio=3.0).loc["x", "reproduced"]) is True
    )


def test_reproduction_table_consumes_analyze_summary() -> None:
    # The analyze_return_streams summary feeds straight into reproduction_table. Using the
    # realized Sharpes themselves as the published anchor => every sleeve reproduces (ratio 1).
    streams = _synthetic_streams()
    summary, _ = analyze_return_streams(streams, periods_per_year=12)
    published = {k: float(summary.loc[k, "sharpe"]) for k in streams}
    table = reproduction_table(summary, published)
    assert set(table.index) == set(streams)
    assert int(table["reproduced"].sum()) == len(streams)
    assert np.allclose(table["ratio"].to_numpy(dtype=float), 1.0)


def test_reproduction_table_validation() -> None:
    realized = pd.DataFrame({"sharpe": [0.5]}, index=["x"])
    with pytest.raises(ValueError):
        reproduction_table(realized, {"x": 0.5}, tol_ratio=0.5)  # tol < 1
    with pytest.raises(ValueError):
        reproduction_table(
            pd.DataFrame({"ann_return": [0.1]}, index=["x"]), {"x": 0.5}
        )  # no sharpe
    with pytest.raises(ValueError):
        reproduction_table(realized, {"y": 0.5})  # no overlap


def test_verification_status_line() -> None:
    line = verification_status_line()
    assert isinstance(line, str)
    assert "Lean build green" in line
    assert "look-ahead" in line
    assert "leakage" in line
    assert "Scope:" in line
    assert "Scope:" not in verification_status_line(include_scope=False)


def _diversifying_streams(n: int = 3, periods: int = 120, seed: int = 2) -> dict[str, pd.Series]:
    idx = pd.date_range("2000-01-31", periods=periods, freq="ME")
    rng = np.random.default_rng(seed)
    return {f"s{k}": pd.Series(0.005 + rng.normal(0.0, 0.03, periods), index=idx) for k in range(n)}


def test_combine_sleeves_equal_weight_mechanics() -> None:
    streams = _diversifying_streams()
    eq = combine_sleeves_walkforward(
        streams, method="equal_weight", min_obs=24, lookback=36, cost_bps=0.0
    )
    panel = pd.DataFrame(streams)
    # One net observation per realised month after the first min_obs months.
    assert len(eq) == len(panel.index) - 24 - 1
    # Equal weight, zero cost => the combined return is just the cross-sleeve mean each month.
    t = eq.index[10]
    assert abs(float(eq.loc[t]) - float(panel.loc[t].mean())) < 1e-12


def test_combine_sleeves_verified_mv_matches_equal_length() -> None:
    streams = _diversifying_streams()
    try:
        mv = combine_sleeves_walkforward(streams, method="verified_mv", min_obs=24, lookback=36)
    except VerifiedSolverUnavailable:
        pytest.skip("verified PGD solver not built in this environment")
    eq = combine_sleeves_walkforward(streams, method="equal_weight", min_obs=24, lookback=36)
    # Both walk the same dates, so the comparison is on a common index.
    assert mv.index.equals(eq.index)
    assert mv.notna().all()


def test_combine_sleeves_validation() -> None:
    idx = pd.date_range("2000-01-31", periods=60, freq="ME")
    with pytest.raises(ValueError):
        combine_sleeves_walkforward({"a": pd.Series(0.01, index=idx)})  # < 2 sleeves
    with pytest.raises(ValueError):
        combine_sleeves_walkforward(_diversifying_streams(), method="bogus")  # bad method
    short = {"a": pd.Series(0.01, index=idx[:5]), "b": pd.Series(0.02, index=idx[:5])}
    with pytest.raises(ValueError):
        combine_sleeves_walkforward(short, min_obs=36)  # too few aligned observations


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
