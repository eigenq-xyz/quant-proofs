"""Strategy abstraction + registry tests.

Confirms the new alpha-agnostic layer (1) reproduces the existing cross-sectional path
exactly, (2) resolves by name with parameter overrides, and (3) is non-anticipating in the
structural sense the engine relies on (``decide`` reads only the panel it is handed).
"""

from __future__ import annotations

import pandas as pd

from research_pipeline import (
    available_strategies,
    get_strategy,
    make_synthetic_panel,
)
from research_pipeline.backtest import run_backtest
from research_pipeline.signals import momentum_signal


def test_registry_lists_builtins() -> None:
    names = available_strategies()
    assert "momentum" in names
    assert "reversal" in names


def test_get_strategy_unknown_raises() -> None:
    try:
        get_strategy("does-not-exist")
    except KeyError as exc:
        assert "unknown strategy" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected KeyError for unknown strategy")


def test_signal_strategy_reproduces_signal_fn() -> None:
    panel = make_synthetic_panel(n_days=500, n_assets=20, seed=0)
    strat = get_strategy("momentum", lookback=126, skip=10)
    # The adapter's vectorised signals match the underlying SignalFn exactly.
    pd.testing.assert_frame_equal(
        strat.signals(panel), momentum_signal(panel, lookback=126, skip=10)
    )


def test_strategy_backtest_matches_legacy_path() -> None:
    panel = make_synthetic_panel(n_days=500, n_assets=20, seed=1)
    strat = get_strategy("momentum")
    via_strategy = run_backtest(panel, strat.signals)
    via_signal_fn = run_backtest(panel, momentum_signal)
    assert via_strategy.summary["net_sharpe"] == via_signal_fn.summary["net_sharpe"]


def test_decide_is_non_anticipating() -> None:
    """``decide`` on the panel truncated at ``t`` equals the time-``t`` weights from the
    full panel: the strategy cannot see past ``t``."""
    panel = make_synthetic_panel(n_days=400, n_assets=15, seed=2)
    strat = get_strategy("momentum")
    cut = panel.prices.index[300]
    truncated = strat.decide(panel.as_of(cut))
    full = strat.signals(panel)
    full_weights_at_cut = strat.weight_fn(full.loc[cut])  # type: ignore[attr-defined]
    common = truncated.index.intersection(full_weights_at_cut.index)
    assert len(common) > 0
    pd.testing.assert_series_equal(
        truncated.reindex(common), full_weights_at_cut.reindex(common), check_names=False
    )
