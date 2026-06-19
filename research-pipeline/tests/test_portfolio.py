"""Portfolio constructor tests — constraint invariants for each construction style."""

from __future__ import annotations

import numpy as np
import pandas as pd

from research_pipeline import (
    available_portfolios,
    directional_weights,
    get_portfolio,
    long_only_weights,
    long_short_quantile_weights,
    signal_to_weights,
)


def _scores() -> pd.Series:
    return pd.Series({"A": 2.0, "B": 1.0, "C": -0.5, "D": -1.0, "E": -1.5, "F": 0.0})


def test_registry_lists_builtins() -> None:
    names = available_portfolios()
    for expected in ("dollar_neutral", "long_only", "long_short_quantile", "directional"):
        assert expected in names
    assert get_portfolio("dollar_neutral") is signal_to_weights


def test_get_portfolio_unknown_raises() -> None:
    try:
        get_portfolio("nope")
    except KeyError as exc:
        assert "unknown portfolio" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected KeyError")


def test_dollar_neutral_invariants() -> None:
    w = signal_to_weights(_scores(), gross=2.0)
    assert abs(float(w.sum())) < 1e-12
    assert abs(float(w.abs().sum()) - 2.0) < 1e-12


def test_long_only_invariants() -> None:
    w = long_only_weights(_scores(), gross=1.0)
    assert (w >= -1e-15).all()
    assert abs(float(w.sum()) - 1.0) < 1e-12


def test_long_short_quantile_invariants() -> None:
    w = long_short_quantile_weights(_scores(), gross=1.0, quantile=1.0 / 3.0)
    assert abs(float(w.sum())) < 1e-12
    assert abs(float(w.abs().sum()) - 1.0) < 1e-12
    assert int((w != 0).sum()) == 4  # 2 long + 2 short of 6 names


def test_directional_holds_net_position() -> None:
    # Single asset with a positive score: a full long, not zero (no cross-sectional demean).
    w = directional_weights(pd.Series({"A": 0.3}), gross=1.0)
    assert abs(float(w["A"]) - 1.0) < 1e-12
    # Multi-asset: sum of |w| == gross, net need not be zero.
    wm = directional_weights(_scores(), gross=1.0)
    assert abs(float(wm.abs().sum()) - 1.0) < 1e-12


def test_degenerate_inputs_return_zero() -> None:
    flat = pd.Series({"A": 1.0, "B": 1.0, "C": 1.0})  # zero after demeaning
    assert float(signal_to_weights(flat).abs().sum()) == 0.0
    nan = pd.Series({"A": np.nan})
    assert float(directional_weights(nan).abs().sum()) == 0.0
