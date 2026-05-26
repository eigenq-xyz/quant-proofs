"""Precision-bleed solver modules for the March 2020 COVID crash reconstruction.

Modules
-------
common         : WindowData / WindowResult dataclasses; hardcoded March 2020 return
                 data (4 dp) for SPY/TLT/GLD/HYG; SLSQP_FEASIBILITY_TOLERANCE and
                 PRODUCTION_HALT_THRESHOLD constants.
slsqp_float    : SciPy SLSQP (tol=1e-12 optimality); Window 1 leverage violation
                 2.79e-9 exceeds the 1e-9 production halt threshold.
trust_constr   : SciPy trust-constr (barrier, 2N-variable reformulation); satisfies
                 constraints to near machine-epsilon.
gurobi         : Gurobi barrier QP (2N vars, box bounds); satisfies constraints to
                 Gurobi's default feasibility tolerance 1e-6.
ortools_gscip  : OR-Tools GSCIP via MathOpt; no license required; satisfies
                 constraints to SCIP's default feasibility tolerance 1e-9.
pgd_integer    : PGD with basis-point integer arithmetic; constraint satisfaction is
                 exact to integer precision (budget_error = 0.0 for all windows).
lean_pgd       : Lean 4 PGD via pgd_ffi (pgd_solve_flat); convergence guaranteed by
                 theorem pgd_convergence; constraint errors at float64 rounding level
                 (~1e-15), well below the production halt threshold.
"""
