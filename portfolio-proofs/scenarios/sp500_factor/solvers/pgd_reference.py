"""Lean 4 PGD (direct subprocess) + Python reference for the sp500-factor scenario.

Primary solver: calls ``optimization-proofs/.lake/build/bin/pgd_solve`` via
subprocess -- no Cython, no FFI layer.  The Lean binary runs ``pgdFlat``
(PGDFlat.lean) with the rank-1 factor-structure gradient O(N) and the Duchi
dual-bisection projection O(N log N).

Python reference (``benchmark``): used for per-step timing comparisons in the
scaling benchmark table.  Uses the same O(N) factor-structure gradient so the
comparison is algorithmic, not language-level.

Projection:
  Duchi et al. (2008) extended projection onto {sum(w)=B, sum|w|<=L},
  allowing negative weights when L > 1.
"""

from __future__ import annotations

import pathlib
import sys
import time
from dataclasses import dataclass

import numpy as np

from .common import ProblemData

# lean_pgd_direct.py lives at portfolio-proofs/
_PORTFOLIO = pathlib.Path(__file__).parent.parent.parent.parent
if str(_PORTFOLIO) not in sys.path:
    sys.path.insert(0, str(_PORTFOLIO))

from lean_pgd_direct import solve as _lean_solve  # noqa: E402


@dataclass
class BenchmarkResult:
    N: int
    solve_time_ms: float
    n_iterations: int
    objective: float
    n_active: int  # number of nonzero positions
    budget_error: float
    leverage_violation: float


def _soft_thresh(z: np.ndarray, mu: float) -> np.ndarray:
    """Soft-threshold operator: sign(z) * max(|z| - mu, 0)."""
    out: np.ndarray = np.sign(z) * np.maximum(np.abs(z) - mu, 0.0)
    return out


def project_budget_l1(
    y: np.ndarray,
    B: float = 1.0,
    L: float = 1.5,
    _bisect: int = 40,
) -> np.ndarray:
    """Project y onto C = {w : sum(w) = B, sum|w| <= L} (allows negative weights).

    Uses the KKT dual characterization:
      w_i = sign(y_i - lambda) * max(|y_i - lambda| - mu, 0)

    where lambda (budget dual) and mu (L1 dual) satisfy:
      sum(w) = B   (budget constraint, always tight)
      sum|w| = L   (L1 constraint, tight when L < sum|w_budget_only|)

    Algorithm:
      1. Check if budget-only projection (mu=0) satisfies L1 constraint.
         Projection onto {sum(w)=B}: lambda = (sum(y) - B) / N, w = y - lambda.
      2. If L1 is active, bisect over mu (outer, _bisect iters) with inner
         bisection over lambda (_bisect iters).

    Cost: O(N) per bisection step, O(_bisect^2) bisection steps total = O(N).
    """
    # Step 1: budget-only projection (mu = 0, L1 may not be active)
    lam_unconstrained = (float(np.sum(y)) - B) / len(y)
    w_budget_only = y - lam_unconstrained
    if float(np.sum(np.abs(w_budget_only))) <= L + 1e-8:
        return w_budget_only

    # Step 2: L1 constraint is active — bisect over (mu, lambda)
    def find_lambda(mu: float) -> float:
        lam_lo = float(np.min(y)) - abs(B) - mu - 1.0
        lam_hi = float(np.max(y)) + abs(B) + mu + 1.0
        for _ in range(_bisect):
            lam_mid = (lam_lo + lam_hi) / 2.0
            val = float(np.sum(_soft_thresh(y - lam_mid, mu)))
            if val > B:
                lam_lo = lam_mid
            else:
                lam_hi = lam_mid
        return (lam_lo + lam_hi) / 2.0

    mu_lo = 0.0
    mu_hi = float(np.max(np.abs(y))) + abs(B) + 2.0
    mu_mid = mu_lo
    lam_s = 0.0
    for _ in range(_bisect):
        mu_mid = (mu_lo + mu_hi) / 2.0
        lam_s = find_lambda(mu_mid)
        w_test = _soft_thresh(y - lam_s, mu_mid)
        lev = float(np.sum(np.abs(w_test)))
        if abs(lev - L) < 1e-9:
            break
        if lev > L:
            mu_lo = mu_mid
        else:
            mu_hi = mu_mid
    lam_s = find_lambda(mu_mid)
    return _soft_thresh(y - lam_s, mu_mid)


def run_pgd(
    p: ProblemData,
    use_factor_gradient: bool = True,
    tol: float = 1e-8,
    max_iter: int = 10000,
) -> tuple[np.ndarray, int]:
    """Run PGD to convergence (or max_iter) and return (weights, n_iterations)."""
    lam_max = float(np.linalg.eigvalsh(p.Sigma)[-1])
    eta = 1.9 / lam_max
    w = np.ones(p.N) / p.N
    for k in range(max_iter):
        if use_factor_gradient:
            grad = p.gradient_factor(w)
        else:
            grad = p.Sigma @ w - p.mu
        w_new = project_budget_l1(w - eta * grad, B=1.0, L=p.leverage_cap)
        if float(np.linalg.norm(w_new - w)) < tol:
            return w_new, k + 1
        w = w_new
    return w, max_iter


# Number of fixed iterations used in the scaling benchmark (same for all N,
# so the measured time reflects per-iteration cost at each scale).
BENCHMARK_FIXED_ITERS: int = 100


def benchmark(p: ProblemData, reps: int = 5) -> BenchmarkResult:
    """Time BENCHMARK_FIXED_ITERS PGD steps (median of reps runs).

    Uses a fixed iteration count rather than running to convergence so that
    the reported time reflects per-iteration cost at each N. This isolates
    the O(N) gradient + O(N) projection scaling from the condition-number
    dependence of the total iteration count.
    """
    lam_max = float(np.linalg.eigvalsh(p.Sigma)[-1])
    eta = 1.9 / lam_max
    times: list[float] = []
    w_final = np.zeros(p.N)
    for _ in range(reps):
        w = np.ones(p.N) / p.N
        t0 = time.perf_counter()
        for _ in range(BENCHMARK_FIXED_ITERS):
            grad = p.gradient_factor(w)
            w = project_budget_l1(w - eta * grad, B=1.0, L=p.leverage_cap)
        times.append((time.perf_counter() - t0) * 1000.0)
        w_final = w
    times.sort()
    med_ms = times[len(times) // 2]
    return BenchmarkResult(
        N=p.N,
        solve_time_ms=med_ms,
        n_iterations=BENCHMARK_FIXED_ITERS,
        objective=float(p.objective(w_final)),
        n_active=int(np.sum(np.abs(w_final) > 1e-9)),
        budget_error=abs(float(np.sum(w_final)) - 1.0),
        leverage_violation=max(
            0.0, float(np.sum(np.abs(w_final))) - p.leverage_cap
        ),
    )


@dataclass
class DirectBenchmarkResult:
    """Timing result from the Lean 4 pgd_solve binary (subprocess call)."""

    N: int
    solve_time_ms: float  # wall-clock including subprocess startup
    objective: float
    n_active: int
    budget_error: float
    lean_weights: np.ndarray


def benchmark_direct(p: ProblemData, reps: int = 3) -> DirectBenchmarkResult:
    """Time the Lean 4 pgd_solve binary on problem p (median of reps runs).

    Includes subprocess startup overhead (~5-15 ms), which dominates at
    small N. For large N the arithmetic cost grows and subprocess overhead
    becomes a smaller fraction.  The Python benchmark() reports pure
    algorithmic cost; this reports the full subprocess round-trip cost.

    Parameters
    ----------
    p:
        Problem instance at a given N.
    reps:
        Number of timed runs (median reported).

    Returns
    -------
    DirectBenchmarkResult
        Timing, objective, and certified weights from the Lean binary.
    """
    times: list[float] = []
    w_final = np.zeros(p.N)
    for _ in range(reps):
        t0 = time.perf_counter()
        w, _ = _lean_solve(p.Sigma, p.mu, p.leverage_cap)
        times.append((time.perf_counter() - t0) * 1000.0)
        w_final = w
    times.sort()
    return DirectBenchmarkResult(
        N=p.N,
        solve_time_ms=times[len(times) // 2],
        objective=float(p.objective(w_final)),
        n_active=int(np.sum(np.abs(w_final) > 1e-9)),
        budget_error=abs(float(np.sum(w_final)) - 1.0),
        lean_weights=w_final,
    )
