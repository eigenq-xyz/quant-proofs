"""Shared problem setup for the phantom-positions scenario.

Synthetic 5-asset mean-variance portfolio with L1 gross leverage cap.
All parameters are chosen so the analytical optimum has exactly 2 active assets
(1 long, 1 short) with 3 assets at exactly zero weight. This is the scenario
that exposes interior-point phantom positions.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

N: int = 5
SIGMA_SQ: float = 0.04  # identical variance for all assets
MU: np.ndarray = np.array([0.20, 0.06, 0.05, -0.02, -0.07])
LEVERAGE_CAP: float = 1.50
ASSET_NAMES: list[str] = ["Tech", "Bonds", "Staples", "Energy", "HiYield"]

# Analytical solution (derived from KKT, see kkt_optimum.py)
W_STAR: np.ndarray = np.array([1.25, 0.0, 0.0, 0.0, -0.25])
OBJ_STAR: float = -0.235  # f(w★) = 0.5*0.04*(1.25²+0.25²) - (0.25+0.0175)
LAMBDA_STAR: float = 0.045  # budget dual variable
NU_STAR: float = 0.105  # leverage dual variable


@dataclass
class ProblemData:
    """All inputs needed by any solver in this scenario."""

    N: int
    Sigma: np.ndarray
    mu: np.ndarray
    leverage_cap: float
    asset_names: list[str]

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
    leverage_violation: float

    def live_position_count(self, threshold: float = 1e-9) -> int:
        """Number of assets with |w_i| > threshold."""
        return int(np.sum(np.abs(self.weights) > threshold))

    def summary_row(self, true_obj: float) -> str:
        """One-line summary for the comparison table."""
        gap = (self.objective - true_obj) / abs(true_obj) * 100
        status = "Converged" if self.converged else "FAILED"
        gap_str = f"{gap:.4f}%" if self.converged else "—"
        pos2 = self.live_position_count(1e-6)
        pos9 = self.live_position_count(1e-9)
        return (
            f"{self.solver_name:<35} {status:<12} "
            f"{self.objective:18.12f}  {gap_str:>12}  "
            f"pos(>1e-6)={pos2}  pos(>1e-9)={pos9}"
        )


def make_problem() -> ProblemData:
    """Construct the 5-asset phantom-positions problem."""
    Sigma = SIGMA_SQ * np.eye(N)
    return ProblemData(
        N=N,
        Sigma=Sigma,
        mu=MU.copy(),
        leverage_cap=LEVERAGE_CAP,
        asset_names=ASSET_NAMES,
    )


def print_problem_header(p: ProblemData) -> None:
    """Print problem setup and analytical solution."""
    eigvals = np.linalg.eigvalsh(p.Sigma)
    print(f"Assets      : N={p.N}  ({', '.join(p.asset_names)})")
    print(f"Covariance  : Sigma = {SIGMA_SQ}*I  (uncorrelated, homoskedastic)")
    print(f"  min eig   = {eigvals[0]:.4e}  max eig = {eigvals[-1]:.4e}")
    print(
        f"  cond(Sigma)   = {eigvals[-1] / eigvals[0]:.1f}  (well-conditioned)"
    )
    print(f"Leverage cap: L = {p.leverage_cap}")
    print()
    print("Expected returns mu (annual):")
    for name, m in zip(p.asset_names, p.mu, strict=True):
        print(f"  {name:8s}: {m:+.2f}")
    print()
    print("KKT-certified global optimum:")
    for name, w in zip(p.asset_names, W_STAR, strict=True):
        flag = "<- active" if abs(w) > 1e-9 else "  (zero)"
        print(f"  {name:8s}: w* = {w:+.4f}  {flag}")
    print(
        f"  f(w*) = {OBJ_STAR:.6f},  lambda = {LAMBDA_STAR},  nu = {NU_STAR}"
    )
