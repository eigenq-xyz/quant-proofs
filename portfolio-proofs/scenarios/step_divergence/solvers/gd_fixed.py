"""Fixed-eta gradient descent (unconstrained) for the step-divergence scenario.

Demonstrates catastrophic divergence when the step size calibrated from the
January 2018 calm period is applied to the post-shock (Volmageddon) covariance.

The update rule is:
    w_{k+1} = w_k - eta * grad f(w_k)
    grad f(w) = Sigma_shock @ w - mu_shock

No projection is applied. The divergence mechanism is isolated in the
unconstrained setting: once eta > 2 / lambda_max(Sigma_shock), the gradient
step amplifies the error component along the max-eigenvalue direction by a
factor |eta * lambda_max - 1| > 1 at every iteration.

Theoretical divergence growth factor (February 2018 parameters):
    |eta_cal * lambda_max_shock - 1| = |5334.47 * 0.002378 - 1| = 11.687
    After 3 steps: ~1,594x error amplification.
"""

from __future__ import annotations

import numpy as np

from .common import ProblemData, SolverResult

_DIVERGENCE_THRESHOLD = 1e4
_MAX_ITERATIONS = 200
_PRINT_STEPS = {0, 1, 2, 5, 10, 50, 100, 150}


def run(p: ProblemData) -> SolverResult:
    """Run unconstrained gradient descent with the calibrated (pre-shock) step size.

    Uses eta = p.eta_calibrated, which was calibrated from January 2018 and
    violates the post-shock Lipschitz stability bound 2 / lambda_max_shock.

    Parameters
    ----------
    p:
        ProblemData; uses p.Sigma_shock, p.mu_shock, p.eta_calibrated.

    Returns
    -------
    SolverResult
        converged=False with message "DIVERGED" when ||w||_inf > 1e4.
        converged=True if the iterates happen to stabilize (should not occur
        with the validated February 2018 parameters).
    """
    eta = p.eta_calibrated
    growth_factor = abs(eta * p.lam_max_shock - 1.0)

    print("=== Fixed-eta Gradient Descent (unconstrained) ===")
    print()
    print(f"Calibrated eta      : {eta:.4f}  (from January 2018)")
    print(
        f"Post-shock bound    : {p.lipschitz_bound:.2f}  (= 2 / {p.lam_max_shock:.6f})"
    )
    print(
        f"Stability violated  : eta = {eta:.2f}  >>  bound = {p.lipschitz_bound:.2f}"
        f"  ({eta / p.lipschitz_bound:.2f}x over)"
    )
    print(
        f"Growth factor / step: |eta * lambda_max - 1| = {growth_factor:.3f}"
    )
    print(
        f"After 3 steps       : error amplification ~{growth_factor**3:.0f}x"
    )
    print()
    print(f"{'Step':>5}  {'||w||_inf':>12}  {'weights (first 5)':>40}")
    print("-" * 65)

    w = np.ones(p.N) / p.N  # uniform start

    diverged_at = -1
    w_final = w.copy()

    for k in range(_MAX_ITERATIONS + 1):
        norm_inf = float(np.max(np.abs(w)))

        if k in _PRINT_STEPS or norm_inf > _DIVERGENCE_THRESHOLD:
            w_str = "  ".join(f"{wi:+.4f}" for wi in w[:5])
            print(f"{k:5d}  {norm_inf:12.4f}  [{w_str} ...]")

        if norm_inf > _DIVERGENCE_THRESHOLD:
            diverged_at = k
            w_final = w.copy()
            print()
            print(
                f"DIVERGENCE DETECTED at step {k}  (||w||_inf = {norm_inf:.3e})"
            )
            break

        if k == _MAX_ITERATIONS:
            w_final = w.copy()
            break

        # Gradient step (unconstrained — no projection)
        grad = p.Sigma_shock @ w - p.mu_shock
        w = w - eta * grad

    converged = diverged_at < 0
    if converged:
        message = f"Stabilized after {_MAX_ITERATIONS} iterations (unexpected)"
        obj_val = p.objective(w_final)
    else:
        message = f"DIVERGED at step {diverged_at}"
        obj_val = float("nan")

    budget_err = (
        float("nan") if not converged else abs(float(np.sum(w_final)) - 1.0)
    )
    lev_viol = (
        float("nan")
        if not converged
        else max(0.0, float(np.sum(np.abs(w_final))) - p.leverage_cap)
    )

    return SolverResult(
        solver_name="Fixed-eta GD (unconstrained)",
        converged=converged,
        message=message,
        objective=obj_val,
        weights=w_final,
        n_iterations=diverged_at if diverged_at >= 0 else _MAX_ITERATIONS,
        budget_error=budget_err,
        leverage_violation=lev_viol,
    )


def print_result(result: SolverResult, p: ProblemData) -> None:
    """Print summary of the divergence run."""
    print()
    print(f"Converged         : {result.converged}")
    print(f"Message           : {result.message}")
    print(f"Iterations to fail: {result.n_iterations}")
    if not result.converged:
        print()
        print(
            "Gradient descent with a step size calibrated from a low-volatility "
            "period diverges catastrophically when applied to the post-shock "
            "covariance. The iterates grow geometrically; no solution is returned."
        )
        eta = p.eta_calibrated
        growth = abs(eta * p.lam_max_shock - 1.0)
        print()
        print(
            f"Root cause: eta = {eta:.2f} > 2 / lambda_max = {p.lipschitz_bound:.2f}."
        )
        print(
            f"The descent lemma requires eta < 2/L. "
            f"Each step amplifies error by {growth:.3f}x instead of reducing it."
        )
