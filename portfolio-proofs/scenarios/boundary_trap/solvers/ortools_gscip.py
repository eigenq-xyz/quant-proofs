"""OR-Tools GSCIP solver for the boundary-trap scenario.

OR-Tools 9.4+ ships GSCIP (SCIP via the MathOpt interface), a general-purpose
solver for convex and non-convex QP. Unlike PDLP (which only handles LP),
GSCIP solves the dense quadratic objective directly without requiring a
diagonal matrix structure.

No per-asset box bounds. The 2N-variable reformulation (w = u - v, u,v >= 0)
enforces the gross leverage constraint; u and v are unbounded above.
"""

from __future__ import annotations

import numpy as np
from ortools.math_opt.python import mathopt

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run OR-Tools GSCIP and return a standardised SolverResult."""
    N = p.N
    model = mathopt.Model(name="boundary_trap")

    # 2N-variable reformulation: w = u - v, |w| = u + v, u,v >= 0
    u = [model.add_variable(lb=0.0, name=f"u{i}") for i in range(N)]
    v = [model.add_variable(lb=0.0, name=f"v{i}") for i in range(N)]

    # Quadratic objective: (1/2)(u-v)' Sigma (u-v) - mu'(u-v)
    obj_lin = mathopt.LinearExpression()
    for i in range(N):
        obj_lin -= p.mu[i] * (u[i] - v[i])
    quad_obj = mathopt.QuadraticExpression(obj_lin)
    for i in range(N):
        for j in range(N):
            quad_obj += 0.5 * p.Sigma[i, j] * (u[i] - v[i]) * (u[j] - v[j])
    model.minimize(quad_obj)

    # Budget constraint: sum(u - v) = 1
    budget = mathopt.LinearExpression()
    for i in range(N):
        budget += u[i] - v[i]
    model.add_linear_constraint(budget == 1.0)

    # Leverage constraint: sum(u + v) <= L
    lev = mathopt.LinearExpression()
    for i in range(N):
        lev += u[i] + v[i]
    model.add_linear_constraint(lev <= p.leverage_cap)

    params = mathopt.SolveParameters(enable_output=True)
    result = mathopt.solve(model, mathopt.SolverType.GSCIP, params=params)

    w = np.array(
        [
            result.variable_values()[u[i]] - result.variable_values()[v[i]]
            for i in range(N)
        ]
    )
    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)
    converged = result.termination.reason == mathopt.TerminationReason.OPTIMAL

    return SolverResult(
        solver_name="OR-Tools GSCIP",
        converged=converged,
        message=f"{result.termination.reason.name}: {result.termination.detail}",
        objective=obj_val,
        weights=w,
        n_iterations=0,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Objective         : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
