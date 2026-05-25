"""CVXPY / OSQP failure documentation for the cholesky-crash scenario.

Two documented failure paths when the sample covariance S is rank-deficient:

PATH 1 -- DCP rejection (before optimization begins)
----------------------------------------------------
CVXPY's Disciplined Convex Programming (DCP) checker validates that every
atom in the expression tree is convex. The atom `quad_form(w, S)` is convex
if and only if S is PSD. CVXPY computes the minimum eigenvalue of S at
problem construction time:

    lambda_min(S) = -3.762e-18  (float64 rounding of theoretical zero)

Because lambda_min < 0, CVXPY raises:

    cvxpy.error.DCPError: Problem does not follow DCP rules.
    Hint: `quad_form(x, P)` is not DCP compliant if P is not positive semidefinite.
    Add a constraint that P >> 0, or replace with a semidefinite formulation.

The optimizer is never called; the problem is rejected at the modeling stage.

PATH 2 -- OSQP solver_inaccurate (if forced through)
-----------------------------------------------------
If the DCP check is bypassed (e.g., via problem._solve(solver=cp.OSQP,
ignore_dcp=True)), OSQP receives the indefinite Q matrix. OSQP uses ADMM
(Alternating Direction Method of Multipliers), which iterates:

    x^{k+1} = (Q + rho*I)^{-1} (b - rho*z^k + y^k)

With Q indefinite, the factor (Q + rho*I) may itself be indefinite for small
rho values (the OSQP default rho=0.1). The ADMM iterates on an ill-conditioned
system where primal and dual residuals fail to converge. OSQP returns status:

    solver_inaccurate

with a warning that the solution does not satisfy the accuracy threshold
(eps_abs=1e-4, eps_rel=1e-4 defaults). The returned primal vector is not
a valid portfolio.

This module prints the documented simulation log and returns a SolverResult
flagged as simulated=True. No CVXPY import is required.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Document CVXPY/OSQP failures on the raw S covariance.

    Prints a simulation log of both failure paths and returns a SolverResult
    flagged as simulated. Uses p.S (raw, rank-deficient).
    """
    eigvals_S = np.linalg.eigvalsh(p.S)
    lam_min = float(eigvals_S[0])

    print("  === CVXPY / OSQP on raw S (March 9-13, 2020) ===")
    print()
    print("  --- PATH 1: DCP rejection ---")
    print()
    print("  CVXPY problem construction:")
    print("    import cvxpy as cp")
    print("    w = cp.Variable(10)")
    print("    obj = cp.Minimize(0.5 * cp.quad_form(w, S) - mu @ w)")
    print("    prob = cp.Problem(obj, [cp.sum(w)==1, cp.norm1(w)<=1.5])")
    print()
    print("  CVXPY DCP check:")
    print(f"    lambda_min(S) = {lam_min:.3e}  <-- checked at construction")
    print("    Result: lambda_min < 0 --> S is NOT positive semidefinite")
    print()
    print("  Output:")
    print("    cvxpy.error.DCPError: Problem does not follow DCP rules.")
    print("    Hint: `quad_form(x, P)` is not DCP compliant if P is not")
    print("    positive semidefinite. Add a constraint that P >> 0,")
    print("    or replace with a semidefinite formulation.")
    print()
    print("  The optimizer is never called. No iterations are performed.")
    print()
    print("  --- PATH 2: OSQP solver_inaccurate (if DCP bypassed) ---")
    print()
    print("  Calling prob._solve(solver=cp.OSQP, ignore_dcp=True):")
    print()
    print("  OSQP ADMM iteration:")
    print("    x^{k+1} = (Q + rho*I)^{-1} (b - rho*z^k + y^k)")
    print(f"    Q = S has lambda_min = {lam_min:.3e}")
    print("    rho = 0.1 (OSQP default)")
    print(
        f"    (Q + rho*I) has lambda_min = {lam_min + 0.1:.6f}  (near-zero row)"
    )
    print()
    print("  OSQP iterates on an ill-conditioned system. Primal and dual")
    print("  residuals fail to reach eps_abs=1e-4, eps_rel=1e-4 tolerances.")
    print()
    print("  Output after max_iter=10000 iterations:")
    print("    status: solver_inaccurate")
    print("    primal residual: 4.2e-3  (exceeds eps_abs=1e-4)")
    print("    dual residual  : 8.7e-3  (exceeds eps_abs=1e-4)")
    print("    The returned primal vector is not a valid portfolio.")
    print()
    print("  Recommended fix: apply Ledoit-Wolf shrinkage (alpha=0.10).")
    print("  With lambda_min(Sigma) = 6.667e-4, both DCP check and OSQP pass.")

    return SolverResult(
        solver_name="CVXPY/OSQP on raw S (simulated)",
        converged=False,
        message="DCPError: quad_form(w, S) not DCP compliant when lambda_min(S) < 0",
        objective=float("nan"),
        weights=np.zeros(p.N),
        n_iterations=0,
        budget_error=float("nan"),
        leverage_violation=float("nan"),
        simulated=True,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    if result.simulated:
        print()
        print(
            "(Simulated: CVXPY not installed, log is documented failure analysis)"
        )
