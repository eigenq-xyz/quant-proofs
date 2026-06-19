"""Stage 5 — backtest. Event-driven, no-look-ahead, net-of-cost engine (the verified stage).

Alignment guarantee (the runtime face of ``ResearchPipeline.NonAnticipating``): weights at
date ``t`` are formed from ``signal(t)`` — a function of prices ``≤ t`` — and earn the
realised forward return over ``(t, t+1]``. Decision information and future returns never overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import pandas as pd

from .costs import proportional_cost
from .data import PricePanel
from .evaluation import sharpe, turnover
from .portfolio import signal_to_weights
from .stats import mean_ic

SignalFn = Callable[[PricePanel], pd.DataFrame]
WeightFn = Callable[..., pd.Series]


@dataclass
class BacktestResult:
    gross_returns: pd.Series
    net_returns: pd.Series
    weights: pd.DataFrame
    summary: dict[str, float]

    def __repr__(self) -> str:
        s = self.summary
        return (
            f"BacktestResult(net_sharpe={s['net_sharpe']:.2f}, "
            f"gross_sharpe={s['gross_sharpe']:.2f}, mean_IC={s['mean_IC']:.3f}, "
            f"avg_turnover={s['avg_turnover']:.3f}, n_days={int(s['n_days'])})"
        )


def run_backtest(
    panel: PricePanel,
    signal_fn: SignalFn,
    cost_bps: float = 10.0,
    gross: float = 1.0,
    weight_fn: WeightFn = signal_to_weights,
) -> BacktestResult:
    signal = signal_fn(panel)
    fwd = panel.forward_returns(1)
    dates = signal.dropna(how="all").index.intersection(fwd.index)

    assets = panel.assets
    weights: dict[object, pd.Series] = {}
    gross_rets: dict[object, float] = {}
    net_rets: dict[object, float] = {}
    prev_w = pd.Series(0.0, index=assets)

    for t in dates:
        w = weight_fn(signal.loc[t], gross=gross).reindex(assets).fillna(0.0)
        fr = fwd.loc[t].reindex(assets)
        gr = float((w * fr).sum())  # NaN forward returns (e.g. last day) drop out of the sum
        cost = proportional_cost(prev_w, w, cost_bps)
        weights[t] = w
        gross_rets[t] = gr
        net_rets[t] = gr - cost
        prev_w = w

    weights_df = pd.DataFrame(weights).T
    gross_s = pd.Series(gross_rets)
    net_s = pd.Series(net_rets)

    summary: dict[str, float] = {
        "gross_sharpe": sharpe(gross_s),
        "net_sharpe": sharpe(net_s),
        "mean_IC": mean_ic(signal, fwd),
        "avg_turnover": turnover(weights_df),
        "cum_net_return": float((1.0 + net_s).prod() - 1.0),
        "n_days": float(len(net_s)),
    }
    return BacktestResult(gross_s, net_s, weights_df, summary)
