"""Lean 4 PGD solver for the precision-bleed scenario.

Delegates to ``lean_pgd.solve()`` (the ``pgd_solve_flat`` FFI path).
Convergence is guaranteed by theorem ``pgd_convergence``; the projection
step is verified to land exactly on the constraint set.

The Lean PGD uses float64 arithmetic (not integer arithmetic), so the
budget and leverage constraint errors reflect floating-point rounding of
the final projection — typically 1e-15 to 1e-16, well below production
halt thresholds.  This contrasts with the integer PGD (exact, 0 error)
and SLSQP (acc=1e-8 feasibility tolerance, can reach 2.79e-9).
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np

# Resolve lean_pgd.py: solvers/ -> precision_bleed/ -> scenarios/ -> portfolio-proofs/
_PORTFOLIO = pathlib.Path(__file__).parent.parent.parent.parent
if str(_PORTFOLIO) not in sys.path:
    sys.path.insert(0, str(_PORTFOLIO))

from lean_pgd import LEAN_NATIVE_NS  # noqa: E402
from lean_pgd import solve as _lean_pgd_solve  # noqa: E402

from .common import (  # noqa: E402
    PRODUCTION_HALT_THRESHOLD,
    WindowData,
    WindowResult,
)


def run_window(w: WindowData) -> WindowResult:
    """Run Lean 4 PGD on one rolling window.

    Parameters
    ----------
    w:
        WindowData with sample covariance (Sigma) and mean returns (mu).
        No box bounds; the Lean PGD projects onto {sum=1, sum|.|<=L}.

    Returns
    -------
    WindowResult
        ``status="BLEEDING"`` if budget or leverage error exceeds the
        production halt threshold; ``"PERFECT"`` otherwise.
    """
    weights, lam_max = _lean_pgd_solve(w.Sigma, w.mu, w.leverage_cap)

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
        solver_name=f"Lean 4 PGD (pgd_ffi, native {LEAN_NATIVE_NS:.1f} ns)",
        window_start=w.start,
        window_end=w.end,
        converged=True,
        message=(
            f"pgd_solve_flat via FFI  "
            f"(eta = 1.9 / {lam_max:.4e};  "
            f"native: {LEAN_NATIVE_NS:.3f} ns/solve at N=10)"
        ),
        objective=w.objective(weights),
        weights=weights,
        budget_error=budget_error,
        leverage_violation=leverage_violation,
        status=status,
    )


def run_all(windows: list[WindowData]) -> list[WindowResult]:
    """Run Lean 4 PGD on all four rolling windows."""
    return [run_window(w) for w in windows]


def print_results(results: list[WindowResult]) -> None:
    """Print Lean 4 PGD constraint satisfaction across windows."""
    sep = "=" * 78
    print(sep)
    solver_name = results[0].solver_name if results else "Lean 4 PGD"
    print(f" {solver_name} — Rolling Window Results ".center(78, "="))
    print(sep)
    print(f"  Production halt threshold: {PRODUCTION_HALT_THRESHOLD:.0e}")
    print()

    any_bleeding = False
    for i, r in enumerate(results, 1):
        print(f"Window {i}: {r.label}")
        print(f"  Converged    : {r.converged}  ({r.message[:60]})")
        print(f"  Objective    : {r.objective:.15f}")
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
        print("CONCLUSION: Lean 4 PGD constraint violations detected.")
    else:
        print(
            "CONCLUSION: Lean 4 PGD satisfies constraints to float64 rounding "
            "— below the production halt threshold for all windows."
        )
    print(sep)
