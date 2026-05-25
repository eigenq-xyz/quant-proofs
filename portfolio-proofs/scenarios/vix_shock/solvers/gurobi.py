"""Gurobi QP solver for the vix-shock scenario (long-only simplex, post-shock).

The long-only simplex problem is:

    min  (1/2) w' Sigma w - mu' w
    s.t. sum(w_i) = 1   (budget)
         w_i >= 0       (long-only; no short positions)

Because all w_i >= 0 and sum(w_i) = 1, the gross leverage sum(|w_i|) = sum(w_i) = 1 <= L
is automatically satisfied. There is no need for slack variables or an L1 reformulation.
Gurobi solves this directly as a convex QP with N non-negative variables and one equality
constraint, yielding the post-shock optimum as a ground-truth check.

This module gracefully handles a missing gurobipy installation with a documented
description of the expected output.
"""

from __future__ import annotations

import numpy as np

from .common import W_STAR_POST, ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run Gurobi QP on the post-shock long-only simplex; fall back gracefully."""
    try:
        return _run_gurobi(p)
    except ImportError:
        return _simulate(p)
    except Exception as exc:  # noqa: BLE001
        return SolverResult(
            solver_name="Gurobi QP (error)",
            converged=False,
            message=str(exc),
            objective=float("nan"),
            weights=np.zeros(p.N),
            n_iterations=0,
            budget_error=float("nan"),
            diverged=False,
            weight_history=np.zeros((1, p.N)),
        )


def _run_gurobi(p: ProblemData) -> SolverResult:
    import gurobipy as gp  # noqa: PLC0415
    from gurobipy import GRB  # noqa: PLC0415

    N = p.N
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 1)  # verbose barrier log
    env.start()

    m = gp.Model("vix_shock", env=env)

    # Variables: w_i >= 0 directly (long-only; no slack needed)
    w_vars = m.addVars(N, lb=0.0, name="w")

    # Objective: (1/2) w' Sigma w - mu' w
    obj = gp.QuadExpr()
    for i in range(N):
        for j in range(N):
            obj += 0.5 * p.Sigma[i, j] * w_vars[i] * w_vars[j]
    for i in range(N):
        obj -= p.mu[i] * w_vars[i]
    m.setObjective(obj, GRB.MINIMIZE)

    # Budget constraint: sum(w_i) = 1
    m.addConstr(gp.quicksum(w_vars[i] for i in range(N)) == 1.0, "budget")
    # No L1 constraint: sum(|w_i|) = sum(w_i) = 1 <= L automatically

    m.optimize()

    w = np.array([w_vars[i].X for i in range(N)])
    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    converged = m.Status == GRB.OPTIMAL

    return SolverResult(
        solver_name="Gurobi QP (post-shock)",
        converged=converged,
        message=f"Gurobi status={m.Status} (2=OPTIMAL)",
        objective=obj_val,
        weights=w,
        n_iterations=int(m.BarIterCount),
        budget_error=budget_err,
        diverged=False,
        weight_history=w.reshape(1, p.N),
    )


def _simulate(p: ProblemData) -> SolverResult:
    """Document the expected Gurobi output without a license installed."""
    print("  [gurobipy not installed -- printing documented expected output]")
    print()
    print("  Gurobi solves the long-only simplex QP directly:")
    print("  N=3 variables w_i >= 0, one equality constraint sum(w_i)=1.")
    print("  No L1 reformulation required since sum(|w_i|) = sum(w_i) = 1.")
    print()
    w_sim = W_STAR_POST.copy()
    obj_sim = p.objective(w_sim)
    print("  Expected Gurobi output:")
    print("    Status: 2 (OPTIMAL)")
    print(f"    ObjVal: {obj_sim:.15f}")
    print(f"    Weights: {w_sim}")
    print(f"    Budget: sum(w) = {np.sum(w_sim):.10f}")

    return SolverResult(
        solver_name="Gurobi QP (simulated -- gurobipy not installed)",
        converged=True,
        message="Simulated: gurobipy not installed",
        objective=obj_sim,
        weights=w_sim,
        n_iterations=0,
        budget_error=abs(float(np.sum(w_sim)) - 1.0),
        diverged=False,
        weight_history=w_sim.reshape(1, p.N),
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted Gurobi solver output."""
    print(f"Converged  : {result.converged}")
    print(f"Message    : {result.message}")
    print(f"Objective  : {result.objective:.15f}")
    if not np.isnan(result.budget_error):
        print(f"Budget err : {result.budget_error:.2e}")
    print()
    print("Weights:")
    for name, wi in zip(p.asset_names, result.weights, strict=True):
        print(f"  {name:12s}  {wi:.10f}")
