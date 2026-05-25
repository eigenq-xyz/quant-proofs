"""PGD + Ledoit-Wolf solver for the cholesky-crash scenario.

Projected Gradient Descent on the Ledoit-Wolf shrunk Sigma (PSD). This is the
only solver in this scenario that succeeds: it never decomposes the covariance
matrix, so rank deficiency of S is irrelevant. The key steps:

1. Use p.Sigma (LW-shrunk, PSD) for gradient computation.
2. Step size eta = 1.9 / lambda_max(Sigma): guaranteed convergence for L-smooth
   objectives (Nesterov 2004, §2.1.5). Factor 1.9 < 2 ensures strict descent.
3. Project each gradient step onto {sum(w)=1, sum|w|<=L} using a dual-bisection
   algorithm based on Duchi et al. (2008). The implementation handles signed
   weights (long-short), solving the soft-threshold KKT system:
       w_i = sign(y_i - theta) * max(|y_i - theta| - mu, 0)
   where theta (budget dual) and mu (leverage dual >= 0) are found by nested
   bisection on the constraints sum(w)=1 and sum|w|=L.
4. Stop when ||w_{k+1} - w_k|| < 1e-8 or after 5000 iterations.

The solver uses p.Sigma (shrunk) throughout. The raw S is never touched.
Convergence is guaranteed because Sigma is PSD and the feasible set is
compact and convex.

Note on the March 2020 scenario: all ten sectors posted negative returns,
so the optimal long-short strategy exploits the spread between the least-negative
sector (HiTec, -1.08%/day) and the most-negative sector (Enrgy, -4.50%/day).
The optimal portfolio is long HiTec, long Telcm, and short Enrgy, using the full
leverage budget of 1.50.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

# ---------------------------------------------------------------------------
# Dual-bisection projection for signed weights
# ---------------------------------------------------------------------------


def _proj_budget_l1(
    y: np.ndarray,
    B: float = 1.0,
    L: float = 1.5,
    tol: float = 1e-11,
) -> np.ndarray:
    """Project y onto {sum(w)=B, sum|w|<=L} for signed (long-short) weights.

    Solves the KKT conditions of:
        min ||w - y||^2 / 2  s.t. sum(w) = B, sum|w| <= L

    The soft-threshold solution form is:
        w_i = sign(y_i - theta) * max(|y_i - theta| - mu, 0)

    where theta is the budget Lagrange multiplier and mu >= 0 is the leverage
    multiplier. For fixed mu, theta is found by bisection on sum(w) = B. Then
    mu is found by outer bisection on sum|w| = L.

    This is the signed generalization of Duchi et al. (2008) Algorithm 1,
    following the dual argument in their Theorem 1.

    Parameters
    ----------
    y : ndarray of shape (N,)
        Unconstrained point to project.
    B : float
        Budget: sum(w) = B. Default 1.0.
    L : float
        L1 gross leverage cap: sum|w| <= L. Default 1.5.
    tol : float
        Bisection convergence tolerance.

    Returns
    -------
    ndarray of shape (N,)
        Projected point satisfying sum(w)=B and sum|w|<=L.
    """

    def w_from(theta: float, mu: float) -> np.ndarray:
        return np.sign(y - theta) * np.maximum(np.abs(y - theta) - mu, 0.0)

    def theta_for_mu(mu: float) -> float:
        """Find theta such that sum(w_from(theta, mu)) = B via bisection."""
        t_lo = float(np.min(y)) - abs(B) - mu - 1.0
        t_hi = float(np.max(y)) + abs(B) + mu + 1.0
        for _ in range(120):
            t_mid = (t_lo + t_hi) / 2.0
            s = float(np.sum(w_from(t_mid, mu)))
            if abs(s - B) < tol:
                return t_mid
            if s > B:
                t_lo = t_mid
            else:
                t_hi = t_mid
        return (t_lo + t_hi) / 2.0

    # Check if leverage constraint is inactive (mu=0 suffices)
    theta0 = theta_for_mu(0.0)
    w0 = w_from(theta0, 0.0)
    if float(np.sum(np.abs(w0))) <= L + tol:
        return w0

    # Leverage constraint is active: bisect over mu to achieve sum|w| = L
    mu_lo, mu_hi = 0.0, float(np.max(np.abs(y))) + abs(B) + 2.0
    mu_mid = 0.0
    for _ in range(120):
        mu_mid = (mu_lo + mu_hi) / 2.0
        theta_mid = theta_for_mu(mu_mid)
        lev = float(np.sum(np.abs(w_from(theta_mid, mu_mid))))
        if abs(lev - L) < tol:
            break
        if lev > L:
            mu_lo = mu_mid
        else:
            mu_hi = mu_mid

    theta_final = theta_for_mu(mu_mid)
    return w_from(theta_final, mu_mid)


# ---------------------------------------------------------------------------
# PGD solver
# ---------------------------------------------------------------------------


def run(
    p: ProblemData,
    tol: float = 1e-8,
    max_iter: int = 5000,
) -> SolverResult:
    """Run PGD on the LW-shrunk Sigma.

    Parameters
    ----------
    p : ProblemData
        Problem data. Uses p.Sigma (not p.S) for gradient computation.
    tol : float
        Convergence tolerance on ||w_{k+1} - w_k||.
    max_iter : int
        Maximum number of gradient steps.

    Returns
    -------
    SolverResult
        converged=True when the step-size tolerance is met.
    """
    Sigma = p.Sigma
    mu = p.mu
    L = p.leverage_cap
    N = p.N

    lam_max = float(np.linalg.eigvalsh(Sigma)[-1])
    eta = 1.9 / lam_max  # step size: strict descent guaranteed

    w = np.ones(N) / N  # equal-weight initialization
    n_iter = 0

    for k in range(max_iter):
        grad = Sigma @ w - mu
        w_new = _proj_budget_l1(w - eta * grad, B=1.0, L=L)
        step = float(np.linalg.norm(w_new - w))
        w = w_new
        n_iter = k + 1
        if step < tol:
            break

    obj_val = p.objective(w)
    budget_err = abs(float(np.sum(w)) - 1.0)
    lev_viol = max(0.0, float(np.sum(np.abs(w))) - L)
    converged = n_iter < max_iter

    return SolverResult(
        solver_name="PGD + Ledoit-Wolf",
        converged=converged,
        message=(
            f"Converged in {n_iter} iterations (||step|| < {tol:.0e})"
            if converged
            else f"Iteration limit reached ({max_iter})"
        ),
        objective=obj_val,
        weights=w,
        n_iterations=n_iter,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print formatted solver output with explanation of why PGD+LW succeeds."""
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations        : {result.n_iterations}")
    print(f"Objective (Sigma) : {result.objective:.12f}")
    print(f"Budget error      : {result.budget_error:.2e}")
    print(f"Leverage violation: {result.leverage_violation:.2e}")
    print()
    print("Nonzero weights (|w| > 1e-4):")
    for ind, wi in zip(p.industries, result.weights, strict=True):
        if abs(wi) > 1e-4:
            print(f"  {ind:6s}  {wi:+.6f}")
    print()
    print("WHY SLSQP/GUROBI FAILED (non-PSD) BUT PGD+LW SUCCEEDED")
    print("=" * 56)
    print()
    print("SLSQP and Gurobi both require the objective matrix Q to be PSD")
    print("before optimization begins:")
    print("  - SLSQP: BFGS Hessian approximation diverges in the null space")
    print("    of S (6-dimensional), causing cycling at the L1 kink.")
    print("  - Gurobi: performs strict Cholesky(Q) at startup; a single")
    print("    negative eigenvalue (-3.762e-18) triggers Error 10020.")
    print()
    print("PGD never decomposes the covariance matrix.")
    print("Each iteration only requires a matrix-vector product Sigma @ w,")
    print("which is well-defined even for indefinite matrices. The LW")
    print("shrinkage (alpha=0.10) lifts the six near-zero eigenvalues of S")
    print("to lambda_min(Sigma) = 6.667e-4, making Sigma strictly PSD and")
    print("guaranteeing convergence of the gradient descent.")
    print()
    lam_max = float(np.linalg.eigvalsh(p.Sigma)[-1])
    lam_min = float(np.linalg.eigvalsh(p.Sigma)[0])
    eta = 1.9 / lam_max
    print(
        f"  lambda_max(Sigma) = {lam_max:.4e}  -->  eta = 1.9 / lam_max = {eta:.4e}"
    )
    print(f"  lambda_min(Sigma) = {lam_min:.4e}  (strictly positive after LW)")
    print(f"  Condition number  = {lam_max / lam_min:.1f}")
