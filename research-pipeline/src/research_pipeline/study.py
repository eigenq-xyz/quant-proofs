"""The desk workflow — orchestrate one end-to-end research study.

idea (a signal) -> data -> statistical testing -> portfolio + backtest -> evaluation.
Returns a structured ``StudyReport`` so a result can be read at a glance and audited stage
by stage. This is the integrative artifact: the individual stages live in their own modules.

Cross-sectional diagnostics (IC, IC decay) are **opt-in**: they require a cross-section of
names and are meaningless for a single-asset / time-series alpha, so they are computed only
when the panel is cross-sectional (auto-detected, overridable). The combination /
incrementality stage runs when a set of known signals is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .backtest import BacktestResult, SignalFn, WeightFn, run_backtest
from .combination import incremental_ic, signal_overlap
from .data import PricePanel
from .evaluation import performance_summary
from .portfolio import signal_to_weights
from .stats import deflated_sharpe_ratio, ic_decay, ic_summary, probabilistic_sharpe_ratio


@dataclass
class StudyReport:
    name: str
    backtest: BacktestResult
    performance: pd.Series  # sharpe/return/vol/drawdown/calmar/...
    psr: float  # probabilistic Sharpe ratio
    dsr: float  # deflated Sharpe ratio (multiple-testing adjusted)
    cross_sectional: bool = True
    ic: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))  # empty if not X-sec
    decay: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    combination: pd.Series | None = None  # incremental IC + overlap vs known signals


def run_research_study(
    panel: PricePanel,
    signal_fn: SignalFn,
    name: str = "signal",
    cost_bps: float = 10.0,
    n_trials: int = 1,
    weight_fn: WeightFn = signal_to_weights,
    horizon: int = 1,
    knowns: dict[str, SignalFn] | None = None,
    cross_sectional: bool | None = None,
) -> StudyReport:
    """Run all stages for one signal. ``n_trials`` feeds the deflated Sharpe (how many
    variants were searched), so significance is honest about multiple testing.

    ``weight_fn`` selects portfolio construction; ``knowns`` (name -> signal fn) turns on the
    combination / incrementality stage; ``cross_sectional`` overrides the auto-detection that
    gates the IC diagnostics (default: panel has >= 3 assets).
    """
    signal = signal_fn(panel)
    fwd = panel.forward_returns(horizon)
    is_xsec = (panel.prices.shape[1] >= 3) if cross_sectional is None else cross_sectional
    bt = run_backtest(panel, signal_fn, cost_bps=cost_bps, weight_fn=weight_fn, horizon=horizon)

    combination: pd.Series | None = None
    if knowns:
        known_signals = {nm: fn(panel) for nm, fn in knowns.items()}
        inc = incremental_ic(signal, known_signals, fwd)
        overlap = signal_overlap(signal, known_signals).rename(index=lambda k: f"overlap_{k}")
        combination = pd.concat([inc, overlap])

    return StudyReport(
        name=name,
        backtest=bt,
        performance=performance_summary(bt.net_returns),
        psr=probabilistic_sharpe_ratio(bt.net_returns),
        dsr=deflated_sharpe_ratio(bt.net_returns, n_trials=n_trials),
        cross_sectional=is_xsec,
        ic=ic_summary(signal, fwd) if is_xsec else pd.Series(dtype=float),
        decay=ic_decay(signal, panel) if is_xsec else pd.Series(dtype=float),
        combination=combination,
    )


def print_report(rep: StudyReport) -> None:
    print(f"================ research study: {rep.name} ================")
    if rep.cross_sectional:
        print("\n[3] Signal statistics (IC)")
        print(rep.ic.round(4).to_string())
        print("\n[3] IC decay by horizon (days)")
        print(rep.decay.round(4).to_string())
    else:
        print("\n[3] Signal statistics (IC): n/a (non-cross-sectional alpha)")
    if rep.combination is not None:
        print("\n[4] Combination / incrementality vs known signals")
        print(rep.combination.round(4).to_string())
    print("\n[5] Backtest (net of costs)")
    print("  ", rep.backtest)
    print("\n[6] Performance")
    print(rep.performance.round(4).to_string())
    print("\n[6] Significance (sample- and multiple-testing-adjusted)")
    print(f"  probabilistic_sharpe_ratio = {rep.psr:.3f}")
    print(f"  deflated_sharpe_ratio      = {rep.dsr:.3f}")
