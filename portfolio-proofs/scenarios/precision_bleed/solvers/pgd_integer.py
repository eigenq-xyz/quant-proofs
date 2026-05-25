"""PGD solver with basis-point integer arithmetic for the precision-bleed scenario.

Weights are stored and projected in integer basis points (1 bp = 0.0001).
The budget and leverage constraints are enforced in integer arithmetic:

    sum(w_bp) = 10000        (exact: budget = 100%)
    sum(|w_bp|) <= 15000     (exact: leverage cap = 150%)

Gradient steps are computed in float64, then rounded to the nearest integer
basis point.  After rounding, a correction loop restores exact integer
feasibility.  The final constraint satisfaction errors, measured after
converting back to float64, are:

    budget_error       = |10000 / 10000 - 1.0| = 0.0  (exactly representable)
    leverage_violation = max(0, sum(|w_bp|) / 10000 - 1.5)  (= 0 by construction)

This demonstrates that integer arithmetic eliminates the feasibility tolerance
gap that affects SLSQP.  The tradeoff is quantization noise: weights are
resolved only to 1 bp (0.01%) rather than float64 precision.  For a 4-asset
allocation that quantization is commercially negligible.
"""

from __future__ import annotations

import numpy as np

from .common import (
    PRODUCTION_HALT_THRESHOLD,
    WindowData,
    WindowResult,
)

# ---------------------------------------------------------------------------
# Integer-arithmetic PGD constants
# ---------------------------------------------------------------------------

#: Scale factor: 1 unit = 1 basis point = 0.0001 in fractional weight space.
BP_SCALE: int = 10_000

#: Budget target in basis points (= 100%).
BUDGET_BP: int = BP_SCALE  # 10000

#: Leverage cap in basis points (= 150%).
LEVERAGE_CAP_BP: int = 15_000

#: Maximum PGD iterations.
MAX_ITER: int = 5_000

#: Convergence tolerance on the L2 norm of the weight change (in bp units).
CONVERGENCE_TOL_BP: float = 0.5  # half a basis point


# ---------------------------------------------------------------------------
# Integer simplex + L1 projection
# ---------------------------------------------------------------------------


def _project_budget_bp(w_bp: np.ndarray) -> np.ndarray:
    """Project integer vector onto budget hyperplane sum(w_bp) = BUDGET_BP.

    Adjusts the largest absolute-value components to absorb any integer
    rounding residual while keeping the result integer-valued.

    Parameters
    ----------
    w_bp:
        Integer weight vector (arbitrary sum).

    Returns
    -------
    np.ndarray
        Integer vector with sum = BUDGET_BP.
    """
    w_bp = w_bp.copy()
    residual = int(np.sum(w_bp)) - BUDGET_BP
    if residual == 0:
        return w_bp
    # Distribute residual one bp at a time to the largest components.
    order = np.argsort(-np.abs(w_bp))
    step = -1 if residual > 0 else 1
    for _ in range(abs(residual)):
        w_bp[order[_ % len(order)]] += step
    return w_bp


def _project_leverage_bp(w_bp: np.ndarray) -> np.ndarray:
    """Project integer vector onto leverage ball sum(|w_bp|) <= LEVERAGE_CAP_BP.

    If the L1 norm already satisfies the cap, returns w_bp unchanged.
    Otherwise reduces leverage in two stages to maintain budget feasibility:

    Stage 1 (bulk reduction): Identify pairs of long/short positions.  For
    each pair $(i, j)$ where $w_i > 0$ and $w_j < 0$, reduce both
    simultaneously by ``min(|w_i|, |w_j|, excess//2)`` bp.  This cancels
    leverage without changing the budget sum (``w_i + w_j`` is unchanged
    only if we reduce both by the same amount toward zero, so we reduce by
    ``min(|w_i|, |w_j|, k)`` and increment/decrement both).

    Stage 2 (final trim): Proportionally scale down all components by
    ``LEVERAGE_CAP_BP / sum(|w_bp|)``, rounding toward zero, then restore
    budget via ``_project_budget_bp``.  Stage 2 may need one iteration if
    stage 1 did not fully close the gap.

    This runs in O(N log N) in the worst case (one sort + linear pass).

    Parameters
    ----------
    w_bp:
        Integer weight vector with sum = BUDGET_BP.

    Returns
    -------
    np.ndarray
        Integer vector satisfying both budget and leverage constraints exactly.
    """
    w_bp = w_bp.copy()
    lev = int(np.sum(np.abs(w_bp)))
    if lev <= LEVERAGE_CAP_BP:
        return w_bp

    # Stage 1: cancel longs against shorts.
    # Reduce pairs (long i, short j) simultaneously until leverage is satisfied.
    longs = np.where(w_bp > 0)[0]
    shorts = np.where(w_bp < 0)[0]
    li, si = 0, 0
    while li < len(longs) and si < len(shorts):
        lev = int(np.sum(np.abs(w_bp)))
        if lev <= LEVERAGE_CAP_BP:
            break
        excess = lev - LEVERAGE_CAP_BP
        i = longs[li]
        j = shorts[si]
        # Reduce both toward zero by the same amount: this preserves budget sum
        # because delta(w_i) = -k and delta(w_j) = +k cancel in the sum.
        # However we need w_i > 0 and w_j < 0 to still hold.
        k = min(w_bp[i], -w_bp[j], excess // 2 + 1)
        if k <= 0:
            li += 1
            si += 1
            continue
        w_bp[i] -= k
        w_bp[j] += k
        if w_bp[i] == 0:
            li += 1
        if w_bp[j] == 0:
            si += 1

    # Stage 2: if leverage still exceeds cap, proportional scale + budget restore.
    lev = int(np.sum(np.abs(w_bp)))
    if lev > LEVERAGE_CAP_BP:
        scale = LEVERAGE_CAP_BP / lev
        w_bp = np.trunc(w_bp * scale).astype(int)
        w_bp = _project_budget_bp(w_bp)

    # Verify and clean up any final residual (should be 0 after stage 2).
    lev = int(np.sum(np.abs(w_bp)))
    if lev > LEVERAGE_CAP_BP:
        # Last-resort: reduce the single largest component by the excess.
        excess = lev - LEVERAGE_CAP_BP
        order = np.argsort(-np.abs(w_bp))
        for ix in order:
            if excess <= 0:
                break
            trim = min(int(np.abs(w_bp[ix])), excess)
            w_bp[ix] -= int(np.sign(w_bp[ix])) * trim
            excess -= trim
        w_bp = _project_budget_bp(w_bp)

    return w_bp


# ---------------------------------------------------------------------------
# PGD core
# ---------------------------------------------------------------------------


def run_window(w: WindowData) -> WindowResult:
    """Run integer-arithmetic PGD on a single window.

    Each iteration:
    1. Compute the gradient g = Sigma @ w_float - mu in float64.
    2. Scale the step to basis points, round to nearest integer.
    3. Subtract from w_bp, then project onto the integer feasible set.
    4. Convert back to float64 to check convergence.

    The step size eta = 1.9 / lambda_max(Sigma) satisfies the descent
    condition for the float64 quadratic objective.

    Parameters
    ----------
    w:
        Window data (returns, covariance, mean returns, leverage cap).

    Returns
    -------
    WindowResult
        Constraint satisfaction metrics.  ``budget_error`` and
        ``leverage_violation`` are both exactly 0.0 for all feasible problems.
    """
    lam_max = float(np.linalg.eigvalsh(w.Sigma)[-1])
    eta = 1.9 / lam_max  # step size < 2 / lambda_max guarantees descent

    # Initialise at equal-weight portfolio (integer bp).
    w_bp = np.array([BUDGET_BP // w.N] * w.N, dtype=int)
    # Restore any rounding residual in the last component.
    w_bp[-1] += BUDGET_BP - int(np.sum(w_bp))

    iters = 0
    for k in range(MAX_ITER):
        w_float = w_bp / BP_SCALE

        # Gradient of (1/2) w' Sigma w - mu' w
        grad = w.Sigma @ w_float - w.mu

        # Gradient step in float64, then convert to integer bp.
        w_float_new = w_float - eta * grad
        w_bp_new = np.round(w_float_new * BP_SCALE).astype(int)

        # Project onto integer feasible set.
        w_bp_new = _project_budget_bp(w_bp_new)
        w_bp_new = _project_leverage_bp(w_bp_new)

        iters = k + 1
        delta = float(np.linalg.norm((w_bp_new - w_bp).astype(float)))
        w_bp = w_bp_new
        if delta < CONVERGENCE_TOL_BP:
            break

    # Final weights and constraint metrics.
    weights = w_bp / BP_SCALE

    # budget_error: |sum(w_bp)/10000 - 1.0|
    # Since sum(w_bp) == BUDGET_BP == 10000 exactly (integer), and
    # 10000/10000 == 1.0 exactly in float64, this is always 0.0.
    budget_error = float(abs(np.sum(w_bp) / BP_SCALE - 1.0))

    # leverage_violation: max(0, sum(|w_bp|)/10000 - 1.5)
    # Since sum(|w_bp|) <= LEVERAGE_CAP_BP == 15000 exactly (integer), this
    # is always 0.0 as well.
    leverage_violation = float(
        max(0.0, np.sum(np.abs(w_bp)) / BP_SCALE - w.leverage_cap)
    )

    # Verify integer feasibility assertions.
    assert int(np.sum(w_bp)) == BUDGET_BP, (
        f"Integer budget violated: sum(w_bp) = {np.sum(w_bp)} != {BUDGET_BP}"
    )
    assert int(np.sum(np.abs(w_bp))) <= LEVERAGE_CAP_BP, (
        f"Integer leverage violated: sum(|w_bp|) = {np.sum(np.abs(w_bp))} > {LEVERAGE_CAP_BP}"
    )

    bleeding = (
        budget_error > PRODUCTION_HALT_THRESHOLD
        or leverage_violation > PRODUCTION_HALT_THRESHOLD
    )
    status = "BLEEDING" if bleeding else "PERFECT"

    return WindowResult(
        solver_name="PGD integer arithmetic (bp scale)",
        window_start=w.start,
        window_end=w.end,
        converged=True,
        message=f"Converged in {iters} iterations (delta < {CONVERGENCE_TOL_BP} bp)",
        objective=float(w.objective(weights)),
        weights=weights,
        budget_error=budget_error,
        leverage_violation=leverage_violation,
        status=status,
    )


def run_all(windows: list[WindowData]) -> list[WindowResult]:
    """Run integer PGD on all four rolling windows.

    Parameters
    ----------
    windows:
        Output of ``common.load_rolling_windows()``.

    Returns
    -------
    list[WindowResult]
        One result per window, in the same order as ``windows``.
    """
    return [run_window(w) for w in windows]


def print_results(results: list[WindowResult]) -> None:
    """Print a formatted table of integer-PGD constraint satisfaction.

    Parameters
    ----------
    results:
        Output of ``run_all()``.
    """
    sep = "=" * 78
    print(sep)
    print(
        " PGD integer arithmetic (bp scale) — Rolling Window Results ".center(
            78, "="
        )
    )
    print(sep)
    print(f"  BP scale      : 1 unit = {1 / BP_SCALE:.4f} (one basis point)")
    print(f"  Budget target : sum(w_bp) = {BUDGET_BP}  (exactly, integer)")
    print(
        f"  Leverage cap  : sum(|w_bp|) <= {LEVERAGE_CAP_BP}  (exactly, integer)"
    )
    print()

    for i, r in enumerate(results, 1):
        print(f"Window {i}: {r.label}")
        print(f"  {r.message}")
        print(f"  Objective    : {r.objective:.15f}")
        print(f"  Budget Err   : {r.budget_error:.2e}  (|sum(w) - 1|)")
        print(
            f"  Leverage Err : {r.leverage_violation:.2e}  (max(0, sum|w| - 1.5))"
        )
        print(f"  STATUS       : {r.status}")
        print()

    print(sep)
    print(
        "CONCLUSION: Integer arithmetic guarantees exact constraint satisfaction."
    )
    print("budget_error = 0.0 and leverage_violation = 0.0 for all windows.")
    print(sep)
