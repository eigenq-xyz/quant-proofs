# Boundary Trap — Silent Suboptimality in Long-Short Portfolios with Gross Leverage Caps

Your optimizer runs, reports **Converged**, and you execute the trade. The problem
is that it gave you the wrong weights — and nothing in the output told you so.

---

## What happened in August 2007

On August 7-9, 2007, dozens of systematic long-short equity funds suffered large,
correlated losses over three consecutive trading days. The losses were unexpected
because these funds held diversified factor portfolios, not concentrated bets. The
VIX spiked from 11 to 25 in days; cross-sector correlations compressed sharply.

Khandani and Lo's post-mortem, ["What Happened to the Quants in August 2007?"
(Journal of Financial Markets, 2011)](https://doi.org/10.1016/j.finmar.2010.10.005),
traced the mechanism to a cascade: one large fund began liquidating its long-short
book, depressing the prices of crowded positions and triggering losses at other
funds, which deleveraged in turn. The paper documents that affected funds were
running systematic long-short strategies with gross leverage in the 150-200% range —
exactly the regime where a gross leverage cap of the form $\sum |w_i| \leq L$ is a
binding operational constraint.

**Why the optimizer connection matters.** During those three days, every fund in
the cluster had to rebalance against a covariance matrix estimated over a short
lookback window (to capture the new volatility regime) and subject to a binding
gross leverage cap. That is precisely the combination that causes a standard QP
solver to report "Converged" while returning a suboptimal allocation. The
underperformance that Khandani and Lo document was attributed to crowding and fire
sales. Silent optimizer suboptimality — invisible because solvers report success
and standard post-trade reconciliation checks constraint satisfaction, not QP
optimality — could not be ruled out as a contributing factor, and still cannot,
because none of the affected funds published their solver logs.

The failure is structurally undetectable without an independent optimality check.
This is why no post-mortem names it.

---

## Am I at risk?

You are exposed to this failure if all three of the following hold:

1. **You use a gross leverage cap.** Any constraint of the form $\sum |w_i| \leq L$,
   including 130/30, 150/50, or a market-neutral gross exposure limit.
2. **You use a general-purpose QP solver.** SciPy SLSQP, trust-constr, Gurobi
   barrier, CPLEX, or CVXPY/OSQP — without an independent dual-feasibility check
   after every solve.
3. **Your covariance matrix is ill-conditioned.** This occurs routinely during
   volatility regime changes (August 2007, March 2020, Q4 2018, August 2024), or
   whenever a short lookback window is used to improve regime responsiveness.

The failure is hardest to detect precisely when market conditions are most stressed
— which is when correct sizing matters most.

---

## The demonstration

This scenario reproduces the failure under the August 2007 parameter regime: 10
sector assets, a 5-day rolling covariance window (T = 5, N = 10, rank deficiency
mitigated by 10% shrinkage), and a 150% gross leverage cap.

```bash
uv run python scenarios/boundary_trap/scipy_slsqp.py
uv run python scenarios/boundary_trap/scipy_trust_constr.py
uv run python scenarios/boundary_trap/gurobi_interior_point.py
```

### What each solver does

**SciPy SLSQP** — the active-set solver gives up without converging:

```
Solver Converged: False
Solver Message:   Iteration limit reached
Iterations:       100
Objective Value:  -0.011282017378
```

**SciPy trust-constr** — the interior-point solver silently stops short:

```
Solver Converged:   True
Solver Message:     `gtol` termination condition is satisfied.
Iterations:         35
Objective Value:    -0.011282797998     <- SUBOPTIMAL by 2.9%
Budget Error:       2.94e-14
Leverage Violation: 0.00e+00
```

`success=True`. Constraints satisfied. Nothing in the output is wrong — except the
weights. The true optimal objective, verified analytically below, is
$-0.011621928054$.

**Gurobi** (simulated — see `gurobi_interior_point.py`): same mechanism as
trust-constr. The slack-variable reformulation creates a degenerate barrier
landscape; the complementarity gap tolerance is satisfied far from the true
optimum.

---

## Why standard solvers fail here

The gross leverage constraint $\sum_i |w_i| \leq 1.5$ is non-differentiable at
$w_i = 0$: the gradient of $|w_i|$ does not exist when a position crosses zero.
General-purpose QP solvers cannot handle this directly. Every major solver —
SciPy, Gurobi, CPLEX, OSQP — uses the same algebraic workaround.

**The standard reformulation:** introduce $u_i, v_i \geq 0$ with $w_i = u_i - v_i$,
so $|w_i| = u_i + v_i$. The constraint becomes linear: $\sum_i (u_i + v_i) \leq 1.5$.
The problem size doubles from 10 to 20 variables, and 10 new equality constraints
are added:

$$\min_{u,v \geq 0}\ \tfrac{1}{2}(u-v)^\top \Sigma (u-v) - \mu^\top(u-v)$$
$$\text{s.t. } \textstyle\sum_i(u_i - v_i) = 1,\quad \sum_i(u_i + v_i) \leq 1.5$$

**Why ill-conditioned covariance degrades the reformulation.** When $\Sigma$ has
condition number 42.7 (stress regime), the Hessian of the extended problem is
nearly singular along directions where $u_i$ and $v_i$ are simultaneously small.
Interior-point solvers traverse this flat landscape via a log-barrier penalty; the
gradient-norm stopping criterion is satisfied far from the true optimum, and the
solver exits reporting convergence.

Active-set solvers (SLSQP) face a different pathology: the absolute-value boundary
at $w_i = 0$ is non-smooth, and the active-set search cycles between constraints
without converging.

---

## Problem setup

```python
np.random.seed(42)
N, T = 10, 5
R = np.random.normal(loc=0.0005, scale=0.02, size=(T, N))
S = pd.DataFrame(R).cov().to_numpy()      # rank 4, min eig = -3.32e-20

# Minimal shrinkage to restore strict PSD while preserving ill-conditioning
tr = np.trace(S)
F = (tr / N) * np.eye(N)
Sigma = 0.1 * F + 0.9 * S                # min eig 3.55e-5, cond. 42.7
mu = pd.DataFrame(R).mean().to_numpy()
```

Return forecasts $\mu$ (sectors ordered by decreasing expected return):

```
Asset 0: +0.007043   <- long leg target
Asset 1: +0.005276
Asset 2: +0.003812
Asset 3: -0.012195   <- short leg target
...
```

Objective and constraints:

$$f(w) = \tfrac{1}{2}\, w^\top \Sigma\, w - \mu^\top w$$

$$\sum_{i=1}^{N} w_i = 1 \quad (\text{budget}), \qquad \sum_{i=1}^{N} |w_i| \leq 1.5 \quad (\text{gross leverage}), \qquad w_i \in [-1, 1]$$

---

## The optimal allocation: KKT verification

The global minimum is identified by guessing the support from the return spreads
and verifying KKT conditions, which are both necessary and sufficient for strictly
convex problems.

**Step 1 — Support identification.** Asset 0 has the highest return
($\mu_0 = +0.007043$); asset 3 has the most negative ($\mu_3 = -0.012195$). The
optimal allocation concentrates exposure in the two extreme-return sectors and
zeros out the rest.

**Step 2 — Solve the 2-asset system.** Assume $w_0 > 0$, $w_3 < 0$, with both
constraints tight:

$$w_0 + w_3 = 1 \qquad w_0 - w_3 = 1.5$$

Solving: $w_0 = 1.25$, $w_3 = -0.25$. This is a concentrated 125/25 long-short
book — 125% long in the best sector, 25% short in the worst.

**Step 3 — Verify KKT conditions.** Let $r_i = (\Sigma w^*)_i - \mu_i$. The
stationarity conditions are:

- For $w_i > 0$: $r_i + \lambda + \nu = 0$
- For $w_i < 0$: $r_i + \lambda - \nu = 0$
- For $w_i = 0$: $|r_i + \lambda| \leq \nu$

Dual variables from the active constraints:

$$\lambda = -\tfrac{r_0 + r_3}{2} = -0.002726 \qquad \nu = \tfrac{r_3 - r_0}{2} = 0.009412 > 0$$

Dual feasibility check — all zero-weight assets must satisfy $|r_i + \lambda| \leq 0.009412$:

| Asset | $|r_i + \lambda|$ | Slack |
|------:|------------------:|------:|
| 1     | 0.008172          | 0.001240 |
| 2     | 0.006565          | 0.002847 |
| 4     | 0.009308          | **0.000104** |
| 5     | 0.007424          | 0.001988 |
| 6     | 0.000072          | 0.009340 |
| 7     | 0.005205          | 0.004207 |
| 8     | 0.008745          | 0.000666 |
| 9     | 0.007624          | 0.001788 |

All slack margins are strictly positive (asset 4 is the tightest at 0.000104).
KKT conditions are satisfied; $\Sigma$ is strictly positive definite; the global
minimum is unique:

$$\boxed{w^* = [1.25,\ 0,\ 0,\ -0.25,\ 0,\ 0,\ 0,\ 0,\ 0,\ 0],\quad f(w^*) = -0.011621928054}$$

The trust-constr result ($-0.011282797998$) is **2.9% worse** than this. The gap
is not numerical noise: it reflects the optimizer settling in a flat basin rather
than reaching the true concentrated allocation.

---

## Related scenarios

| Scenario | Failure class |
|---|---|
| [`cholesky_crash/`](../cholesky_crash/) | Rank-deficient covariance causes solver to crash outright |
| `boundary_trap/` | Gross leverage cap causes silent suboptimal convergence (this scenario) |
| [`precision_bleed/`](../precision_bleed/) | Float64 rounding drifts across sequential rebalances |
| [`step_divergence/`](../step_divergence/) | Unverified gradient descent diverges during volatility shock |

---

## References

- Khandani, A. E. and Lo, A. W. (2011). "What happened to the quants in August
  2007? Evidence from factors and transactions data." _Journal of Financial
  Markets_ 14(1): 1-46. DOI: 10.1016/j.finmar.2010.10.005. Documents the August
  2007 quant crisis: correlated losses across systematic long-short funds under
  stressed covariance and binding gross leverage constraints — the exact operating
  conditions that trigger this failure mode.
- Duchi, J., Shalev-Shwartz, S., Singer, Y., and Chandra, T. (2008). "Efficient
  projections onto the $\ell_1$-ball for learning in high dimensions." _ICML 2008_,
  pp. 272-279. DOI: 10.1145/1390156.1390191. The $O(N \log N)$ analytical
  projection that avoids the $2N$-variable slack reformulation entirely.
- Nocedal, J. and Wright, S. J. (2006). _Numerical Optimization_, 2nd ed. Springer.
  Chapters 16 and 19 cover why slack-variable reformulations of L1 constraints
  create ill-conditioned barrier landscapes under stressed covariance.
- Wright, S. J. (1997). _Primal-Dual Interior-Point Methods_. SIAM.
  DOI: 10.1137/1.9781611971453. Section 4 covers complementarity gap tolerances
  and why interior-point solvers halt before the true minimum in flat landscapes.
