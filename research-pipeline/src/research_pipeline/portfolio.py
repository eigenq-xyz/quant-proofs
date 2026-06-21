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
import warnings
from typing import TYPE_CHECKING, Callable

import numpy as np
import pandas as pd

if TYPE_CHECKING:
    from .data import PricePanel

# A portfolio constructor maps one cross-sectional score row to target weights.
PortfolioConstructor = Callable[..., pd.Series]


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


def long_only_weights(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
    """Long-only tilt: hold above-average names ∝ their demeaned score; ``sum(w) = gross``.

    Below-average names get zero weight. Suits a constrained book that cannot short.
    """
    s = signal_row.dropna()
    s = (s - s.mean()).clip(lower=0.0)
    denom = float(s.sum())
    if denom == 0.0 or not np.isfinite(denom):
        return pd.Series(0.0, index=s.index)
    return s / denom * gross


def long_short_quantile_weights(
    signal_row: pd.Series, gross: float = 1.0, quantile: float = 1.0 / 3.0
) -> pd.Series:
    """Equal-weight long/short of the top/bottom ``quantile`` cross-sectional names.

    ``sum(w) = 0``, ``sum(|w|) = gross``. The classic cross-sectional decile/tercile book;
    less sensitive to score outliers than the proportional ``signal_to_weights``.
    """
    s = signal_row.dropna()
    n = len(s)
    if n < 3:
        return pd.Series(0.0, index=s.index)
    k = max(1, int(n * quantile))
    ranked = s.sort_values()
    shorts, longs = ranked.index[:k], ranked.index[-k:]
    w = pd.Series(0.0, index=s.index)
    w.loc[longs] = 0.5 * gross / len(longs)
    w.loc[shorts] = -0.5 * gross / len(shorts)
    return w


def directional_weights(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
    """Sign-based weights WITHOUT cross-sectional demeaning, scaled to ``sum(|w|) = gross``.

    Unlike the dollar-neutral constructors this does not net to zero, so it carries a
    directional (net long/short) position. Required for single-asset / time-series alphas,
    where cross-sectional demeaning would annihilate the only position.
    """
    s = signal_row.dropna()
    sign = np.sign(s)
    denom = float(sign.abs().sum())
    if denom == 0.0 or not np.isfinite(denom):
        return pd.Series(0.0, index=s.index)
    return pd.Series(sign / denom * gross, index=s.index)


class VerifiedSolverUnavailable(RuntimeError):
    """The compiled Lean PGD solver could not be reached.

    Raised by :func:`verified_pgd_weights` instead of silently degrading to an unverified
    baseline. A result is "verified end-to-end" only if it actually ran through the verified
    solver; a silent fallback would let unverified weights masquerade as verified ones, which
    is precisely the data-mining failure this project exists to rule out.
    """


def verified_pgd_weights(
    mu: pd.Series,
    cov: pd.DataFrame,
    leverage_cap: float = 1.5,
    allow_fallback: bool = False,
) -> pd.Series:
    """Budget-constrained mean-variance weights via the verified Lean 4 PGD solver.

    Solves ``sum(w) ≈ 1``, ``sum|w| ≤ leverage_cap``. Requires the compiled ``pgd_solve``
    binary in ``portfolio-proofs`` (``cd portfolio-proofs && lake build``).

    **No silent fallback.** If the verified solver is unavailable this *raises*
    :class:`VerifiedSolverUnavailable` (the default), so a study can never present an
    unverified baseline as a verified result. Pass ``allow_fallback=True`` to degrade to the
    dollar-neutral baseline instead, in which case a :class:`UserWarning` is emitted and the
    fallback is loud, never silent.

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
    except VerifiedSolverUnavailable:
        raise
    except Exception as exc:  # solver not built / import or runtime failure
        if not allow_fallback:
            raise VerifiedSolverUnavailable(
                "verified PGD solver unavailable (build portfolio-proofs: "
                "`cd portfolio-proofs && lake build`). Refusing to silently substitute an "
                "unverified baseline; pass allow_fallback=True to opt in to a loud fallback."
            ) from exc
        warnings.warn(
            f"verified PGD solver unavailable ({exc}); falling back to the UNVERIFIED "
            "dollar-neutral baseline. These weights are NOT verified.",
            UserWarning,
            stacklevel=2,
        )
        return signal_to_weights(mu)


def _ledoit_wolf_shrink(cov: np.ndarray, intensity: float = 0.1) -> np.ndarray:
    """Shrink a sample covariance toward a scaled identity; guarantees positive definiteness.

    Mirrors the ``shrinkage_psd`` theorem in ``optimization-proofs``:
    ``delta * (trace/n) * I + (1 - delta) * cov`` is positive definite for any symmetric PSD
    ``cov``, so the verified PGD solver always receives a well-posed (PD) covariance.
    """
    n = cov.shape[0]
    target = (np.trace(cov) / n) * np.eye(n)
    return np.asarray(intensity * target + (1.0 - intensity) * cov, dtype=float)


def make_verified_pgd_weight_fn(
    panel: "PricePanel",
    lookback: int = 252,
    leverage_cap: float = 1.5,
    min_obs: int = 120,
    shrink: float = 0.1,
    periods_per_year: int = 252,
    risk_aversion: float = 1.0,
) -> PortfolioConstructor:
    """Build a per-date weight function that routes construction through the **verified** PGD solver.

    Returns a standard ``(signal_row, gross=...) -> Series`` constructor so it drops straight into
    :func:`research_pipeline.backtest.run_backtest`. At each date ``t`` (``= signal_row.name``) it
    forms a trailing Ledoit--Wolf covariance from returns with timestamp ``<= t`` *only* (preserving
    the verified no-look-ahead property end to end), takes the signal row as expected returns ``mu``,
    and solves the verified budget-constrained mean-variance problem
    (``sum w = 1``, ``sum|w| <= leverage_cap``). Names with a missing signal or an incomplete
    covariance window at ``t`` are dropped; fewer than three survivors yields a flat book.

    This is the **budget** book (``sum w = 1``) — the constraint the projection is *proven* for. It
    is a different book from the dollar-neutral baseline; the dollar-neutral (``sum w = 0``) verified
    projection is a tracked ``optimization-proofs`` theorem (see ROADMAP). ``gross`` is ignored: the
    verified solver normalises to ``sum w = 1``.
    """
    rets = panel.prices.astype(float).pct_change()

    def _verified_pgd_weight_fn(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
        flat = pd.Series(0.0, index=signal_row.index)
        mu_row = signal_row.dropna()
        if len(mu_row) < 3:
            return flat
        window = rets.loc[: signal_row.name].iloc[-lookback:]
        window = window.loc[:, mu_row.index].dropna(axis=1, how="any")
        if window.shape[0] < min_obs or window.shape[1] < 3:
            return flat
        assets = list(window.columns)
        # Put Sigma on the SAME (annual) horizon as the momentum mu. The signal is a ~12-month return,
        # but np.cov of daily returns is a per-DAY covariance, so without annualising, the risk term
        # (1/2) w' Sigma w is ~252x too small relative to mu' w and the MV solution degenerates into a
        # concentrated max-return corner bet. risk_aversion further scales the risk term.
        sample = np.cov(window.to_numpy(dtype=float), rowvar=False) * (
            risk_aversion * periods_per_year
        )
        cov_df = pd.DataFrame(_ledoit_wolf_shrink(sample, shrink), index=assets, columns=assets)
        w = verified_pgd_weights(mu_row.loc[assets], cov_df, leverage_cap=leverage_cap)
        return w.reindex(signal_row.index).fillna(0.0)

    return _verified_pgd_weight_fn


# --- registry ---------------------------------------------------------------
# Registers the row-to-weights constructors (signature ``(signal_row, gross=...) -> Series``).
# ``verified_pgd_weights`` is intentionally absent: it needs a covariance matrix, a different
# interface, so it is wired in explicitly rather than selected by name.

_PORTFOLIO_REGISTRY: dict[str, PortfolioConstructor] = {
    "dollar_neutral": signal_to_weights,
    "long_only": long_only_weights,
    "long_short_quantile": long_short_quantile_weights,
    "directional": directional_weights,
}


def register_portfolio(name: str, fn: PortfolioConstructor) -> None:
    """Register a portfolio constructor under ``name`` (overwrites an existing entry)."""
    _PORTFOLIO_REGISTRY[name] = fn


def available_portfolios() -> list[str]:
    """Names of all registered portfolio constructors, sorted."""
    return sorted(_PORTFOLIO_REGISTRY)


def get_portfolio(name: str) -> PortfolioConstructor:
    """Look up a registered portfolio constructor by name."""
    if name not in _PORTFOLIO_REGISTRY:
        raise KeyError(f"unknown portfolio {name!r}; available: {available_portfolios()}")
    return _PORTFOLIO_REGISTRY[name]
