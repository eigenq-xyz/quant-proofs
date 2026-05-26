"""KKT analytical derivation of the global minima for the vix-shock scenario.

For a strictly convex QP the KKT conditions are both necessary and
sufficient (Boyd and Vandenberghe 2004, section 5.5.3). The long-only
simplex problem has the form:

    min  (1/2) w' Sigma w - mu' w
    s.t. sum(w_i) = 1,  w_i >= 0  for all i

KKT stationarity conditions (one per asset):
    Sigma_ii * w_i - mu_i + lambda - nu_i = 0  for all i
    nu_i >= 0,  nu_i * w_i = 0  (complementary slackness)

Since Sigma = sigma_sq * I (diagonal), each active asset (w_i > 0, nu_i = 0)
satisfies:
    sigma_sq * w_i = mu_i - lambda

For the long-only simplex the support S = {i : w_i > 0} is found by trying
candidate support sets and checking dual feasibility.

Pre-shock (Sigma = 0.04*I):
    Support S = {0} (Equity only).
    lambda = mu_0 - sigma_sq * w_0; with w_0 = 1 (budget tight on support),
    lambda = 0.15 - 0.04 = 0.11.
    Check dual feasibility: mu_1 = 0.10 <= 0.11 = lambda, mu_2 = 0.05 <= 0.11. Both hold.

Post-shock (Sigma = 0.16*I):
    Support S = {0, 1, 2} (all three assets).
    sum over S: (sum(mu_i) - |S|*lambda) / sigma_sq = 1
    (0.30 - 3*lambda) / 0.16 = 1 => lambda = (0.30 - 0.16) / 3 = 7/150.
    w_i = (mu_i - lambda) / sigma_sq for each i.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .common import (
    ProblemData,
    SolverResult,
)


@dataclass
class KKTCertificate:
    """Full KKT certificate for the global minimum on the long-only simplex."""

    support: list[int]  # indices of active assets (w_i > 0)
    weights: np.ndarray  # optimal weights
    lam: float  # budget dual variable (lambda)
    dual_margins: (
        np.ndarray
    )  # lambda - mu_i for inactive assets (must be >= 0)
    budget_error: float
    all_satisfied: bool


def derive_pre_shock(p: ProblemData) -> tuple[SolverResult, KKTCertificate]:
    """Derive and certify the pre-shock global minimum via KKT conditions.

    Support S = {0} (Equity only). With budget tight: w_0 = 1.
    lambda = mu_0 - sigma_sq * 1 = 0.15 - 0.04 = 0.11.
    Dual feasibility for inactive assets: mu_i <= lambda for i not in S.
    """
    sigma_sq = p.sigma_sq
    mu = p.mu
    N = p.N

    # Support: asset 0 (Equity) only
    support = [0]
    w_star = np.zeros(N)
    w_star[0] = 1.0  # budget tight on single-asset support

    lam = float(mu[0] - sigma_sq * w_star[0])  # = 0.11

    # Dual feasibility: for inactive assets i != 0, need mu_i <= lambda
    inactive = [k for k in range(N) if k not in support]
    dual_margins = np.array([lam - float(mu[k]) for k in inactive])
    all_satisfied = bool(np.all(dual_margins >= -1e-12))

    budget_err = abs(float(np.sum(w_star)) - 1.0)

    cert = KKTCertificate(
        support=support,
        weights=w_star.copy(),
        lam=lam,
        dual_margins=dual_margins,
        budget_error=budget_err,
        all_satisfied=all_satisfied,
    )

    result = SolverResult(
        solver_name="KKT global optimum (pre-shock)",
        converged=True,
        message="Analytically certified: support S={Equity}",
        objective=p.objective(w_star),
        weights=w_star,
        n_iterations=0,
        budget_error=budget_err,
        diverged=False,
        weight_history=w_star.reshape(1, N),
    )

    return result, cert


def derive_post_shock(p: ProblemData) -> tuple[SolverResult, KKTCertificate]:
    """Derive and certify the post-shock global minimum via KKT conditions.

    Support S = {0, 1, 2} (all assets active).
    Solve: sum_i (mu_i - lambda) / sigma_sq = 1
    => (sum(mu) - |S|*lambda) / sigma_sq = 1
    => lambda = (sum(mu) - sigma_sq) / |S| = (0.30 - 0.16) / 3 = 7/150.
    w_i = (mu_i - lambda) / sigma_sq for each i.
    All w_i > 0 must be verified; no dual feasibility check needed since all assets active.
    """
    sigma_sq = p.sigma_sq
    mu = p.mu
    N = p.N

    # Support: all three assets
    support = list(range(N))

    # Solve for lambda: (sum(mu) - N*lambda) / sigma_sq = 1
    sum_mu = float(np.sum(mu))  # = 0.30
    lam = (sum_mu - sigma_sq) / N  # = (0.30 - 0.16) / 3 = 7/150

    w_star = np.array([(float(mu[i]) - lam) / sigma_sq for i in range(N)])

    # Verify: all weights positive, sum = 1
    all_positive = bool(np.all(w_star >= -1e-12))
    budget_err = abs(float(np.sum(w_star)) - 1.0)
    all_satisfied = all_positive and budget_err < 1e-10

    cert = KKTCertificate(
        support=support,
        weights=w_star.copy(),
        lam=float(lam),
        dual_margins=np.array(
            []
        ),  # all assets active; no inactive set to check
        budget_error=budget_err,
        all_satisfied=all_satisfied,
    )

    result = SolverResult(
        solver_name="KKT global optimum (post-shock)",
        converged=True,
        message="Analytically certified: support S={Equity, Bonds, Commodities}",
        objective=p.objective(w_star),
        weights=w_star,
        n_iterations=0,
        budget_error=budget_err,
        diverged=False,
        weight_history=w_star.reshape(1, N),
    )

    return result, cert


def print_certificate(
    cert: KKTCertificate, result: SolverResult, p: ProblemData
) -> None:
    """Print the full KKT certificate."""
    print(f"Solver    : {result.solver_name}")
    print(f"Message   : {result.message}")
    print()
    print("Support set (active assets, w_i > 0):")
    for i in cert.support:
        print(
            f"  {p.asset_names[i]:12s}  w* = {cert.weights[i]:.10f}"
            f"  (mu = {p.mu[i]:.4f})"
        )
    print()
    print(f"lambda (budget dual) = {cert.lam:.10f}")
    print()
    print(f"Budget: sum(w*) = {np.sum(cert.weights):.15f}  (must = 1.0)")
    print(f"Budget error   = {cert.budget_error:.2e}")
    print()

    inactive = [k for k in range(p.N) if k not in cert.support]
    if inactive:
        print(
            "Dual feasibility -- inactive assets must satisfy mu_i <= lambda:"
        )
        print(
            f"  {'Asset':12s}  {'mu_i':>8}  {'lambda - mu_i':>14}  {'OK?':>4}"
        )
        for k, margin in zip(inactive, cert.dual_margins, strict=True):
            flag = "OK" if margin >= -1e-12 else "VIOLATED"
            print(
                f"  {p.asset_names[k]:12s}  {p.mu[k]:8.5f}  {margin:14.10f}  {flag}"
            )
        print()

    if cert.all_satisfied:
        print(
            "All KKT conditions satisfied. This is the unique global minimum."
        )
        print()
        print(f"  f(w*) = {result.objective:.15f}")
    else:
        print("KKT conditions NOT satisfied -- check derivation.")
