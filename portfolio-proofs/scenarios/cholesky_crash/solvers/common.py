"""Shared data loading and problem setup for the cholesky-crash scenario.

Loads the Ken French 10 Industry Portfolio daily VW returns, extracts the
five-day March 2020 window (March 9-13, 2020), and defines the mean-variance QP
used by all solver modules.

Key difference from boundary-trap: this module stores both the raw sample
covariance S (rank-deficient, T=5 < N=10) and the Ledoit-Wolf shrunk Sigma
(PSD). Solvers that require a Cholesky decomposition of S will fail before
optimization begins.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve relative to this file: solvers/ -> cholesky_crash/ -> scenarios/
# -> portfolio-proofs/ -> data/
_DATA = (
    pathlib.Path(__file__).parent.parent.parent.parent
    / "data"
    / "french_10ind_daily_vw.parquet"
)

WINDOW_START = "2020-03-09"
WINDOW_END = "2020-03-13"

LEVERAGE_CAP: float = 1.50
SHRINKAGE_ALPHA: float = 0.10

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ProblemData:
    """All inputs needed by any solver in this scenario."""

    window: pd.DataFrame
    industries: list[str]
    N: int
    T: int
    S: np.ndarray  # raw sample covariance (rank-deficient, min eig < 0)
    Sigma: np.ndarray  # LW-shrunk, strictly PD covariance
    mu: np.ndarray  # mean returns (daily fraction)
    leverage_cap: float
    alpha: float  # shrinkage parameter

    def objective(self, w: np.ndarray) -> float:
        """Mean-variance objective using shrunk Sigma: (1/2) w' Sigma w - mu' w."""
        return float(0.5 * w @ self.Sigma @ w - self.mu @ w)

    def raw_objective(self, w: np.ndarray) -> float:
        """Mean-variance objective using raw S (rank-deficient): (1/2) w' S w - mu' w.

        This is what SLSQP and Gurobi attempt to minimize. With S non-PSD the
        objective is unbounded below along null-space directions of S.
        """
        return float(0.5 * w @ self.S @ w - self.mu @ w)


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
    simulated: bool = False

    def summary_row(self, true_obj: float) -> str:
        """One-line summary for the comparison table."""
        gap = (self.objective - true_obj) / abs(true_obj) * 100
        status = "Converged" if self.converged else "FAILED"
        gap_str = (
            f"{gap:.2f}%" if self.converged and not self.simulated else "—"
        )
        sim_tag = " (sim)" if self.simulated else ""
        return (
            f"{self.solver_name:<38} {status:<12}"
            f"{self.objective:18.12f}  {gap_str:>10}{sim_tag}"
        )


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------


def load_problem(
    data_path: pathlib.Path | None = None,
) -> ProblemData:
    """Load the March 2020 five-day window and build both covariance matrices.

    Parameters
    ----------
    data_path:
        Override the default parquet path (useful in tests).

    Returns
    -------
    ProblemData
        Contains both S (raw, rank-deficient) and Sigma (LW-shrunk, PSD).
    """
    path = data_path or _DATA
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            "Run `dvc pull` from portfolio-proofs/ to fetch it."
        )

    df = pd.read_parquet(path)
    window = df.loc[WINDOW_START:WINDOW_END]
    industries = list(window.columns)
    N = len(industries)
    T = len(window)

    S = window.cov().to_numpy()
    mu = window.mean().to_numpy()

    # Ledoit-Wolf style shrinkage: Sigma = alpha * F + (1-alpha) * S
    # F = (tr(S)/N) * I  (scaled identity — the diagonal target)
    tr = np.trace(S)
    F = (tr / N) * np.eye(N)
    Sigma = SHRINKAGE_ALPHA * F + (1 - SHRINKAGE_ALPHA) * S

    return ProblemData(
        window=window,
        industries=industries,
        N=N,
        T=T,
        S=S,
        Sigma=Sigma,
        mu=mu,
        leverage_cap=LEVERAGE_CAP,
        alpha=SHRINKAGE_ALPHA,
    )


def print_problem_header(p: ProblemData) -> None:
    """Print the problem dimensions and covariance diagnostics."""
    eigvals = np.linalg.eigvalsh(p.Sigma)
    rank_S = np.linalg.matrix_rank(p.S)
    eigvals_S = np.linalg.eigvalsh(p.S)

    print(f"Window : {WINDOW_START} to {WINDOW_END} ({p.T} trading days)")
    print(
        f"Assets : N={p.N} industries,  T={p.T} days  ->  rank(S)={rank_S}"
        f"  (T < N: rank-deficient)"
    )
    print(f"Min eig (raw S)     : {eigvals_S[0]:.3e}")
    print(
        f"Shrunk Sigma (a={p.alpha}): "
        f"min={eigvals[0]:.3e},  max={eigvals[-1]:.3e},  "
        f"cond={eigvals[-1] / eigvals[0]:.1f}"
    )
    print(f"Leverage cap        : L={p.leverage_cap}")
    print()
    print("Mean returns (daily %):")
    for i, (ind, m) in enumerate(zip(p.industries, p.mu, strict=True)):
        print(f"  {i:2d}  {ind:6s}  {m * 100:+.4f}%")
