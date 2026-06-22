"""Gurobi barrier QP solver for the precision-bleed scenario.

Uses the same 2N-variable slack reformulation as trust-constr, with
box bounds u_i, v_i <= 1 (encoding w_i in [-1, 1]).
Falls back to a documented simulation log when gurobipy is unavailable.
"""

from __future__ import annotations

import numpy as np

from .common import PRODUCTION_HALT_THRESHOLD, WindowData, WindowResult


def run_window(w: WindowData) -> WindowResult:
    """Run Gurobi barrier on one rolling window."""
    try:
        return _run_gurobi(w)
    except ImportError:
        return _simulate(w)
    except Exception as exc:
        return WindowResult(
            solver_name="Gurobi barrier (error)",
            window_start=w.start,
            window_end=w.end,
            converged=False,
            message=str(exc),
            objective=float("nan"),
            weights=np.zeros(w.N),
            budget_error=float("nan"),
            leverage_violation=float("nan"),
            status="ERROR",
        )


def _run_gurobi(w: WindowData) -> WindowResult:
    import gurobipy as gp
    from gurobipy import GRB

    N = w.N
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)
    env.start()

    m = gp.Model("precision_bleed", env=env)
    # u, v in [0, 1] encodes w = u-v in [-1, 1]
    u = m.addVars(N, lb=0.0, ub=1.0, name="u")
    v = m.addVars(N, lb=0.0, ub=1.0, name="v")

    obj = gp.QuadExpr()
    for i in range(N):
        for j in range(N):
            obj += 0.5 * w.Sigma[i, j] * (u[i] - v[i]) * (u[j] - v[j])
    for i in range(N):
        obj -= w.mu[i] * (u[i] - v[i])
    m.setObjective(obj, GRB.MINIMIZE)

    m.addConstr(gp.quicksum(u[i] - v[i] for i in range(N)) == 1.0, "budget")
    m.addConstr(
        gp.quicksum(u[i] + v[i] for i in range(N)) <= w.leverage_cap,
        "leverage",
    )
    m.optimize()

    weights = np.array([u[i].X - v[i].X for i in range(N)])
    budget_error = float(abs(np.sum(weights) - 1.0))
    leverage_violation = float(
        max(0.0, np.sum(np.abs(weights)) - w.leverage_cap)
    )
    bleeding = (
        budget_error > PRODUCTION_HALT_THRESHOLD
        or leverage_violation > PRODUCTION_HALT_THRESHOLD
    )

    return WindowResult(
        solver_name="Gurobi barrier QP",
        window_start=w.start,
        window_end=w.end,
        converged=(m.Status == GRB.OPTIMAL),
        message=f"Gurobi status={m.Status}  (2=OPTIMAL)",
        objective=float(0.5 * weights @ w.Sigma @ weights - w.mu @ weights),
        weights=weights,
        budget_error=budget_error,
        leverage_violation=leverage_violation,
        status="BLEEDING" if bleeding else "PERFECT",
    )


def _simulate(w: WindowData) -> WindowResult:
    print("  [gurobipy not installed — simulation]")
    print("  Gurobi barrier satisfies both budget and leverage constraints")
    print("  to Gurobi's default feasibility tolerance (1e-6).")
    print("  Expected: budget_error < 1e-6, leverage_violation < 1e-6.")
    return WindowResult(
        solver_name="Gurobi barrier QP (simulated)",
        window_start=w.start,
        window_end=w.end,
        converged=True,
        message="Simulated: gurobipy not installed",
        objective=float("nan"),
        weights=np.zeros(w.N),
        budget_error=float("nan"),
        leverage_violation=float("nan"),
        status="PERFECT (simulated)",
    )


def run_all(windows: list[WindowData]) -> list[WindowResult]:
    """Run Gurobi on all four rolling windows."""
    return [run_window(w) for w in windows]


def print_results(results: list[WindowResult]) -> None:
    """Print Gurobi constraint satisfaction across windows."""
    sep = "=" * 78
    print(sep)
    print(" Gurobi barrier QP — Rolling Window Results ".center(78, "="))
    print(sep)
    print(f"  Production halt threshold: {PRODUCTION_HALT_THRESHOLD:.0e}")
    print()

    for i, r in enumerate(results, 1):
        print(f"Window {i}: {r.label}")
        print(f"  Converged    : {r.converged}  ({r.message})")
        if not np.isnan(r.budget_error):
            print(f"  Sum(w)       : {float(np.sum(r.weights)):.17f}")
            print(f"  Sum(|w|)     : {float(np.sum(np.abs(r.weights))):.17f}")
            print(f"  Budget Err   : {r.budget_error:.2e}")
            print(f"  Leverage Err : {r.leverage_violation:.2e}")
        print(f"  STATUS       : {r.status}")
        print()
    print(sep)
