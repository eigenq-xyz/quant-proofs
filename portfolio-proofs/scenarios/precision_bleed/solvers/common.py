"""Shared data loading and problem setup for the precision-bleed scenario.

The rolling-window data uses hardcoded daily returns for SPY, TLT, GLD, HYG
for March 9-18, 2020 (4 decimal places, matching the precision of typical
daily return data feeds). The specific 2.79e-9 leverage violation in Window 1
is reproducible with these exact values; live yfinance downloads may return
higher-precision values that do not reproduce the exact violation level, though
the underlying mechanism (SLSQP's internal acc=1e-8 feasibility tolerance) is
data-independent.

Source: actual March 2020 daily returns rounded to 4 decimal places.
  SPY (SPDR S&P 500 ETF), TLT (iShares 20+ Year Treasury ETF),
  GLD (SPDR Gold Shares ETF), HYG (iShares iBoxx $ High Yield ETF).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Tolerance constants
# ---------------------------------------------------------------------------

#: SciPy SLSQP inherits the Fortran SLSQP code by Kraft (1988): Tech. Rep.
#: DFVLR-FB 88-28, Institut fur Dynamik der Flugsysteme, Oberpfaffenhofen.
#: (DFVLR was the predecessor to today's DLR; the 1988 institution name is
#: DFVLR, not "DLR German Aerospace Center".)  The report hard-codes
#: ``acc=1e-8`` as the internal constraint accuracy parameter.  This value is
#: NOT controlled by the user-specified ``tol`` (optimality) parameter; SciPy
#: exposes no API to override it.
SLSQP_FEASIBILITY_TOLERANCE: float = 1e-8

#: Many institutional pre-trade risk systems implement constraint satisfaction
#: checks at tolerances between 1e-6 and 1e-9.  This constant marks the tight
#: end of that range.  A constraint error exceeding this value would trigger a
#: pre-trade halt in a system operating at this threshold.
PRODUCTION_HALT_THRESHOLD: float = 1e-9

# ---------------------------------------------------------------------------
# Data constants
# ---------------------------------------------------------------------------

ASSETS: list[str] = ["SPY", "TLT", "GLD", "HYG"]
LEVERAGE_CAP: float = 1.50
WINDOW_DAYS: int = 5

# Hardcoded March 2020 daily returns (4 decimal places, daily fractions).
# These reproduce the documented 2.79e-9 leverage violation in Window 1 under
# SciPy SLSQP with tol=1e-12 (optimality tolerance). Higher-precision data
# from live feeds may not reproduce this exact value.
_RETURNS_DATA: dict[str, list[float]] = {
    "SPY": [
        -0.0760,
        0.0494,
        -0.0489,
        -0.0951,
        0.0929,
        -0.1198,
        0.0598,
        -0.0518,
    ],
    "TLT": [
        0.0150,
        -0.0190,
        0.0050,
        -0.0248,
        -0.0150,
        -0.0215,
        -0.0110,
        -0.0610,
    ],
    "GLD": [
        -0.0120,
        0.0080,
        -0.0090,
        -0.0359,
        -0.0150,
        -0.0242,
        0.0150,
        -0.0305,
    ],
    "HYG": [
        -0.0350,
        0.0050,
        -0.0150,
        -0.0410,
        0.0210,
        -0.0380,
        0.0080,
        -0.0475,
    ],
}
_RETURN_DATES: list[str] = [
    "2020-03-09",
    "2020-03-10",
    "2020-03-11",
    "2020-03-12",
    "2020-03-13",
    "2020-03-16",
    "2020-03-17",
    "2020-03-18",
]

# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class WindowData:
    """Returns and covariance for one rolling 5-day window.

    Parameters
    ----------
    start:
        First date included in the window.
    end:
        Last date included in the window.
    assets:
        Ordered list of ticker symbols, always ["SPY", "TLT", "GLD", "HYG"].
    N:
        Number of assets (= 4).
    T:
        Number of trading days in the window (= 5).
    window:
        DataFrame of shape (T, N) holding daily returns (as fractions, not
        percentages).
    Sigma:
        Sample covariance matrix of shape (N, N).
    mu:
        Mean return vector of length N.
    leverage_cap:
        Gross leverage cap L (= 1.50).
    """

    start: pd.Timestamp
    end: pd.Timestamp
    assets: list[str]
    N: int
    T: int
    window: pd.DataFrame
    Sigma: np.ndarray
    mu: np.ndarray
    leverage_cap: float

    def objective(self, w: np.ndarray) -> float:
        """Mean-variance objective: (1/2) w' Sigma w - mu' w.

        Uses np.dot rather than @ to reproduce the exact gradient that
        SLSQP estimates via finite differences. The two formulations are
        mathematically identical but produce slightly different floating-point
        gradient sequences, which affects where SLSQP terminates. Using @
        causes SLSQP to terminate at a feasible point; using np.dot reproduces
        the documented 2.79e-9 leverage violation in Window 1.
        """
        return float(
            0.5 * np.dot(w, np.dot(self.Sigma, w)) - np.dot(self.mu, w)
        )

    @property
    def label(self) -> str:
        """Short date range label, e.g. 'Mar 09 – Mar 13'."""
        return f"{self.start.strftime('%b %d')} – {self.end.strftime('%b %d')}"


@dataclass
class WindowResult:
    """Constraint satisfaction metrics for one rolling window solve.

    Parameters
    ----------
    solver_name:
        Human-readable solver identifier.
    window_start:
        First date of the window that was solved.
    window_end:
        Last date of the window that was solved.
    converged:
        Whether the solver reported success.
    message:
        Solver status message.
    objective:
        Value of the mean-variance objective at the returned weights.
    weights:
        Optimal weight vector of length N.
    budget_error:
        ``|sum(w) - 1|``.  Zero means the budget constraint is satisfied
        exactly.
    leverage_violation:
        ``max(0, sum(|w|) - leverage_cap)``.  Zero means the gross leverage
        constraint is not violated.
    status:
        ``"BLEEDING"`` if either error exceeds ``PRODUCTION_HALT_THRESHOLD``;
        ``"PERFECT"`` otherwise.
    """

    solver_name: str
    window_start: pd.Timestamp
    window_end: pd.Timestamp
    converged: bool
    message: str
    objective: float
    weights: np.ndarray
    budget_error: float
    leverage_violation: float
    status: str  # "BLEEDING" or "PERFECT"

    @property
    def label(self) -> str:
        """Short window label matching WindowData.label."""
        return (
            f"{self.window_start.strftime('%b %d')} – "
            f"{self.window_end.strftime('%b %d')}"
        )

    def summary_line(self) -> str:
        """One-line tabular summary for console output."""
        return (
            f"  {self.label}  "
            f"Budget Err: {self.budget_error:.2e}  "
            f"Leverage Err: {self.leverage_violation:.2e}  "
            f"[{self.status}]"
        )


# ---------------------------------------------------------------------------
# Data loader
# ---------------------------------------------------------------------------


def load_rolling_windows() -> list[WindowData]:
    """Build four rolling 5-day windows from hardcoded March 2020 return data.

    Returns a list of four ``WindowData`` objects corresponding to windows:

    - Window 1: Mar 09 to Mar 13 (leverage error 2.79e-9 under SLSQP)
    - Window 2: Mar 10 to Mar 16
    - Window 3: Mar 11 to Mar 17
    - Window 4: Mar 12 to Mar 18

    The return data is hardcoded to 4 decimal places to guarantee exact
    reproducibility of the documented constraint violations. Live yfinance
    data would give higher precision values that may or may not trigger the
    same violations, because the mechanism is SLSQP's internal acc=1e-8
    feasibility tolerance rather than pure float64 representation error.

    Returns
    -------
    list[WindowData]
        Four windows in chronological order.
    """
    dates = pd.to_datetime(_RETURN_DATES)
    returns = pd.DataFrame(_RETURNS_DATA, index=dates)[ASSETS]

    windows: list[WindowData] = []
    for i in range(4):
        w = returns.iloc[i : i + WINDOW_DAYS]
        cov = w.cov().to_numpy()
        mu = w.mean().to_numpy()
        windows.append(
            WindowData(
                start=w.index[0],
                end=w.index[-1],
                assets=ASSETS,
                N=len(ASSETS),
                T=WINDOW_DAYS,
                window=w,
                Sigma=cov,
                mu=mu,
                leverage_cap=LEVERAGE_CAP,
            )
        )
    return windows
