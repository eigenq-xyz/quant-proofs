"""Transaction-cost model. Evaluation is net-of-cost, always."""

from __future__ import annotations

import pandas as pd


def proportional_cost(prev_w: pd.Series, new_w: pd.Series, cost_bps: float) -> float:
    """Cost = ``(bps/1e4) * one-way turnover`` = ``(bps/1e4) * sum|Δw|``.

    Future work: replace with spread + square-root market-impact for capacity realism.
    """
    idx = prev_w.index.union(new_w.index)
    dw = new_w.reindex(idx).fillna(0.0) - prev_w.reindex(idx).fillna(0.0)
    return float(cost_bps / 1e4 * dw.abs().sum())
