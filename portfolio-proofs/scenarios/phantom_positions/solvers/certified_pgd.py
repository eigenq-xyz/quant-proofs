"""Reference PGD implementation for the phantom-positions scenario.

Projected Gradient Descent with the Duchi et al. (2008) dual-bisection
projection onto the intersection of the budget hyperplane and the L1 ball.

This is an unverified Python implementation for benchmarking and demonstration
purposes only. The Lean 4 implementation in optimization-proofs/ provides the
formally certified guarantees (projection_correctness theorem).

Key property: the Duchi projection sets components to exactly zero when
|y_i - theta*| <= mu*, an algebraic condition on the dual bisection output.
This is not an asymptotic statement -- components below the threshold are set
to zero by construction in the projection algorithm, not by numerical
convergence toward zero. PGD with Duchi projection therefore produces exact
zeros (or machine-epsilon zeros) at inactive assets.

Compare with the barrier methods (trust-constr, Gurobi): those methods
approach zero asymptotically as the barrier parameter mu_B -> 0, but never
reach exactly zero in finite iterations.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult


def _project_budget_l1(
    y: np.ndarray, budget: float, leverage: float
) -> np.ndarray:
    """Project y onto {w : sum(w) = budget, sum(|w|) <= leverage}.

    Uses the dual-bisection algorithm derived from Duchi et al. (2008). The
    projection allows negative weights (unlike the simplex projection, which
    enforces w >= 0). The feasible set here is the intersection of a budget
    hyperplane and an L1 ball, both without a non-negativity constraint.

    The dual of this projection has the form: find (theta*, mu*) such that

        w_i* = sign(y_i - theta*) * max(|y_i - theta*| - mu*, 0)

    satisfies sum(w_i*) = budget and sum(|w_i*|) = leverage. The dual
    bisection finds (theta*, mu*) via nested binary search:

        Outer loop: bisect over mu >= 0 to enforce sum(|w|) = leverage.
        Inner loop: for each mu_mid, bisect over theta to enforce sum(w) = budget.

    Step 1: Check if the L1 constraint is inactive (unconstrained budget
            projection suffices). The unconstrained minimiser of (1/2)||w-y||^2
            subject to sum(w) = budget is w = y - ((sum(y)-budget)/N) * 1.
            If this satisfies sum(|w|) <= leverage, return it directly.

    Step 2: Otherwise the L1 constraint is active. Use nested bisection.

    Key property: components with |y_i - theta*| <= mu* are set to exactly
    zero by the max(..., 0) operation. This is a hard algebraic threshold,
    not an asymptotic limit. When the bisection converges, the inactive
    assets have w_i* = 0 exactly (up to bisection precision ~1e-11).

    Parameters
    ----------
    y:
        Input vector to project.
    budget:
        Target budget: sum(w) = budget.
    leverage:
        L1 cap: sum(|w|) <= leverage.

    Returns
    -------
    w:
        Projected vector satisfying sum(w) = budget and sum(|w|) <= leverage.
    """
    N = len(y)

    # Step 1: Check if L1 constraint is inactive
    # Unconstrained budget projection: shift y uniformly
    theta_unconstrained = (float(np.sum(y)) - budget) / N
    w_unconstrained = y - theta_unconstrained
    if float(np.sum(np.abs(w_unconstrained))) <= leverage + 1e-12:
        return w_unconstrained

    # Step 2: L1 constraint is active; use nested dual bisection
    # Parametrize: w_i(theta, mu) = sign(y_i - theta) * max(|y_i - theta| - mu, 0)
    def w_fn(theta: float, mu: float) -> np.ndarray:
        """Compute projected weights given dual variables (theta, mu)."""
        diff = y - theta
        return np.sign(diff) * np.maximum(np.abs(diff) - mu, 0.0)

    # Outer bisection over mu in [0, mu_hi] to enforce sum(|w|) = leverage.
    # Upper bound: with mu=0, sum(|w|) is at most sum(|y|) + |budget| (loose).
    mu_lo, mu_hi = 0.0, float(np.max(np.abs(y)) + abs(budget) + 2.0)
    theta_final = 0.0
    mu_final = 0.0

    for _ in range(80):
        mu_mid = (mu_lo + mu_hi) / 2.0
        # Inner bisection over theta to enforce sum(w) = budget given mu_mid.
        # sum(w_fn(theta, mu_mid)) is non-increasing in theta; we want it = budget.
        t_lo = float(np.min(y)) - mu_mid - abs(budget) - 2.0
        t_hi = float(np.max(y)) + mu_mid + abs(budget) + 2.0
        for _ in range(80):
            t_mid = (t_lo + t_hi) / 2.0
            if float(np.sum(w_fn(t_mid, mu_mid))) > budget:
                t_lo = t_mid
            else:
                t_hi = t_mid
        theta_mid = (t_lo + t_hi) / 2.0
        lev = float(np.sum(np.abs(w_fn(theta_mid, mu_mid))))
        if abs(lev - leverage) < 1e-11:
            theta_final = theta_mid
            mu_final = mu_mid
            break
        if lev > leverage:
            mu_lo = mu_mid
        else:
            mu_hi = mu_mid
        theta_final = theta_mid
        mu_final = mu_mid

    return w_fn(theta_final, mu_final)


def run(
    p: ProblemData,
    step_size_factor: float = 1.9,
    tol: float = 1e-10,
    max_iter: int = 10_000,
) -> SolverResult:
    """Run reference PGD with Duchi projection and return a SolverResult.

    The step size is eta = step_size_factor / lambda_max(Sigma). For
    convergence we need eta < 2 / lambda_max; setting step_size_factor = 1.9
    is safe and close to the Lipschitz bound.

    For this problem: lambda_max(Sigma) = sigma_sq = 0.04, so
    eta = 1.9 / 0.04 = 47.5.

    The algorithm terminates when ||w_{k+1} - w_k||_2 < tol. Because the
    Duchi projection produces exact zeros at inactive assets (not merely
    small values), the final weights have exactly 2 nonzero entries matching
    the KKT-certified solution.

    Parameters
    ----------
    p:
        Problem data for the phantom-positions scenario.
    step_size_factor:
        Numerator for step size; must be < 2.0.
    tol:
        Convergence tolerance on consecutive iterates.
    max_iter:
        Maximum number of gradient steps.

    Returns
    -------
    SolverResult with exact zero weights at inactive assets.
    """
    lam_max = float(np.linalg.eigvalsh(p.Sigma)[-1])
    eta = step_size_factor / lam_max  # = 47.5 for this problem

    # Initialise at equal weights
    w = np.ones(p.N) / p.N

    n_iters = max_iter
    for k in range(max_iter):
        grad = p.Sigma @ w - p.mu
        y = w - eta * grad
        w_new = _project_budget_l1(y, budget=1.0, leverage=p.leverage_cap)
        if float(np.linalg.norm(w_new - w)) < tol:
            n_iters = k + 1
            w = w_new
            break
        w = w_new

    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)
    converged = n_iters < max_iter

    return SolverResult(
        solver_name="Reference PGD (Duchi projection)",
        converged=converged,
        message="Converged" if converged else "Max iterations reached",
        objective=obj_val,
        weights=w,
        n_iterations=n_iters,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted PGD output, emphasising the exact zeros at inactive assets."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective         : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    print()
    print("Weights and exact zero status:")
    print(f"  {'Asset':>8}  {'w_i':>14}  {'|w_i|':>14}  {'Note'}")
    for name, wi in zip(p.asset_names, result.weights, strict=True):
        abs_wi = abs(wi)
        if abs_wi > 1e-6:
            note = "<- active"
        elif abs_wi > 1e-12:
            note = "near-zero (machine epsilon?)"
        else:
            note = "EXACT ZERO"
        print(f"  {name:>8}  {wi:14.10f}  {abs_wi:14.3e}  {note}")
    print()
    n_exact_zero = int(np.sum(np.abs(result.weights) <= 1e-12))
    n_near_zero = int(
        np.sum(
            (np.abs(result.weights) > 1e-12) & (np.abs(result.weights) <= 1e-9)
        )
    )
    print(f"  Exact zeros  (|w_i| <= 1e-12): {n_exact_zero} assets")
    print(f"  Near-zeros   (1e-12 < |w_i| <= 1e-9): {n_near_zero} assets")
    print(
        f"  Active       (|w_i| > 1e-9): {result.live_position_count(1e-9)} assets"
    )
    print()
    print("The Duchi projection sets components below the dual threshold to")
    print("exactly zero (hard threshold, not numerical convergence).")
    print("The Lean 4 theorem projection_correctness certifies this property.")
