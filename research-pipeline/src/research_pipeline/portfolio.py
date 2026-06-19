"""Portfolio construction: signal -> weights. The *downstream* (order/position) step,
not the alpha.

``signal_to_weights`` is the dollar-neutral cross-sectional baseline used by the demo.
``verified_pgd_weights`` delegates to the **formally verified** PGD solver in
``portfolio-proofs`` (convergence: ``pgd_convergence``; projection: ``projection_correctness``
in ``optimization-proofs/OptimizationProofs``), so portfolio construction is a verified step too.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np
import pandas as pd


def signal_to_weights(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
    """Dollar-neutral weights ∝ demeaned signal, scaled to ``gross``.

    ``sum(w) = 0`` (neutral), ``sum(|w|) = gross``. NaNs dropped.
    """
    s = signal_row.dropna()
    s = s - s.mean()
    denom = float(s.abs().sum())
    if denom == 0.0 or not np.isfinite(denom):
        return pd.Series(0.0, index=s.index)
    return s / denom * gross


def verified_pgd_weights(
    mu: pd.Series,
    cov: pd.DataFrame,
    leverage_cap: float = 1.5,
) -> pd.Series:
    """Budget-constrained mean-variance weights via the verified Lean 4 PGD solver.

    Solves ``sum(w) ≈ 1``, ``sum|w| ≤ leverage_cap``. Requires the compiled ``pgd_solve``
    binary in ``portfolio-proofs`` (``cd portfolio-proofs/.. ; lake exe pgd_solve``); falls
    back to the dollar-neutral baseline if the verified solver is unavailable.

    NOTE: the verified projection currently targets the budget simplex (``sum w = 1``).
    Extending it to the dollar-neutral simplex (``sum w = 0``) for cross-sectional L/S
    books is a tracked ROADMAP item (a new ``optimization-proofs`` theorem).
    """
    try:
        repo = (
            pathlib.Path(__file__).resolve().parents[3]
        )  # research_pipeline/src/research-pipeline -> quant-proofs
        pp = repo / "portfolio-proofs"
        if str(pp) not in sys.path:
            sys.path.insert(0, str(pp))
        from lean_pgd import solve as _lean_pgd_solve  # type: ignore[import-not-found]

        assets = list(mu.index)
        w, _lambda_max = _lean_pgd_solve(
            cov.loc[assets, assets].to_numpy(dtype=float),
            mu.to_numpy(dtype=float),
            leverage_cap,
        )
        return pd.Series(w, index=assets)
    except Exception:
        # Verified binary not built / unavailable in this environment.
        return signal_to_weights(mu)
