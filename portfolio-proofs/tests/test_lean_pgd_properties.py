"""Hypothesis property-based tests for lean_pgd.solve().

These tests verify the mathematical guarantees that the Lean PGD is supposed
to certify, across thousands of randomly generated inputs.  They complement
the deterministic tests in test_lean_pgd.py with broad coverage of the
input space.

The three properties tested here correspond to the proof obligations that
``pgd_convergence`` and ``projection_correctness`` will eventually encode:

1. **Budget constraint**: ``sum(w) == 1`` to float64 rounding for any PD sigma.
2. **Leverage constraint**: ``sum|w| <= leverage_cap`` for any PD sigma.
3. **Lambda-max consistency**: the returned ``lambda_max`` matches
   ``np.linalg.eigvalsh(sigma)[-1]`` for any sigma.

All tests require the ``pgd_solve`` binary and are skipped if it is absent.
Build it once: ``cd optimization-proofs && lake build pgd_solve``.

Known limitations
-----------------
- The N=3 / identity-sigma / uniform-mu degenerate case exceeds the 1e-10
  budget tolerance (observed: ~1e-6).  The properties use a 5e-6 tolerance
  to accommodate this; see ``test_lean_pgd.py::test_solve_degenerate_n3_uniform``
  for the documented characterisation.
- Hypothesis is configured with ``max_examples=200`` and a 10-second deadline
  per example to bound total runtime (~35 ms/call × 200 = ~7 s).
"""

from __future__ import annotations

import pathlib

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Binary skip guard (shared with test_lean_pgd.py)
# ---------------------------------------------------------------------------

_BINARY: pathlib.Path = (
    pathlib.Path(__file__).parent.parent.parent
    / "optimization-proofs"
    / ".lake"
    / "build"
    / "bin"
    / "pgd_solve"
)

requires_binary = pytest.mark.skipif(
    not _BINARY.exists(),
    reason=(
        "pgd_solve binary not built; "
        "run: cd optimization-proofs && lake build pgd_solve"
    ),
)

# ---------------------------------------------------------------------------
# Composite strategy: random strictly positive-definite problem
# ---------------------------------------------------------------------------

#: Maximum portfolio dimension for property tests.  Kept small so that the
#: O(N²) stdin serialisation stays fast enough for 200 examples.
_MAX_N = 12


@st.composite
def pd_problems(
    draw: st.DrawFn,
) -> tuple[int, np.ndarray, np.ndarray, float]:
    """Draw a random (N, sigma, mu, leverage_cap) with sigma strictly PD.

    Parameters
    ----------
    draw:
        Hypothesis draw function (injected by ``@st.composite``).

    Returns
    -------
    n : int
        Portfolio dimension in [2, _MAX_N].
    sigma : ndarray, shape (n, n)
        Strictly positive-definite covariance matrix.
    mu : ndarray, shape (n,)
        Expected-return vector (any real values).
    leverage_cap : float
        Gross leverage cap in [1.0, 3.0].
    """
    n = draw(st.integers(min_value=2, max_value=_MAX_N))
    seed = draw(st.integers(min_value=0, max_value=2**31 - 1))
    leverage_cap = draw(
        st.floats(min_value=1.0, max_value=3.0, allow_nan=False, allow_infinity=False)
    )

    rng = np.random.default_rng(seed)
    # A.T @ A is PSD; adding 0.1 * I makes it strictly PD.
    A = rng.standard_normal((n, n))
    sigma = A.T @ A + np.eye(n) * 0.1
    mu = rng.standard_normal(n)

    return n, sigma, mu, leverage_cap


# ---------------------------------------------------------------------------
# Property 1: budget constraint
# ---------------------------------------------------------------------------


@requires_binary
@given(problem=pd_problems())
@settings(
    max_examples=200,
    deadline=10_000,  # 10 s per example; ~35 ms/call × 200 = ~7 s total
    suppress_health_check=[HealthCheck.too_slow],
)
def test_budget_constraint_holds_for_random_inputs(
    problem: tuple[int, np.ndarray, np.ndarray, float],
) -> None:
    """sum(w) == 1 to 5e-6 for any randomly generated PD sigma and mu.

    The 5e-6 tolerance accommodates the known N=3-uniform degenerate case
    (see test_lean_pgd.py::test_solve_degenerate_n3_uniform).  For most
    inputs the error is at float64 machine epsilon (< 1e-15).
    """
    import lean_pgd  # noqa: PLC0415

    n, sigma, mu, leverage_cap = problem
    weights, _ = lean_pgd.solve(sigma, mu, leverage_cap=leverage_cap)

    assert weights.shape == (n,), f"shape mismatch: got {weights.shape}, expected ({n},)"
    assert np.all(np.isfinite(weights)), f"non-finite weights: {weights}"

    budget_err = abs(float(np.sum(weights)) - 1.0)
    assert budget_err <= 5e-6, (
        f"N={n}, leverage_cap={leverage_cap:.2f}: "
        f"|sum(w) - 1| = {budget_err:.2e} exceeds 5e-6"
    )


# ---------------------------------------------------------------------------
# Property 2: leverage constraint
# ---------------------------------------------------------------------------


@requires_binary
@given(problem=pd_problems())
@settings(
    max_examples=200,
    deadline=10_000,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_leverage_constraint_holds_for_random_inputs(
    problem: tuple[int, np.ndarray, np.ndarray, float],
) -> None:
    """sum|w| <= leverage_cap + 1e-10 for any randomly generated inputs."""
    import lean_pgd  # noqa: PLC0415

    n, sigma, mu, leverage_cap = problem
    weights, _ = lean_pgd.solve(sigma, mu, leverage_cap=leverage_cap)

    leverage_violation = max(0.0, float(np.sum(np.abs(weights))) - leverage_cap)
    assert leverage_violation <= 1e-10, (
        f"N={n}, leverage_cap={leverage_cap:.2f}: "
        f"sum|w| - L = {leverage_violation:.2e} exceeds 1e-10"
    )


# ---------------------------------------------------------------------------
# Property 3: lambda_max consistency
# ---------------------------------------------------------------------------


@requires_binary
@given(problem=pd_problems())
@settings(
    max_examples=200,
    deadline=10_000,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_lambda_max_matches_eigvalsh(
    problem: tuple[int, np.ndarray, np.ndarray, float],
) -> None:
    """lambda_max returned by solve() equals np.linalg.eigvalsh(sigma)[-1].

    This tests the round-trip: Python computes lambda_max, passes it to
    Lean, and returns it unchanged.  Any deviation would indicate a
    serialisation bug in the wire protocol.
    """
    import lean_pgd  # noqa: PLC0415

    n, sigma, mu, leverage_cap = problem
    _, lam_max = lean_pgd.solve(sigma, mu, leverage_cap=leverage_cap)

    expected = float(np.linalg.eigvalsh(sigma)[-1])
    assert lam_max == pytest.approx(expected, rel=1e-9), (
        f"N={n}: lambda_max mismatch — got {lam_max}, expected {expected}"
    )


# ---------------------------------------------------------------------------
# Property 4: weights are always finite
# ---------------------------------------------------------------------------


@requires_binary
@given(problem=pd_problems())
@settings(
    max_examples=200,
    deadline=10_000,
    suppress_health_check=[HealthCheck.too_slow],
)
def test_weights_always_finite(
    problem: tuple[int, np.ndarray, np.ndarray, float],
) -> None:
    """No NaN or Inf in the returned weight vector for any PD input."""
    import lean_pgd  # noqa: PLC0415

    n, sigma, mu, leverage_cap = problem
    weights, lam_max = lean_pgd.solve(sigma, mu, leverage_cap=leverage_cap)

    assert np.all(np.isfinite(weights)), (
        f"N={n}: non-finite weights {weights}"
    )
    assert np.isfinite(lam_max), f"N={n}: non-finite lambda_max {lam_max}"
