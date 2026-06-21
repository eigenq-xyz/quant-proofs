"""Out-of-sample walk-forward: split hygiene + runs."""

from __future__ import annotations

import numpy as np

from research_pipeline import make_synthetic_panel, momentum_signal
from research_pipeline.oos import run_walk_forward, walk_forward_splits


def test_splits_are_ordered_with_embargo() -> None:
    panel = make_synthetic_panel(n_days=600, n_assets=10, seed=2)
    embargo = 5
    splits = walk_forward_splits(panel.prices.index, n_splits=5, embargo=embargo)
    assert len(splits) >= 1
    for train, test in splits:
        # test starts strictly after train ends, with at least the embargo gap.
        gap = panel.prices.index.get_loc(test[0]) - panel.prices.index.get_loc(train[-1])
        assert gap >= embargo


def test_walk_forward_runs() -> None:
    panel = make_synthetic_panel(n_days=800, n_assets=20, seed=5)
    out = run_walk_forward(panel, momentum_signal, n_splits=5, embargo=5)
    assert np.isfinite(out["oos_sharpe"])  # type: ignore[arg-type]
    assert len(out["folds"]) >= 1  # type: ignore[arg-type]
