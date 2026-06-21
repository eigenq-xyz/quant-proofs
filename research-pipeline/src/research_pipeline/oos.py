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


def leakage_gap(index: pd.Index, splits: list[tuple[pd.Index, pd.Index]], horizon: int = 1) -> int:
    """Minimum slack (in index positions) between a training label's forward window and the
    first test index, over all splits.

    Runtime witness of the Lean ``ResearchPipeline.embargo_blocks_label_leakage`` contract on
    the splits actually produced: ``slack = first_test_pos - (last_train_pos + horizon)``.
    ``slack >= 1`` for every split means no training label bleeds into its test window;
    ``slack <= 0`` means a label leaks. Returns the minimum (the worst case).
    """
    slacks: list[int] = []
    for train, test in splits:
        if len(train) == 0 or len(test) == 0:
            continue
        last_train_pos = int(index.get_indexer(pd.Index([train[-1]]))[0])
        first_test_pos = int(index.get_indexer(pd.Index([test[0]]))[0])
        slacks.append(first_test_pos - (last_train_pos + horizon))
    return min(slacks) if slacks else 0


def no_leakage_holds(
    index: pd.Index, splits: list[tuple[pd.Index, pd.Index]], horizon: int = 1
) -> bool:
    """True iff no training label leaks into any test window (``leakage_gap >= 1``)."""
    return leakage_gap(index, splits, horizon) >= 1


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
