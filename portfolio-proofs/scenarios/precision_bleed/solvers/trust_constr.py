"""SciPy trust-constr (interior-point barrier) solver for the precision-bleed scenario.

Uses the 2N-variable slack reformulation: w = u - v, sum|w| = sum(u+v).
Box bounds w_i in [-1, 1] are enforced via upper bounds u_i, v_i <= 1,
matching the original flat-script problem statement.

The barrier method satisfies constraints to near machine-epsilon, typically
giving budget and leverage errors around 1e-14 to 1e-15 — well below the
production halt threshold of 1e-9.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .common import PRODUCTION_HALT_THRESHOLD, WindowData, WindowResult


def run_window(w: WindowData) -> WindowResult:
    """Run trust-constr barrier on one rolling window."""
    N = w.N

    def obj_uv(x: np.ndarray) -> float:
        wt = x[:N] - x[N:]
        return float(0.5 * np.dot(wt, np.dot(w.Sigma, wt)) - np.dot(w.mu, wt))

    A = np.zeros((2, 2 * N))
    A[0, :N] = 1.0
    A[0, N:] = -1.0  # budget:   sum(u - v) = 1
    A[1, :N] = 1.0
    A[1, N:] = 1.0  # leverage: sum(u + v) <= L

    # u, v in [0, 1] encodes w = u-v in [-1, 1] with u, v >= 0
    bounds = Bounds(np.zeros(2 * N), np.ones(2 * N))
    lc = LinearConstraint(A, [1.0, 0.0], [1.0, w.leverage_cap])
    x0 = np.ones(2 * N) / (2 * N)

    res = minimize(
        obj_uv,
        x0,
        method="trust-constr",
        bounds=bounds,
        constraints=lc,
        tol=1e-12,
    )

    weights = res.x[:N] - res.x[N:]
    budget_error = float(abs(np.sum(weights) - 1.0))
    leverage_violation = float(
        max(0.0, np.sum(np.abs(weights)) - w.leverage_cap)
    )
    bleeding = (
        budget_error > PRODUCTION_HALT_THRESHOLD
        or leverage_violation > PRODUCTION_HALT_THRESHOLD
    )
    status = "BLEEDING" if bleeding else "PERFECT"

    return WindowResult(
        solver_name="SciPy trust-constr (barrier, 2N vars)",
        window_start=w.start,
        window_end=w.end,
        converged=bool(res.success),
        message=res.message,
        objective=float(0.5 * weights @ w.Sigma @ weights - w.mu @ weights),
        weights=weights,
        budget_error=budget_error,
        leverage_violation=leverage_violation,
        status=status,
    )


def run_all(windows: list[WindowData]) -> list[WindowResult]:
    """Run trust-constr on all four rolling windows."""
    return [run_window(w) for w in windows]


def print_results(results: list[WindowResult]) -> None:
    """Print trust-constr constraint satisfaction across windows."""
    sep = "=" * 78
    print(sep)
    print(" SciPy trust-constr — Rolling Window Results ".center(78, "="))
    print(sep)
    print(f"  Production halt threshold: {PRODUCTION_HALT_THRESHOLD:.0e}")
    print()

    any_bleeding = False
    for i, r in enumerate(results, 1):
        print(f"Window {i}: {r.label}")
        print(f"  Converged    : {r.converged}  ({r.message[:60]})")
        print(f"  Sum(w)       : {float(np.sum(r.weights)):.17f}")
        print(f"  Sum(|w|)     : {float(np.sum(np.abs(r.weights))):.17f}")
        print(f"  Budget Err   : {r.budget_error:.2e}  (|sum(w) - 1|)")
        print(
            f"  Leverage Err : {r.leverage_violation:.2e}  (max(0, sum|w| - 1.5))"
        )
        if r.status == "BLEEDING":
            print("  STATUS       : BLEEDING")
            any_bleeding = True
        else:
            print("  STATUS       : PERFECT")
        print()

    print(sep)
    if any_bleeding:
        print("CONCLUSION: trust-constr constraint violations detected.")
    else:
        print(
            "CONCLUSION: trust-constr satisfies constraints below halt threshold."
        )
    print(sep)
