"""Track 1 — validate the pipeline itself ("validate the validator").

A/B / synthetic-truth harness: plant a *known* alpha and confirm the pipeline detects it;
feed pure noise and confirm it reports null; inject a look-ahead bug and confirm the guard
catches it. These functions answer "does the pipeline do what it claims?" before any real
study trusts its numbers.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from .data import PricePanel
from .stats import _rank_ic_series, newey_west_tstat

SignalFn = Callable[[PricePanel], pd.DataFrame]


def make_predictable_panel(
    n_days: int, n_assets: int, beta: float, noise: float = 0.01, seed: int = 0
) -> tuple[PricePanel, pd.DataFrame]:
    """Ground-truth construction: a hidden score ``X`` (AR(1), known at ``t``) drives the
    *forward* return ``r_{t->t+1} = beta * X_t + eps``. Returns the price panel AND the true
    non-anticipating signal ``X``. ``beta = 0`` => pure noise (no alpha)."""
    rng = np.random.default_rng(seed)
    x = np.zeros((n_days, n_assets))
    for t in range(1, n_days):
        x[t] = 0.95 * x[t - 1] + rng.normal(0.0, 0.05, n_assets)
    x = x - x.mean(axis=1, keepdims=True)  # cross-sectionally demeaned score
    fwd = beta * x + rng.normal(0.0, noise, (n_days, n_assets))  # fwd[t] = ret (t -> t+1)
    ret = np.zeros((n_days, n_assets))
    ret[1:] = fwd[:-1]  # realise the forward return on the next day
    prices = 100.0 * np.cumprod(1.0 + ret, axis=0)
    dates = pd.bdate_range("2015-01-01", periods=n_days)
    cols = [f"A{i:03d}" for i in range(n_assets)]
    panel = PricePanel(pd.DataFrame(prices, index=dates, columns=cols))
    signal = pd.DataFrame(x, index=dates, columns=cols)
    return panel, signal


def signal_fn_from(signal_df: pd.DataFrame) -> SignalFn:
    """Wrap a precomputed (non-anticipating) signal as a pipeline ``SignalFn``."""

    def fn(panel: PricePanel) -> pd.DataFrame:
        return signal_df.reindex(index=panel.prices.index)

    return fn


def leaky_signal(panel: PricePanel) -> pd.DataFrame:
    """A deliberately BUGGED signal: it uses next-day returns (the future). The
    no-look-ahead guard must catch this."""
    return panel.forward_returns(1)


def boundary_lookahead_discrepancy(
    signal_fn: SignalFn, panel: PricePanel, n_cutoffs: int = 20
) -> float:
    """Max change in the time-``c`` signal value when the panel is truncated at ``c`` vs full.

    Zero for a non-anticipating signal; positive if the signal peeks past ``c`` (this is the
    strict, boundary version of the no-look-ahead check — a one-day leak only shows at ``c``).
    """
    full = signal_fn(panel)
    idx = panel.prices.index
    positions = np.linspace(60, len(idx) - 2, n_cutoffs).astype(int)
    worst = 0.0
    for c in idx[positions]:
        trunc = signal_fn(panel.as_of(c))
        if c not in full.index or c not in trunc.index:
            continue
        a, b = full.loc[c], trunc.loc[c]
        common = a.dropna().index.intersection(b.dropna().index)
        if len(common):
            worst = max(worst, float((a[common] - b[common]).abs().max()))
        missing = a.notna() & ~b.reindex(a.index).notna()
        if missing.any():
            worst = max(worst, float(a[missing].abs().max()))
    return worst


def _significant(panel: PricePanel, signal_df: pd.DataFrame, tstat_thresh: float) -> bool:
    ic = _rank_ic_series(signal_fn_from(signal_df)(panel), panel.forward_returns(1))
    t = newey_west_tstat(ic)
    return bool(np.isfinite(t) and abs(t) > tstat_thresh)


def detection_rate(
    beta: float,
    n_runs: int = 20,
    n_days: int = 400,
    n_assets: int = 20,
    tstat_thresh: float = 1.96,
    base_seed: int = 0,
) -> float:
    """Fraction of independent runs in which the pipeline flags the planted alpha
    significant (two-sided, HAC). High at strong ``beta`` = good statistical power."""
    hits = sum(
        _significant(
            *make_predictable_panel(n_days, n_assets, beta, seed=base_seed + s), tstat_thresh
        )
        for s in range(n_runs)
    )
    return hits / n_runs


def false_positive_rate(
    n_runs: int = 40,
    n_days: int = 400,
    n_assets: int = 20,
    tstat_thresh: float = 1.96,
    base_seed: int = 1000,
) -> float:
    """Detection rate under ``beta = 0`` (pure noise). Should sit near the nominal 5%."""
    return detection_rate(0.0, n_runs, n_days, n_assets, tstat_thresh, base_seed)
