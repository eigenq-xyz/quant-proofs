"""SciPy trust-constr (interior-point barrier) solver for the vix-shock scenario.

Applied to the post-shock long-only simplex problem (Sigma_post = 0.16*I,
leverage_cap = 1.0). Uses the 2N-variable slack reformulation (w = u - v,
u, v >= 0) to handle the L1 leverage constraint. Since L=1.0 and all
weights are non-negative, the leverage constraint is automatically satisfied.

trust-constr uses its own adaptive interior-point step size and is not
affected by the stale-eta failure that causes uncertified gradient descent
to oscillate between corner solutions.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy trust-constr on the post-shock long-only simplex problem."""
    N = p.N

    def obj_uv(x: np.ndarray) -> float:
        w = x[:N] - x[N:]
        return p.objective(w)

    # Budget: sum(u - v) = 1; Leverage: sum(u + v) <= L
    A = np.zeros((2, 2 * N))
    A[0, :N] = 1.0
    A[0, N:] = -1.0
    A[1, :N] = 1.0
    A[1, N:] = 1.0

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
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy trust-constr",
        converged=bool(res.success),
        message=res.message,
        objective=float(p.objective(w)),
        weights=w,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        diverged=False,
        weight_history=np.empty((0, N)),
    )
