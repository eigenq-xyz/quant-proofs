"""SciPy SLSQP solver for the precision-bleed scenario.

Runs SciPy SLSQP with ``tol=1e-12`` (optimality tolerance) on each rolling
5-day window.  The optimality tolerance controls when SLSQP declares the
objective converged; it does NOT control the internal constraint satisfaction
accuracy.  SciPy inherits the Fortran SLSQP code by Kraft (1988), Tech.
Rep. DFVLR-FB 88-28, Institut für Dynamik der Flugsysteme, Oberpfaffenhofen
(DFVLR, the predecessor to today's DLR), which hard-codes ``acc=1e-8`` as
the feasibility tolerance.

Consequence: SLSQP may report ``success=True`` while violating constraints at
the 1e-8 level.  Window 1 (Mar 09-13) produces a leverage error of 2.79e-9,
which exceeds ``PRODUCTION_HALT_THRESHOLD = 1e-9`` and would trigger a
pre-trade risk halt in a system using that threshold.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from . import common
from .common import (
    PRODUCTION_HALT_THRESHOLD,
    WindowData,
    WindowResult,
)


def run_window(w: WindowData) -> WindowResult:
    """Run SciPy SLSQP on a single window.

    Parameters
    ----------
    w:
        Window data (returns, covariance, mean returns, leverage cap).

    Returns
    -------
    WindowResult
        Constraint satisfaction metrics.  ``status`` is ``"BLEEDING"`` if
        either ``budget_error`` or ``leverage_violation`` exceeds
        ``PRODUCTION_HALT_THRESHOLD``; ``"PERFECT"`` otherwise.
    """
    # Box bounds and leverage cap matching the original flat script.
    lev = w.leverage_cap
    constraints = [
        {"type": "eq", "fun": lambda x: np.sum(x) - 1.0},
        {"type": "ineq", "fun": lambda x, lc=lev: lc - np.sum(np.abs(x))},
    ]
    # Box bounds [-1, 1] per asset, matching the original flat script.
    bounds = [(-1.0, 1.0)] * w.N
    w0 = np.ones(w.N) / w.N

    res = minimize(
        w.objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        tol=1e-12,
    )

    weights = res.x
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
        solver_name="SciPy SLSQP (float64, tol=1e-12)",
        window_start=w.start,
        window_end=w.end,
        converged=bool(res.success),
        message=res.message,
        objective=float(res.fun),
        weights=weights,
        budget_error=budget_error,
        leverage_violation=leverage_violation,
        status=status,
    )


def run_all(windows: list[WindowData]) -> list[WindowResult]:
    """Run SLSQP on all four rolling windows.

    Parameters
    ----------
    windows:
        Output of ``common.load_rolling_windows()``.

    Returns
    -------
    list[WindowResult]
        One result per window, in the same order as ``windows``.
    """
    return [run_window(w) for w in windows]


def print_results(results: list[WindowResult]) -> None:
    """Print a formatted table of SLSQP constraint satisfaction across windows.

    Parameters
    ----------
    results:
        Output of ``run_all()``.
    """
    sep = "=" * 78
    print(sep)
    print(
        " SciPy SLSQP (float64, tol=1e-12) — Rolling Window Results ".center(
            78, "="
        )
    )
    print(sep)
    print(
        f"  Internal feasibility tolerance (Kraft 1988 acc): {common.SLSQP_FEASIBILITY_TOLERANCE:.0e}"
    )
    print(
        f"  Production halt threshold                       : {PRODUCTION_HALT_THRESHOLD:.0e}"
    )
    print()

    any_bleeding = False
    for i, r in enumerate(results, 1):
        print(f"Window {i}: {r.label}")
        print(f"  Converged    : {r.converged}  ({r.message})")
        print(f"  Objective    : {r.objective:.15f}")
        print(f"  Sum(w)       : {float(np.sum(r.weights)):.17f}")
        print(f"  Sum(|w|)     : {float(np.sum(np.abs(r.weights))):.17f}")
        print(f"  Budget Err   : {r.budget_error:.2e}  (|sum(w) - 1|)")
        print(
            f"  Leverage Err : {r.leverage_violation:.2e}  (max(0, sum|w| - 1.5))"
        )
        if r.status == "BLEEDING":
            print(
                f"  STATUS       : BLEEDING — error exceeds production halt threshold {PRODUCTION_HALT_THRESHOLD:.0e}"
            )
            any_bleeding = True
        else:
            print("  STATUS       : PERFECT")
        print()

    print(sep)
    if any_bleeding:
        print(
            "CONCLUSION: SLSQP feasibility tolerance (acc=1e-8) permits constraint"
        )
        print(
            "violations that exceed production pre-trade risk halt thresholds."
        )
    else:
        print("CONCLUSION: All windows within production halt threshold.")
    print(sep)
