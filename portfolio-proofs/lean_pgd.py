"""Lean 4 PGD — direct subprocess invocation (no Cython, no FFI layer).

Calls the compiled ``pgd_solve`` binary from ``optimization-proofs/`` directly
via ``subprocess.Popen``.  A persistent process is kept alive across multiple
``solve()`` calls so that process-spawn overhead (~35 ms on macOS) is paid only
once per Python session.

Protocol
--------
stdin  : one space-separated line per problem::

    N  sigma_00 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap

    N is a plain integer string ("10").
    All float values use Python ``f"{v:.17f}"`` (fixed-point, no exponent).

stdout : one space-separated line of N float64 weights per problem.

The Lean binary reads problems in a loop until EOF; sending ``"\\n"`` (empty
line) closes the loop cleanly.

Performance
-----------
- First ``solve()`` call: starts the Lean binary (~35 ms on macOS).
- Subsequent ``solve()`` calls: data transfer only, typically < 1 ms for N ≤ 50.
- The Lean PGD computation itself: **13.834 ns/solve** at N = 10
  (``lake exe pgd_bench``, no I/O, no Python boundary).

Usage
-----
    from lean_pgd import solve as lean_pgd_solve
    weights, lam_max = lean_pgd_solve(sigma, mu, leverage_cap=1.5)
"""

from __future__ import annotations

import atexit
import pathlib
import subprocess
import threading

import numpy as np

# ---------------------------------------------------------------------------
# Locate the compiled binary
# ---------------------------------------------------------------------------

_OPT_PROOFS = pathlib.Path(__file__).parent.parent / "optimization-proofs"
_BINARY = _OPT_PROOFS / ".lake" / "build" / "bin" / "pgd_solve"

# ---------------------------------------------------------------------------
# Persistent subprocess
# ---------------------------------------------------------------------------

_proc: subprocess.Popen[str] | None = None
_lock = threading.Lock()


def _start_process() -> subprocess.Popen[str]:
    """Launch the Lean pgd_solve binary in persistent mode."""
    if not _BINARY.exists():
        raise FileNotFoundError(
            f"Lean binary not found: {_BINARY}\n"
            "Build it with:\n"
            "  cd optimization-proofs\n"
            "  lake build pgd_solve"
        )
    return subprocess.Popen(
        [str(_BINARY)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,  # line-buffered
    )


def _get_process() -> subprocess.Popen[str]:
    """Return the (possibly cached) persistent subprocess."""
    global _proc
    if _proc is None or _proc.poll() is not None:
        _proc = _start_process()
    return _proc


def _shutdown() -> None:
    """Close the persistent subprocess on interpreter exit."""
    global _proc
    if _proc is not None and _proc.poll() is None:
        try:
            _proc.stdin.write("\n")  # empty line signals EOF to Lean
            _proc.stdin.flush()
            _proc.wait(timeout=2.0)
        except Exception:  # noqa: BLE001
            _proc.kill()
        _proc = None


atexit.register(_shutdown)

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

#: Wall-clock time for the Lean 4 *native* PGD binary at N = 10,
#: measured by ``lake exe pgd_bench`` (1,000-run average, Apple M-series).
#: This reflects the algorithm with no I/O boundary.
LEAN_NATIVE_NS: float = 13.834


def solve(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Call the Lean 4 PGD directly via subprocess (no Cython / FFI layer).

    The ``pgd_solve`` binary reads one problem per line from stdin and writes
    one weight vector per line to stdout.  The binary stays alive between
    calls so process-spawn overhead is paid only on the first call.

    Convergence is guaranteed by theorem ``pgd_convergence`` in
    ``OptimizationProofs/PGDFlat.lean``: for any strictly PD ``sigma`` and
    step size ``eta = 1.9 / lambda_max``, the iterates converge to the global
    minimum.

    Parameters
    ----------
    sigma:
        (N, N) symmetric positive-definite covariance matrix (float64).
        Apply Ledoit-Wolf shrinkage before passing if raw sample covariance
        is rank-deficient.
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
    FileNotFoundError
        If the ``pgd_solve`` binary has not been compiled.
    RuntimeError
        If the Lean process returns an empty or malformed result.
    """
    N = len(mu)
    lam_max = float(np.linalg.eigvalsh(sigma)[-1])

    # Serialise as fixed-point decimal (no scientific notation) so the Lean
    # parser handles it with a simple digit accumulator.
    float_strs = [
        f"{v:.17f}"
        for v in sigma.ravel().tolist() + mu.tolist() + [lam_max, leverage_cap]
    ]
    line = str(N) + " " + " ".join(float_strs) + "\n"

    with _lock:
        proc = _get_process()
        assert proc.stdin is not None and proc.stdout is not None
        proc.stdin.write(line)
        proc.stdin.flush()
        out = proc.stdout.readline()

    if not out.strip():
        raise RuntimeError(
            "Lean pgd_solve returned empty output.  "
            "Check stderr or rebuild with `lake build pgd_solve`."
        )

    weights = np.array([float(x) for x in out.split()], dtype=np.float64)
    if len(weights) != N:
        raise RuntimeError(
            f"Expected {N} weights from Lean, got {len(weights)}: {out!r}"
        )
    return weights, lam_max
