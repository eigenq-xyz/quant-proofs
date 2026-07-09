"""Cross-asset generalisation across the verified daily backtester.

Run the *same* signal across asset classes and compare, routed through the verified
event-driven backtester (``run_backtest``) so this path inherits the no-look-ahead
guarantee. Use when you own the underlying raw-price cross-section.

For the pre-built-return-stream variant (AQR's free TSMOM / Value-and-Momentum-Everywhere
monthly factors, which do NOT run through the verified backtester), see
``extensions/research-ideas/crossasset.py`` — that path is exploratory breadth evidence,
not a verified result, and deliberately lives outside this package.
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
    """Returns (summary table per asset class, correlation matrix of net-return streams).

    Routes each raw price panel through the verified daily backtester, so this path inherits the
    no-look-ahead guarantee.
    """
    summaries: dict[str, dict[str, float]] = {}
    net_streams: dict[str, pd.Series] = {}
    for name, panel in panels.items():
        res = run_backtest(panel, signal_fn, cost_bps=cost_bps)
        summaries[name] = res.summary
        net_streams[name] = res.net_returns
    summary_df = pd.DataFrame(summaries).T
    corr_df = pd.DataFrame(net_streams).corr()
    return summary_df, corr_df
