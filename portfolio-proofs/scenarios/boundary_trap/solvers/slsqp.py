"""SciPy SLSQP (active-set SQP) solver for the boundary-trap scenario.

The problem has no per-asset position limits. In a long-short strategy
the gross leverage cap already bounds total exposure; individual box
bounds would be a separate mandate requirement not modelled here.

SLSQP handles the L1 leverage constraint directly via active-set boundary
search on absolute-value approximations. Because |w_i| is non-differentiable
at w_i = 0, the active-set search cycles at the kink without converging
(Nocedal and Wright 2006, Ch. 16).
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy SLSQP and return a standardised SolverResult."""
    constraints = [
        {"type": "eq", "fun": lambda w: float(np.sum(w) - 1.0)},
        {
            "type": "ineq",
            "fun": lambda w: float(p.leverage_cap - np.sum(np.abs(w))),
        },
    ]
    # No per-asset box bounds — only budget and leverage constraints.
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
        solver_name="SciPy SLSQP (active-set)",
        converged=bool(res.success),
        message=res.message,
        objective=float(res.fun),
        weights=res.x,
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
    if not result.converged:
        print()
        print(
            "❌  SLSQP FAILED: active-set search cycles at the non-differentiable"
        )
        print("    |w_i|=0 boundary without converging.")
        print("    Output weights are numerically unstable.")
