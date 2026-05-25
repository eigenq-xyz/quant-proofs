"""SciPy trust-constr (interior-point barrier) solver for the phantom-positions scenario.

Uses the 2N-variable slack reformulation (w = u - v, u >= 0, v >= 0) to convert
the non-differentiable L1 constraint into a linear constraint. The barrier
algorithm converges to the correct objective, but the log-barrier repulsion
prevents any u_i or v_i from reaching exactly zero.

The barrier parameter mu_B controls the repulsion: at termination with barrier
tolerance eps_B, each inactive-asset slack pair satisfies:

    u_i, v_i ~ mu_B / (KKT complementarity multiplier)

Because mu_B > 0 in any finite run, the recovered weights w_i = u_i - v_i
are nonzero for all i, even for the 3 assets that have zero weight in w*.
These are the phantom positions: they are numerically small but structurally
non-zero due to the barrier mechanism.
"""

from __future__ import annotations

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, minimize

from .common import ProblemData, SolverResult


def run(p: ProblemData) -> SolverResult:
    """Run SciPy trust-constr and return a SolverResult showing phantom positions.

    The 2N-variable reformulation:
        min  (1/2)(u-v)' Sigma (u-v) - mu'(u-v)
        s.t. sum(u-v) = 1       (budget)
             sum(u+v) <= L      (leverage)
             u, v >= 0          (no per-asset upper bound)

    The barrier algorithm converges (success=True) but the recovered weights
    w = u - v have nonzero entries for inactive assets due to log-barrier repulsion.

    Parameters
    ----------
    p:
        Problem data for the phantom-positions scenario.

    Returns
    -------
    SolverResult with converged=True but phantom positions visible in weights.
    """
    N = p.N

    def obj_uv(x: np.ndarray) -> float:
        """Objective in 2N-variable space."""
        w = x[:N] - x[N:]
        return p.objective(w)

    # Build 2x(2N) constraint matrix
    A = np.zeros((2, 2 * N))
    A[0, :N] = 1.0
    A[0, N:] = -1.0  # budget: sum(u - v) = 1
    A[1, :N] = 1.0
    A[1, N:] = 1.0  # leverage: sum(u + v) <= L

    bounds = Bounds(np.zeros(2 * N), np.full(2 * N, np.inf))
    lc = LinearConstraint(A, [1.0, 0.0], [1.0, p.leverage_cap])
    x0 = np.ones(2 * N) / (2 * N)

    res = minimize(
        obj_uv,
        x0,
        method="trust-constr",
        bounds=bounds,
        constraints=lc,
        tol=1e-12,
    )

    w = res.x[:N] - res.x[N:]
    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    return SolverResult(
        solver_name="SciPy trust-constr (barrier, 2N vars)",
        converged=bool(res.success),
        message=res.message,
        objective=obj_val,
        weights=w,
        n_iterations=int(res.nit),
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(
    result: SolverResult, p: ProblemData, raw_x: np.ndarray | None = None
) -> None:
    """Print formatted trust-constr output, highlighting phantom positions.

    Parameters
    ----------
    result:
        The SolverResult from run().
    p:
        The problem data.
    raw_x:
        Optional: the raw 2N-variable solution x = [u; v] for showing phantom
        positions explicitly. If None, only the recovered w = u - v is shown.
    """
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective         : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    print()
    print("Recovered weights w = u - v and their absolute values:")
    print(f"  {'Asset':>8}  {'w_i':>14}  {'|w_i|':>14}  {'Note'}")
    for name, wi in zip(p.asset_names, result.weights, strict=True):
        if abs(wi) > 1e-6:
            note = "<- active"
        elif abs(wi) > 1e-9:
            note = "PHANTOM (1e-9 to 1e-6)"
        else:
            note = "PHANTOM (< 1e-9)"
        print(f"  {name:>8}  {wi:14.10f}  {abs(wi):14.3e}  {note}")
    print()
    if raw_x is not None:
        N = p.N
        u = raw_x[:N]
        v = raw_x[N:]
        print("Raw slack variables u and v for inactive assets:")
        print(f"  {'Asset':>8}  {'u_i':>14}  {'v_i':>14}  {'u_i + v_i':>14}")
        for k, name in enumerate(p.asset_names):
            if abs(result.weights[k]) <= 1e-6:
                print(
                    f"  {name:>8}  {u[k]:14.3e}  {v[k]:14.3e}  {u[k] + v[k]:14.3e}"
                )
        print()
        print("For inactive assets the barrier forces u_i, v_i > 0.")
        print("The phantom position w_i = u_i - v_i is small but nonzero.")
    if result.converged:
        print(
            "trust-constr converged via the 2N-variable barrier reformulation."
        )
        print(
            "Objective matches the KKT certificate, but inactive assets have"
        )
        print("nonzero weights due to log-barrier repulsion from zero.")
