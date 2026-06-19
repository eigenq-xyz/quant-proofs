"""research_pipeline — a full quant-research-desk workflow with verified load-bearing steps.

Stages (idea -> data -> signal -> statistical testing -> portfolio -> backtest -> evaluation
-> cross-asset), orchestrated by ``study.run_research_study``. The backtesting stage carries a
formal no-look-ahead guarantee (Lean ``ResearchPipeline.NonAnticipating``); the statistical
layer is unverified but rigorous — it is where numpy/pandas/scipy discipline is demonstrated.
"""

from .data import PricePanel, make_synthetic_panel
from .signals import momentum_signal, reversal_signal, conditional_scale
from .stats import (
    ic_summary,
    ic_decay,
    mean_ic,
    newey_west_tstat,
    signal_correlation,
    bootstrap_sharpe_ci,
    probabilistic_sharpe_ratio,
    deflated_sharpe_ratio,
    permutation_ic_test,
)
from .oos import walk_forward_splits, run_walk_forward
from .validation import detection_rate, false_positive_rate, boundary_lookahead_discrepancy
from .portfolio import signal_to_weights, verified_pgd_weights
from .costs import proportional_cost
from .backtest import BacktestResult, run_backtest
from .evaluation import (
    performance_summary,
    max_drawdown,
    sharpe,
    turnover,
    factor_attribution,
)
from .crossasset import run_cross_asset
from .study import StudyReport, run_research_study, print_report

__all__ = [
    "PricePanel",
    "make_synthetic_panel",
    "momentum_signal",
    "reversal_signal",
    "conditional_scale",
    "ic_summary",
    "ic_decay",
    "mean_ic",
    "newey_west_tstat",
    "signal_correlation",
    "bootstrap_sharpe_ci",
    "probabilistic_sharpe_ratio",
    "deflated_sharpe_ratio",
    "permutation_ic_test",
    "walk_forward_splits",
    "run_walk_forward",
    "detection_rate",
    "false_positive_rate",
    "boundary_lookahead_discrepancy",
    "signal_to_weights",
    "verified_pgd_weights",
    "proportional_cost",
    "BacktestResult",
    "run_backtest",
    "performance_summary",
    "max_drawdown",
    "sharpe",
    "turnover",
    "factor_attribution",
    "run_cross_asset",
    "StudyReport",
    "run_research_study",
    "print_report",
]
