"""The desk workflow — orchestrate one end-to-end research study.

idea (a signal) -> data -> statistical testing -> portfolio + backtest -> evaluation.
Returns a structured ``StudyReport`` so a result can be read at a glance and audited stage
by stage. This is the integrative artifact: the individual stages live in their own modules.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .backtest import BacktestResult, SignalFn, run_backtest
from .data import PricePanel
from .evaluation import performance_summary
from .stats import deflated_sharpe_ratio, ic_decay, ic_summary, probabilistic_sharpe_ratio


@dataclass
class StudyReport:
    name: str
    ic: pd.Series  # ic_summary: mean/std/IR/HAC t-stat/hit-rate
    decay: pd.Series  # mean IC by horizon
    backtest: BacktestResult
    performance: pd.Series  # sharpe/return/vol/drawdown/calmar/...
    psr: float  # probabilistic Sharpe ratio
    dsr: float  # deflated Sharpe ratio (multiple-testing adjusted)


def run_research_study(
    panel: PricePanel,
    signal_fn: SignalFn,
    name: str = "signal",
    cost_bps: float = 10.0,
    n_trials: int = 1,
) -> StudyReport:
    """Run all stages for one signal. ``n_trials`` feeds the deflated Sharpe (how many
    variants were searched), so significance is honest about multiple testing."""
    signal = signal_fn(panel)
    fwd = panel.forward_returns(1)
    bt = run_backtest(panel, signal_fn, cost_bps=cost_bps)
    return StudyReport(
        name=name,
        ic=ic_summary(signal, fwd),
        decay=ic_decay(signal, panel),
        backtest=bt,
        performance=performance_summary(bt.net_returns),
        psr=probabilistic_sharpe_ratio(bt.net_returns),
        dsr=deflated_sharpe_ratio(bt.net_returns, n_trials=n_trials),
    )


def print_report(rep: StudyReport) -> None:
    print(f"================ research study: {rep.name} ================")
    print("\n[3] Signal statistics (IC)")
    print(rep.ic.round(4).to_string())
    print("\n[3] IC decay by horizon (days)")
    print(rep.decay.round(4).to_string())
    print("\n[5] Backtest (net of costs)")
    print("  ", rep.backtest)
    print("\n[6] Performance")
    print(rep.performance.round(4).to_string())
    print("\n[6] Significance (sample- and multiple-testing-adjusted)")
    print(f"  probabilistic_sharpe_ratio = {rep.psr:.3f}")
    print(f"  deflated_sharpe_ratio      = {rep.dsr:.3f}")
