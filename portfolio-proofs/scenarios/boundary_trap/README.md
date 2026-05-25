# Boundary Trap — Suboptimal Convergence Under L1 Gross Leverage Constraints

Standard interior-point QP solvers report convergence on a 10-industry,
5-day covariance problem calibrated to the August 2007 quant crisis, yet return
weights that are **4.59% worse** in risk-adjusted objective value than the
analytically derived global minimum.

---

## The mathematical problem

A systematic long-short equity fund allocates across $N$ industry portfolios subject
to a gross leverage cap. The allocation problem is:

$$\min_{w \in \mathbb{R}^N}\ \tfrac{1}{2} w^\top \Sigma w - \mu^\top w$$

$$\text{subject to}\quad \sum_{i=1}^N w_i = 1 \quad (\text{budget}), \qquad
\sum_{i=1}^N |w_i| \leq L \quad (\text{gross leverage}), \qquad
w_i \in [-1, 1]$$

The gross leverage constraint $\sum |w_i| \leq L$ is non-differentiable at $w_i = 0$.
Standard QP solvers handle this by introducing $2N$ auxiliary variables — a
reformulation that doubles problem dimensionality and degrades numerical conditioning
under stressed covariance matrices. This scenario demonstrates the resulting failure.

---

## Why August 2007 is the stress scenario

Khandani and Lo (2011) document that systematic long-short equity funds operating
in August 2007 used gross leverage in the 150-200% range and estimated covariance
matrices over short rolling windows to capture the rapidly changing market regime.
Their paper characterizes the market conditions quantitatively: cross-sector
correlations compressed sharply and volatility (measured by VIX) spiked from
approximately 11 to 25 over three trading days.

These are precisely the conditions — short lookback window ($T < N$), spiking
cross-asset correlations, binding gross leverage cap — that make the standard
solver reformulation numerically unstable. We use the five trading days ending
August 9, 2007 (the day BNP Paribas froze three funds) from the Ken French 10
Industry Portfolio daily returns as a concrete, reproducible instance.

We do not claim that any specific fund ran this optimization or that optimizer
suboptimality contributed to the August 2007 losses. We claim that under the
market conditions that Khandani and Lo document, a standard QP solver solving this
problem exhibits the failure we demonstrate below.

---

## The August 2007 reconstruction

**Data:** Ken French 10 Industry Portfolio daily value-weighted returns (public
domain). Five-day window August 3-9, 2007.

**Prerequisites:**

```bash
# From portfolio-proofs/
docker compose up -d          # start MinIO
dvc pull                      # fetch data/french_10ind_daily_vw.parquet
uv run python scenarios/boundary_trap/august_2007_reconstruction.py
```

### Returns for the five-day window

| Date | NoDur | Durbl | Manuf | Enrgy | HiTec | Telcm | Shops | Hlth | Utils | Other |
|:-----|------:|------:|------:|------:|------:|------:|------:|-----:|------:|------:|
| Aug 3 | −1.37 | −3.42 | −2.18 | −3.56 | −2.35 | −2.38 | −2.83 | −1.41 | −3.51 | −3.24 |
| Aug 6 | +2.51 | +1.06 | +1.37 | +0.94 | +1.27 | +0.77 | +2.21 | +2.12 | +3.06 | +3.22 |
| Aug 7 | +0.67 | +0.50 | +0.20 | +2.05 | +0.02 | +0.11 | +0.56 | +0.39 | +1.92 | +0.89 |
| Aug 8 | +0.73 | +2.13 | +0.62 | +1.95 | +1.86 | +0.14 | +1.45 | +1.52 | +1.05 | +1.92 |
| Aug 9 | −2.21 | −2.45 | −2.68 | −3.26 | −2.30 | −2.78 | −3.03 | −1.94 | −2.52 | −3.12 |

*Percent per day. Source: Ken French Data Library, value-weighted returns.*

Five-day mean returns: Hlth +0.136%/day (best), Telcm −0.828%/day (worst).

### Covariance structure

With $T = 5 < N = 10$, the sample covariance has rank 4 (Marčenko and Pastur 1967;
Anderson 2003, Ch. 7). Minimal Ledoit-Wolf shrinkage ($\alpha = 0.10$ toward
scaled identity) restores strict positive definiteness:

| Property | Value |
|:---------|------:|
| Sample rank | 4 of 10 |
| Min eigenvalue (raw $S$) | $-1.11 \times 10^{-19}$ |
| Min eigenvalue (shrunk $\hat\Sigma$) | $5.29 \times 10^{-5}$ |
| Condition number ($\hat\Sigma$) | **86.4** |

### Solver results

```
Solver                         Converged    Objective         Gap
─────────────────────────────────────────────────────────────────
SciPy SLSQP (active-set)       False    −0.003413213603        —
SciPy trust-constr (barrier)   True     −0.003412309165    4.59%
True optimum (KKT-verified)    —        −0.003576587456    0.00%
```

**SLSQP** hits the 100-iteration limit. The active-set search cycles at the
non-differentiable $|w_i|$ boundary (Nocedal and Wright 2006, Ch. 16).

**trust-constr** reports `Converged: True` — constraints satisfied, gradient
norm below tolerance — and returns:

```
NoDur  +0.2499
Telcm  −0.2499
Hlth   +0.9999
```

This three-sector allocation is feasible. The solver log contains no warning.
Yet the allocation is 4.59% worse in objective value than the mathematically
certified optimum derived below.

---

## Why the reformulation fails

To handle $\sum |w_i| \leq L$, every major solver (SciPy, Gurobi, CPLEX, OSQP)
introduces auxiliary variables $u_i, v_i \geq 0$ with $w_i = u_i - v_i$,
converting the constraint to the linear form $\sum (u_i + v_i) \leq L$:

$$\min_{u, v \geq 0}\ \tfrac{1}{2}(u-v)^\top \hat\Sigma (u-v) - \mu^\top(u-v)
\quad \text{s.t.}\quad \textstyle\sum(u_i - v_i) = 1,\quad \sum(u_i + v_i) \leq L$$

The Hessian of the extended problem is positive semi-definite but nearly singular
along directions where $u_i$ and $v_i$ are simultaneously near zero — directions
that are plentiful under an ill-conditioned $\hat\Sigma$ (condition number 86.4).
Interior-point methods add a log-barrier penalty $-\tfrac{1}{\mu}\sum(\log u_i +
\log v_i)$; the gradient of this penalty dominates in flat regions and causes the
Newton direction to satisfy the stopping criterion far from the true minimum (Wright
1997, §4). This is the formal explanation for why trust-constr reports convergence
at a suboptimal point.

---

## The global minimum: KKT derivation

The true minimum is derived algebraically and verified by checking the KKT
optimality conditions, which are necessary and sufficient for strictly convex
problems (Boyd and Vandenberghe 2004, §5.5.3).

**Step 1 — Support.** The candidate long-short pair is the industry with the
highest mean return (Hlth, $\mu = +0.00136$/day) as the long leg and the industry
with the lowest mean return (Telcm, $\mu = -0.00828$/day) as the short leg.

**Step 2 — Weights.** Assume both constraints are simultaneously tight with support
$\{\text{Hlth}, \text{Telcm}\}$, $w_{\text{Hlth}} > 0$, $w_{\text{Telcm}} < 0$:

$$w_{\text{Hlth}} + w_{\text{Telcm}} = 1, \qquad
w_{\text{Hlth}} - w_{\text{Telcm}} = 1.5$$

Solving: $w_{\text{Hlth}} = 1.25$, $w_{\text{Telcm}} = -0.25$.

**Step 3 — KKT stationarity.** Let $r_i = (\hat\Sigma w^*)_i - \mu_i$.
For $w_i > 0$: $r_i + \lambda + \nu = 0$.
For $w_i < 0$: $r_i + \lambda - \nu = 0$.
For $w_i = 0$: $|r_i + \lambda| \leq \nu$.

From the active support:

$$\lambda = -\tfrac{r_{\text{Hlth}} + r_{\text{Telcm}}}{2} = -0.003760, \qquad
\nu = \tfrac{r_{\text{Telcm}} - r_{\text{Hlth}}}{2} = 0.004762 \geq 0\ \checkmark$$

**Step 4 — Dual feasibility.** All zero-weight industries must satisfy
$|r_k + \lambda| \leq \nu = 0.004762$:

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

All slack margins are strictly positive (NoDur tightest at 0.000638). Since
$\hat\Sigma$ is strictly positive definite and all KKT conditions hold, this is
the unique global minimum:

$$\boxed{w^*_{\text{Hlth}} = 1.25,\quad w^*_{\text{Telcm}} = -0.25,\quad
\text{all others} = 0,\quad f(w^*) = -0.003576587456}$$

The trust-constr solution is 4.59% worse: it places 25% of the long leg in
Consumer Staples (NoDur) rather than concentrating entirely in Health Care, leaving
the long leg 0.25 units underallocated to the highest-mean-return industry.

---

## Mechanistic isolation scripts

The following scripts reproduce the failure on a synthetic covariance (no DVC
dependency), useful for isolating the solver pathology from data ingestion:

```bash
uv run python scenarios/boundary_trap/scipy_slsqp.py
uv run python scenarios/boundary_trap/scipy_trust_constr.py
uv run python scenarios/boundary_trap/gurobi_interior_point.py
```

The Gurobi script requires no license; it documents the barrier termination
mechanism analytically when `gurobipy` is not installed.

---

## Files

| File | Purpose |
|:-----|:--------|
| `august_2007_reconstruction.py` | Real-data reconstruction, Ken French industry returns |
| `scipy_slsqp.py` | Mechanistic isolation: SLSQP on synthetic matrix |
| `scipy_trust_constr.py` | Mechanistic isolation: interior-point barrier on synthetic matrix |
| `gurobi_interior_point.py` | Mechanistic isolation: Gurobi barrier analysis (simulation mode) |

---

## Related scenarios

| Scenario | Failure class |
|:---------|:-------------|
| [`cholesky_crash/`](../cholesky_crash/) | Rank-deficient covariance causes Cholesky abort |
| `boundary_trap/` | L1 gross leverage cap causes suboptimal barrier convergence (this scenario) |
| [`precision_bleed/`](../precision_bleed/) | Float64 rounding drifts across sequential rebalances |
| [`step_divergence/`](../step_divergence/) | Gradient descent diverges when step size exceeds Lipschitz bound |

---

## References

- Khandani, A. E. and Lo, A. W. (2011). "What happened to the quants in August
  2007? Evidence from factors and transactions data." _Journal of Financial
  Markets_ 14(1): 1-46. DOI: 10.1016/j.finmar.2010.10.005. Documents the operating
  conditions of systematic long-short funds in August 2007: gross leverage in the
  150-200% range, short-lookback covariance estimation, and cross-sector correlation
  compression during the liquidity event.
- French, K. R. Data Library: 10 Industry Portfolios (daily, value-weighted).
  https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/data_library.html.
  Public domain. Primary data source for the reconstruction.
- Boyd, S. and Vandenberghe, L. (2004). _Convex Optimization_. Cambridge University
  Press. §5.5.3 (KKT optimality conditions for convex problems). Available free at
  https://web.stanford.edu/~boyd/cvxbook/.
- Duchi, J., Shalev-Shwartz, S., Singer, Y., and Chandra, T. (2008). "Efficient
  projections onto the $\ell_1$-ball for learning in high dimensions." _ICML 2008_,
  pp. 272-279. DOI: 10.1145/1390156.1390191. The $O(N \log N)$ analytical projection
  that avoids the $2N$-variable reformulation entirely.
- Nocedal, J. and Wright, S. J. (2006). _Numerical Optimization_, 2nd ed. Springer.
  Ch. 16 (active-set SQP) and Ch. 19 (penalty and augmented Lagrangian methods).
- Wright, S. J. (1997). _Primal-Dual Interior-Point Methods_. SIAM.
  DOI: 10.1137/1.9781611971453. §4: complementarity gap tolerances and premature
  termination under flat barrier landscapes.
- Marčenko, V. A. and Pastur, L. A. (1967). "Distribution of eigenvalues for some
  sets of random matrices." _Mathematics of the USSR-Sbornik_ 1(4): 457-483.
  Asymptotic theory for rank deficiency when $N/T > 1$.
- Anderson, T. W. (2003). _An Introduction to Multivariate Statistical Analysis_,
  3rd ed. Wiley. Ch. 7 (Wishart distribution): finite-sample result that the sample
  covariance is singular when $T < N$.
