"""Gurobi interior-point QP for the sp500-factor scenario.

Uses the standard 2N-variable slack reformulation:
  w = u - v, u,v >= 0
  sum(u-v) = 1    (budget)
  sum(u+v) <= L   (leverage)
  min (1/2)(u-v)'Sigma(u-v) - mu'(u-v)

The dense Newton step requires O((2N)^3) per iteration. At N=250 this is
approximately 1.5e8 operations per step times 25 steps = approximately 4e9 total,
which should visibly exceed 1 second on typical hardware.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from .common import ProblemData


@dataclass
class GurobiResult:
    N: int
    solve_time_ms: float
    converged: bool
    objective: float
    timed_out: bool
    n_bar_iters: int


TIMEOUT_SECONDS: float = 30.0  # fail-safe timeout per solve


def benchmark(
    p: ProblemData, reps: int = 3, timeout: float = TIMEOUT_SECONDS
) -> GurobiResult:
    """Run Gurobi and time it, with timeout handling."""
    try:
        import gurobipy as gp
        from gurobipy import GRB
    except ImportError:
        return GurobiResult(
            N=p.N,
            solve_time_ms=float("nan"),
            converged=False,
            objective=float("nan"),
            timed_out=False,
            n_bar_iters=0,
        )

    N = p.N
    times: list[float] = []
    obj_val = float("nan")
    bar_iters = 0
    timed_out = False

    for _ in range(reps):
        env = gp.Env(empty=True)
        env.setParam("OutputFlag", 0)
        env.setParam("TimeLimit", timeout)
        env.start()
        m = gp.Model(env=env)
        u = m.addVars(N, lb=0.0, name="u")
        v = m.addVars(N, lb=0.0, name="v")
        # Build quadratic objective
        obj = gp.QuadExpr()
        for i in range(N):
            for j in range(N):
                obj += 0.5 * p.Sigma[i, j] * (u[i] - v[i]) * (u[j] - v[j])
        for i in range(N):
            obj -= p.mu[i] * (u[i] - v[i])
        m.setObjective(obj, GRB.MINIMIZE)
        m.addConstr(
            gp.quicksum(u[i] - v[i] for i in range(N)) == 1.0, "budget"
        )
        m.addConstr(
            gp.quicksum(u[i] + v[i] for i in range(N)) <= p.leverage_cap,
            "leverage",
        )
        t0 = time.perf_counter()
        m.optimize()
        elapsed = (time.perf_counter() - t0) * 1000.0
        times.append(elapsed)
        if m.Status == GRB.OPTIMAL:
            obj_val = float(m.ObjVal)
            bar_iters = int(m.BarIterCount)
        elif m.Status == GRB.TIME_LIMIT:
            timed_out = True
        m.dispose()
        env.dispose()

    times.sort()
    return GurobiResult(
        N=N,
        solve_time_ms=times[len(times) // 2],
        converged=(not timed_out),
        objective=obj_val,
        timed_out=timed_out,
        n_bar_iters=bar_iters,
    )
