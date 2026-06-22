"""Shared data loading and problem setup for the boundary-trap scenario.

Loads the Ken French 10 Industry Portfolio daily VW returns, extracts the
five-day August 2007 window, and defines the mean-variance QP used by all
solver modules.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve relative to this file: solvers/ -> boundary_trap/ -> scenarios/
# -> portfolio-proofs/ -> data/
_DATA = (
    pathlib.Path(__file__).parent.parent.parent.parent
    / "data"
    / "french_10ind_daily_vw.parquet"
)

WINDOW_START = "2007-08-03"
WINDOW_END = "2007-08-09"

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
    S: np.ndarray  # raw sample covariance (rank-deficient)
    Sigma: np.ndarray  # shrunk, strictly PD covariance
    mu: np.ndarray  # mean returns (daily fraction)
    leverage_cap: float
    alpha: float  # shrinkage parameter

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

    @property
    def industries(self) -> list[str]:
        """Return list of industries (provided externally via ProblemData)."""
        raise NotImplementedError("Set .industries after construction")

    def summary_row(self, true_obj: float) -> str:
        """One-line summary for the comparison table."""
        gap = (self.objective - true_obj) / abs(true_obj) * 100
        status = "Converged" if self.converged else "FAILED"
        gap_str = f"{gap:.2f}%" if self.converged else "—"
        return (
            f"{self.solver_name:<32} {status:<12} "
            f"{self.objective:18.12f}  {gap_str:>10}"
        )


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------


def load_problem(
    data_path: pathlib.Path | None = None,
) -> ProblemData:
    """Load the August 2007 five-day window and build the covariance matrix.

    Parameters
    ----------
    data_path:
        Override the default parquet path (useful in tests).
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
        f"Assets : N={p.N} industries,  T={p.T} days  →  rank(S)={rank_S}  (T < N)"
    )
    print(f"Min eig (raw S)     : {eigvals_S[0]:.3e}")
    print(
        f"Shrunk Sigma (α={p.alpha}): "
        f"min={eigvals[0]:.3e},  max={eigvals[-1]:.3e},  "
        f"cond={eigvals[-1] / eigvals[0]:.1f}"
    )
    print(f"Leverage cap        : L={p.leverage_cap}")
    print()
    print("Mean returns (daily %):")
    for i, (ind, m) in enumerate(zip(p.industries, p.mu, strict=True)):
        print(f"  {i:2d}  {ind:6s}  {m * 100:+.4f}%")
