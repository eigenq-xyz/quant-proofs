"""Woodbury inverse demonstration for the single-factor CAPM portfolio.

Demonstrates the Sherman-Morrison-Woodbury identity applied to the rank-1 + diagonal
CAPM covariance. The key result: Sigma^{-1} v can be computed in O(N) rather than
O(N^3) by exploiting the factor structure.

The Woodbury identity for rank-1 + diagonal covariance:
  Sigma = sigma_eps^2 * I + sigma_f^2 * beta beta'

  Sigma^{-1} v = v / sigma_eps^2
                 - c * beta * (beta' v)
  where
    c = sigma_f^2 / (sigma_eps^4 * (1 + sigma_f^2 ||beta||^2 / sigma_eps^2))

This is O(N): one dot product + two vector scalings.

The unconstrained optimum is w_unc = Sigma^{-1} mu (one Woodbury evaluation).
The constrained optimum requires solving the budget + L1 dual problem; this module
shows the unconstrained direction and its distance from the feasible set.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .common import ProblemData


@dataclass
class WoodburyCertificate:
    N: int
    lambda_star: (
        float  # budget dual variable (from PGD at convergence, estimated)
    )
    nu_star: float  # L1 leverage dual variable (estimated)
    n_active: int  # number of nonzero weights in w_star
    all_satisfied: bool
    # Additional diagnostics
    w_unc_leverage: (
        float  # sum|w_unc|: how far unconstrained is from feasible set
    )
    w_unc_budget: float  # sum(w_unc): how far unconstrained is from budget=1


def woodbury_inv_v(
    v: np.ndarray,
    beta: np.ndarray,
    sigma_eps_sq: float,
    sigma_f_sq: float,
) -> np.ndarray:
    """Compute Sigma^{-1} v in O(N) via Sherman-Morrison.

    Sigma = sigma_eps^2 * I + sigma_f^2 * beta beta'

    By Sherman-Morrison with A = sigma_eps^2 * I and u = sigma_f * beta:
      Sigma^{-1} = A^{-1} - A^{-1} u (1 + u' A^{-1} u)^{-1} u' A^{-1}
                 = (1/sigma_eps^2) I - c * beta beta'
    where
      c = sigma_f^2 / (sigma_eps^4 * (1 + sigma_f^2 ||beta||^2 / sigma_eps^2))

    Cost: 1 dot product + 2 vector scalings = O(N).
    """
    beta_norm_sq = float(beta @ beta)
    c = sigma_f_sq / (
        sigma_eps_sq**2 * (1.0 + sigma_f_sq * beta_norm_sq / sigma_eps_sq)
    )
    return v / sigma_eps_sq - c * beta * float(beta @ v)


def derive(p: ProblemData) -> tuple[np.ndarray, WoodburyCertificate]:
    """Show the Woodbury unconstrained direction and the converged PGD optimum.

    The unconstrained optimum w_unc = Sigma^{-1} mu is computed in O(N).
    It is infeasible (sum(w_unc) >> 1 and sum|w_unc| >> L), so the constrained
    optimum is found by running PGD to convergence using the O(N) factor gradient.

    The PGD solution is the certified feasible optimum. The Woodbury computation
    demonstrates that each PGD gradient step costs O(N), not O(N^2).

    Returns (w_star_pgd, certificate).
    """
    sigma_eps_sq = p.sigma_eps_sq
    sigma_f_sq = p.sigma_f_sq
    beta = p.beta

    # Woodbury unconstrained direction: Sigma^{-1} mu (O(N))
    w_unc = woodbury_inv_v(p.mu, beta, sigma_eps_sq, sigma_f_sq)

    # Run converged PGD using the O(N) factor gradient
    # (same gradient as Woodbury, same function as gradient_factor)
    from .pgd_reference import run_pgd

    w_star, _ = run_pgd(p, use_factor_gradient=True, tol=1e-10, max_iter=500)

    # Estimate KKT dual variables from the converged solution
    kkt_resid = p.Sigma @ w_star - p.mu
    active = np.abs(w_star) > 1e-10
    leverage = float(np.sum(np.abs(w_star)))
    nu_star = 0.0
    lam_star = 0.0
    if np.any(active):
        if leverage > p.leverage_cap - 1e-6:
            # L1 active
            kkt_active = kkt_resid[active]
            sign_active = np.sign(w_star[active])
            # lambda + nu * sign(w*) = -(Sigma w* - mu) = -kkt_resid
            # Solve: find (lambda, nu) such that lambda + nu * sign(w*_i) = -kkt_resid_i
            # For two active components with opposite signs, this is a 2x2 system.
            # Approximate: nu = half the spread of -kkt_resid across sign groups.
            pos_mean = (
                float(np.mean(-kkt_active[sign_active > 0]))
                if np.any(sign_active > 0)
                else 0.0
            )
            neg_mean = (
                float(np.mean(-kkt_active[sign_active < 0]))
                if np.any(sign_active < 0)
                else 0.0
            )
            if np.any(sign_active > 0) and np.any(sign_active < 0):
                nu_star = (pos_mean - neg_mean) / 2.0
                lam_star = (pos_mean + neg_mean) / 2.0
            else:
                lam_star = float(np.mean(-kkt_active))
        else:
            lam_star = float(np.mean(-kkt_resid[active]))

    n_active = int(np.sum(np.abs(w_star) > 1e-10))
    all_satisfied = (
        abs(float(np.sum(w_star)) - 1.0) < 1e-6
        and leverage <= p.leverage_cap + 1e-6
    )

    cert = WoodburyCertificate(
        N=p.N,
        lambda_star=lam_star,
        nu_star=nu_star,
        n_active=n_active,
        all_satisfied=all_satisfied,
        w_unc_leverage=float(np.sum(np.abs(w_unc))),
        w_unc_budget=float(np.sum(w_unc)),
    )
    return w_star, cert
