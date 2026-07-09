"""Gurobi barrier QP solver for the phantom-positions scenario.

Gurobi uses the same 2N-variable slack reformulation as trust-constr.
The barrier algorithm converges to the correct objective, but log-barrier
repulsion prevents exact zeros at inactive assets. Phantom positions appear
at magnitudes on the order of the barrier parameter at termination (~1e-8
to 1e-10 for default complementarity tolerance 1e-8).

This is a benchmark script, not production code: without gurobipy installed and a
valid license, run() raises rather than substituting a documented-but-fake result
(the phantom-position magnitude below is a fact about Gurobi's barrier method that
must come from an actual solve, not a fabricated weight vector).
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run Gurobi barrier QP. Raises if gurobipy is unavailable or unlicensed.

    Parameters
    ----------
    p:
        Problem data for the phantom-positions scenario.

    Returns
    -------
    SolverResult with correct objective but nonzero phantom weights at
    inactive assets.
    """
    try:
        return _run_gurobi(p)
    except ImportError as exc:
        raise RuntimeError(
            "gurobipy is required for this benchmark (phantom_positions Gurobi "
            "solver); install it and provide a valid license before running "
            "reports/benchmark_all_solvers.py, or exclude this solver explicitly."
        ) from exc
    except Exception as exc:
        return SolverResult(
            solver_name="Gurobi barrier (error)",
            converged=False,
            message=str(exc),
            objective=float("nan"),
            weights=np.zeros(p.N),
            n_iterations=0,
            budget_error=float("nan"),
            leverage_violation=float("nan"),
        )


def _run_gurobi(p: ProblemData) -> SolverResult:
    """Run Gurobi with a valid license."""
    import gurobipy as gp
    from gurobipy import GRB

    N = p.N
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1)  # show barrier log
    env.start()

    m = gp.Model("phantom_positions", env=env)
    # No per-asset box bounds -- u, v >= 0 only.
    u = m.addVars(N, lb=0.0, name="u")
    v = m.addVars(N, lb=0.0, name="v")

    # Objective: (1/2)(u-v)' Sigma (u-v) - mu'(u-v)
    obj = gp.QuadExpr()
    for i in range(N):
        for j in range(N):
            obj += 0.5 * p.Sigma[i, j] * (u[i] - v[i]) * (u[j] - v[j])
    for i in range(N):
        obj -= p.mu[i] * (u[i] - v[i])
    m.setObjective(obj, GRB.MINIMIZE)

    m.addConstr(gp.quicksum(u[i] - v[i] for i in range(N)) == 1.0, "budget")
    m.addConstr(
        gp.quicksum(u[i] + v[i] for i in range(N)) <= p.leverage_cap,
        "leverage",
    )

    m.optimize()

    w = np.array([u[i].X - v[i].X for i in range(N)])
    u_vals = np.array([u[i].X for i in range(N)])
    v_vals = np.array([v[i].X for i in range(N)])

    print(f"\nStatus      : {m.Status}  (2 = OPTIMAL)")
    print(f"ObjVal      : {m.ObjVal:.15f}")
    print(f"BarIterCount: {m.BarIterCount}")
    print()
    print("Recovered weights w = u - v:")
    for name, wi, ui, vi in zip(p.asset_names, w, u_vals, v_vals, strict=True):
        print(f"  {name:8s}: w = {wi:+.10f}  (u = {ui:.3e}, v = {vi:.3e})")

    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)
    converged = m.Status == GRB.OPTIMAL

    return SolverResult(
        solver_name="Gurobi barrier QP (2N vars)",
        converged=converged,
        message=f"Gurobi status={m.Status}",
        objective=float(obj_val),
        weights=w,
        n_iterations=int(m.BarIterCount),
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


# Expected behavior without gurobipy (kept for context; run() raises instead of
# returning this as a fabricated result). Gurobi uses the 2N-variable
# reformulation w = u - v, with u, v >= 0 enforced by a log-barrier term:
#
#     B(x; mu_B) = f(w) - mu_B * sum(log(u_i) + log(v_i))
#
# For inactive assets (w_i* = 0), the barrier optimality condition for u_i, v_i is
# (partial f / partial u_i) - mu_B / u_i = 0, so u_i = mu_B / (KKT complementarity
# multiplier). With default complementarity gap tolerance 1e-8 and multiplier
# ~0.1 for this problem, u_i, v_i ~ 1e-8 / 0.1 = 1e-7 for inactive assets, giving
# phantom |w_i| = |u_i - v_i| ~ 1e-7 to 1e-8. Gurobi reports OPTIMAL (status=2)
# because the duality gap is below the complementarity tolerance, not because
# w* = 0 for inactive assets.
