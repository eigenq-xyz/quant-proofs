"""Step-divergence solver modules for the February 2018 Volmageddon reconstruction.

Citation notes for step_divergence.qmd
---------------------------------------
- VIX methodology/formula: cite the CBOE (2019) white paper
  <https://cdn.cboe.com/resources/vix/VIX_Methodology.pdf>
  footnote key: cboe2019
- February 5, 2018 spike event (Volmageddon / XIV collapse): cite
  U.S. SEC DERA (2025). "Demystify the Surge in VIX."
  <https://www.sec.gov/files/dera-vix-working-paper-2504.pdf>
  footnote key: sec_dera
- Whaley (2009) DOI: 10.3905/JPM.2009.35.3.098

Modules
-------
common        : ProblemData / SolverResult dataclasses; calibration + shock data loader.
gd_fixed      : Fixed-eta gradient descent (unconstrained); diverges when eta_cal >> 2/lam_max_shock.
pgd_adaptive  : Adaptive-eta PGD; recomputes step size from post-shock covariance, converges.
slsqp         : SciPy SLSQP — active-set SQP; hits 100-iteration limit due to L1 kink
                (same failure mode as boundary_trap); returns converged=False.
trust_constr  : SciPy trust-constr — interior-point barrier; converges via 2N reform.
gurobi        : Gurobi barrier QP; converges exactly (requires license).
kkt_optimum   : Analytical KKT derivation and dual-feasibility certificate.
"""
