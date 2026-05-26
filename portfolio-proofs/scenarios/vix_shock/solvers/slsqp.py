"""SciPy SLSQP (active-set SQP) solver for the vix-shock scenario.

Applied to the post-shock long-only simplex problem (Sigma_post = 0.16*I,
leverage_cap = 1.0). Since L=1.0 and all weights must satisfy sum(w)=1
with w_i >= 0, the L1 leverage constraint is automatically tight (sum of
non-negative weights equals the budget). SLSQP uses its own internal
step-size logic and is not affected by the stale-eta failure that causes
uncertified gradient descent to oscillate.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy SLSQP on the post-shock long-only simplex problem."""
    N = p.N

    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {
            "type": "ineq",
            "fun": lambda w: float(p.leverage_cap - np.sum(np.abs(w))),
        },
    ]
    # Long-only: w_i >= 0
    bounds = [(0.0, None)] * N
    w0 = np.ones(N) / N

    res = minimize(
        p.objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        tol=1e-12,
    )

    budget_err = abs(float(np.sum(res.x)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(res.x))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy SLSQP",
        converged=bool(res.success),
        message=res.message,
        objective=float(res.fun),
        weights=res.x,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        diverged=False,
        weight_history=np.empty((0, N)),
    )
