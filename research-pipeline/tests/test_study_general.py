"""Study-level generality tests: opt-in cross-sectional metrics, time-series alpha path,
and the optional combination stage."""

from __future__ import annotations

from research_pipeline import get_strategy, make_synthetic_panel, run_research_study
from research_pipeline.signals import reversal_signal


def test_cross_sectional_metrics_skipped_for_single_asset() -> None:
    panel = make_synthetic_panel(n_days=500, n_assets=1, seed=0)
    strat = get_strategy("ts_momentum")  # directional, single-asset capable
    rep = run_research_study(panel, strat.signals, weight_fn=strat.weight_fn)
    assert rep.cross_sectional is False
    assert rep.ic.empty and rep.decay.empty
    # The backtest still ran and produced a Sharpe.
    assert "net_sharpe" in rep.backtest.summary


def test_cross_sectional_metrics_present_for_panel() -> None:
    panel = make_synthetic_panel(n_days=600, n_assets=20, seed=0)
    strat = get_strategy("momentum")
    rep = run_research_study(panel, strat.signals, weight_fn=strat.weight_fn)
    assert rep.cross_sectional is True
    assert "mean_IC" in rep.ic.index


def test_combination_stage_runs_when_knowns_given() -> None:
    panel = make_synthetic_panel(n_days=600, n_assets=20, seed=2)
    strat = get_strategy("momentum")
    rep = run_research_study(
        panel,
        strat.signals,
        weight_fn=strat.weight_fn,
        knowns={"reversal": reversal_signal},
    )
    assert rep.combination is not None
    assert "raw_IC" in rep.combination.index
    assert "overlap_reversal" in rep.combination.index


def test_time_series_strategy_holds_directional_book() -> None:
    panel = make_synthetic_panel(n_days=500, n_assets=10, seed=3)
    strat = get_strategy("ts_momentum")
    rep = run_research_study(panel, strat.signals, weight_fn=strat.weight_fn)
    # Directional book: at least some dates carry a net (non-zero-sum) position.
    net_exposure = rep.backtest.weights.sum(axis=1).abs()
    assert float(net_exposure.max()) > 1e-6
