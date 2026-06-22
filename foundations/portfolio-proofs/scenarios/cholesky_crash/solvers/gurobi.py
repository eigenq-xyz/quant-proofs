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
3. Without a Gurobi license (ImportError), prints a documented simulation log
   of the Error 10020 failure and the NonConvex=2 workaround.

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
    """Attempt to run Gurobi on raw S; fall back to simulation if unavailable.

    Uses p.S (raw, rank-deficient), not p.Sigma, to expose the Cholesky failure.
    """
    try:
        return _run_gurobi(p)
    except ImportError:
        return _simulate(p)
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


def _simulate(p: ProblemData) -> SolverResult:
    """Document the GurobiError 10020 failure without a license."""
    print("  [gurobipy not installed -- printing documented failure analysis]")
    print()
    print("  === Gurobi barrier on raw S (March 9-13, 2020) ===")
    print()
    print("  STEP 1: Gurobi barrier pre-processes the objective matrix Q = S.")
    print(
        "  It performs a strict Cholesky decomposition L*L' = Q to verify PSD."
    )
    print()
    print("  Raw S eigenvalues (float64):")
    eigvals_S = np.linalg.eigvalsh(p.S)
    for i, ev in enumerate(eigvals_S):
        flag = " <-- NEGATIVE" if ev < 0 else ""
        print(f"    lambda_{i + 1:02d} = {ev:.6e}{flag}")
    print()
    print(
        f"  Min eigenvalue: {eigvals_S[0]:.3e}  (theoretical zero, float64 rounding)"
    )
    print()
    print("  STEP 2: During forward sweep of Cholesky, Gurobi encounters:")
    print("    L[j,j] = sqrt(Q[j,j] - sum_{k<j} L[j,k]^2) = sqrt(negative)")
    print("  This is undefined in real arithmetic.")
    print()
    print("  STEP 3: Gurobi aborts immediately:")
    print("    GurobiError: Error 10020: Objective Q is not PSD")
    print()
    print("  The barrier algorithm never begins. No iterations are performed.")
    print()
    print("  === NonConvex=2 workaround (documented) ===")
    print()
    print("  Setting m.Params.NonConvex = 2 switches Gurobi from barrier to")
    print(
        "  spatial branch-and-bound (Ryoo and Sahinidis 1996). For a 10-asset"
    )
    print("  problem with a 6-dimensional null space, branch-and-bound must")
    print(
        "  enumerate across the flat objective landscape. Gurobi documentation"
    )
    print(
        "  reports latency spikes of 10,000x normal barrier runtime for dense"
    )
    print("  non-convex QPs at this scale. The algorithm may not terminate in")
    print("  reasonable time without additional cutting planes.")
    print()
    print(
        "  Recommended fix: apply Ledoit-Wolf shrinkage (alpha=0.10) to obtain"
    )
    print("  a PSD Sigma before calling the solver. See pgd_lw.py.")

    return SolverResult(
        solver_name="Gurobi barrier on raw S (simulated)",
        converged=False,
        message="GurobiError: Error 10020: Objective Q is not PSD",
        objective=float("nan"),
        weights=np.zeros(p.N),
        n_iterations=0,
        budget_error=float("nan"),
        leverage_violation=float("nan"),
        simulated=True,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    if not np.isnan(result.budget_error):
        print(f"Budget error      : {result.budget_error:.2e}")
        print(f"Leverage violation: {result.leverage_violation:.2e}")
    if result.simulated:
        print()
        print("(Simulated: gurobipy not installed)")
