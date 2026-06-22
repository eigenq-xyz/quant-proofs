"""SciPy trust-constr (interior-point barrier) solver for the step-divergence scenario.

No per-asset box bounds. The 2N-variable reformulation (w = u - v,
|w| = u + v, u,v >= 0) suffices to enforce the gross leverage constraint
without additionally bounding u and v from above.

Uses the post-shock shrunk covariance (Sigma_shock) and mean returns (mu_shock).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy trust-constr and return a standardised SolverResult.

    The 2N-variable reformulation used internally:
        min  (1/2)(u-v)' Sigma_shock (u-v) - mu_shock'(u-v)
        s.t. sum(u-v) = 1    (budget)
             sum(u+v) <= L   (leverage)
             u, v >= 0       (no upper bound)
    """
    N = p.N

    def obj_uv(x: np.ndarray) -> float:
        w = x[:N] - x[N:]
        return p.objective(w)

    A = np.zeros((2, 2 * N))
    A[0, :N] = 1.0
    A[0, N:] = -1.0  # budget: sum(u - v) = 1
    A[1, :N] = 1.0
    A[1, N:] = 1.0  # leverage: sum(u + v) <= L

    bounds = Bounds(np.zeros(2 * N), np.full(2 * N, np.inf))
    lc = LinearConstraint(A, [1.0, 0.0], [1.0, p.leverage_cap])
    x0 = np.ones(2 * N) / (2 * N)

    res = minimize(
        obj_uv,
        x0,
        method="trust-constr",
        bounds=bounds,
        constraints=lc,
        tol=1e-12,
    )

    w = res.x[:N] - res.x[N:]
    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy trust-constr (barrier)",
        converged=bool(res.success),
        message=res.message,
        objective=obj_val,
        weights=w,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective         : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    print("Nonzero weights   :")
    for ind, wi in zip(p.industries, result.weights, strict=True):
        if abs(wi) > 1e-4:
            print(f"  {ind:6s}  {wi:+.6f}")
    if result.converged:
        print()
        print(
            "trust-constr converged via the 2N-variable barrier reformulation."
        )
