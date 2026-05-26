"""SciPy trust-constr (interior-point barrier) solver for the cholesky-crash scenario.

Run on the raw (rank-deficient) sample covariance S via p.raw_objective.
Uses the 2N-variable slack reformulation (w = u - v, u, v >= 0) to smooth
the L1 leverage constraint. The non-PSD Hessian causes trust-constr to
encounter an indefinite barrier Hessian, leading to premature termination
or numerical failure despite reporting a nominal convergence status.

Compare with SLSQP: SLSQP explicitly fails (iteration limit); trust-constr
may report success but converges to a suboptimal point due to the ill-conditioned
null-space directions in the rank-deficient S.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy trust-constr on the raw (rank-deficient) S covariance.

    Uses the 2N-variable reformulation to smooth the L1 constraint.
    The raw (non-PSD) Hessian causes numerical instability.
    """
    N = p.N

    def obj_uv(x: np.ndarray) -> float:
        w = x[:N] - x[N:]
        return p.raw_objective(w)

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
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy trust-constr on raw S",
        converged=bool(res.success),
        message=res.message,
        objective=float(p.raw_objective(w)),
        weights=w,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )
