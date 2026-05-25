"""Adaptive-eta projected gradient descent for the step-divergence scenario.

Demonstrates convergence when the step size is recomputed from the post-shock
covariance rather than applied blindly from a pre-shock calibration.

The projection operator uses dual bisection onto the feasible set
C = {w : sum(w) = 1, sum|w| <= L}, allowing signed (long and short) weights.
This is the signed-weight generalization of Duchi et al. (2008).[^duchi2008]

Key difference from gd_fixed: eta is set to 1.9 / lambda_max(Sigma_shock),
which satisfies eta < 2 / lambda_max(Sigma_shock) by construction.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

_MAX_ITERATIONS = 5000
_TOL = 1e-8


# ---------------------------------------------------------------------------
# Dual-bisection projection onto {sum(w)=budget, sum|w|<=L} with signed weights
# ---------------------------------------------------------------------------


def _proj_signed_l1(
    y: np.ndarray, budget: float = 1.0, L: float = 1.5
) -> np.ndarray:
    """Project y onto {sum(w)=budget, sum|w|<=L} via dual bisection.

    Allows negative weights (long-short portfolios). The projection solves:
        min  0.5 ||w - y||^2
        s.t. sum(w) = budget,  sum|w| <= L

    KKT conditions give the closed-form per-component solution:
        w_i(lambda, mu) = sign(y_i - lambda) * max(|y_i - lambda| - mu, 0)
    where lambda is the budget dual and mu >= 0 is the leverage dual.

    When mu = 0 (L1 constraint inactive): w = y - (sum(y) - budget)/N * 1.
    When mu > 0 (L1 constraint active): find (lambda, mu) via nested bisection.

    Parameters
    ----------
    y:
        Unconstrained gradient-step point.
    budget:
        Budget equality constraint (sum of weights = budget). Default 1.0.
    L:
        Gross leverage cap (L1 norm bound). Default 1.5.

    Returns
    -------
    np.ndarray
        Projection of y onto the constrained set.
    """
    # First try: L1 constraint inactive (project onto budget hyperplane only)
    w_eq = y - (float(np.sum(y)) - budget) / len(y)
    if float(np.sum(np.abs(w_eq))) <= L + 1e-10:
        return w_eq

    # L1 constraint is active: dual bisection
    def _w(lam: float, mu: float) -> np.ndarray:
        return np.sign(y - lam) * np.maximum(np.abs(y - lam) - mu, 0.0)

    def _find_lam(mu: float) -> float:
        """Given mu, bisect to find lambda satisfying sum(w(lambda,mu)) = budget."""
        scale = float(np.max(np.abs(y))) + abs(budget) + 2.0
        lam_lo = float(np.min(y)) - scale
        lam_hi = float(np.max(y)) + scale
        for _ in range(100):
            lam_mid = (lam_lo + lam_hi) / 2.0
            if float(np.sum(_w(lam_mid, mu))) > budget:
                lam_lo = lam_mid
            else:
                lam_hi = lam_mid
        return (lam_lo + lam_hi) / 2.0

    # Bisect over mu >= 0 until sum|w(lambda(mu), mu)| = L
    scale = float(np.max(np.abs(y))) + abs(budget) + 2.0
    mu_lo, mu_hi = 0.0, scale

    for _ in range(100):
        mu_mid = (mu_lo + mu_hi) / 2.0
        lam_mid = _find_lam(mu_mid)
        lev = float(np.sum(np.abs(_w(lam_mid, mu_mid))))
        if abs(lev - L) < 1e-12:
            break
        if lev > L:
            mu_lo = mu_mid
        else:
            mu_hi = mu_mid

    mu_star = (mu_lo + mu_hi) / 2.0
    lam_star = _find_lam(mu_star)
    return _w(lam_star, mu_star)


# ---------------------------------------------------------------------------
# Adaptive-eta PGD
# ---------------------------------------------------------------------------


def run(p: ProblemData) -> SolverResult:
    """Run adaptive-eta PGD with step size recomputed from post-shock covariance.

    Parameters
    ----------
    p:
        ProblemData; uses p.Sigma_shock, p.mu_shock, p.lam_max_shock,
        p.lipschitz_bound, p.leverage_cap.

    Returns
    -------
    SolverResult
        converged=True when ||w_{k+1} - w_k|| < 1e-8.
    """
    eta_adaptive = 1.9 / p.lam_max_shock
    bound = p.lipschitz_bound  # 2 / lam_max_shock

    print("=== Adaptive-eta PGD ===")
    print()
    print(
        f"Adaptive eta = {eta_adaptive:.4f}  "
        f"< bound {bound:.2f}  (1.9 / {p.lam_max_shock:.6f}) ✓"
    )
    print(
        f"Calibrated eta from January = {p.eta_calibrated:.2f}  "
        f"(rejected — would diverge)"
    )
    print()

    w = np.ones(p.N) / p.N  # uniform start
    converged = False
    k_final = _MAX_ITERATIONS

    for k in range(_MAX_ITERATIONS):
        grad = p.Sigma_shock @ w - p.mu_shock
        w_new = _proj_signed_l1(
            w - eta_adaptive * grad, budget=1.0, L=p.leverage_cap
        )
        step_norm = float(np.linalg.norm(w_new - w))
        w = w_new

        if step_norm < _TOL:
            converged = True
            k_final = k + 1
            break

    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - p.leverage_cap)

    status = (
        "converged" if converged else f"reached max_iter={_MAX_ITERATIONS}"
    )
    print(f"Iterations     : {k_final}  ({status})")
    print(f"Objective      : {obj_val:.12f}")
    print(f"Budget error   : {budget_err:.2e}")
    print(f"Leverage viol. : {lev_viol:.2e}")
    print("Nonzero weights:")
    for ind, wi in zip(p.industries, w, strict=True):
        if abs(wi) > 1e-4:
            print(f"  {ind:6s}  {wi:+.6f}")

    return SolverResult(
        solver_name="Adaptive-eta PGD",
        converged=converged,
        message=f"||w_new - w|| < {_TOL} after {k_final} iterations"
        if converged
        else f"Reached max_iter={_MAX_ITERATIONS}",
        objective=obj_val,
        weights=w,
        n_iterations=k_final,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )
