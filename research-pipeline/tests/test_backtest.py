"""Backtester sanity + dollar-neutrality / leverage invariants."""

from __future__ import annotations

import numpy as np

from research_pipeline import make_synthetic_panel, momentum_signal, run_backtest


def test_backtest_runs_and_reports() -> None:
    panel = make_synthetic_panel(n_days=600, n_assets=30, seed=3)
    res = run_backtest(panel, momentum_signal, cost_bps=5.0)
    assert res.summary["n_days"] > 0
    for key in ("gross_sharpe", "net_sharpe", "mean_IC", "avg_turnover"):
        assert np.isfinite(res.summary[key])
    assert res.summary["net_sharpe"] <= res.summary["gross_sharpe"] + 1e-9


def test_book_is_dollar_neutral_and_gross_normalised() -> None:
    panel = make_synthetic_panel(n_days=400, n_assets=25, seed=4)
    res = run_backtest(panel, momentum_signal, gross=1.0)
    active = res.weights.loc[res.weights.abs().sum(axis=1) > 0]
    assert np.allclose(active.sum(axis=1).values, 0.0, atol=1e-9)
    assert np.allclose(active.abs().sum(axis=1).values, 1.0, atol=1e-9)
