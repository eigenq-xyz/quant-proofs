# Portfolio Optimization — EigenQ Research Series

Formally verified portfolio optimization: every solver guarantee is machine-checked
in Lean 4. The core claim is that standard QP solvers fail in predictable, testable
ways. This section documents seven stress scenarios, each designed to expose one
failure mode, each paired with an analytically certified KKT optimum.

## Research report

[**Lean PGD: Formally Verified Portfolio Optimization**](lean_pgd_performance) —
Performance across seven stress scenarios. Includes the 5×7 solver comparison matrix
(rows = solvers, columns = scenarios), accuracy table (objective gap vs KKT certificate),
speed table (wall-clock ms), and combined speed-accuracy scatter figure.

## Stress scenarios

| Scenario | Failure mode | N | Result |
|---|---|---|---|
| [Boundary Trap](boundary_trap) | L1 kink cycling; solver suboptimality | 10 | SLSQP fails; trust-constr suboptimal; Lean PGD exact |
| [Phantom Positions](phantom_positions) | Log-barrier prevents exact zeros | 5 | Interior-point: 5 phantom positions; Lean PGD: 2 exact |
| [VIX Shock](vix_shock) | Stale step size violates Lipschitz bound | 3 | GD oscillates; Lean PGD certified convergence |
| [S&P 500 Factor](sp500_factor) | O(N³) vs O(N) scaling | 10–500 | Gurobi impractical at N≥300; Lean PGD O(N) gradient |
| [Cholesky Crash](cholesky_crash) | Rank-deficient covariance (T < N) | 10 | SLSQP/Gurobi crash; Lean PGD LW shrinkage |
| [Precision Bleed](precision_bleed) | IEEE 754 constraint drift | 4 | SLSQP triggers production halt; Lean PGD exact |
| [Step Divergence](step_divergence) | Stale calibration after vol shock | 10 | GD diverges to NaN; Lean PGD certified |

## Implementation

The solver is implemented in Lean 4 (`optimization-proofs/`) and called from Python via
a persistent subprocess (`lean_pgd.py`). The native binary runs at **14.8 ns per solve**
at N=10; subprocess overhead is ~35 ms on first call. Build with:

```bash
cd optimization-proofs && lake build pgd_solve
```

The Python wrapper handles concurrent callers (module-level lock) and auto-restarts on
process failure. See `portfolio-proofs/lean_pgd.py` for the implementation.
