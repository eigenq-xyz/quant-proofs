"""Shared problem setup for the vix-shock scenario.

Three-asset portfolio under an overnight VIX-doubling event. The optimal
portfolio changes as higher variance diversifies away concentration risk.
The step size calibrated on pre-shock covariance violates the Lipschitz
stability bound after the shock, causing uncertified gradient descent to diverge.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

N: int = 3
MU: np.ndarray = np.array([0.15, 0.10, 0.05])
SIGMA_SQ_PRE: float = 0.04  # pre-shock variance (sigma = 20% annual)
SIGMA_SQ_POST: float = (
    0.16  # post-shock variance (sigma = 40% annual, VIX doubles)
)
LEVERAGE_CAP: float = 1.0  # long-only simplex
ASSET_NAMES: list[str] = ["Equity", "Bonds", "Commodities"]

# Analytically certified optima
W_STAR_PRE: np.ndarray = np.array([1.0, 0.0, 0.0])
W_STAR_POST: np.ndarray = np.array([0.6458333333, 0.3333333333, 0.0208333333])
LAMBDA_PRE: float = 0.11
LAMBDA_POST: float = 7.0 / 150.0  # exactly 0.04̄6̄

# Step sizes
ETA_PRE: float = 1.9 / SIGMA_SQ_PRE  # = 47.5 (stale after shock)
ETA_POST: float = 1.9 / SIGMA_SQ_POST  # = 11.875 (certified)
STABILITY_BOUND_POST: float = 2.0 / SIGMA_SQ_POST  # = 12.5


@dataclass
class ProblemData:
    """All inputs needed by any solver in this scenario."""

    N: int
    Sigma: np.ndarray
    mu: np.ndarray
    leverage_cap: float
    asset_names: list[str]
    sigma_sq: float  # diagonal variance (for step-size analysis)

    def objective(self, w: np.ndarray) -> float:
        """Mean-variance objective: (1/2) w' Sigma w - mu' w."""
        return float(0.5 * w @ self.Sigma @ w - self.mu @ w)


@dataclass
class SolverResult:
    """Standardised output from any solver module."""

    solver_name: str
    converged: bool
    message: str
    objective: float
    weights: np.ndarray
    n_iterations: int
    budget_error: float
    diverged: bool  # True if weights exceeded 1e6 (divergence detection)
    weight_history: np.ndarray  # shape (n_iters, N) for trajectory plots


def make_pre_shock() -> ProblemData:
    """Pre-shock problem: sigma = 20%, VIX ~ 15."""
    return ProblemData(
        N=N,
        Sigma=SIGMA_SQ_PRE * np.eye(N),
        mu=MU.copy(),
        leverage_cap=LEVERAGE_CAP,
        asset_names=ASSET_NAMES,
        sigma_sq=SIGMA_SQ_PRE,
    )


def make_post_shock() -> ProblemData:
    """Post-shock problem: sigma = 40%, VIX ~ 30 (VIX doubled overnight)."""
    return ProblemData(
        N=N,
        Sigma=SIGMA_SQ_POST * np.eye(N),
        mu=MU.copy(),
        leverage_cap=LEVERAGE_CAP,
        asset_names=ASSET_NAMES,
        sigma_sq=SIGMA_SQ_POST,
    )
