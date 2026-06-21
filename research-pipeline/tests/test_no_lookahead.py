"""Runtime witness of the Lean ``NonAnticipating`` spec (``lean/ResearchPipeline/NoLookahead.lean``).

If a signal is non-anticipating, truncating the *future* of the price path must not change
the signal's values on the past. We assert exactly that.
"""

from __future__ import annotations

import numpy as np

from research_pipeline import make_synthetic_panel, momentum_signal, reversal_signal
from research_pipeline.signals import conditional_scale


def _assert_no_lookahead(signal_fn) -> None:  # type: ignore[no-untyped-def]
    panel = make_synthetic_panel(n_days=500, n_assets=20, seed=1)
    cutoff = panel.prices.index[400]

    full = signal_fn(panel)
    truncated = signal_fn(panel.as_of(cutoff))  # only data <= cutoff

    shared = truncated.index.intersection(full.index)
    a, b = full.loc[shared], truncated.loc[shared]
    both_valid = a.notna() & b.notna()
    assert np.allclose(a.values[both_valid.values], b.values[both_valid.values])


def test_momentum_no_lookahead() -> None:
    _assert_no_lookahead(momentum_signal)


def test_reversal_no_lookahead() -> None:
    _assert_no_lookahead(reversal_signal)


def test_conditional_no_lookahead() -> None:
    def fn(panel):  # type: ignore[no-untyped-def]
        return conditional_scale(momentum_signal(panel), panel)

    _assert_no_lookahead(fn)
