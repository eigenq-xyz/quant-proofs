"""Property-based verification contracts (hypothesis).

Bridges the exact Lean / analytic claims to the floating-point implementation across many
random inputs: estimator sanity, accounting integrity, and the no-leakage contract that
mirrors the Lean ``embargo_blocks_label_leakage`` theorem on the splits actually produced.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from hypothesis import given, settings
from hypothesis import strategies as st

from research_pipeline import make_synthetic_panel, momentum_signal, run_backtest
from research_pipeline.oos import leakage_gap, walk_forward_splits
from research_pipeline.stats import (
    deflated_sharpe_ratio,
    mean_ic,
    probabilistic_sharpe_ratio,
)

# --- estimator sanity -------------------------------------------------------


@settings(max_examples=60, deadline=None)
@given(seed=st.integers(0, 10**6), n=st.integers(40, 300))
def test_psr_in_unit_interval(seed: int, n: int) -> None:
    rng = np.random.default_rng(seed)
    psr = probabilistic_sharpe_ratio(pd.Series(rng.normal(0.0, 0.01, n)))
    assert np.isnan(psr) or (0.0 <= psr <= 1.0)


@settings(max_examples=60, deadline=None)
@given(
    seed=st.integers(0, 10**6),
    n=st.integers(40, 300),
    k1=st.integers(1, 30),
    k2=st.integers(1, 30),
)
def test_deflated_sharpe_monotone_in_trials(seed: int, n: int, k1: int, k2: int) -> None:
    rng = np.random.default_rng(seed)
    r = pd.Series(rng.normal(0.0005, 0.01, n))
    lo, hi = sorted((k1, k2))
    d_lo, d_hi = deflated_sharpe_ratio(r, n_trials=lo), deflated_sharpe_ratio(r, n_trials=hi)
    if np.isnan(d_lo) or np.isnan(d_hi):
        return
    # More variants searched => a weakly higher bar => weakly lower significance.
    assert d_hi <= d_lo + 1e-9


@settings(max_examples=30, deadline=None)
@given(seed=st.integers(0, 1000))
def test_mean_ic_bounded(seed: int) -> None:
    panel = make_synthetic_panel(n_days=400, n_assets=12, seed=seed)
    ic = mean_ic(momentum_signal(panel), panel.forward_returns(1))
    assert np.isnan(ic) or (-1.0 <= ic <= 1.0)


# --- accounting integrity ---------------------------------------------------


@settings(max_examples=30, deadline=None)
@given(seed=st.integers(0, 1000), cost_bps=st.floats(0.0, 50.0))
def test_costs_are_non_negative(seed: int, cost_bps: float) -> None:
    panel = make_synthetic_panel(n_days=400, n_assets=12, seed=seed)
    bt = run_backtest(panel, momentum_signal, cost_bps=cost_bps)
    # Accounting identity: net = gross - cost with cost >= 0, so net <= gross everywhere.
    assert float((bt.gross_returns - bt.net_returns).min()) >= -1e-12


# --- no-leakage contract (mirrors the Lean theorem) -------------------------


@settings(max_examples=120, deadline=None)
@given(
    n=st.integers(60, 400),
    n_splits=st.integers(2, 6),
    embargo=st.integers(0, 10),
    horizon=st.integers(1, 5),
)
def test_no_leakage_iff_embargo_at_least_horizon(
    n: int, n_splits: int, embargo: int, horizon: int
) -> None:
    idx = pd.RangeIndex(n)
    splits = walk_forward_splits(idx, n_splits=n_splits, embargo=embargo)
    if not splits:
        return
    gap = leakage_gap(idx, splits, horizon)
    # The runtime witness agrees exactly with embargo_blocks_label_leakage:
    # the splits are leakage-free iff the embargo is at least the label horizon.
    assert (gap >= 1) == (embargo >= horizon)
