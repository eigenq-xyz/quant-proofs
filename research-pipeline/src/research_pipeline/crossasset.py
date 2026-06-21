"""Cross-asset generalisation study.

Run the *same* signal across asset classes and compare. A structural effect should appear
wherever its driver exists; single-market-only results are a data-mining red flag. Going
cross-asset multiplies the multiple-testing problem, so deflated-Sharpe discipline matters more
here (see ``stats.deflated_sharpe_ratio``).

Two entry points, by what the data gives you:

- ``run_cross_asset(panels, signal_fn)`` — raw price ``PricePanel``s per asset class, routed
  through the **verified** daily event-driven backtester (``run_backtest``). Use when you own
  the underlying cross-section.
- ``analyze_return_streams(streams)`` — already-built factor *return streams* per asset class
  (e.g. AQR's free TSMOM / Value-and-Momentum-Everywhere monthly factors). These do **not** run
  through the verified backtester.

VERIFICATION-SCOPE CAVEAT (read before quoting these numbers): the no-look-ahead theorem covers
the daily event-driven backtester only. ``analyze_return_streams`` consumes pre-built return
streams that never touch that engine, so its output is **breadth/generalisation evidence**, not
a verified result. Never let "verified" stretch over runs the proof did not cover; scope that
claim to the daily equity backtest.
"""

from __future__ import annotations

import pandas as pd

from .backtest import SignalFn, run_backtest
from .data import PricePanel
from .evaluation import performance_summary
from .stats import deflated_sharpe_ratio


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


def analyze_return_streams(
    streams: dict[str, pd.Series],
    periods_per_year: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-asset-class performance + multiple-testing-adjusted significance from return streams.

    ``streams`` maps an asset-class name to its periodic return series (decimals), e.g. AQR's
    per-asset-class TSMOM or VME momentum factors (``periods_per_year=12`` for monthly). For each
    class this computes the standard performance summary (annualised Sharpe, return, vol,
    drawdown, ...) and a **deflated Sharpe ratio** whose ``n_trials`` equals the number of asset
    classes tested, so significance is honest about searching across classes. Also returns the
    cross-asset correlation table of the return streams, the evidence for a common-factor /
    structural reading of the effect.

    Returns ``(summary_df, corr_df)``: ``summary_df`` is indexed by asset class with the
    performance columns plus ``deflated_sharpe``; ``corr_df`` is the pairwise correlation matrix.

    NOT routed through the verified backtester. These are pre-built factor return streams, so the
    output is generalisation evidence, not a verified no-look-ahead result.
    """
    if not streams:
        raise ValueError("analyze_return_streams requires at least one return stream")
    n_trials = len(streams)
    summaries: dict[str, dict[str, float]] = {}
    for name, series in streams.items():
        perf = performance_summary(series, periods_per_year=periods_per_year)
        row = {str(k): float(v) for k, v in perf.items()}
        row["deflated_sharpe"] = deflated_sharpe_ratio(
            series, n_trials=n_trials, periods_per_year=periods_per_year
        )
        summaries[name] = row
    summary_df = pd.DataFrame(summaries).T
    corr_df = pd.DataFrame(streams).corr()
    return summary_df, corr_df
