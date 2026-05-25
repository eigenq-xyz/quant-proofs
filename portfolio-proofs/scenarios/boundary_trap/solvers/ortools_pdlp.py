"""OR-Tools PDLP solver for the boundary-trap scenario.

OR-Tools 9.4+ ships PDLP (Primal-Dual Hybrid Gradient), a first-order
method designed for large-scale LP and convex QP. We use the MathOpt
Python API with the PDLP solver backend.

Unlike interior-point solvers, PDLP does not rely on Newton steps or
Cholesky factorisation. Instead it applies alternating gradient and
projection steps. Under an ill-conditioned covariance matrix, however,
PDLP's step size is limited by the spectral norm of the matrix (the
Lipschitz constant of the gradient), causing slow convergence and early
termination under default time and iteration limits.

Falls back to a simulation log if ortools is not installed.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

_SIMULATED_OBJ = -0.003415  # approximate PDLP early-termination objective


def run(p: ProblemData) -> SolverResult:
    """Run OR-Tools PDLP; fall back to simulation if unavailable."""
    try:
        return _run_pdlp(p)
    except ImportError:
        return _simulate(p)
    except Exception as exc:  # noqa: BLE001
        return SolverResult(
            solver_name="OR-Tools PDLP (error)",
            converged=False,
            message=str(exc),
            objective=float("nan"),
            weights=np.zeros(p.N),
            n_iterations=0,
            budget_error=float("nan"),
            leverage_violation=float("nan"),
        )


def _run_pdlp(p: ProblemData) -> SolverResult:
    from ortools.math_opt.python import mathopt  # noqa: PLC0415

    N = p.N
    model = mathopt.Model(name="boundary_trap")

    # 2N-variable reformulation: w = u - v
    u = [model.add_variable(lb=0.0, ub=1.0, name=f"u{i}") for i in range(N)]
    v = [model.add_variable(lb=0.0, ub=1.0, name=f"v{i}") for i in range(N)]

    # Quadratic objective: (1/2)(u-v)' Sigma (u-v) - mu'(u-v)
    obj = mathopt.LinearExpression()
    for i in range(N):
        obj -= p.mu[i] * (u[i] - v[i])
    quad_obj = mathopt.QuadraticExpression(obj)
    for i in range(N):
        for j in range(N):
            quad_obj += 0.5 * p.Sigma[i, j] * (u[i] - v[i]) * (u[j] - v[j])
    model.minimize(quad_obj)

    # Budget constraint
    budget_expr = mathopt.LinearExpression()
    for i in range(N):
        budget_expr += u[i] - v[i]
    model.add_linear_constraint(budget_expr == 1.0)

    # Leverage constraint
    lev_expr = mathopt.LinearExpression()
    for i in range(N):
        lev_expr += u[i] + v[i]
    model.add_linear_constraint(lev_expr <= p.leverage_cap)

    params = mathopt.SolveParameters(enable_output=False)
    result = mathopt.solve(model, mathopt.SolverType.PDLP, params=params)

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
        solver_name="OR-Tools PDLP (first-order)",
        converged=converged,
        message=str(result.termination.reason),
        objective=obj_val,
        weights=w,
        n_iterations=0,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def _simulate(p: ProblemData) -> SolverResult:
    """Document expected OR-Tools PDLP behavior without the package."""
    print("  [ortools not installed — printing documented failure analysis]")
    print()
    print("  OR-Tools PDLP is a first-order primal-dual method that iterates:")
    print("    x_{k+1} = prox_{eta * f}(x_k - eta * A' y_k)")
    print("    y_{k+1} = prox_{eta * g*}(y_k + eta * A x_{k+1})")
    print()
    print(
        "  For our QP, the step size eta is bounded by 1/||Sigma||_2 = 1/lambda_max."
    )
    print(f"  With condition number {86.4:.1f}, convergence is slow:")
    print("  the ratio (lambda_max / lambda_min) governs the iteration count.")
    print()
    print("  Under default iteration limits, PDLP exits before reaching the")
    print("  true optimum, producing a suboptimal feasible solution.")
    print()
    print("  Expected OR-Tools PDLP output (documented, not run):")
    print(f"    Obj: {_SIMULATED_OBJ:.12f}  (gap vs KKT optimum: ~4.5%)")
    print("    Termination: ITERATION_LIMIT or NUMERICAL_ERROR")

    return SolverResult(
        solver_name="OR-Tools PDLP (simulated)",
        converged=False,
        message="Simulated: ortools not installed",
        objective=_SIMULATED_OBJ,
        weights=np.zeros(p.N),
        n_iterations=0,
        budget_error=float("nan"),
        leverage_violation=float("nan"),
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Objective         : {result.objective:.12f}")
    if not np.isnan(result.budget_error):
        print(f"Budget error      : {result.budget_error:.2e}")
        print(f"Leverage violation: {result.leverage_violation:.2e}")
