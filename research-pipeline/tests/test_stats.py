"""Statistical-layer sanity checks."""

from __future__ import annotations

import numpy as np
import pandas as pd

from research_pipeline import (
    deflated_sharpe_ratio,
    factor_attribution,
    ic_summary,
    make_synthetic_panel,
    momentum_signal,
    probabilistic_sharpe_ratio,
    run_backtest,
)
from research_pipeline.stats import newey_west_tstat


def test_ic_summary_positive_and_significant_on_synthetic() -> None:
    panel = make_synthetic_panel(n_days=800, n_assets=30, seed=5)
    summ = ic_summary(momentum_signal(panel), panel.forward_returns(1))
    assert summ["mean_IC"] > 0
    assert np.isfinite(summ["IC_tstat_NW"])


def test_newey_west_tstat_small_for_iid_noise() -> None:
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(0.0, 1.0, 2000))
    assert abs(newey_west_tstat(x)) < 3.0  # mean is ~0, should not look significant


def test_psr_dsr_in_unit_interval() -> None:
    panel = make_synthetic_panel(n_days=800, n_assets=30, seed=6)
    bt = run_backtest(panel, momentum_signal)
    psr = probabilistic_sharpe_ratio(bt.net_returns)
    dsr = deflated_sharpe_ratio(bt.net_returns, n_trials=20)
    assert 0.0 <= psr <= 1.0
    assert 0.0 <= dsr <= 1.0
    assert dsr <= psr + 1e-9  # deflation can only lower significance


def test_factor_attribution_recovers_beta() -> None:
    rng = np.random.default_rng(0)
    mkt = pd.Series(rng.normal(0.0, 0.01, 500))
    strat = 0.5 * mkt + pd.Series(rng.normal(0.0, 1e-6, 500))
    out = factor_attribution(strat, pd.DataFrame({"mkt": mkt}))
    assert abs(out["beta_mkt"] - 0.5) < 0.05
    assert abs(out["alpha"]) < 1e-3
