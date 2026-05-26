"""Lean 4 PGD -- Cython FFI wrapper.

Calls the compiled Lean 4 code **in-process** via a Cython extension, eliminating
the subprocess pipe round-trip (~0.5 ms on macOS).

Two back-ends are exposed, matching the two paths in ``ffi/pgd_ffi.pyx``:

``solve_flat``
    Fast path: ``FloatArray`` (unboxed doubles).  Marshalling: N^2+N
    ``lean_float_array_push`` calls.  Equivalent latency to the subprocess path
    because the compute dominates and the same ``FloatArray.get!`` bounds checks
    apply inside the Lean code.

``solve_boxed``
    Slow-marshal path: ``Array Float`` (boxed doubles).  Marshalling: N^2+N
    ``lean_box_float`` calls.  Counterintuitively **faster** than ``solve_flat``
    for large, high-condition problems (cond >= 150) due to different code
    generation in the boxed variant.

Performance summary (Apple M-series, warm, iters=53)
-----------------------------------------------------
| Problem                    | Subprocess | FFI-flat | FFI-boxed |
|----------------------------|-----------|----------|-----------|
| N=2 diag (pipe floor)      |    2.0 ms |   2.0 ms |    6.7 ms |
| N=5 diag (phantom_pos)     |    3.5 ms |   3.5 ms |    4.9 ms |
| N=3 diag (vix shock)       |    6.4 ms |   6.4 ms |   24.5 ms |
| N=10 CAPM, cond~36         |   56.0 ms |  55.0 ms |  122.1 ms |
| N=10 rand, cond~204        |  233.3 ms | 233.0 ms |  155.1 ms |

Key: for N <= 50 problems with cond < 100, ``subprocess`` or ``solve_flat`` are
equivalent.  For cond >= 150, ``solve_boxed`` is faster.

Usage
-----
::

    from lean_pgd_ffi import solve_flat, solve_boxed

    # One-time initialisation on first import (< 1 ms).
    weights = solve_flat(sigma, mu, leverage_cap=1.5)

    # Or use the dispatch function that chooses the faster back-end:
    weights = solve(sigma, mu, leverage_cap=1.5)
"""

from __future__ import annotations

import pathlib
import sys

import numpy as np

# ---------------------------------------------------------------------------
# Path setup -- add ffi/ dir from optimization-proofs so pgd_ffi is importable
# ---------------------------------------------------------------------------

_REPO_ROOT: pathlib.Path = pathlib.Path(__file__).parent.parent
_FFI_DIR: pathlib.Path = _REPO_ROOT / "optimization-proofs" / "ffi"
if str(_FFI_DIR) not in sys.path:
    sys.path.insert(0, str(_FFI_DIR))

_FFI_AVAILABLE: bool = False

try:
    import pgd_ffi as _pgd_ffi_mod  # type: ignore[import-not-found]

    _FFI_AVAILABLE = True
    _pgd_ffi_mod.initialize_lean()
except ImportError:
    _pgd_ffi_mod = None

# ---------------------------------------------------------------------------
# Imports from subprocess wrapper (validation + fallback)
# ---------------------------------------------------------------------------

from lean_pgd import _validate_inputs  # noqa: E402
from lean_pgd import solve as _subprocess_solve  # noqa: E402

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _cond_number(sigma: np.ndarray) -> float:
    """Cheap condition number estimate via eigenvalue ratio."""
    eigs = np.linalg.eigvalsh(sigma)
    return float(eigs[-1] / max(eigs[0], 1e-12))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def solve_flat(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Solve via FFI FloatArray (flat) path.

    Equivalent latency to the subprocess path for all tested problems.
    Falls back to subprocess if the FFI extension is not built.

    Returns
    -------
    weights : ndarray, shape (N,)
    lambda_max : float
    """
    _validate_inputs(sigma, mu, leverage_cap)
    lam_max = float(np.linalg.eigvalsh(sigma)[-1])
    if not _FFI_AVAILABLE or _pgd_ffi_mod is None:
        return _subprocess_solve(sigma, mu, leverage_cap=leverage_cap)
    sigma = np.ascontiguousarray(sigma, dtype=np.float64)
    mu = np.ascontiguousarray(mu, dtype=np.float64)
    weights: np.ndarray = _pgd_ffi_mod.pgd_solve_flat(
        sigma, mu, lam_max, leverage_cap
    )
    return weights, lam_max


def solve_boxed(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Solve via FFI Array Float (boxed) path.

    Faster than ``solve_flat`` for high-condition problems (cond >= 150) because
    the ``Array Float`` code generation in ``PGD.lean`` is more efficiently
    compiled for that regime.  Falls back to subprocess if the FFI extension is
    not built.

    Returns
    -------
    weights : ndarray, shape (N,)
    lambda_max : float
    """
    _validate_inputs(sigma, mu, leverage_cap)
    lam_max = float(np.linalg.eigvalsh(sigma)[-1])
    if not _FFI_AVAILABLE or _pgd_ffi_mod is None:
        return _subprocess_solve(sigma, mu, leverage_cap=leverage_cap)
    sigma = np.ascontiguousarray(sigma, dtype=np.float64)
    mu = np.ascontiguousarray(mu, dtype=np.float64)
    weights: np.ndarray = _pgd_ffi_mod.pgd_solve(
        sigma, mu, lam_max, leverage_cap
    )
    return weights, lam_max


def solve(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Dispatch to the faster FFI back-end based on problem structure.

    Routing rule (empirical, Apple M-series, iters=53):
      - cond(sigma) < 150  ->  ``solve_flat``   (same speed as subprocess)
      - cond(sigma) >= 150 ->  ``solve_boxed``  (~1.5x faster at cond=200)

    Falls back gracefully to the subprocess path if the FFI extension is not
    built (see ``optimization-proofs/ffi/setup_ffi.py``).

    Returns
    -------
    weights : ndarray, shape (N,)
    lambda_max : float
    """
    if not _FFI_AVAILABLE:
        return _subprocess_solve(sigma, mu, leverage_cap=leverage_cap)
    cond = _cond_number(sigma)
    if cond >= 150.0:
        return solve_boxed(sigma, mu, leverage_cap)
    return solve_flat(sigma, mu, leverage_cap)
