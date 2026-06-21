"""Combination / incrementality — does a candidate add information beyond known factors?

The question a research desk asks of every "new" signal: is it incremental, or just a known
factor (momentum, value, ...) in disguise? Two complementary views:

- **Overlap** (``signal_overlap``): average cross-sectional correlation of the candidate to
  each known signal. High overlap is a red flag on its own.
- **Incremental IC** (``incremental_ic``): orthogonalise the candidate against the known
  signals cross-sectionally (OLS residual, per date), then measure the residual's IC. The
  fraction of raw IC that survives orthogonalisation is the information the candidate adds
  *beyond* the known set. A signal can be highly correlated to a known factor yet still
  carry incremental IC, and vice versa, so both views matter.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .stats import mean_ic, signal_correlation


def signal_overlap(candidate: pd.DataFrame, knowns: dict[str, pd.DataFrame]) -> pd.Series:
    """Average cross-sectional correlation of ``candidate`` to each known signal."""
    return pd.Series(
        {name: signal_correlation(candidate, known) for name, known in knowns.items()},
        name="overlap",
    )


def _residualize(candidate: pd.DataFrame, knowns: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Per-date OLS residual of the candidate cross-section on the known cross-sections."""
    dates = candidate.index
    for known in knowns.values():
        dates = dates.intersection(known.index)
    names = list(knowns)
    out: dict[object, pd.Series] = {}
    for t in dates:
        frame = pd.concat(
            [candidate.loc[t].rename("c")] + [knowns[n].loc[t].rename(n) for n in names],
            axis=1,
        ).dropna()
        if len(frame) < len(names) + 2:
            continue
        y = frame["c"].to_numpy(dtype=float)
        x = np.column_stack([np.ones(len(frame))] + [frame[n].to_numpy(dtype=float) for n in names])
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        out[t] = pd.Series(y - x @ beta, index=frame.index)
    return pd.DataFrame(out).T


def incremental_ic(
    candidate: pd.DataFrame,
    knowns: dict[str, pd.DataFrame],
    fwd_returns: pd.DataFrame,
) -> pd.Series:
    """Raw vs orthogonalised IC: how much of the candidate's IC survives the known set.

    ``IC_retained`` near 1 means the candidate's predictive power is largely incremental;
    near 0 means it is explained away by the known factors.
    """
    raw = mean_ic(candidate, fwd_returns)
    residual = mean_ic(_residualize(candidate, knowns), fwd_returns)
    retained = residual / raw if np.isfinite(raw) and raw != 0.0 else float("nan")
    return pd.Series(
        {"raw_IC": raw, "residual_IC": residual, "IC_retained": retained},
        name="incremental_IC",
    )
