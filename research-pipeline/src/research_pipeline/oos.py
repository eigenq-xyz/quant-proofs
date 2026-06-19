"""Out-of-sample evaluation — expanding walk-forward with an embargo (purge) gap.

In-sample Sharpe is not evidence. This evaluates net returns only on held-out windows that
start an ``embargo`` gap after the training data ends, so the one-step label horizon cannot
leak across the split. Concatenated test windows give a single honest OOS track record.
"""

from __future__ import annotations

import pandas as pd

from .backtest import SignalFn, run_backtest
from .data import PricePanel
from .evaluation import sharpe


def walk_forward_splits(
    index: pd.Index, n_splits: int = 5, embargo: int = 5
) -> list[tuple[pd.Index, pd.Index]]:
    """Expanding (train, test) date splits with an embargo gap between train end and test start."""
    n = len(index)
    fold = n // (n_splits + 1)
    splits: list[tuple[pd.Index, pd.Index]] = []
    for k in range(1, n_splits + 1):
        train_end = fold * k
        test_start = train_end + embargo
        test_end = min(fold * (k + 1), n)
        if test_start >= test_end:
            continue
        splits.append((index[:train_end], index[test_start:test_end]))
    return splits


def run_walk_forward(
    panel: PricePanel,
    signal_fn: SignalFn,
    n_splits: int = 5,
    embargo: int = 5,
    cost_bps: float = 10.0,
) -> dict[str, object]:
    """Backtest each held-out window, concatenate the OOS net returns, report per-fold + overall."""
    splits = walk_forward_splits(panel.prices.index, n_splits, embargo)
    oos_chunks: list[pd.Series] = []
    folds: list[dict[str, object]] = []
    for _train, test in splits:
        sub = PricePanel(panel.prices.loc[: test[-1]])
        res = run_backtest(sub, signal_fn, cost_bps=cost_bps)
        oos_ret = res.net_returns.reindex(test).dropna()
        oos_chunks.append(oos_ret)
        folds.append({"test_start": test[0], "test_end": test[-1], "net_sharpe": sharpe(oos_ret)})
    oos_all = pd.concat(oos_chunks) if oos_chunks else pd.Series(dtype=float)
    return {
        "oos_net_returns": oos_all,
        "oos_sharpe": sharpe(oos_all),
        "folds": pd.DataFrame(folds),
    }
