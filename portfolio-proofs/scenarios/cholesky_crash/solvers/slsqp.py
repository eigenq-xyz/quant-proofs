"""SciPy SLSQP solver for the cholesky-crash scenario, run on the raw S covariance.

This module intentionally solves the problem using the raw (rank-deficient) sample
covariance S via p.raw_objective. SLSQP fails for two compounding reasons:

1. Non-PSD Hessian: S has rank 4 (T=5, N=10); the null space of S spans 6 directions
   along which the objective is flat. SLSQP's Hessian approximation (BFGS update)
   oscillates in these null-space directions without progress.
2. L1 kink: the gross leverage constraint sum|w| <= L is non-differentiable at w_i=0.
   Active-set cycling at the kink (Nocedal and Wright 2006, Ch. 16) is the same failure
   mode as boundary-trap, now compounded by curvature degeneracy.

The solver exhausts its 100-iteration limit and returns converged=False.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy SLSQP on the raw (rank-deficient) S covariance.

    Uses p.raw_objective to expose the non-PSD failure mode. Returns
    converged=False when the solver hits the 100-iteration limit.
    """
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
        p.raw_objective,
        w0,
        method="SLSQP",
        bounds=None,
        constraints=constraints,
        tol=1e-12,
    )

    budget_err = abs(float(np.sum(res.x)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(res.x))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy SLSQP on raw S",
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
    print(f"Objective (raw S) : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    if not result.converged:
        print()
        print(
            "SLSQP FAILED: rank-deficient Hessian (rank 4 of 10) combined with"
        )
        print("the non-differentiable L1 kink causes the active-set search to")
        print(
            "cycle without converging. The output weights are not a solution."
        )
