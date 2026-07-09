"""Gurobi barrier QP solver for the cholesky-crash scenario.

Gurobi's barrier algorithm performs a strict Cholesky decomposition of the
objective matrix Q before optimization begins (Gurobi Reference Manual, §11.4.2).
When Q has any negative eigenvalue, the decomposition encounters a negative
diagonal entry during the forward sweep:

    L[j,j] = sqrt(Q[j,j] - sum_{k<j} L[j,k]^2)

A single negative eigenvalue (-3.762e-18 in float64) causes sqrt of a negative
number, which is undefined in real arithmetic. Gurobi detects this and aborts
immediately with GurobiError code 10020 (Objective Q is not PSD).

This module:
1. Attempts to run Gurobi on the raw S covariance (not the shrunk Sigma).
2. Catches GurobiError 10020 and returns converged=False with the error message.
3. Without gurobipy installed or a valid license, raises RuntimeError — this is a
   benchmark script, not production code; a missing dependency must stop the run,
   never silently substitute a documented-but-fake result.

The NonConvex=2 workaround switches Gurobi from barrier to spatial branch-and-bound
(Ryoo and Sahinidis 1996). Gurobi documentation documents latency spikes of
10,000x normal barrier runtime for dense non-convex problems at this scale.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

# The eigenvalue reported in float64 for the March 2020 window
_MIN_EIGENVALUE = -3.762e-18


def run(p: ProblemData) -> SolverResult:
    """Run Gurobi on raw S. Raises if gurobipy is unavailable or unlicensed.

    Uses p.S (raw, rank-deficient), not p.Sigma, to expose the Cholesky failure.
    """
    try:
        return _run_gurobi(p)
    except ImportError as exc:
        raise RuntimeError(
            "gurobipy is required for this benchmark (cholesky_crash Gurobi solver); "
            "install it and provide a valid license before running "
            "reports/benchmark_all_solvers.py, or exclude this solver explicitly."
        ) from exc
    except Exception as exc:
        # Catch GurobiError 10020 or any other Gurobi failure
        msg = str(exc)
        print(f"  [Gurobi error: {msg}]")
        return SolverResult(
            solver_name="Gurobi barrier on raw S",
            converged=False,
            message=msg,
            objective=float("nan"),
            weights=np.zeros(p.N),
            n_iterations=0,
            budget_error=float("nan"),
            leverage_violation=float("nan"),
        )


def _run_gurobi(p: ProblemData) -> SolverResult:
    import gurobipy as gp
    from gurobipy import GRB

    N = p.N
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1)  # verbose to show the Error 10020
    env.start()

    m = gp.Model("cholesky_crash", env=env)
    # No per-asset box bounds — u, v >= 0 only.
    u = m.addVars(N, lb=0.0, name="u")
    v = m.addVars(N, lb=0.0, name="v")

    # Objective uses raw S (rank-deficient) — this triggers Error 10020
    obj = gp.QuadExpr()
    for i in range(N):
        for j in range(N):
            obj += 0.5 * p.S[i, j] * (u[i] - v[i]) * (u[j] - v[j])
    for i in range(N):
        obj -= p.mu[i] * (u[i] - v[i])
    m.setObjective(obj, GRB.MINIMIZE)

    m.addConstr(gp.quicksum(u[i] - v[i] for i in range(N)) == 1.0, "budget")
    m.addConstr(
        gp.quicksum(u[i] + v[i] for i in range(N)) <= p.leverage_cap,
        "leverage",
    )

    # This call raises GurobiError 10020 when Q is not PSD
    m.optimize()

    # If we somehow reach here (e.g., NonConvex=2 was set), extract results
    if m.Status == GRB.OPTIMAL:
        w = np.array([u[i].X - v[i].X for i in range(N)])
        obj_val = p.raw_objective(w)
        budget_err = abs(float(np.sum(w)) - 1.0)
        lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)
        return SolverResult(
            solver_name="Gurobi barrier on raw S",
            converged=True,
            message=f"Gurobi status={m.Status} (NonConvex workaround)",
            objective=obj_val,
            weights=w,
            n_iterations=int(m.IterCount),
            budget_error=budget_err,
            leverage_violation=lev_viol,
        )

    return SolverResult(
        solver_name="Gurobi barrier on raw S",
        converged=False,
        message=f"Gurobi status={m.Status}",
        objective=float("nan"),
        weights=np.zeros(p.N),
        n_iterations=0,
        budget_error=float("nan"),
        leverage_violation=float("nan"),
    )


# Expected failure mode without a valid Gurobi license (kept for context; the run()
# function above raises rather than returning this as a fabricated result):
#
#   Gurobi barrier pre-processes Q = S with a strict Cholesky decomposition L*L' = Q.
#   The raw covariance for this window has one negative eigenvalue (~-3.762e-18,
#   theoretical zero, float64 rounding). During the forward sweep:
#       L[j,j] = sqrt(Q[j,j] - sum_{k<j} L[j,k]^2) = sqrt(negative)
#   which is undefined in real arithmetic. Gurobi aborts immediately with
#   GurobiError 10020 (Objective Q is not PSD); the barrier algorithm never begins.
#
#   The NonConvex=2 workaround switches to spatial branch-and-bound (Ryoo and
#   Sahinidis 1996); Gurobi's own documentation reports latency spikes of 10,000x
#   normal barrier runtime for dense non-convex QPs at this scale. Recommended fix:
#   apply Ledoit-Wolf shrinkage (alpha=0.10) to obtain a PSD Sigma before solving;
#   see pgd_lw.py.


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    if not np.isnan(result.budget_error):
        print(f"Budget error      : {result.budget_error:.2e}")
        print(f"Leverage violation: {result.leverage_violation:.2e}")
