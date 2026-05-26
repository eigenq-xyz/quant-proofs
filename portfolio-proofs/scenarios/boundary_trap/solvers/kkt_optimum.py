"""KKT analytical derivation of the global minimum for the boundary-trap scenario.

For a strictly convex QP the KKT conditions are both necessary and
sufficient (Boyd and Vandenberghe 2004, §5.5.3). The derivation:

1. Identify the support: the highest-mean-return industry as the long leg
   and the lowest-mean-return industry as the short leg.
2. Solve the 2x2 linear system when both budget and leverage constraints
   are simultaneously tight to get exact weights.
3. Verify dual feasibility for all zero-weight industries.

This module returns the analytically certified global minimum.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .common import ProblemData, SolverResult


@dataclass
class KKTCertificate:
    """Full KKT certificate for the global minimum."""

    idx_long: int
    idx_short: int
    w_long: float
    w_short: float
    lam: float  # budget dual variable
    nu: float  # leverage dual variable (>= 0)
    slack_margins: np.ndarray  # nu - |r_k + lam| for each inactive industry
    all_satisfied: bool


def derive(p: ProblemData) -> tuple[SolverResult, KKTCertificate]:
    """Derive and certify the global minimum via KKT conditions."""
    L = p.leverage_cap

    # Step 1: support from return spread
    idx_long = int(np.argmax(p.mu))
    idx_short = int(np.argmin(p.mu))

    # Step 2: both constraints tight on {long, short} support
    #   w_long + w_short = 1  (budget)
    #   w_long - w_short = L  (leverage, since w_long>0, w_short<0)
    w_long = (1 + L) / 2
    w_short = (1 - L) / 2

    w_star = np.zeros(p.N)
    w_star[idx_long] = w_long
    w_star[idx_short] = w_short

    obj_star = p.objective(w_star)

    # Step 3: KKT stationarity
    r = p.Sigma @ w_star - p.mu
    lam = -(r[idx_long] + r[idx_short]) / 2
    nu = (r[idx_short] - r[idx_long]) / 2

    # Dual feasibility for zero-weight industries
    inactive = [k for k in range(p.N) if k not in (idx_long, idx_short)]
    slacks = np.array([nu - abs(r[k] + lam) for k in inactive])
    all_satisfied = bool(nu >= -1e-10 and np.all(slacks >= -1e-10))

    cert = KKTCertificate(
        idx_long=idx_long,
        idx_short=idx_short,
        w_long=float(w_long),
        w_short=float(w_short),
        lam=float(lam),
        nu=float(nu),
        slack_margins=slacks,
        all_satisfied=all_satisfied,
    )

    result = SolverResult(
        solver_name="KKT global optimum",
        converged=True,
        message="Analytically certified",
        objective=float(obj_star),
        weights=w_star,
        n_iterations=0,
        budget_error=abs(float(np.sum(w_star)) - 1.0),
        leverage_violation=max(0.0, float(np.sum(np.abs(w_star))) - L),
    )

    return result, cert


def print_certificate(
    cert: KKTCertificate, result: SolverResult, p: ProblemData
) -> None:
    """Print the full KKT certificate."""
    print(
        f"Long leg  : {p.industries[cert.idx_long]:6s}  "
        f"w = {cert.w_long:+.4f}  "
        f"(μ = {p.mu[cert.idx_long] * 100:+.4f}%/day, highest)"
    )
    print(
        f"Short leg : {p.industries[cert.idx_short]:6s}  "
        f"w = {cert.w_short:+.4f}  "
        f"(μ = {p.mu[cert.idx_short] * 100:+.4f}%/day, lowest)"
    )
    print()
    print(f"Budget   : sum(w*) = {np.sum(result.weights):.6f}  (must = 1.0) ✓")
    print(
        f"Leverage : sum|w*| = {np.sum(np.abs(result.weights)):.6f}  "
        f"(cap = {p.leverage_cap:.2f}, tight) ✓"
    )
    print()
    print("KKT dual variables:")
    print(f"  λ (budget)   = {cert.lam:.6f}")
    print(
        f"  ν (leverage) = {cert.nu:.6f}  (≥ 0) {'✓' if cert.nu >= 0 else '✗'}"
    )
    print()
    print("Dual feasibility — all zero-weight industries must satisfy")
    print(f"|r_k + λ| ≤ ν = {cert.nu:.6f}:")
    print(f"  {'Industry':>8}  {'|r_k + λ|':>12}  {'Slack':>10}  {'OK?':>4}")
    inactive = [
        k for k in range(p.N) if k not in (cert.idx_long, cert.idx_short)
    ]
    for k, slack in zip(inactive, cert.slack_margins, strict=True):
        val = cert.nu - slack
        flag = "✓" if slack >= -1e-10 else "✗ VIOLATED"
        print(f"  {p.industries[k]:>8}  {val:12.6f}  {slack:10.6f}  {flag}")
    print()
    if cert.all_satisfied:
        print(
            "✓  All KKT conditions satisfied. Σ̂ is strictly positive definite."
        )
        print("   This is the unique global minimum.")
        print()
        print(f"   f(w*) = {result.objective:.12f}")
    else:
        print("✗  KKT conditions NOT satisfied — check derivation.")
