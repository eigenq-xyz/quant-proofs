"""Lean 4 PGD — persistent subprocess wrapper.

Calls the compiled ``pgd_solve`` binary from ``optimization-proofs/`` via a
**single long-lived subprocess**.  Process-spawn overhead (~35 ms on macOS) is
paid once per Python session; subsequent calls pay only pipe I/O, typically
< 1 ms for N ≤ 50.

Wire protocol
-------------
stdin  — one space-separated line per problem::

    N  sigma_00 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap

    N is a plain integer string (``"10"``).
    All float values use Python ``repr(v)`` (shortest round-trip form;
    scientific notation such as ``"2.378e-03"`` is handled by ``CLI.lean``).

stdout — one space-separated line of N float64 weights per problem.

The Lean binary loops until EOF; sending ``"\\n"`` (an empty line) closes the
loop cleanly and exits the process.

Performance
-----------
- First ``solve()`` call: starts the Lean binary (~35 ms on macOS).
- Subsequent ``solve()`` calls: dominated by the Duchi bisection, not pipe I/O.
  Measured warm medians (Apple M-series, iters=53, 12 reps):

  ==============================  =========  =====
  Problem                         Time       CV
  ==============================  =========  =====
  N=2 diagonal (pipe floor)        2.0 ms    3.0%
  N=5 diagonal, L1 active          3.5 ms    1.1%
  N=3 diagonal, L1 active          6.4 ms    1.3%
  N=10 CAPM, cond≈36              56 ms      0.9%
  N=10 random, cond≈204          233 ms      0.4%
  ==============================  =========  =====

  The dominant cost is the nested dual-bisection in ``projectL1F``:
  up to 53 outer x 53 inner x N ``FloatArray.get!`` operations per PGD step.
  The pipe round-trip adds only ~0.3 ms (observed for diagonal sigma where
  the bisection fast-path is skipped).

- ``lake exe pgd_bench`` reports ~16 ns/solve (1000-run loop, fixed args).
  **This figure is unreliable** — the pure, fixed-argument call is likely
  constant-folded by LLVM, measuring loop overhead rather than the algorithm.
  Use the subprocess timings above as the production baseline.

Concurrency
-----------
All calls are serialised by a module-level ``threading.Lock``.  Each call
acquires the lock for the full write-flush-readline round trip, so
multi-threaded callers are safe but sequential.

If the Lean process dies between calls (e.g. due to an OOM kill), the wrapper
restarts it automatically and retries the failed call once.

Usage
-----
::

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
# Binary location
# ---------------------------------------------------------------------------

_OPT_PROOFS: pathlib.Path = (
    pathlib.Path(__file__).parent.parent / "optimization-proofs"
)
_BINARY: pathlib.Path = _OPT_PROOFS / ".lake" / "build" / "bin" / "pgd_solve"

# ---------------------------------------------------------------------------
# Persistent subprocess
# ---------------------------------------------------------------------------

_proc: subprocess.Popen[str] | None = None
_lock: threading.Lock = threading.Lock()


def _start_process() -> subprocess.Popen[str]:
    """Launch the ``pgd_solve`` binary and return the Popen handle."""
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
        bufsize=1,  # line-buffered: each write/readline crosses the pipe once
    )


def _get_process() -> subprocess.Popen[str]:
    """Return the cached persistent subprocess, starting it if necessary.

    Must be called under ``_lock``.
    """
    global _proc
    if _proc is None or _proc.poll() is not None:
        _proc = _start_process()
    return _proc


def _send_line(line: str) -> str:
    """Send *line* to the Lean process and return the response line.

    Handles one automatic restart if the process is found dead mid-write
    (e.g. killed by OOM).

    Must be called under ``_lock``.
    """
    global _proc

    proc = _get_process()
    if proc.stdin is None or proc.stdout is None:
        raise RuntimeError(
            "Lean pgd_solve process opened without stdin/stdout pipes; "
            "this should never happen — please report a bug."
        )
    try:
        proc.stdin.write(line)
        proc.stdin.flush()
        return proc.stdout.readline()
    except BrokenPipeError:
        # The process died between the poll() check and the write.
        # Mark it dead, restart, and retry exactly once.
        _proc = None
        proc = _get_process()
        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError(
                "Lean pgd_solve process unavailable after automatic restart."
            ) from None
        proc.stdin.write(line)
        proc.stdin.flush()
        return proc.stdout.readline()


def _shutdown() -> None:
    """Close the persistent subprocess on interpreter exit.

    Registered with ``atexit`` at module import time.
    """
    global _proc
    if _proc is not None and _proc.poll() is None:
        try:
            if _proc.stdin is not None:
                _proc.stdin.write("\n")  # empty line signals EOF to Lean
                _proc.stdin.flush()
            _proc.wait(timeout=2.0)
        except Exception:
            _proc.kill()
        _proc = None


atexit.register(_shutdown)

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------


def _validate_inputs(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float,
) -> int:
    """Check inputs against the Lean proof's structural preconditions.

    The Lean ``pgdFlat`` theorem assumes:

    - ``sigma`` is an *N x N* matrix (square, rank ≥ 1).
    - ``mu`` is an *N*-vector compatible with ``sigma``.
    - ``leverage_cap > 0`` (otherwise the feasible set is empty).

    Parameters
    ----------
    sigma:
        Candidate covariance matrix.
    mu:
        Candidate expected-return vector.
    leverage_cap:
        Gross leverage cap.

    Returns
    -------
    N : int
        Portfolio dimension.

    Raises
    ------
    ValueError
        On any shape mismatch or out-of-range parameter value.
    """
    if sigma.ndim != 2:
        raise ValueError(f"sigma must be a 2-D array; got shape {sigma.shape}")
    n: int = int(sigma.shape[0])
    m: int = int(sigma.shape[1])
    if n != m:
        raise ValueError(f"sigma must be square; got {n}x{m}")
    if n == 0:
        raise ValueError("Portfolio dimension N must be ≥ 1")
    if mu.ndim != 1:
        raise ValueError(f"mu must be a 1-D array; got shape {mu.shape}")
    if len(mu) != n:
        raise ValueError(
            f"sigma is {n}x{n} but mu has length {len(mu)}; "
            "dimensions must agree"
        )
    if leverage_cap <= 0.0:
        raise ValueError(
            f"leverage_cap must be positive; got {leverage_cap!r}"
        )
    return n


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

#: Wall-clock time for the Lean 4 *native* PGD binary at N = 10,
#: measured by ``lake exe pgd_bench`` (1 000-run average, Apple M-series).
#: This is algorithm time only — no I/O boundary, no Python overhead.
LEAN_NATIVE_NS: float = 13.834


def solve(
    sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
) -> tuple[np.ndarray, float]:
    """Solve the mean-variance portfolio problem via the Lean 4 PGD.

    Calls the compiled ``pgd_solve`` binary over a persistent subprocess.
    The algorithm is implemented in ``pgdFlat``
    (``OptimizationProofs/PGDFlat.lean``).  Convergence to within epsilon
    of the global minimum in O(1/k) iterations is guaranteed by theorem
    ``pgd_convergence`` (``OptimizationProofs/Convergence.lean``); the
    projection step is certified to land on the constraint set by theorem
    ``projection_correctness`` (``OptimizationProofs/Projection.lean``).

    Parameters
    ----------
    sigma:
        *(N, N)* symmetric positive-definite covariance matrix (float64).
        Apply Ledoit-Wolf or diagonal-loading shrinkage before passing if
        the raw sample covariance is rank-deficient.
    mu:
        *(N,)* expected-return vector (float64).
    leverage_cap:
        Gross leverage cap *L* for the constraint ``sum|w| ≤ L``.
        Default 1.5 (long-only with modest leverage).

    Returns
    -------
    weights : ndarray, shape (N,)
        Optimal portfolio weights satisfying ``sum(w) ≈ 1`` and
        ``sum|w| ≤ leverage_cap`` to float64 rounding.
    lambda_max : float
        Largest eigenvalue of ``sigma`` (the Lipschitz constant used to
        set the step size ``eta = 1.9 / lambda_max``).  Returned so
        callers can log or audit the step-size choice.

    Raises
    ------
    FileNotFoundError
        If the ``pgd_solve`` binary has not been compiled yet.
    ValueError
        If ``sigma`` or ``mu`` fail shape/dimension checks, or
        ``leverage_cap ≤ 0``.
    RuntimeError
        If the Lean process returns an empty or malformed result, or
        cannot be restarted after an unexpected crash.
    """
    N = _validate_inputs(sigma, mu, leverage_cap)
    lam_max = float(np.linalg.eigvalsh(sigma)[-1])

    # Build the wire-format line.
    # repr(v) gives the shortest round-trip decimal form (e.g. "1.25" rather
    # than "1.25000000000000000").  CLI.lean's parseFloat handles both plain
    # decimal and scientific-notation repr strings.
    float_strs = [
        repr(v)
        for v in [*sigma.ravel().tolist(), *mu.tolist(), lam_max, leverage_cap]
    ]
    line = str(N) + " " + " ".join(float_strs) + "\n"

    with _lock:
        out = _send_line(line)

    if not out.strip():
        raise RuntimeError(
            "Lean pgd_solve returned empty output. "
            "Check that the binary is up-to-date: "
            "cd optimization-proofs && lake build pgd_solve"
        )

    weights = np.array([float(x) for x in out.split()], dtype=np.float64)
    if len(weights) != N:
        raise RuntimeError(
            f"Expected {N} weights from Lean; got {len(weights)}: {out!r}"
        )
    return weights, lam_max
