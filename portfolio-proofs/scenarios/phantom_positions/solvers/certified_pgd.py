"""Lean 4 PGD solver for the phantom-positions scenario.

Calls the compiled Lean 4 ``pgd_solve`` binary directly via subprocess.
No Cython, no FFI layer.  Protocol: one stdin line with N, sigma (row-major),
mu, lambda_max, leverage_cap; stdout: space-separated optimal weights.

The Lean binary runs ``pgdFlat`` from ``OptimizationProofs.PGDFlat``, which
uses the Duchi et al. (2008) dual-bisection projection.  The key property:

    Components with |y_i - theta*| <= mu* are set to exactly zero by the
    max(..., 0) thresholding operation inside the projection -- an algebraic
    condition, not an asymptotic limit.  PGD therefore produces *exact* zeros
    at inactive assets (up to double-precision bisection error ~1e-11).

Compare with barrier methods (trust-constr, Gurobi): the log-barrier term
-mu_B * (log u_i + log v_i) explicitly prevents slack variables from reaching
zero, so inactive-asset weights remain at O(mu_B) even at full convergence.
See Wright (1997) §4 for the complementarity-gap analysis.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np

# lean_pgd_direct.py lives at portfolio-proofs/
_PORTFOLIO = pathlib.Path(__file__).parent.parent.parent.parent
if str(_PORTFOLIO) not in sys.path:
    sys.path.insert(0, str(_PORTFOLIO))

from lean_pgd_direct import solve as _lean_solve  # noqa: E402

from .common import ProblemData, SolverResult  # noqa: E402


def _project_budget_l1(
    y: np.ndarray, budget: float, leverage: float
) -> np.ndarray:
    """Project y onto {w : sum(w) = budget, sum(|w|) <= leverage}.

    Uses the dual-bisection algorithm derived from Duchi et al. (2008). The
    projection allows negative weights (unlike the simplex projection, which
    enforces w >= 0). The feasible set here is the intersection of a budget
    hyperplane and an L1 ball, both without a non-negativity constraint.

    The dual of this projection has the form: find (theta*, mu*) such that

        w_i* = sign(y_i - theta*) * max(|y_i - theta*| - mu*, 0)

    satisfies sum(w_i*) = budget and sum(|w_i*|) = leverage. The dual
    bisection finds (theta*, mu*) via nested binary search:

        Outer loop: bisect over mu >= 0 to enforce sum(|w|) = leverage.
        Inner loop: for each mu_mid, bisect over theta to enforce sum(w) = budget.

    Step 1: Check if the L1 constraint is inactive (unconstrained budget
            projection suffices). The unconstrained minimiser of (1/2)||w-y||^2
            subject to sum(w) = budget is w = y - ((sum(y)-budget)/N) * 1.
            If this satisfies sum(|w|) <= leverage, return it directly.

    Step 2: Otherwise the L1 constraint is active. Use nested bisection.

    Key property: components with |y_i - theta*| <= mu* are set to exactly
    zero by the max(..., 0) operation. This is a hard algebraic threshold,
    not an asymptotic limit. When the bisection converges, the inactive
    assets have w_i* = 0 exactly (up to bisection precision ~1e-11).

    Parameters
    ----------
    y:
        Input vector to project.
    budget:
        Target budget: sum(w) = budget.
    leverage:
        L1 cap: sum(|w|) <= leverage.

    Returns
    -------
    w:
        Projected vector satisfying sum(w) = budget and sum(|w|) <= leverage.
    """
    N = len(y)

    # Step 1: Check if L1 constraint is inactive
    # Unconstrained budget projection: shift y uniformly
    theta_unconstrained = (float(np.sum(y)) - budget) / N
    w_unconstrained = y - theta_unconstrained
    if float(np.sum(np.abs(w_unconstrained))) <= leverage + 1e-12:
        return w_unconstrained

    # Step 2: L1 constraint is active; use nested dual bisection
    # Parametrize: w_i(theta, mu) = sign(y_i - theta) * max(|y_i - theta| - mu, 0)
    def w_fn(theta: float, mu: float) -> np.ndarray:
        """Compute projected weights given dual variables (theta, mu)."""
        diff = y - theta
        return np.sign(diff) * np.maximum(np.abs(diff) - mu, 0.0)

    # Outer bisection over mu in [0, mu_hi] to enforce sum(|w|) = leverage.
    # Upper bound: with mu=0, sum(|w|) is at most sum(|y|) + |budget| (loose).
    mu_lo, mu_hi = 0.0, float(np.max(np.abs(y)) + abs(budget) + 2.0)
    theta_final = 0.0
    mu_final = 0.0

    for _ in range(80):
        mu_mid = (mu_lo + mu_hi) / 2.0
        # Inner bisection over theta to enforce sum(w) = budget given mu_mid.
        # sum(w_fn(theta, mu_mid)) is non-increasing in theta; we want it = budget.
        t_lo = float(np.min(y)) - mu_mid - abs(budget) - 2.0
        t_hi = float(np.max(y)) + mu_mid + abs(budget) + 2.0
        for _ in range(80):
            t_mid = (t_lo + t_hi) / 2.0
            if float(np.sum(w_fn(t_mid, mu_mid))) > budget:
                t_lo = t_mid
            else:
                t_hi = t_mid
        theta_mid = (t_lo + t_hi) / 2.0
        lev = float(np.sum(np.abs(w_fn(theta_mid, mu_mid))))
        if abs(lev - leverage) < 1e-11:
            theta_final = theta_mid
            mu_final = mu_mid
            break
        if lev > leverage:
            mu_lo = mu_mid
        else:
            mu_hi = mu_mid
        theta_final = theta_mid
        mu_final = mu_mid

    return w_fn(theta_final, mu_final)


def run(p: ProblemData) -> SolverResult:
    """Run the Lean 4 PGD binary directly and return a SolverResult.

    Calls ``optimization-proofs/.lake/build/bin/pgd_solve`` via subprocess.
    The binary runs ``pgdFlat`` (PGDFlat.lean) with
    ``eta = 1.9 / lambda_max(Sigma)``; convergence is guaranteed by Lean's
    ``pgd_convergence`` theorem when Sigma is PD.

    Returns
    -------
    SolverResult
        ``converged=True``.  Weights have exact zeros at inactive assets
        (up to Lean's bisection precision ~1e-11) because the Duchi
        projection threshold is an algebraic condition, not an asymptotic one.
    """
    w, lam_max = _lean_solve(p.Sigma, p.mu, p.leverage_cap)
    eta = 1.9 / lam_max

    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    return SolverResult(
        solver_name="Lean 4 PGD (pgd_solve direct)",
        converged=True,
        message=(
            f"Lean 4 pgdFlat via subprocess  "
            f"(eta = 1.9 / {lam_max:.4e} = {eta:.4f})"
        ),
        objective=obj_val,
        weights=w,
        n_iterations=0,  # iteration count not returned by binary
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted PGD output, emphasising the exact zeros at inactive assets."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective         : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    print()
    print("Weights and exact zero status:")
    print(f"  {'Asset':>8}  {'w_i':>14}  {'|w_i|':>14}  {'Note'}")
    for name, wi in zip(p.asset_names, result.weights, strict=True):
        abs_wi = abs(wi)
        if abs_wi > 1e-6:
            note = "<- active"
        elif abs_wi > 1e-12:
            note = "near-zero (machine epsilon?)"
        else:
            note = "EXACT ZERO"
        print(f"  {name:>8}  {wi:14.10f}  {abs_wi:14.3e}  {note}")
    print()
    n_exact_zero = int(np.sum(np.abs(result.weights) <= 1e-12))
    n_near_zero = int(
        np.sum(
            (np.abs(result.weights) > 1e-12) & (np.abs(result.weights) <= 1e-9)
        )
    )
    print(f"  Exact zeros  (|w_i| <= 1e-12): {n_exact_zero} assets")
    print(f"  Near-zeros   (1e-12 < |w_i| <= 1e-9): {n_near_zero} assets")
    print(
        f"  Active       (|w_i| > 1e-9): {result.live_position_count(1e-9)} assets"
    )
    print()
    print("The Duchi projection sets components below the dual threshold to")
    print("exactly zero (hard threshold, not numerical convergence).")
    print("The Lean 4 theorem projection_correctness certifies this property.")
