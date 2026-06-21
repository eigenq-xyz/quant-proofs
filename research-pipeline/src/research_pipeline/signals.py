"""Stage 2 — signals. Alpha construction, non-anticipating by construction.

Every signal's value at date ``t`` is a function of prices at dates ``≤ t`` only; this is
the runtime instance of the Lean ``ResearchPipeline.NonAnticipating`` predicate, checked
empirically in ``tests/test_no_lookahead.py``. Signals are cross-sectionally demeaned so
the book is dollar-neutral. Known effects (momentum, reversal) are used as controls.
"""

from __future__ import annotations

import pandas as pd

from .data import PricePanel


def _cross_sectional_demean(sig: pd.DataFrame) -> pd.DataFrame:
    return sig.sub(sig.mean(axis=1), axis=0)


def momentum_signal(panel: PricePanel, lookback: int = 252, skip: int = 21) -> pd.DataFrame:
    """12-1 momentum: return from ``t-lookback`` to ``t-skip`` (both ``≤ t``)."""
    p = panel.prices
    raw = p.shift(skip) / p.shift(lookback) - 1.0
    return _cross_sectional_demean(raw)


def ts_momentum_signal(panel: PricePanel, lookback: int = 252, skip: int = 21) -> pd.DataFrame:
    """Time-series (absolute) momentum: an asset's OWN trailing return ``t-lookback -> t-skip``.

    Not cross-sectionally demeaned, so it expresses a directional (net long/short) view and
    works for a single asset. Pair with the ``directional`` portfolio constructor; demeaning
    it would collapse a single-asset book to zero. Non-anticipating (uses prices ``<= t``).
    """
    p = panel.prices
    return p.shift(skip) / p.shift(lookback) - 1.0


def reversal_signal(panel: PricePanel, lookback: int = 21) -> pd.DataFrame:
    """Short-term reversal: negative of the last ``lookback``-day return."""
    p = panel.prices
    raw = -(p / p.shift(lookback) - 1.0)
    return _cross_sectional_demean(raw)


def conditional_scale(
    signal: pd.DataFrame, panel: PricePanel, vol_window: int = 63
) -> pd.DataFrame:
    """Conditional twist: damp the signal in high-volatility regimes.

    The regime indicator uses only past returns (``≤ t``), so the result stays
    non-anticipating. ROADMAP: replace ``1/(1+vol)`` with a real regime/state model.
    """
    realized_vol = panel.simple_returns().rolling(vol_window).std()
    scale = 1.0 / (1.0 + realized_vol)
    return _cross_sectional_demean(signal * scale)
