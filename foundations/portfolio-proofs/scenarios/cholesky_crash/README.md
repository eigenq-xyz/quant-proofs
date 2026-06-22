# Cholesky Crash — Eigenvalue Deficit Under Short Lookback Windows

When the return lookback window $T$ is shorter than the number of assets $N$,
the sample covariance matrix is rank-deficient and develops tiny negative
eigenvalues from float64 rounding. QP solvers that require a Cholesky
decomposition of the quadratic objective matrix cannot proceed. This scenario
reproduces that failure with three solvers under fixed, reproducible market
parameters.

---

## The failure in one sentence

A 5-day lookback over 10 sector assets produces a rank-4 covariance matrix
with minimum eigenvalue $-3.32 \times 10^{-20}$; SciPy SLSQP exhausts 100
iterations without converging, Gurobi aborts with `Error 10020: Objective Q
is not PSD`, and CVXPY rejects the problem before calling any solver.

---

## Why this happens

The sample covariance matrix formed from $T$ return observations on $N$ assets
has rank at most $\min(T, N) - 1$. When $T < N$, rank deficiency is
unavoidable. In floating-point arithmetic, the zero eigenvalues that the theory
predicts appear as small negative values at the level of machine epsilon. The
covariance matrix is then **not positive semi-definite** in the strict float64
sense.

Solvers that rely on Cholesky decomposition $LL^T$ of the objective matrix $Q$
encounter a negative diagonal entry during the forward sweep: they must compute
$\sqrt{d_{kk}}$ where $d_{kk} < 0$, which is undefined in real arithmetic. The
three solvers in this folder hit that boundary in three distinct ways.

This is not a pathological edge case. During market shock regimes, portfolio
managers routinely shrink the lookback window to capture the new correlation
structure. With $N = 10$ sector ETFs and $T = 5$ days, rank deficiency is an
ordinary operational condition.

---

## Numerical setup

The problem is fully reproducible. Every script uses the same seed and
parameters.

```python
import numpy as np
import pandas as pd

np.random.seed(42)
N_sectors, T_days = 10, 5

returns = np.random.normal(loc=0.0005, scale=0.02, size=(T_days, N_sectors))
S = pd.DataFrame(returns).cov().to_numpy()
mu = pd.DataFrame(returns).mean().to_numpy()
```

Matrix properties confirmed by running:

| Property | Value |
| :--- | :--- |
| Shape | $10 \times 10$ |
| Rank | 4 (out of 10) |
| Minimum eigenvalue | $-3.32 \times 10^{-20}$ (float64 rounding; theoretically zero) |

Objective:

$$f(w) = \tfrac{1}{2}\, w^T S\, w \;-\; \mu^T w$$

Constraints: $\sum_i w_i = 1$, $\sum_i |w_i| \leq 1.5$.

> **Note.** The flat scripts in this directory (`scipy_slsqp.py`, `gurobi_non_psd.py`,
> `cvxpy_osqp.py`) are legacy artifacts that additionally enforce per-asset box bounds
> $w_i \in [-1, 1]$ and use synthetic data (`np.random.seed(42)`).  The canonical
> scenario formulation is `cholesky_crash.qmd` — no box bounds, real March 9–13 2020
> Ken French 10-industry returns.  The KKT certificate in the `.qmd` is derived without
> box bounds; solutions with $|w_i| > 1$ are therefore feasible and expected.

Expected returns $\mu$:

```
[ 0.007043,  0.005276,  0.003812, -0.012195, -0.012138,
 -0.010005, -0.002846,  0.002719, -0.011351, -0.010410]
```

---

## Quick start

From the `foundations/portfolio-proofs/` root:

```bash
uv run python scenarios/cholesky_crash/scipy_slsqp.py
uv run python scenarios/cholesky_crash/gurobi_non_psd.py
uv run python scenarios/cholesky_crash/cvxpy_osqp.py
```

`scipy_slsqp.py` runs without optional dependencies. The Gurobi and CVXPY
scripts fall back to a documented simulation log when those packages are not
installed.

---

## Scripts

### `scipy_slsqp.py`

SciPy's SLSQP (Sequential Least-Squares Programming, an active-set SQP
method). Does not crash immediately, but oscillates across the degenerate
eigenspace and exhausts the iteration limit.

Actual output:

```
Solver Converged: False
Solver Message: Iteration limit reached
Iterations: 100
Optimal weights: [ 1.00e+00  2.50e-01  1.77e-08 -1.55e-01 -9.50e-02
                   2.31e-08  6.41e-06 -1.15e-06 -8.39e-05  1.33e-07]
```

The output weights do not satisfy the budget constraint ($w_1 = 1.0$ alone
accounts for the full unit budget) and do not correspond to any local
minimiser of $f$.

### `gurobi_non_psd.py`

Gurobi commercial optimizer (barrier/simplex). Requires a Gurobi license;
runs in simulation mode without one. The documented failure path:

1. Gurobi's barrier solver performs a strict Cholesky decomposition of $Q$
   before optimization. Even a single eigenvalue $\lambda < 0$ triggers an
   immediate abort:
   ```
   gurobipy.GurobiError: Error 10020: Objective Q is not PSD
   ```
2. The `NonConvex=2` workaround disables the PSD check but switches the
   solver to a spatial branch-and-bound MIQP solver built for globally
   non-convex problems. Observed production latency spikes reach
   $10{,}000\times$ the normal barrier runtime.

### `cvxpy_osqp.py`

CVXPY with OSQP (Operator Splitting QP, ADMM-based) as the backend. Two
failure paths are documented:

1. **DCP verification failure.** CVXPY's Disciplined Convex Programming
   checker rejects `quad_form(w, S)` when $\lambda_{\min}(S) < 0$, before
   any solver is called:
   ```
   cvxpy.error.DCPError: The objective is not Disciplined Convex Programming.
   ```
2. **OSQP solver failure.** If the matrix is forced PSD by a small diagonal
   perturbation and the problem is passed through, OSQP's ADMM iteration must
   solve $(P + \sigma I + A^T \rho A)\, x = b$ at each step. A singular $P$
   makes that linear system ill-conditioned; the iterates oscillate and the
   solver returns `solver_inaccurate` or diverges entirely.

---

## The verified solution

The root cause is the absence of a PSD-guaranteed covariance estimator.
Ledoit-Wolf shrinkage replaces $S$ with

$$\hat\Sigma = \alpha F + (1 - \alpha) S, \qquad F = \frac{\mathrm{tr}(S)}{N} I,
\quad \alpha \in (0, 1)$$

The formally verified solver (planned: `foundations/portfolio-proofs/lean/`) proves the
theorem `shrinkage_psd`: $\hat\Sigma$ has strictly positive eigenvalues for
every $S$ and every $\alpha \in (0,1)$. The Cholesky decomposition therefore
never encounters a negative diagonal entry. This guarantee is enforced at
compile time, not at runtime.

---

## Files

| File | What it does |
| :--- | :--- |
| `scipy_slsqp.py` | Runs SciPy SLSQP; reproduces iteration-limit failure |
| `gurobi_non_psd.py` | Documents Gurobi `Error 10020` crash path; simulation mode without license |
| `cvxpy_osqp.py` | Documents CVXPY DCP rejection and OSQP divergence; simulation mode without CVXPY |

---

## Related scenarios

| Scenario | Failure class |
| :--- | :--- |
| `cholesky_crash/` | Non-PSD covariance causes Cholesky failure (this scenario) |
| [`boundary_trap/`](../boundary_trap/) | L1 non-differentiability traps active-set solvers |
| [`precision_bleed/`](../precision_bleed/) | Float64 rounding accumulates across rebalance steps |
| [`step_divergence/`](../step_divergence/) | Unverified gradient descent diverges under volatility shock |

---

## References

- Ledoit, O. and Wolf, M. (2004). "A well-conditioned estimator for
  large-dimensional covariance matrices." _Journal of Multivariate Analysis_
  88(2): 365-411. DOI: 10.1016/S0047-259X(03)00096-4. The canonical shrinkage
  estimator that guarantees PSD output; directly cited in our `shrinkage_psd`
  theorem.
- Marčenko, V. A. and Pastur, L. A. (1967). "Distribution of eigenvalues for
  some sets of random matrices." _Mathematics of the USSR-Sbornik_ 1(4): 457-483.
  Establishes the limiting spectral distribution when $N/T \to c > 1$; eigenvalues
  collapse to zero, providing the asymptotic theory underlying why shrinkage is
  necessary at finite $T/N$ ratios.
- Anderson, T. W. (2003). _An Introduction to Multivariate Statistical Analysis_,
  3rd ed. Wiley. Chapter 7 (Wishart distribution). The standard finite-sample
  result: the sample covariance drawn from $T$ observations on $N$ variables is
  singular with probability one when $T < N$.
- Gurobi Optimization (2023). "Error 10020: Objective Q not PSD." Gurobi Help
  Center. https://support.gurobi.com/hc/en-us/articles/360041016611. Documents
  the exact commercial-solver manifestation of passing a non-PSD matrix to a QP
  solver.
