"""Combination / incrementality tests.

Two deterministic invariants pin down the stage: a signal regressed against ITSELF retains
no incremental IC (the residual is identically zero, so its IC is undefined/NaN), while a
signal orthogonalised against a genuinely unrelated (random) factor keeps essentially all of
its IC.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research_pipeline import incremental_ic, make_synthetic_panel, signal_overlap
from research_pipeline.signals import momentum_signal


def test_signal_against_itself_has_no_increment() -> None:
    panel = make_synthetic_panel(n_days=600, n_assets=25, seed=0)
    sig = momentum_signal(panel)
    fwd = panel.forward_returns(1)
    overlap = signal_overlap(sig, {"self": sig})
    assert abs(float(overlap["self"]) - 1.0) < 1e-6
    inc = incremental_ic(sig, {"self": sig}, fwd)
    # Orthogonalising a signal against itself leaves an all-zero residual: no information.
    residual = float(inc["residual_IC"])
    assert np.isnan(residual) or abs(residual) < 0.02


def test_unrelated_known_preserves_increment() -> None:
    panel = make_synthetic_panel(n_days=800, n_assets=30, seed=1)
    candidate = momentum_signal(panel)
    fwd = panel.forward_returns(1)
    # A purely random factor, independent of returns: cannot explain the candidate's IC.
    rng = np.random.default_rng(7)
    noise = pd.DataFrame(
        rng.normal(size=candidate.shape), index=candidate.index, columns=candidate.columns
    )
    overlap = signal_overlap(candidate, {"noise": noise})
    assert abs(float(overlap["noise"])) < 0.1  # essentially uncorrelated
    inc = incremental_ic(candidate, {"noise": noise}, fwd)
    assert np.isfinite(inc["raw_IC"]) and inc["raw_IC"] != 0.0
    # Almost all of the candidate's IC survives orthogonalisation against noise.
    assert float(inc["IC_retained"]) > 0.8
