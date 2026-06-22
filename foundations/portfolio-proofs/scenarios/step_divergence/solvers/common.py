"""Shared data loading and problem setup for the step-divergence scenario.

Loads the Ken French 10 Industry Portfolio daily VW returns, extracts a
21-day January 2018 calibration window (full-rank) and a 5-day shock window
ending February 5, 2018 (Volmageddon), and defines the mean-variance QP
used by all solver modules.

The key asymmetry: eta calibrated from January has eta_cal = 5334.47, but
the post-shock Lipschitz bound is 2 / lam_max_shock = 840.90. The calibrated
step size exceeds the post-shock stability bound by 6.3x, causing divergence.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

# Resolve relative to this file: solvers/ -> step_divergence/ -> scenarios/
# -> portfolio-proofs/ -> data/
_DATA = (
    pathlib.Path(__file__).parent.parent.parent.parent
    / "data"
    / "french_10ind_daily_vw.parquet"
)

CAL_START = "2018-01-02"
CAL_END = "2018-01-31"
SHOCK_START = "2018-01-30"
SHOCK_END = "2018-02-05"

LEVERAGE_CAP: float = 1.50
SHRINKAGE_ALPHA: float = 0.10

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ProblemData:
    """All inputs needed by any solver in this scenario."""

    # Pre-shock calibration window (January 2018, full-rank)
    cal_window: pd.DataFrame
    lam_max_cal: float  # lambda_max of S_cal (full-rank, no shrinkage needed)
    eta_calibrated: float  # 1.9 / lam_max_cal = 5334.47

    # Post-shock window (5 days ending Feb 5, 2018)
    shock_window: pd.DataFrame
    industries: list[str]
    N: int  # = 10
    S_shock: np.ndarray  # raw sample cov (rank-deficient, T=5 < N=10)
    Sigma_shock: np.ndarray  # LW-shrunk, PSD
    mu_shock: np.ndarray  # mean returns of shock window
    lam_max_shock: float  # lambda_max(Sigma_shock) = 0.002378
    lipschitz_bound: float  # 2 / lam_max_shock = 840.90
    leverage_cap: float
    alpha: float  # shrinkage parameter

    def objective(self, w: np.ndarray) -> float:
        """Mean-variance objective using post-shock shrunk covariance.

        f(w) = (1/2) w' Sigma_shock w - mu_shock' w
        """
        return float(0.5 * w @ self.Sigma_shock @ w - self.mu_shock @ w)


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

    def summary_row(self, true_obj: float) -> str:
        """One-line summary for the comparison table."""
        gap = (self.objective - true_obj) / abs(true_obj) * 100
        status = "Converged" if self.converged else "FAILED/DIVERGED"
        gap_str = f"{gap:.2f}%" if self.converged else "—"
        return (
            f"{self.solver_name:<36} {status:<16} "
            f"{self.objective:18.12f}  {gap_str:>10}"
        )


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------


def load_problem(
    data_path: pathlib.Path | None = None,
) -> ProblemData:
    """Load calibration and shock windows and build the covariance matrices.

    Parameters
    ----------
    data_path:
        Override the default parquet path (useful in tests).

    Returns
    -------
    ProblemData
        Populated with January 2018 calibration (full-rank) and
        5-day post-shock window (LW-shrunk).
    """
    path = data_path or _DATA
    if not path.exists():
        raise FileNotFoundError(
            f"Data file not found: {path}\n"
            "Run `dvc pull` from portfolio-proofs/ to fetch it."
        )

    df = pd.read_parquet(path)

    # --- Calibration window: January 2018, full-rank ---------------------
    cal_window = df.loc[CAL_START:CAL_END]
    S_cal = cal_window.cov().to_numpy()
    eigvals_cal = np.linalg.eigvalsh(S_cal)
    lam_max_cal = float(eigvals_cal[-1])
    eta_calibrated = 1.9 / lam_max_cal

    # --- Shock window: Jan 30 – Feb 5, 2018 (Volmageddon) ---------------
    shock_window = df.loc[SHOCK_START:SHOCK_END]
    industries = list(shock_window.columns)
    N = len(industries)

    S_shock = shock_window.cov().to_numpy()
    mu_shock = shock_window.mean().to_numpy()

    # Ledoit-Wolf style shrinkage: Sigma = alpha * F + (1-alpha) * S
    # F = (tr(S)/N) * I  (scaled identity target)
    tr = np.trace(S_shock)
    F = (tr / N) * np.eye(N)
    Sigma_shock = SHRINKAGE_ALPHA * F + (1 - SHRINKAGE_ALPHA) * S_shock

    eigvals_shock = np.linalg.eigvalsh(Sigma_shock)
    lam_max_shock = float(eigvals_shock[-1])
    lipschitz_bound = 2.0 / lam_max_shock

    return ProblemData(
        cal_window=cal_window,
        lam_max_cal=lam_max_cal,
        eta_calibrated=eta_calibrated,
        shock_window=shock_window,
        industries=industries,
        N=N,
        S_shock=S_shock,
        Sigma_shock=Sigma_shock,
        mu_shock=mu_shock,
        lam_max_shock=lam_max_shock,
        lipschitz_bound=lipschitz_bound,
        leverage_cap=LEVERAGE_CAP,
        alpha=SHRINKAGE_ALPHA,
    )


def print_problem_header(p: ProblemData) -> None:
    """Print calibration and shock window diagnostics."""
    rank_S_cal = np.linalg.matrix_rank(p.cal_window.cov().to_numpy())
    rank_S_shock = np.linalg.matrix_rank(p.S_shock)
    eigvals_shrunk = np.linalg.eigvalsh(p.Sigma_shock)

    print("=== Calibration window ===")
    print(
        f"Window : {CAL_START} to {CAL_END} ({len(p.cal_window)} trading days)"
    )
    print(
        f"Assets : N={p.N}  T={len(p.cal_window)}  rank(S_cal)={rank_S_cal}  (FULL RANK)"
    )
    print(f"lambda_max(S_cal)    : {p.lam_max_cal:.6f}")
    print(f"Stability bound 2/lambda_max(S_cal): {2.0 / p.lam_max_cal:.2f}")
    print(
        f"Calibrated eta       : {p.eta_calibrated:.2f}  (= 1.9 / {p.lam_max_cal:.6f})"
    )
    print()
    print("=== Shock window (Volmageddon) ===")
    print(
        f"Window : {SHOCK_START} to {SHOCK_END} ({len(p.shock_window)} trading days)"
    )
    print(
        f"Assets : N={p.N}  T={len(p.shock_window)}  rank(S_shock)={rank_S_shock}  "
        f"(RANK-DEFICIENT — T < N)"
    )
    print(
        f"Shrunk Sigma (alpha={p.alpha}): "
        f"min={eigvals_shrunk[0]:.3e},  max={eigvals_shrunk[-1]:.3e},  "
        f"cond={eigvals_shrunk[-1] / eigvals_shrunk[0]:.1f}"
    )
    print(f"lambda_max(Sigma_shock)  : {p.lam_max_shock:.6f}")
    print(f"Lipschitz bound (2/lambda): {p.lipschitz_bound:.2f}")
    print()
    growth = abs(p.eta_calibrated * p.lam_max_shock - 1.0)
    print("=== Stability violation ===")
    print(
        f"Calibrated eta = {p.eta_calibrated:.2f}  >>  "
        f"Lipschitz bound = {p.lipschitz_bound:.2f}  "
        f"(factor {p.eta_calibrated / p.lipschitz_bound:.2f}x OVER bound)"
    )
    print(
        f"Divergence growth factor per step: |eta * lambda_max - 1| = {growth:.3f}"
    )
    print(f"After 3 steps: error amplification ~{growth**3:.0f}x")
    print()
    print("Mean returns of shock window (daily %):")
    for i, (ind, m) in enumerate(zip(p.industries, p.mu_shock, strict=True)):
        print(f"  {i:2d}  {ind:6s}  {m * 100:+.4f}%")
