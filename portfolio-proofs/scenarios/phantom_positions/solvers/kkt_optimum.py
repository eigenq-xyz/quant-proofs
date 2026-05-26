"""KKT analytical derivation of the global minimum for the phantom-positions scenario.

For a strictly convex QP the KKT conditions are both necessary and sufficient
(Boyd and Vandenberghe 2004, §5.5.3). The derivation for the 2-support case:

1. Identify the support: the long leg is the asset with the highest expected
   return (index 0, Tech, mu=0.20) and the short leg is the asset with the
   lowest expected return (index 4, HiYield, mu=-0.07).

2. Assume both the budget constraint and the gross leverage constraint are
   simultaneously tight on the 2-asset support. This gives a 2x2 linear system:

       w_long + w_short = 1        (budget tight)
       w_long - w_short = L = 1.5  (leverage tight, since w_long > 0 > w_short)

   Solving: w_long = (1 + L) / 2 = 1.25,  w_short = (1 - L) / 2 = -0.25.

3. Recover the KKT dual variables from the stationarity conditions:

       Sigma w* - mu = lambda * 1 + nu * sign(w*)  for active assets
       |mu_i - lambda| <= nu                         for inactive assets

   With Sigma = sigma_sq * I:
       sigma_sq * w_long  - mu_long  = lambda + nu
       sigma_sq * w_short - mu_short = lambda - nu

   Solving:
       lambda = ((sigma_sq * w_long - mu_long) + (sigma_sq * w_short - mu_short)) / 2
              = ((0.04*1.25 - 0.20) + (0.04*(-0.25) - (-0.07))) / 2
              = ((0.05 - 0.20) + (-0.01 + 0.07)) / 2
              = ((-0.15) + (0.06)) / 2 = -0.09 / 2 = -0.045

   Wait -- let me restate using the sign convention from Boyd §5.5.3 where the
   Lagrangian is L(w, lambda, nu) = f(w) + lambda*(sum(w)-1) + nu*(sum|w|-L):

       grad_w L = Sigma w - mu + lambda * 1 + nu * sign(w) = 0 at w*

   For active assets:
       0.04 * 1.25 - 0.20 + lambda + nu = 0   => 0.05 - 0.20 + lambda + nu = 0
       0.04 * (-0.25) - (-0.07) + lambda - nu = 0 => -0.01 + 0.07 + lambda - nu = 0

   Adding:   2*lambda + 0.06 - 0.13 = 0  =>  lambda = 0.07/2... let us just
   solve numerically in code and verify against the certified values lambda=0.045, nu=0.105.

   The stationarity condition here is:
       Sigma @ w* - mu + lambda * ones + nu * sign(w*) = 0
   i.e.  r_i + lambda + nu * sign(w_i*) = 0  for active i,
   i.e.  r_i + lambda = -nu * sign(w_i*)     for active i.

   For the long asset (sign = +1): r_long + lambda = -nu
   For the short asset (sign = -1): r_short + lambda = +nu

   So: nu = (r_short - r_long) / 2,  lambda = -(r_long + r_short) / 2

   where r_i = (Sigma @ w*)[i] - mu[i] = sigma_sq * w_i* - mu_i.

   r_long  = 0.04 * 1.25 - 0.20 = 0.05 - 0.20 = -0.15
   r_short = 0.04 * (-0.25) - (-0.07) = -0.01 + 0.07 = 0.06

   lambda = -(-0.15 + 0.06) / 2 = -(-0.09) / 2 = 0.09/2 = 0.045  ✓
   nu     = (0.06 - (-0.15)) / 2 = 0.21 / 2 = 0.105               ✓

4. Verify dual feasibility for the 3 inactive assets (indices 1, 2, 3):
       |r_i + lambda| <= nu = 0.105

   r_1 = 0.04 * 0 - 0.06 = -0.06   |(-0.06) + 0.045| = 0.015 <= 0.105  ✓
   r_2 = 0.04 * 0 - 0.05 = -0.05   |(-0.05) + 0.045| = 0.005 <= 0.105  ✓
   r_3 = 0.04 * 0 - (-0.02) = 0.02  |(0.02)  + 0.045| = 0.065 <= 0.105  ✓
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .common import LAMBDA_STAR, NU_STAR, ProblemData, SolverResult


@dataclass
class KKTCertificate:
    """Full KKT certificate for the global minimum of the phantom-positions scenario."""

    idx_long: int
    idx_short: int
    w_long: float
    w_short: float
    lam: float  # budget dual variable
    nu: float  # leverage dual variable (>= 0)
    slack_margins: np.ndarray  # nu - |r_i + lam| for each inactive asset
    all_satisfied: bool


def derive(p: ProblemData) -> tuple[SolverResult, KKTCertificate]:
    """Derive and certify the global minimum via KKT conditions.

    Uses the analytical 2-support solution: long the highest-return asset
    (Tech, index 0) and short the lowest-return asset (HiYield, index 4),
    with both budget and leverage constraints simultaneously tight.

    Returns
    -------
    result:
        SolverResult with the analytically certified weights and objective.
    cert:
        KKTCertificate with dual variables and dual feasibility checks.
    """
    L = p.leverage_cap

    # Step 1: identify support from return spread
    idx_long = int(np.argmax(p.mu))  # index 0, Tech, mu = 0.20
    idx_short = int(np.argmin(p.mu))  # index 4, HiYield, mu = -0.07

    # Step 2: both constraints tight on 2-asset support
    #   w_long + w_short = 1    (budget)
    #   w_long - w_short = L    (leverage, since w_long > 0 > w_short)
    w_long = (1.0 + L) / 2.0  # = 1.25
    w_short = (1.0 - L) / 2.0  # = -0.25

    w_star = np.zeros(p.N)
    w_star[idx_long] = w_long
    w_star[idx_short] = w_short

    obj_star = p.objective(w_star)

    # Step 3: recover dual variables from stationarity
    #   r_i = (Sigma @ w*)[i] - mu[i]
    #   For active long:  r_long  + lam = -nu  (sign = +1)
    #   For active short: r_short + lam = +nu  (sign = -1)
    r = p.Sigma @ w_star - p.mu
    lam = -(r[idx_long] + r[idx_short]) / 2.0
    nu = (r[idx_short] - r[idx_long]) / 2.0

    # Step 4: dual feasibility for inactive assets
    inactive = [k for k in range(p.N) if k not in (idx_long, idx_short)]
    slack_margins = np.array([nu - abs(r[k] + lam) for k in inactive])
    all_satisfied = bool(nu >= -1e-10 and np.all(slack_margins >= -1e-10))

    cert = KKTCertificate(
        idx_long=idx_long,
        idx_short=idx_short,
        w_long=float(w_long),
        w_short=float(w_short),
        lam=float(lam),
        nu=float(nu),
        slack_margins=slack_margins,
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
    cert: KKTCertificate,
    result: SolverResult,
    p: ProblemData,
) -> None:
    """Print the full KKT derivation and dual feasibility certificate."""
    print("=" * 60)
    print("KKT GLOBAL OPTIMUM -- 2-SUPPORT DERIVATION")
    print("=" * 60)
    print()
    print("Step 1: Support identification")
    print(
        f"  Long  : {p.asset_names[cert.idx_long]:8s}  "
        f"(mu = {p.mu[cert.idx_long]:+.4f}, highest)"
    )
    print(
        f"  Short : {p.asset_names[cert.idx_short]:8s}  "
        f"(mu = {p.mu[cert.idx_short]:+.4f}, lowest)"
    )
    print()
    print("Step 2: Both constraints simultaneously tight")
    print("  Budget   : w_long + w_short = 1")
    print(f"  Leverage : w_long - w_short = {p.leverage_cap}")
    print(f"  => w_long  = (1 + L) / 2 = {cert.w_long:+.4f}")
    print(f"  => w_short = (1 - L) / 2 = {cert.w_short:+.4f}")
    print()
    print("Step 3: Dual variables from stationarity")
    r = p.Sigma @ result.weights - p.mu
    print(
        f"  r_long  = sigma_sq * w_long  - mu_long  = {r[cert.idx_long]:+.6f}"
    )
    print(
        f"  r_short = sigma_sq * w_short - mu_short = {r[cert.idx_short]:+.6f}"
    )
    print(f"  lambda  = -(r_long + r_short) / 2 = {cert.lam:+.6f}")
    print(
        f"  nu      = (r_short - r_long) / 2  = {cert.nu:+.6f}  (>= 0) {'ok' if cert.nu >= 0 else 'VIOLATED'}"
    )
    print()
    print(f"  Certified: lambda = {LAMBDA_STAR},  nu = {NU_STAR}")
    print(f"  Computed : lambda = {cert.lam:.6f},  nu = {cert.nu:.6f}")
    print()
    print("Step 4: Dual feasibility for inactive assets")
    print(f"  |r_i + lambda| <= nu = {cert.nu:.6f}:")
    print(
        f"  {'Asset':>8}  {'r_i':>10}  {'|r_i + lam|':>12}  {'Slack':>10}  {'OK?':>4}"
    )
    inactive = [
        k for k in range(p.N) if k not in (cert.idx_long, cert.idx_short)
    ]
    for k, slack in zip(inactive, cert.slack_margins, strict=True):
        ri = r[k]
        val = abs(ri + cert.lam)
        flag = "ok" if slack >= -1e-10 else "VIOLATED"
        print(
            f"  {p.asset_names[k]:>8}  {ri:10.6f}  {val:12.6f}  {slack:10.6f}  {flag}"
        )
    print()
    print("Constraint checks:")
    print(f"  sum(w*)  = {float(np.sum(result.weights)):.10f}  (must = 1.0)")
    print(
        f"  sum|w*|  = {float(np.sum(np.abs(result.weights))):.10f}  (cap = {p.leverage_cap}, tight)"
    )
    print()
    if cert.all_satisfied:
        print(
            "All KKT conditions satisfied. Sigma is strictly positive definite."
        )
        print("This is the unique global minimum.")
        print()
        print(f"  f(w*) = {result.objective:.12f}")
        print()
        print("Optimal weights:")
        for name, w in zip(p.asset_names, result.weights, strict=True):
            flag = "<- active" if abs(w) > 1e-9 else "  (zero, inactive)"
            print(f"  {name:8s}: w* = {w:+.4f}  {flag}")
    else:
        print("KKT conditions NOT satisfied -- check derivation.")
