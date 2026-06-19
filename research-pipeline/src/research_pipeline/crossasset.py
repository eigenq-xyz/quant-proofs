"""Cross-asset generalisation study.

Run the *same* signal + pipeline across asset classes and compare. A structural effect
should appear wherever its driver exists; single-market-only results are a data-mining
red flag. Going cross-asset multiplies the multiple-testing problem, so deflated-Sharpe
discipline matters more here (see ``stats.deflated_sharpe_ratio``).
"""

from __future__ import annotations

import pandas as pd

from .backtest import SignalFn, run_backtest
from .data import PricePanel


def run_cross_asset(
    panels: dict[str, PricePanel],
    signal_fn: SignalFn,
    cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (summary table per asset class, correlation matrix of net-return streams)."""
    summaries: dict[str, dict[str, float]] = {}
    net_streams: dict[str, pd.Series] = {}
    for name, panel in panels.items():
        res = run_backtest(panel, signal_fn, cost_bps=cost_bps)
        summaries[name] = res.summary
        net_streams[name] = res.net_returns
    summary_df = pd.DataFrame(summaries).T
    corr_df = pd.DataFrame(net_streams).corr()
    return summary_df, corr_df
