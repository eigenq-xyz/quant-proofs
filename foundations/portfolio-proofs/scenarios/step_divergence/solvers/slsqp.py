"""SciPy SLSQP (active-set SQP) solver for the step-divergence scenario.

Uses the post-shock shrunk covariance (Sigma_shock) and mean returns (mu_shock).
No per-asset box bounds; only budget and leverage constraints.

SLSQP uses its own internal step-size logic (sequential quadratic programming)
and is not affected by the Lipschitz stability violation that causes the fixed-eta
gradient descent to diverge. It converges correctly on the post-shock problem.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy SLSQP on the post-shock mean-variance problem."""
    N = p.N

    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {
            "type": "ineq",
            "fun": lambda w: float(p.leverage_cap - np.sum(np.abs(w))),
        },
    ]
    w0 = np.ones(N) / N

    res = minimize(
        p.objective,
        w0,
        method="SLSQP",
        bounds=None,
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
        leverage_violation=lev_viol,
    )
