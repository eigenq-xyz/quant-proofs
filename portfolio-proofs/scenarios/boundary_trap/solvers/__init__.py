"""Boundary-trap solver modules for the August 2007 stressed-covariance reconstruction.

Modules
-------
common        : ProblemData / SolverResult dataclasses; data loader (no box bounds).
slsqp         : SciPy SLSQP — active-set SQP; cycles at the L1 kink, fails.
trust_constr  : SciPy trust-constr — interior-point barrier; converges via 2N reform.
gurobi        : Gurobi barrier QP; converges exactly (requires license).
ortools_gscip : OR-Tools GSCIP — global solver via MathOpt; converges exactly.
kkt_optimum   : Analytical KKT derivation and dual-feasibility certificate.
"""
