"""SciPy SLSQP (active-set SQP) solver for the phantom-positions scenario.

SLSQP handles the L1 leverage constraint directly via an inequality constraint
on sum(|w_i|). Because |w_i| is non-differentiable at w_i = 0, the active-set
search cycles at the kink without converging (Nocedal and Wright 2006, Ch. 16).

The non-differentiability arises because the subdifferential of |w_i| at 0 is
the interval [-1, 1], so any active-set method that requires a unique descent
direction gets stuck: it cannot determine which side of zero to move toward,
and it cycles through candidate active sets without satisfying the KKT conditions.

This solver is expected to FAIL (reach the iteration limit) on this problem.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy SLSQP on the direct L1 formulation and return a SolverResult.

    The L1 constraint sum(|w_i|) <= L is passed directly as a SciPy inequality
    constraint. This exposes the non-differentiability at w_i = 0, causing SLSQP
    to cycle at the kinks and reach the iteration limit without converging.

    Parameters
    ----------
    p:
        Problem data for the phantom-positions scenario.

    Returns
    -------
    SolverResult with converged=False and the last iterate (not a solution).
    """
    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {
            "type": "ineq",
            "fun": lambda w: float(p.leverage_cap - np.sum(np.abs(w))),
        },
    ]
    # No per-asset box bounds -- only budget and leverage constraints.
    w0 = np.ones(p.N) / p.N

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
        solver_name="SciPy SLSQP (direct L1)",
        converged=bool(res.success),
        message=res.message,
        objective=float(res.fun),
        weights=res.x,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )
