"""Cholesky-crash solver modules for the March 2020 rank-deficient covariance reconstruction.

Modules
-------
common       : ProblemData / SolverResult dataclasses; data loader storing both raw S
               (rank-deficient) and shrunk Sigma (PSD). No per-asset box bounds.
slsqp        : SciPy SLSQP — run on raw S (rank-deficient Hessian). Hits iteration
               limit (100 iterations) due to non-PSD curvature and L1 kink; returns
               converged=False.
gurobi       : Gurobi barrier QP — run on raw S. Raises GurobiError 10020
               (Objective Q is not PSD) before optimization begins, because the barrier
               algorithm performs a strict Cholesky decomposition of Q first. Simulated
               log documents the failure and the NonConvex=2 branch-and-bound workaround.
cvxpy_osqp   : CVXPY / OSQP — two documented failure paths: (1) DCP rejection when
               lambda_min(S) < 0; (2) OSQP solver_inaccurate under ill-conditioning
               if forced through. Simulation log only.
pgd_lw       : PGD + Ledoit-Wolf shrinkage — uses the PSD Sigma; O(N^2) gradient step
               plus O(N log N) dual-bisection projection. Converges to the global minimum.
"""
