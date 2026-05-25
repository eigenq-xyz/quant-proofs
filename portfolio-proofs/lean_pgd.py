"""Shared Lean 4 PGD wrapper for portfolio-proofs scenarios.

Wraps ``pgd_solve_flat()`` — the fast FloatArray path — from the compiled
``pgd_ffi`` Cython extension in ``optimization-proofs/``.

Usage
-----
    from lean_pgd import solve as lean_pgd_solve
    weights, lam_max = lean_pgd_solve(sigma, mu, leverage_cap=1.5)

The first call initializes the Lean runtime (once per process).

Performance notes
-----------------
The FFI path marshals sigma via N² + N calls to ``lean_float_array_push()``.
Each push runs in roughly 100 µs due to Lean's incremental reference-counting
runtime, giving approximately (N² + N) × 100 µs of marshalling overhead.  At
N = 10 this is ~11 ms; the actual PGD computation (Lean native) is ~14 ns.

The Lean *native* binary (``lake exe pgd_bench``, no FFI boundary) achieves
the timing quoted in the scenario notebooks: **13.834 ns/solve** for N = 10
(1,000-run average, Apple M-series).  Use ``LEAN_NATIVE_NS`` to reference
this number in prose.

The FFI path is used in the scenario solver-result cells (N = 10 or N = 4),
where the 11 ms overhead is acceptable.  The benchmark scaling tables use the
Python PGD reference to demonstrate the O(N²) vs O(N³) complexity difference,
since the Python path uses vectorised numpy BLAS whereas the Lean path uses
scalar double loops.
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Locate and register optimization-proofs on sys.path
# ---------------------------------------------------------------------------

_OPT_PROOFS = pathlib.Path(__file__).parent.parent / "optimization-proofs"
if str(_OPT_PROOFS) not in sys.path:
    sys.path.insert(0, str(_OPT_PROOFS))

# ---------------------------------------------------------------------------
# Lazy initialisation — called once per process
# ---------------------------------------------------------------------------

_lean_initialized: bool = False
_pgd_solve_flat_fn: object | None = None


def _ensure_initialized() -> None:
    """Initialize the Lean runtime and load the FFI symbols (once per process)."""
    global _lean_initialized, _pgd_solve_flat_fn
    if _lean_initialized:
        return
    try:
        from pgd_ffi import (  # type: ignore[import-not-found]
            initialize_lean,
            pgd_solve_flat,
        )

        initialize_lean()
        _pgd_solve_flat_fn = pgd_solve_flat
    except (ImportError, OSError) as exc:
        raise ImportError(
            "Lean 4 FFI not available.  Rebuild with:\n"
            "  cd optimization-proofs\n"
            "  lake build\n"
            "  uv run python ffi/setup_ffi.py build_ext --inplace\n"
            "Then restart the Python kernel."
        ) from exc
    _lean_initialized = True


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

#: Wall-clock time for the Lean 4 *native* PGD binary at N = 10,
#: measured by ``lake exe pgd_bench`` (1,000-run average, Apple M-series).
#: This reflects the algorithm with no FFI boundary; cite in notebook prose.
LEAN_NATIVE_NS: float = 13.834


def solve(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Call the formally verified Lean 4 PGD (``pgd_solve_flat`` via FFI).

    Computes ``lambda_max`` in Python then delegates the entire PGD loop to
    the Lean 4 LLVM-compiled solver.  The step size ``eta = 1.9 / lambda_max``
    is enforced *inside* Lean, so convergence is guaranteed by theorem
    ``pgd_convergence``.

    Parameters
    ----------
    sigma:
        (N, N) symmetric positive-definite covariance matrix (float64).
        Apply Ledoit-Wolf shrinkage before passing if the raw sample
        covariance is rank-deficient.
    mu:
        (N,) expected return vector (float64).
    leverage_cap:
        Gross leverage cap L for the constraint sum|w| ≤ L.  Default 1.5.

    Returns
    -------
    weights : ndarray shape (N,)
        Optimal portfolio weights.
    lambda_max : float
        Largest eigenvalue of ``sigma`` (the Lipschitz constant used by Lean).

    Raises
    ------
    ImportError
        If the Lean FFI extension has not been compiled.
    """
    _ensure_initialized()
    lam_max = float(np.linalg.eigvalsh(sigma)[-1])
    sigma_c = np.ascontiguousarray(sigma, dtype=np.float64)
    mu_c = np.ascontiguousarray(mu, dtype=np.float64)
    assert _pgd_solve_flat_fn is not None
    weights: np.ndarray = _pgd_solve_flat_fn(
        sigma_c, mu_c, lam_max, leverage_cap
    )  # type: ignore[operator]
    return weights, lam_max
