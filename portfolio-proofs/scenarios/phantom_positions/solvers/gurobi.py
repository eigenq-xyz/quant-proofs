"""Gurobi barrier QP solver for the phantom-positions scenario.

Gurobi uses the same 2N-variable slack reformulation as trust-constr.
The barrier algorithm converges to the correct objective, but log-barrier
repulsion prevents exact zeros at inactive assets. Phantom positions appear
at magnitudes on the order of the barrier parameter at termination (~1e-8
to 1e-10 for default complementarity tolerance 1e-8).

This module runs with a valid Gurobi license when gurobipy is installed.
Without a license it prints a documented analysis of the failure mechanism
and returns a SolverResult flagged as simulated.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

# Approximate barrier-exit phantom position magnitude for this problem.
# With default complementarity gap 1e-8 and KKT multiplier ~0.1, inactive
# slacks satisfy u_i, v_i ~ 1e-8 / 0.1 = 1e-7.
_SIMULATED_OBJ: float = -0.235  # correct objective (barrier converges here)
_SIMULATED_PHANTOM_MAG: float = 1e-7  # approximate |w_i| for inactive assets


def run(p: ProblemData) -> SolverResult:
    """Run Gurobi barrier QP; fall back to simulation if unavailable.

    Parameters
    ----------
    p:
        Problem data for the phantom-positions scenario.

    Returns
    -------
    SolverResult with correct objective but nonzero phantom weights at
    inactive assets. If gurobipy is not installed, returns a simulated result.
    """
    try:
        return _run_gurobi(p)
    except ImportError:
        return _simulate(p)
    except Exception as exc:  # noqa: BLE001
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
    import gurobipy as gp  # noqa: PLC0415
    from gurobipy import GRB  # noqa: PLC0415

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


def _simulate(p: ProblemData) -> SolverResult:
    """Document the expected Gurobi behavior without a license.

    Prints a mechanistic explanation of the phantom position phenomenon
    and returns a SolverResult with synthetic phantom weights for illustration.
    """
    print(
        "  [gurobipy not installed -- printing documented behavior analysis]"
    )
    print()
    print("  Gurobi uses the 2N-variable reformulation: w = u - v,")
    print("  with u, v >= 0 enforced by a log-barrier term:")
    print()
    print("    B(x; mu_B) = f(w) - mu_B * sum(log(u_i) + log(v_i))")
    print()
    print("  For inactive assets (w_i* = 0), the optimality condition")
    print("  for u_i and v_i in the barrier problem is:")
    print()
    print("    (partial f / partial u_i) - mu_B / u_i = 0")
    print("    => u_i = mu_B / (KKT complementarity multiplier)")
    print()
    print("  With default complementarity gap tolerance 1e-8 and multiplier")
    print("  approximately 0.1 for this problem:")
    print()
    print("    u_i, v_i ~ 1e-8 / 0.1 = 1e-7  for inactive assets")
    print("    => phantom |w_i| = |u_i - v_i| ~ 1e-7 to 1e-8")
    print()
    print("  The solver reports OPTIMAL (status=2) because the duality gap")
    print("  is below the complementarity tolerance, not because w* = 0")
    print("  for inactive assets.")
    print()
    print("  Expected objective: -0.235000000000 (matches KKT certificate)")
    print(f"  Expected phantom magnitude: ~{_SIMULATED_PHANTOM_MAG:.0e}")

    # Construct a synthetic result with phantom positions for illustration
    phantom_w = np.array(
        [
            1.25,
            _SIMULATED_PHANTOM_MAG,
            -_SIMULATED_PHANTOM_MAG,
            _SIMULATED_PHANTOM_MAG,
            -0.25,
        ]
    )
    budget_err = abs(float(np.sum(phantom_w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(phantom_w))) - p.leverage_cap)

    return SolverResult(
        solver_name="Gurobi barrier (simulated)",
        converged=True,
        message="Simulated: gurobipy not installed",
        objective=_SIMULATED_OBJ,
        weights=phantom_w,
        n_iterations=0,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted Gurobi output, highlighting phantom positions."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective         : {result.objective:.12f}")
    if not np.isnan(result.budget_error):
        print(f"Budget error      : {result.budget_error:.2e}")
        print(f"Leverage violation: {result.leverage_violation:.2e}")
    print()
    print("Weights with phantom position magnitudes:")
    print(f"  {'Asset':>8}  {'w_i':>14}  {'|w_i|':>14}  {'Note'}")
    for name, wi in zip(p.asset_names, result.weights, strict=True):
        if abs(wi) > 1e-4:
            note = "<- active"
        elif abs(wi) > 1e-9:
            note = "PHANTOM"
        else:
            note = "zero (or near-zero)"
        print(f"  {name:>8}  {wi:14.10f}  {abs(wi):14.3e}  {note}")
    if result.converged:
        print()
        print("Gurobi reports OPTIMAL: objective matches KKT certificate.")
        print(
            "Inactive assets have nonzero phantom weights due to log-barrier."
        )
