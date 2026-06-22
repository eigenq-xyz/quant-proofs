"""Call the Lean 4 PGD solver directly via subprocess — no FFI, no Cython.

Protocol: one line on stdin, space-separated tokens:
    N  sigma_00 sigma_01 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap

Output: space-separated float weights on a single line.

The binary is built by ``cd optimization-proofs && lake build pgd_solve``.
It compiles to native code via LLVM; there is no Python interpreter or Cython
layer at any point in the call stack.
"""

from __future__ import annotations

import pathlib
import subprocess

import numpy as np

# Binary location: portfolio-proofs/../optimization-proofs/.lake/build/bin/pgd_solve
_BINARY: pathlib.Path = (
    pathlib.Path(__file__).parent.parent
    / "optimization-proofs"
    / ".lake"
    / "build"
    / "bin"
    / "pgd_solve"
)


def solve(
    Sigma: np.ndarray,
    mu: np.ndarray,
    leverage_cap: float = 1.5,
    timeout: float = 30.0,
) -> tuple[np.ndarray, float]:
    """Run the Lean 4 PGD directly via subprocess.

    Parameters
    ----------
    Sigma:
        NxN positive-definite covariance matrix (Ledoit-Wolf shrunk).
    mu:
        N-vector of expected returns.
    leverage_cap:
        Gross leverage cap L (default 1.5).
    timeout:
        Subprocess timeout in seconds.

    Returns
    -------
    w:
        Optimal portfolio weights (N-vector, exactly satisfying the
        Duchi projection constraints by Lean's certified projection).
    lambda_max:
        λ_max(Σ) used as the Lipschitz constant; determines step size
        η = 1.9 / λ_max.  Returned so callers can log it.
    """
    if not _BINARY.exists():
        raise FileNotFoundError(
            f"pgd_solve binary not found at {_BINARY}.\n"
            "Build it: cd optimization-proofs && lake build pgd_solve"
        )

    N = len(mu)
    lambda_max = float(np.linalg.eigvalsh(Sigma)[-1])

    # Build the single stdin line: N, N² sigma values, N mu values, λ_max, L
    tokens: list[str] = (
        [str(N)]
        + [repr(float(x)) for x in Sigma.flatten()]
        + [repr(float(x)) for x in mu]
        + [repr(lambda_max), repr(float(leverage_cap))]
    )
    stdin_line = " ".join(tokens)

    result = subprocess.run(
        [str(_BINARY)],
        input=stdin_line,
        capture_output=True,
        text=True,
        timeout=timeout,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Lean pgd_solve failed (exit {result.returncode}):\n{result.stderr}"
        )
    if result.stderr:
        raise RuntimeError(f"Lean pgd_solve error:\n{result.stderr}")

    w = np.array([float(x) for x in result.stdout.split()])
    if len(w) != N:
        raise RuntimeError(
            f"Lean pgd_solve: expected {N} weights, got {len(w)}"
        )
    return w, lambda_max
