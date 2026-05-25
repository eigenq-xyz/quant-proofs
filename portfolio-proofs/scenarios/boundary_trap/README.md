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
underperformance Khandani and Lo document was attributed to crowding and fire sales.
Silent optimizer suboptimality — invisible because solvers report success and
standard post-trade reconciliation checks constraint satisfaction, not QP optimality
— could not be ruled out as a contributing factor, and still cannot, because none of
the affected funds published their solver logs.

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

## Real-world reconstruction: August 3-9, 2007

This reconstruction runs standard solvers on the exact optimization problem a
systematic long-short fund would have faced on the morning of August 9, 2007, using
real market data.

**Data source:** Ken French 10 Industry Portfolio daily value-weighted returns
(public domain). Five-day window August 3-9, 2007, ending the day BNP Paribas froze
three funds. Fetched via `scripts/ingest_french_10ind.py`; tracked in DVC.

**Prerequisites:**

```bash
# From portfolio-proofs/
docker compose up -d          # start MinIO
dvc pull                      # fetch data/french_10ind_daily_vw.parquet
```

**Run the reconstruction:**

```bash
uv run python scenarios/boundary_trap/august_2007_reconstruction.py
```

### The five trading days

| Date | NoDur | Durbl | Manuf | Enrgy | HiTec | Telcm | Shops | Hlth | Utils | Other |
|:-----|------:|------:|------:|------:|------:|------:|------:|-----:|------:|------:|
| Aug 3 | −1.37 | −3.42 | −2.18 | −3.56 | −2.35 | −2.38 | −2.83 | −1.41 | −3.51 | −3.24 |
| Aug 6 | +2.51 | +1.06 | +1.37 | +0.94 | +1.27 | +0.77 | +2.21 | +2.12 | +3.06 | +3.22 |
| Aug 7 | +0.67 | +0.50 | +0.20 | +2.05 | +0.02 | +0.11 | +0.56 | +0.39 | +1.92 | +0.89 |
| Aug 8 | +0.73 | +2.13 | +0.62 | +1.95 | +1.86 | +0.14 | +1.45 | +1.52 | +1.05 | +1.92 |
| **Aug 9** | −2.21 | −2.45 | −2.68 | −3.26 | −2.30 | **−2.78** | −3.03 | **−1.94** | −2.52 | −3.12 |

*All values in percent per day. Source: Ken French Data Library, VW returns.*

The defensive character of Health Care (Hlth, best five-day mean: +0.136%/day) and
the risk-off selloff in Telecom (Telcm, worst five-day mean: −0.828%/day) are the
dominant features of this window.

### Covariance structure

With T = 5 days and N = 10 industries, the sample covariance has rank 4. Minimal
Ledoit-Wolf style shrinkage (α = 0.10 toward scaled identity) restores strict
positive definiteness while preserving ill-conditioning:

| Property | Value |
|:---------|------:|
| Sample rank | 4 (of 10) |
| Min eigenvalue (raw) | −1.11 × 10⁻¹⁹ |
| Min eigenvalue (shrunk) | 5.29 × 10⁻⁵ |
| Max eigenvalue (shrunk) | 4.57 × 10⁻³ |
| Condition number | **86.4** |

### What each solver returns

```
Solver                         Status         Objective      Gap to optimum
----------------------------------------------------------------------
SciPy SLSQP (active-set)       FAILED    -0.003413213603               —
SciPy trust-constr (barrier)   Converged -0.003412309165           4.59%
True optimum (KKT-verified)    —         -0.003576587456           0.00%
```

**SciPy SLSQP** cycles at the L1 boundary and exhausts 100 iterations without
converging (leverage violation: 1.63 × 10⁻⁵).

**SciPy trust-constr** reports `Converged: True` and returns:

```
Weights: NoDur +0.2499 / Telcm −0.2499 / Hlth +0.9999
```

This three-sector allocation (NoDur long 25%, Hlth long 100%, Telcm short 25%)
looks reasonable. Budget is satisfied. Leverage cap is met. The solver log contains
no warning. But the allocation is **4.59% worse** than the true optimum in
risk-adjusted objective value.

### The true optimal allocation

The KKT-verified global minimum concentrates entirely on the two highest-spread
sectors:

$$\boxed{w^* = \text{Hlth}\ {+}1.25,\quad \text{Telcm}\ {-}0.25,\quad \text{all others}\ 0}$$

$$f(w^*) = -0.003576587456$$

This is a concentrated 125/25 long-short book: 125% long in Health Care (the
defensive outperformer of the week) and 25% short in Telecom (the largest loser).
The trust-constr weights spread 25% of the long leg across Consumer Staples instead
— an allocation that is feasible but suboptimal by 4.59%.

---

## Why standard solvers fail here

The gross leverage constraint $\sum_i |w_i| \leq 1.5$ is non-differentiable at
$w_i = 0$. General-purpose solvers rewrite it by doubling the variable space:
introduce $u_i, v_i \geq 0$ with $w_i = u_i - v_i$ so $|w_i| = u_i + v_i$.

$$\min_{u,v \geq 0}\ \tfrac{1}{2}(u-v)^\top \Sigma (u-v) - \mu^\top(u-v)$$
$$\text{s.t. } \textstyle\sum_i(u_i - v_i) = 1,\quad \sum_i(u_i + v_i) \leq 1.5$$

The problem grows from 10 to 20 variables. Under an ill-conditioned $\Sigma$
(condition number 86.4), the Hessian of the extended problem is nearly singular
along directions where $u_i$ and $v_i$ are simultaneously near zero. The interior-
point log-barrier penalty creates an extremely flat landscape in those directions.
The gradient-norm stopping criterion is satisfied far from the true optimum, and the
solver exits reporting convergence.

Active-set solvers (SLSQP) face a different pathology: the $|w_i|$ boundary is
non-smooth, and the active-set search cycles without converging.

---

## The optimal allocation: KKT derivation

The true minimum is derived algebraically — not asserted numerically.

**Step 1 — Support identification.** Hlth has the highest mean return
(+0.136%/day); Telcm has the most negative (−0.828%/day). The optimal long-short
book concentrates exposure on these two sectors.

**Step 2 — Solve the 2-industry system.** Assume $w_{\text{Hlth}} > 0$ and
$w_{\text{Telcm}} < 0$, both constraints tight:

$$w_{\text{Hlth}} + w_{\text{Telcm}} = 1 \qquad w_{\text{Hlth}} - w_{\text{Telcm}} = 1.5$$

Solving: $w_{\text{Hlth}} = 1.25$, $w_{\text{Telcm}} = -0.25$.

**Step 3 — Verify KKT conditions.** Let $r_i = (\Sigma w^*)_i - \mu_i$.
Stationarity gives:

$$\lambda = -\tfrac{r_{\text{Hlth}} + r_{\text{Telcm}}}{2} = -0.003760
\qquad
\nu = \tfrac{r_{\text{Telcm}} - r_{\text{Hlth}}}{2} = 0.004762 > 0$$

Dual feasibility — each zero-weight industry must satisfy $|r_k + \lambda| \leq \nu = 0.004762$:

| Industry | $|r_k + \lambda|$ | Slack |
|:---------|------------------:|------:|
| NoDur    | 0.004124          | **0.000638** |
| Durbl    | 0.000957          | 0.003805 |
| Manuf    | 0.001868          | 0.002894 |
| Enrgy    | 0.000391          | 0.004371 |
| HiTec    | 0.000448          | 0.004315 |
| Shops    | 0.000085          | 0.004677 |
| Utils    | 0.003337          | 0.001426 |
| Other    | 0.002623          | 0.002139 |

All slack margins are strictly positive (NoDur is tightest at 0.000638). Since
$\Sigma$ is strictly positive definite and KKT conditions are both necessary and
sufficient, this is the unique global minimum.

---

## Mechanistic isolation scripts

The following scripts reproduce the failure mechanism on a synthetic matrix (no data
dependency), useful for understanding the solver pathology in isolation:

```bash
uv run python scenarios/boundary_trap/scipy_slsqp.py
uv run python scenarios/boundary_trap/scipy_trust_constr.py
uv run python scenarios/boundary_trap/gurobi_interior_point.py
```

These use a synthetic 10-asset, 5-day covariance (condition number 42.7) with the
same failure structure. The Gurobi script runs without a license, printing a
mathematical analysis of the barrier termination mechanism.

---

## Files

| File | Purpose |
|:-----|:--------|
| `august_2007_reconstruction.py` | Real-data reconstruction using Ken French industry returns |
| `scipy_slsqp.py` | Mechanistic isolation: active-set SQP on synthetic matrix |
| `scipy_trust_constr.py` | Mechanistic isolation: interior-point barrier on synthetic matrix |
| `gurobi_interior_point.py` | Mechanistic isolation: Gurobi barrier analysis (simulation mode) |

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
  stressed covariance and binding gross leverage constraints.
- French, K. R. Data Library: 10 Industry Portfolios (daily).
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html.
  Public domain. Primary data source for the reconstruction.
- Duchi, J., Shalev-Shwartz, S., Singer, Y., and Chandra, T. (2008). "Efficient
  projections onto the $\ell_1$-ball for learning in high dimensions." _ICML 2008_,
  pp. 272-279. DOI: 10.1145/1390156.1390191. The $O(N \log N)$ analytical
  projection that avoids the $2N$-variable slack reformulation.
- Nocedal, J. and Wright, S. J. (2006). _Numerical Optimization_, 2nd ed. Springer.
  Chapters 16 and 19 cover active-set and interior-point methods for QP.
- Wright, S. J. (1997). _Primal-Dual Interior-Point Methods_. SIAM.
  DOI: 10.1137/1.9781611971453. Section 4 covers complementarity gap tolerances
  and premature termination in flat barrier landscapes.
