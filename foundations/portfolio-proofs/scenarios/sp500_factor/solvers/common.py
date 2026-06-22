"""Shared problem setup for the sp500-factor scenario.

Single-factor CAPM covariance with heteroskedastic betas. Used to benchmark
PGD's O(N log N) projection against interior-point methods at scales ranging
from N=10 (boundary_trap size) to N=500 (S&P 500 constituents).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

SIGMA_F: float = 0.15  # factor volatility
SIGMA_EPS: float = 0.05  # idiosyncratic volatility (identical for all assets)
R_F: float = 0.03  # risk-free rate
EQUITY_PREMIUM: float = 0.07  # market risk premium
LEVERAGE_CAP: float = 1.50

BENCHMARK_N: list[int] = [10, 50, 100, 250, 500]
BENCHMARK_REPS: int = 5  # median of REPS timing runs


@dataclass
class ProblemData:
    """Factor-model portfolio problem for a given N."""

    N: int
    beta: np.ndarray  # factor loadings, shape (N,)
    Sigma: np.ndarray  # full covariance matrix, shape (N, N)
    mu: np.ndarray  # expected returns, shape (N,)
    leverage_cap: float
    # Factor model components (for efficient PGD gradient)
    sigma_f_sq: float
    sigma_eps_sq: float

    def objective(self, w: np.ndarray) -> float:
        return float(0.5 * w @ self.Sigma @ w - self.mu @ w)

    def gradient_factor(self, w: np.ndarray) -> np.ndarray:
        """O(N) gradient using rank-1 factor structure: Σw - μ = σ_f²·β(βᵀw) + σ_ε²·w - μ."""
        result: np.ndarray = (
            self.sigma_f_sq * self.beta * float(self.beta @ w)
            + self.sigma_eps_sq * w
            - self.mu
        )
        return result


def make_problem(N: int) -> ProblemData:
    """Build the N-asset single-factor CAPM problem."""
    beta = np.arange(1, N + 1, dtype=float) / N  # βᵢ = i/N ∈ [1/N, 1]
    sigma_f_sq = SIGMA_F**2
    sigma_eps_sq = SIGMA_EPS**2
    Sigma = sigma_f_sq * np.outer(beta, beta) + sigma_eps_sq * np.eye(N)
    mu = R_F + EQUITY_PREMIUM * beta
    return ProblemData(
        N=N,
        beta=beta,
        Sigma=Sigma,
        mu=mu,
        leverage_cap=LEVERAGE_CAP,
        sigma_f_sq=sigma_f_sq,
        sigma_eps_sq=sigma_eps_sq,
    )
