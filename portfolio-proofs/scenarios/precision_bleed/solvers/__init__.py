"""Precision-bleed solver modules for the March 2020 COVID crash reconstruction.

Modules
-------
common      : WindowData / WindowResult dataclasses; yfinance data loader for
              SPY/TLT/GLD/HYG rolling windows; SLSQP_FEASIBILITY_TOLERANCE and
              PRODUCTION_HALT_THRESHOLD constants.
slsqp_float : SciPy SLSQP with optimality tol=1e-12 on float64 weights; reports
              success=True but may violate constraints at the 1e-8 feasibility level.
pgd_integer : PGD with basis-point integer arithmetic; constraint satisfaction is
              exact to integer precision (budget_error = 0.0 for all windows).
"""
