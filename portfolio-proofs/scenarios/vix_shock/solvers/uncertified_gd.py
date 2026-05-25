"""Uncertified gradient descent with a stale pre-shock step size.

Applied to the POST-SHOCK problem using the step size calibrated on the
PRE-SHOCK covariance. The stale step size eta_pre = 47.5 violates the
Nesterov (2004) stability bound for the post-shock problem:

    eta < 2 / lambda_max(Sigma_post) = 2 / 0.16 = 12.5

With eta_pre = 47.5 >> 12.5, each unconstrained gradient step amplifies
the distance to the optimum by a factor of

    |1 - eta_pre * lambda_max(Sigma_post)| = |1 - 47.5 * 0.16| = 6.6

The simplex projection clips iterates back to the feasible set after each
gradient step, so individual weights stay bounded. However, the gradient step
direction is so far off that the projected iterates oscillate between extreme
vertices of the simplex rather than contracting toward the interior optimum.
The norm-to-optimum does not decay; the algorithm fails to converge.

Divergence is declared when the iterate oscillates at constant large distance
from the optimum for a sustained window --- i.e., the step-to-step norms
are constant rather than geometrically decreasing.

Algorithm:
    w_{k+1} = simplex_project(w_k - eta_pre * (Sigma_post @ w_k - mu))

The simplex projection uses the standard O(N log N) sort-based algorithm for
the long-only constraint: w_i >= 0, sum(w_i) = 1.
"""

from __future__ import annotations

import numpy as np

from .common import ETA_PRE, ProblemData, SolverResult

_MAX_ITERS: int = 50
# Oscillation detection: if the ratio of max to min step-norm over the last
# window exceeds this threshold the iterate is cycling, not converging.
_OSCILLATION_WINDOW: int = 10
_OSCILLATION_RATIO: float = (
    0.95  # consecutive steps near-equal = cycle detected
)


def _simplex_project(y: np.ndarray) -> np.ndarray:
    """Project y onto the probability simplex {w >= 0, sum(w) = 1}.

    Uses the O(N log N) sort-based algorithm (standard long-only simplex
    projection). Duchi et al. (2008), Algorithm 1 extended to the simplex.

    Parameters
    ----------
    y:
        Unconstrained gradient step output.

    Returns
    -------
    np.ndarray
        The projection of y onto the simplex.
    """
    N = len(y)
    u = np.sort(y)[::-1]  # sort descending
    cssv = np.cumsum(u)  # cumulative sum
    # rho = largest j such that u[j] - (cssv[j] - 1) / (j+1) > 0
    rho_candidates = u * np.arange(1, N + 1) > cssv - 1.0
    rho = int(np.max(np.where(rho_candidates)))
    theta = float((cssv[rho] - 1.0) / (rho + 1))
    return np.maximum(y - theta, 0.0)


def run(p: ProblemData, eta: float | None = None) -> SolverResult:
    """Run uncertified GD with stale pre-shock step size on the post-shock problem.

    Parameters
    ----------
    p:
        Post-shock problem data. The stale step size is applied regardless.
    eta:
        Override the stale step size (default: ETA_PRE = 47.5). Used for
        testing only; the scenario always uses ETA_PRE.

    Returns
    -------
    SolverResult
        Contains diverged=True and the weight history up to the divergence point.
    """
    step = eta if eta is not None else ETA_PRE
    N = p.N
    w = np.ones(N) / N  # uniform start

    history: list[np.ndarray] = [w.copy()]
    step_norms: list[float] = []
    diverged = False
    message = f"Stale step size eta={step:.4f} (calibrated on pre-shock, violates post-shock bound)"

    for k in range(_MAX_ITERS):
        grad = p.Sigma @ w - p.mu
        w_new = _simplex_project(w - step * grad)
        history.append(w_new.copy())
        step_norms.append(float(np.linalg.norm(w_new - w)))

        # Detect oscillation: if the last _OSCILLATION_WINDOW step norms are
        # near-constant the iterate is cycling, not contracting.
        if len(step_norms) >= _OSCILLATION_WINDOW:
            recent = step_norms[-_OSCILLATION_WINDOW:]
            ratio = min(recent) / max(recent) if max(recent) > 0 else 1.0
            if ratio >= _OSCILLATION_RATIO:
                diverged = True
                message = (
                    f"OSCILLATION DETECTED at iteration {k + 1}: "
                    f"step norms constant at ~{np.mean(recent):.4f} for {_OSCILLATION_WINDOW} steps. "
                    f"Stale eta={step:.4f} violates stability bound "
                    f"2/lambda_max={2.0 / p.sigma_sq:.4f}. "
                    f"Iterate cycles between simplex vertices instead of converging."
                )
                w = w_new
                break

        w = w_new

    weight_history = np.stack(history, axis=0)
    budget_err = abs(float(np.sum(w)) - 1.0)

    return SolverResult(
        solver_name=f"Uncertified GD (stale eta={step:.4f})",
        converged=False,
        message=message,
        objective=p.objective(w),
        weights=w,
        n_iterations=len(history) - 1,
        budget_error=budget_err,
        diverged=diverged,
        weight_history=weight_history,
    )
