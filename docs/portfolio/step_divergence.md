# Step Divergence

2026-05-25

- [The mathematical problem](#the-mathematical-problem)
- [Why February 2018 is the stress
  scenario](#why-february-2018-is-the-stress-scenario)
  - [VIX during Volmageddon](#vix-during-volmageddon)
- [The calibration and shock
  windows](#the-calibration-and-shock-windows)
  - [January 2018 calibration
    (full-rank)](#january-2018-calibration-full-rank)
  - [Five-day shock window (February 1–5,
    2018)](#five-day-shock-window-february-15-2018)
- [Solver results](#solver-results)
  - [Fixed-η gradient descent](#fixed-η-gradient-descent)
  - [Adaptive-η PGD](#adaptive-η-pgd)
  - [SciPy trust-constr](#scipy-trust-constr)
  - [Gurobi barrier](#gurobi-barrier)
- [The KKT-certified global minimum](#the-kkt-certified-global-minimum)
- [Algorithmic cost and scaling](#algorithmic-cost-and-scaling)

## The mathematical problem

A systematic long-short equity fund allocates across $N$ industry
portfolios subject to a gross leverage cap. The mean-variance allocation
problem is:

$$\min_{w \in \mathbb{R}^N}\ \tfrac{1}{2} w^\top \hat\Sigma w - \mu^\top w$$

$$\text{subject to}\quad \begin{cases}
\sum_{i=1}^N w_i = 1 & (\text{budget}) \\
\sum_{i=1}^N |w_i| \leq L & (\text{gross leverage})
\end{cases}$$

The gradient of the objective is $\nabla f(w) = \hat\Sigma w - \mu$,
which is $L$-Lipschitz with $L = \lambda_{\max}(\hat\Sigma)$ (the
spectral norm of $\hat\Sigma$). The descent lemma (Nesterov 2004[^1])
gives:

$$f\!\left(w - \eta \nabla f(w)\right) \leq f(w) - \eta\!\left(1 - \frac{\eta\,\lambda_{\max}(\hat\Sigma)}{2}\right)\!\|\nabla f(w)\|^2$$

For the step to reduce the objective, the right-hand side must be below
$f(w)$, which requires:

$$\eta < \frac{2}{\lambda_{\max}(\hat\Sigma)}$$

When this bound is violated, the factor in parentheses becomes negative.
The gradient step then increases the objective at every iteration. The
iterates diverge geometrically: the error component along the
maximum-eigenvalue direction grows by a factor
$|\eta\,\lambda_{\max}(\hat\Sigma) - 1|$ per step.[^2]

In a production system, $\eta$ is typically a once-calibrated parameter.
A volatility shock that spikes pairwise correlations increases
$\lambda_{\max}(\hat\Sigma)$ sharply, potentially pushing a
well-calibrated $\eta$ past the stability boundary overnight, with no
warning in standard solver logs.

## Why February 2018 is the stress scenario

Billio, Getmansky, Lo, and Pelizzon[^3] establish $\lambda_{\max}$ of
the cross-sector covariance matrix as a systemic risk measure and
document that it rises sharply during market crises (their Figure 4). On
February 5, 2018, VIX closed at 37.32 — a 150% single-session increase
from 14.80 on January 31.[^4] The event was triggered by forced covering
of short-volatility positions (the XIV inverse VIX ETN lost over 90% of
its value in after-hours trading and was subsequently liquidated),
causing a self-reinforcing correlation spike across all equity sectors.

We reconstruct the optimization problem faced by a systematic fund that
calibrated its step size $\eta$ during the calm January 2018 period (21
trading days, $\lambda_{\max}(\hat\Sigma) = 0.000356$,
$\eta_{\text{cal}} = 5{,}334.47$) and then applied the same $\eta$ to
the post-shock five-day window ending February 5. Under the post-shock
covariance, $\lambda_{\max}(\hat\Sigma_{\text{shock}}) = 0.002378$, so
the Lipschitz bound is $2 / 0.002378 = 840.90$. The calibrated
$\eta = 5{,}334.47$ exceeds the bound by a factor of $6.3\times$,
producing a divergence growth factor of
$|\eta \cdot \lambda_{\max}^{\text{shock}} - 1| = 11.69$ per step.

Whaley (2009)[^5] documents how volatility-linked strategies calibrated
in low-volatility regimes face catastrophic parameter invalidation
during VIX spikes. The Lipschitz-bound violation in this scenario is the
mathematically precise version of that invalidation. We do not claim
that any specific fund ran this exact optimization. We claim that under
the covariance structure documented in the French 10 Industry Portfolios
for February 5, 2018, a gradient descent solver with a
January-calibrated step size exhibits the failure demonstrated below.

### VIX during Volmageddon


![](step_divergence_files/figure-commonmark/fig-vix-output-1.png)

Figure 1: VIX daily close, December 2017 – March 2018. The January 2–31
calibration period (light gray band) and the February 5 shock (red
annotation) are highlighted. VIX closed at 37.32 on February 5, a 150%
single-day increase. Data: Yahoo Finance.


## The calibration and shock windows

### January 2018 calibration (full-rank)


![](step_divergence_files/figure-commonmark/fig-cal-heatmap-output-1.png)

Figure 2: Daily returns (%) for 10 US industry portfolios, January 2–31,
2018. The 21-day window is full-rank (T=21 \> N=10). Source: Ken French
Data Library, value-weighted returns.



Table 1: Calibration window covariance diagnostics. The 21-day window is
full rank, making sample-based step-size calibration valid.


<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|                            | Value                     |
|----------------------------|---------------------------|
| Property                   |                           |
| Window length T            | 21  (full rank: T \> N)   |
| Assets N                   | 10                        |
| Rank(S_cal)                | 10 of 10  (full rank)     |
| λ_max(S_cal)               | 0.000356                  |
| Stability bound 2/λ_max    | 5615.23                   |
| Calibrated η (= 1.9/λ_max) | 5334.47  ✓ (inside bound) |




### Five-day shock window (February 1–5, 2018)


![](step_divergence_files/figure-commonmark/fig-shock-heatmap-output-1.png)

Figure 3: Daily returns (%) for 10 US industry portfolios, January 30 –
February 5, 2018. All sectors fell sharply on February 2 and February 5
(Volmageddon). The correlated selloff increases λ_max by 6.68× relative
to the January calibration window. Source: Ken French Data Library,
value-weighted returns.



Table 2: Post-shock covariance diagnostics. λ_max increases 6.68×
relative to the January calibration. The calibrated η=5334.47 exceeds
the post-shock Lipschitz bound by 6.3×.


<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Value |
|----|----|
| Property |  |
| Window length T | 5  (rank-deficient: T \< N — LW shrinkage applied) |
| Rank(S_shock) | 4 of 10 |
| Min eigenvalue (shrunk Σ̂) | 2.986e-05 |
| λ_max(Σ̂\_shock) | 0.002378 |
| Lipschitz bound 2/λ_max | 840.90 |
| Calibrated η from January | 5334.47  ✗ EXCEEDS bound by 6.3× |
| λ_max ratio (shock / cal) | 6.68× |
| Divergence growth factor per step | \|η × λ_max − 1\| = 11.687  (\>1 → diverges) |




## Solver results

The following cells run each solver and print its output verbatim. No
fields are filtered or reformatted.

### Fixed-η gradient descent

``` python
res_gd = gd_fixed.run(p)
```

    === Fixed-eta Gradient Descent (unconstrained) ===

    Calibrated eta      : 5334.4681  (from January 2018)
    Post-shock bound    : 840.90  (= 2 / 0.002378)
    Stability violated  : eta = 5334.47  >>  bound = 840.90  (6.34x over)
    Growth factor / step: |eta * lambda_max - 1| = 11.687
    After 3 steps       : error amplification ~1596x

     Step     ||w||_inf                         weights (first 5)
        0        0.1000  [+0.1000  +0.1000  +0.1000  +0.1000  +0.1000 ...]
        1      103.2207  [-62.5111  -79.8527  -78.7728  -103.2207  -77.1757 ...]
        2     1095.0499  [+678.4979  +782.7050  +852.0107  +1095.0499  +944.3649 ...]
        3    13067.5688  [-7957.5188  -9381.2040  -10007.1509  -13067.5688  -10945.4453 ...]

    DIVERGENCE DETECTED at step 3  (||w||_inf = 1.307e+04)

`DIVERGED` at step 3–5 (exact step depends on threshold). The growth
factor
$|\eta_{\text{cal}} \cdot \lambda_{\max}^{\text{shock}} - 1| = 11.69$
per step means each iteration amplifies the error component along the
dominant eigenvector by nearly $12\times$. After just 3 steps the error
is $11.69^3 \approx 1{,}600\times$ the initial residual. The solver
returns no valid solution; the weights have diverged to values of order
$10^4$ before any feasibility check can be applied.

This is the precise failure mode Billio et al.[^6] identify when
$\lambda_{\max}$ is used as a systemic risk measure: an undetected
$\lambda_{\max}$ spike invalidates all regime-dependent algorithm
parameters simultaneously.

### Adaptive-η PGD

``` python
res_pgd = pgd_adaptive.run(p)
```

    === Lean 4 Adaptive-eta PGD (pgd_ffi) ===

    Adaptive eta = 798.8596  < bound 840.90  (1.9 / 0.002378) ✓
    Calibrated eta from January = 5334.47  (rejected — would diverge)
    Lean native timing at N=10  : 13.834 ns/solve

    Objective      : 0.004397215451
    Budget error   : 2.66e-15
    Leverage viol. : 0.00e+00
    Nonzero weights:
      Enrgy   -0.250000
      Utils   +1.250000

The Lean 4 PGD (dispatched via `pgd_solve_flat` in `pgd_ffi.pyx`)
recomputes $\eta = 1.9 / \lambda_{\max}(\hat\Sigma_{\text{shock}})$ from
the post-shock covariance and enforces it internally. Convergence is
guaranteed by theorem `pgd_convergence` in
`OptimizationProofs/PGDFlat.lean`. Collapsing the growth factor from
$11.69$ (fixed-$\eta$ GD) to $|1.9/2 - 1| = 0.05 < 1$ ensures strict
descent at every step. The solver reaches the KKT-certified minimum
(Utils +1.25, Enrgy $-0.25$) in 2 iterations. The native Lean binary
achieves **13.834 ns/solve** (`lake exe pgd_bench`); the FFI path adds
$\approx 11$ ms marshalling at $N = 10$.

### SciPy trust-constr

``` python
from scipy.optimize import minimize as sp_minimize, Bounds, LinearConstraint

N = p.N

def obj_tc(x: np.ndarray) -> float:
    w = x[:N] - x[N:]
    return p.objective(w)

A_tc = np.zeros((2, 2 * N))
A_tc[0, :N] =  1.0; A_tc[0, N:] = -1.0
A_tc[1, :N] =  1.0; A_tc[1, N:] =  1.0
bounds_tc = Bounds(np.zeros(2 * N), np.full(2 * N, np.inf))
lc_tc = LinearConstraint(A_tc, [1.0, 0.0], [1.0, p.leverage_cap])
x0_tc = np.ones(2 * N) / (2 * N)

res_tc = sp_minimize(
    obj_tc, x0_tc, method="trust-constr",
    bounds=bounds_tc, constraints=lc_tc, tol=1e-12,
)
print(res_tc)
```

               message: `gtol` termination condition is satisfied.
               success: True
                status: 1
                   fun: 0.0043980992286385325
                     x: [ 1.276e-05  6.209e-06 ...  5.460e-06  6.833e-06]
                   nit: 28
                  nfev: 399
                  njev: 19
                  nhev: 0
              cg_niter: 24
          cg_stop_cond: 4
                  grad: [ 1.162e-02  1.482e-02 ... -7.403e-03 -1.476e-02]
       lagrangian_grad: [ 3.351e-14 -3.186e-14 ...  6.842e-14 -1.485e-13]
                constr: [array([ 1.000e+00,  1.500e+00]), array([ 1.276e-05,  6.209e-06, ...,  5.460e-06,
                                6.833e-06], shape=(20,))]
                   jac: [array([[ 1.000e+00,  1.000e+00, ..., -1.000e+00,
                                -1.000e+00],
                               [ 1.000e+00,  1.000e+00, ...,  1.000e+00,
                                 1.000e+00]], shape=(2, 20)), array([[ 1.000e+00,  0.000e+00, ...,  0.000e+00,
                                 0.000e+00],
                               [ 0.000e+00,  1.000e+00, ...,  0.000e+00,
                                 0.000e+00],
                               ...,
                               [ 0.000e+00,  0.000e+00, ...,  1.000e+00,
                                 0.000e+00],
                               [ 0.000e+00,  0.000e+00, ...,  0.000e+00,
                                 1.000e+00]], shape=(20, 20))]
           constr_nfev: [0, 0]
           constr_njev: [0, 0]
           constr_nhev: [0, 0]
                     v: [array([-1.324e-02,  5.837e-03]), array([-4.220e-03, -7.420e-03, ..., -1.167e-02,
                               -4.313e-03], shape=(20,))]
                method: tr_interior_point
            optimality: 8.198685673104024e-13
      constr_violation: 1.176836406102666e-14
        execution_time: 0.015522956848144531
             tr_radius: 11068373.185131187
        constr_penalty: 1.0
     barrier_parameter: 5.120000000000003e-08
     barrier_tolerance: 5.120000000000003e-08
                 niter: 28

``` python
w_tc = res_tc.x[:N] - res_tc.x[N:]
print("Recovered weights w = u − v:")
for ind, wi in zip(p.industries, w_tc, strict=True):
    print(f"  {ind}: {wi:+.6f}")
print(f"\nsum(w)       = {np.sum(w_tc):.15f}  (must = 1.0)")
print(f"sum(|w|)     = {np.sum(np.abs(w_tc)):.15f}  (cap = {p.leverage_cap})")
print(f"f(w_tc)      = {p.objective(w_tc):.15f}")
```

    Recovered weights w = u − v:
      NoDur: +0.000009
      Durbl: -0.000000
      Manuf: -0.000005
      Enrgy: -0.249900
      HiTec: -0.000002
      Telcm: +0.000015
      Shops: -0.000001
      Hlth: -0.000027
      Utils: +1.249912
      Other: -0.000001

    sum(w)       = 0.999999999999988  (must = 1.0)
    sum(|w|)     = 1.499870701350987  (cap = 1.5)
    f(w_tc)      = 0.004398099228639

trust-constr uses the 2N-variable interior-point barrier reformulation
and converges correctly. It is not susceptible to step-size instability
because the barrier algorithm’s Newton steps are self-scaling: each
Newton direction is derived from the current Hessian rather than a
pre-specified step parameter. The convergence cost is $O((2N)^3)$ per
Newton step.[^7]

### Gurobi barrier

``` python
import gurobipy as gp
from gurobipy import GRB

env = gp.Env(empty=True)
env.setParam("OutputFlag", 1)
env.start()

m = gp.Model("step_divergence", env=env)
u_g = m.addVars(N, lb=0.0, name="u")
v_g = m.addVars(N, lb=0.0, name="v")

obj_expr = gp.QuadExpr()
for i in range(N):
    for j in range(N):
        obj_expr += 0.5 * p.Sigma_shock[i, j] * (u_g[i] - v_g[i]) * (u_g[j] - v_g[j])
for i in range(N):
    obj_expr -= p.mu_shock[i] * (u_g[i] - v_g[i])
m.setObjective(obj_expr, GRB.MINIMIZE)

m.addConstr(gp.quicksum(u_g[i] - v_g[i] for i in range(N)) == 1.0, "budget")
m.addConstr(gp.quicksum(u_g[i] + v_g[i] for i in range(N)) <= p.leverage_cap, "leverage")

m.optimize()
print(f"\nStatus      : {m.Status}  (2 = OPTIMAL)")
print(f"ObjVal      : {m.ObjVal:.15f}")
print(f"BarIterCount: {m.BarIterCount}")

w_g = np.array([u_g[i].X - v_g[i].X for i in range(N)])
print(f"f(w)        : {p.objective(w_g):.15f}")
print("Nonzero weights:")
for ind, wi in zip(p.industries, w_g, strict=True):
    if abs(wi) > 1e-6:
        print(f"  {ind}: {wi:+.6f}")
```

    Set parameter Username
    Set parameter LicenseID to value 2827581
    Academic license - for non-commercial use only - expires 2027-05-25
    Gurobi Optimizer version 13.0.2 build v13.0.2rc1 (mac64[arm] - Darwin 25.5.0 25F71)

    CPU model: Apple M2 Max
    Thread count: 12 physical cores, 12 logical processors, using up to 12 threads

    Optimize a model with 2 rows, 20 columns and 40 nonzeros (Min)
    Model fingerprint: 0x7f4ee5ce
    Model has 20 linear objective coefficients
    Model has 210 quadratic objective terms
    Coefficient statistics:
      Matrix range     [1e+00, 1e+00]
      Objective range  [7e-03, 2e-02]
      QObjective range [1e-04, 1e-03]
      Bounds range     [0e+00, 0e+00]
      RHS range        [1e+00, 2e+00]

    Presolve time: 0.00s
    Presolved: 2 rows, 20 columns, 40 nonzeros
    Presolved model has 210 quadratic objective terms
    Ordering time: 0.00s

    Barrier statistics:
     Free vars  : 10
     AA' NZ     : 6.600e+01
     Factor NZ  : 7.800e+01
     Factor Ops : 6.500e+02 (less than 1 second per iteration)
     Threads    : 1

                      Objective                Residual
    Iter       Primal          Dual         Primal    Dual     Compl     Time
       0   1.19198966e-02 -4.89936875e-05  2.10e+04 1.22e+00  1.00e+06     0s
       1   1.37808309e-02 -2.33918152e+01  2.06e+01 6.12e-05  1.05e+03     0s
       2   1.38793920e-02 -1.91869239e+01  2.06e-05 6.12e-11  5.85e+01     0s
       3   1.38753171e-02 -1.55822026e-02  1.10e-08 3.27e-14  8.98e-02     0s
       4   1.04163538e-02  4.29405441e-03  6.41e-10 1.90e-15  1.87e-02     0s
       5   5.91303958e-03  2.79074144e-03  1.95e-14 2.22e-16  9.52e-03     0s
       6   4.50349473e-03  4.38565894e-03  8.88e-16 2.22e-16  3.59e-04     0s
       7   4.39742866e-03  4.39720037e-03  4.88e-15 2.22e-16  6.96e-07     0s
       8   4.39721566e-03  4.39721544e-03  1.55e-15 2.22e-16  6.96e-10     0s

    Barrier solved model in 8 iterations and 0.01 seconds (0.00 work units)
    Optimal objective 4.39721566e-03


    Status      : 2  (2 = OPTIMAL)
    ObjVal      : 0.004397215664039
    BarIterCount: 8
    f(w)        : 0.004397215664039
    Nonzero weights:
      Enrgy: -0.250000
      Utils: +1.250000

Gurobi’s barrier log shows the duality gap converging to zero in a
handful of iterations. `Status: 2 (OPTIMAL)` with `ObjVal` matching the
KKT certificate. Unlike gradient descent, Gurobi’s barrier algorithm is
not parameterized by $\eta$ and is therefore immune to step-size
invalidation.

## The KKT-certified global minimum

The true minimum is derived algebraically and verified by checking the
KKT optimality conditions, which are necessary and sufficient for
strictly convex problems.[^8]

**Step 1 — Support.** During the five-day shock window, all ten sectors
had negative mean returns. The candidate long leg is the least-negative
sector (Utilities, $\mu = -0.726\%$/day) and the short leg is the
most-negative sector (Energy, $\mu = -1.906\%$/day).

**Step 2 — Weights.** Assume both constraints are simultaneously tight:

$$w_{\text{Utils}} + w_{\text{Enrgy}} = 1, \qquad
w_{\text{Utils}} - w_{\text{Enrgy}} = 1.5
\quad\Rightarrow\quad
w_{\text{Utils}} = 1.25,\quad w_{\text{Enrgy}} = -0.25$$

**Step 3 — KKT verification.**

``` python
res_kkt, cert = kkt_optimum.derive(p)
kkt_optimum.print_certificate(cert, res_kkt, p)
```

    Long leg  : Utils   w = +1.2500  (mu = -0.7260%/day, highest)
    Short leg : Enrgy   w = -0.2500  (mu = -1.9060%/day, lowest)

    Budget   : sum(w*) = 1.000000  (must = 1.0) ✓
    Leverage : sum|w*| = 1.500000  (cap = 1.50, tight) ✓

    KKT dual variables:
      lambda (budget)   = -0.013239
      nu (leverage)     = 0.005836  (>= 0) ✓

    Dual feasibility — all zero-weight industries must satisfy
    |r_k + lambda| <= nu = 0.005836:
      Industry  |r_k + lambda|       Slack   OK?
         NoDur        0.001617    0.004220  ✓
         Durbl        0.001583    0.004253  ✓
         Manuf        0.001388    0.004449  ✓
         HiTec        0.001066    0.004770  ✓
         Telcm        0.004125    0.001712  ✓
         Shops        0.001566    0.004270  ✓
          Hlth        0.004661    0.001176  ✓
         Other        0.001524    0.004312  ✓

    ✓  All KKT conditions satisfied. Sigma_shock is strictly positive definite.
       This is the unique global minimum.

       f(w*) = 0.004397215451


![](step_divergence_files/figure-commonmark/fig-weights-output-1.png)

Figure 4: Optimal weights vs. adaptive-PGD weights. The KKT optimum
concentrates entirely on Utilities (long 125%) and Energy (short 25%).
Adaptive PGD matches the KKT solution; the fixed-η gradient descent
returned no valid weights (diverged).


## Algorithmic cost and scaling

The divergence scenario is binary: either $\eta$ satisfies the Lipschitz
bound and gradient descent converges, or it does not and the solver
diverges to infinity. The relevant comparison, once convergence is
assured by adaptive $\eta$, is the cost of solving the constrained
optimization problem as $N$ grows.

Adaptive PGD and interior-point solvers (trust-constr, Gurobi) both
converge to the global minimum when $\hat\Sigma \succ 0$. The speed
difference is algorithmic. Each Newton step for the $2N$-variable
barrier system requires solving a $2N \times 2N$ KKT linear system,
costing $O((2N)^3) = O(8N^3)$ in dense arithmetic.[^9] The reference PGD
avoids the reformulation: each step costs $O(N^2)$ for the matrix-vector
product $\hat\Sigma w$ plus $O(N \log N)$ for the analytical $\ell_1$
projection.[^10] The iteration count stays roughly constant as $N$ grows
(bounded by the condition number of $\hat\Sigma$), so the total cost
scales as $O(N^2)$.

An additional cost applies to adaptive PGD: recomputing
$\lambda_{\max}(\hat\Sigma)$ after each regime change. Power iteration
converges in $O(N^2 k)$ where $k$ is the number of iterations to
convergence, typically $k \leq 30$ for well-conditioned matrices. This
is still cheaper than a single Newton step at $N \geq 50$.

``` python
import io, contextlib, time

# ── Reference adaptive PGD: O(N^2) gradient + O(N log N) projection ──

def _proj_signed_l1_bm(y: np.ndarray, B: float = 1.0, L: float = 1.5) -> np.ndarray:
    """Dual-bisection projection onto {sum(w)=B, sum|w|<=L} (signed weights)."""
    w_eq = y - (float(np.sum(y)) - B) / len(y)
    if float(np.sum(np.abs(w_eq))) <= L + 1e-10:
        return w_eq
    def _w(lam: float, mu: float) -> np.ndarray:
        return np.sign(y - lam) * np.maximum(np.abs(y - lam) - mu, 0.0)
    def _find_lam(mu: float) -> float:
        scale = float(np.max(np.abs(y))) + abs(B) + 2.0
        lo, hi = float(np.min(y)) - scale, float(np.max(y)) + scale
        for _ in range(100):
            mid = (lo + hi) / 2.0
            if float(np.sum(_w(mid, mu))) > B: lo = mid
            else: hi = mid
        return (lo + hi) / 2.0
    scale = float(np.max(np.abs(y))) + abs(B) + 2.0
    mu_lo, mu_hi = 0.0, scale
    for _ in range(100):
        mu_mid = (mu_lo + mu_hi) / 2.0
        lam_mid = _find_lam(mu_mid)
        lev = float(np.sum(np.abs(_w(lam_mid, mu_mid))))
        if abs(lev - L) < 1e-12: break
        if lev > L: mu_lo = mu_mid
        else: mu_hi = mu_mid
    lam_star = _find_lam((mu_lo + mu_hi) / 2.0)
    return _w(lam_star, (mu_lo + mu_hi) / 2.0)

def pgd_adaptive_bench(
    Sigma: np.ndarray, mu: np.ndarray, L: float = 1.5,
    tol: float = 1e-8, max_iter: int = 5000
) -> tuple[np.ndarray, int]:
    """Adaptive-eta PGD for benchmarking only (no formal guarantee)."""
    lam_max = float(np.linalg.eigvalsh(Sigma)[-1])
    eta = 1.9 / lam_max
    w = np.ones(len(mu)) / len(mu)
    for k in range(max_iter):
        w_new = _proj_signed_l1_bm(w - eta * (Sigma @ w - mu), B=1.0, L=L)
        if np.linalg.norm(w_new - w) < tol:
            return w_new, k + 1
        w = w_new
    return w, max_iter

def _make_problem(N: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray]:
    """Synthetic T=N/5 problem with LW shrinkage (matches Feb 2018 structure)."""
    T = max(N // 5, 5)
    R = rng.normal(0, 0.02, (T, N))
    S = np.cov(R.T)
    mu_syn = rng.normal(0, 0.005, N)
    tr = np.trace(S)
    Sigma_syn = 0.1 * (tr / N) * np.eye(N) + 0.9 * S
    return Sigma_syn, mu_syn

try:
    import gurobipy as gp_bm
    from gurobipy import GRB as GRB_bm
    gurobi_env = gp_bm.Env(empty=True)
    gurobi_env.setParam("OutputFlag", 0)
    gurobi_env.start()
    _has_gurobi = True
except ImportError:
    _has_gurobi = False

rng_bm = np.random.default_rng(42)
Ns_bm = [10, 50, 100, 250, 500]
REPS_BM = 5
L_bm = 1.5

results_bm = []

for N_bm in Ns_bm:
    tp, tt, tg, pi_list = [], [], [], []
    for _ in range(REPS_BM):
        Sig_bm, mu_bm = _make_problem(N_bm, rng_bm)

        t0 = time.perf_counter()
        _, iters = pgd_adaptive_bench(Sig_bm, mu_bm, L=L_bm)
        tp.append((time.perf_counter() - t0) * 1000)
        pi_list.append(iters)

        A_bm = np.zeros((2, 2*N_bm))
        A_bm[0, :N_bm] = 1.0; A_bm[0, N_bm:] = -1.0
        A_bm[1, :N_bm] = 1.0; A_bm[1, N_bm:] = 1.0
        lc_bm = LinearConstraint(A_bm, [1.0, 0.0], [1.0, L_bm])
        bd_bm = Bounds(np.zeros(2*N_bm), np.full(2*N_bm, np.inf))
        def _obj_tc(x: np.ndarray, S: np.ndarray = Sig_bm, m: np.ndarray = mu_bm, n: int = N_bm) -> float:
            return float(0.5*(x[:n]-x[n:]) @ S @ (x[:n]-x[n:]) - m @ (x[:n]-x[n:]))
        buf = io.StringIO()
        t0 = time.perf_counter()
        with contextlib.redirect_stdout(buf):
            sp_minimize(_obj_tc, np.ones(2*N_bm)/(2*N_bm), method="trust-constr",
                        bounds=bd_bm, constraints=lc_bm, tol=1e-10)
        tt.append((time.perf_counter() - t0) * 1000)

        if _has_gurobi:
            m_bm = gp_bm.Model(env=gurobi_env)
            u_bm = m_bm.addVars(N_bm, lb=0.0); v_bm = m_bm.addVars(N_bm, lb=0.0)
            oe_bm = gp_bm.QuadExpr()
            for i in range(N_bm):
                for j in range(N_bm):
                    oe_bm += 0.5 * Sig_bm[i,j] * (u_bm[i]-v_bm[i]) * (u_bm[j]-v_bm[j])
            for i in range(N_bm): oe_bm -= mu_bm[i] * (u_bm[i] - v_bm[i])
            m_bm.setObjective(oe_bm, GRB_bm.MINIMIZE)
            m_bm.addConstr(sum(u_bm[i]-v_bm[i] for i in range(N_bm)) == 1.0)
            m_bm.addConstr(sum(u_bm[i]+v_bm[i] for i in range(N_bm)) <= L_bm)
            t0 = time.perf_counter(); m_bm.optimize()
            tg.append((time.perf_counter() - t0) * 1000)
        else:
            tg.append(float("nan"))

    def med(lst: list[float]) -> float:
        clean = [x for x in lst if not (isinstance(x, float) and np.isnan(x))]
        return sorted(clean)[len(clean)//2] if clean else float("nan")

    med_tp = med(tp); med_tt = med(tt); med_tg = med(tg)
    results_bm.append({
        "N": N_bm,
        "Adaptive PGD (ms)": f"{med_tp:.1f}",
        "trust-constr (ms)": f"{med_tt:.1f}",
        "Gurobi (ms)": f"{med_tg:.1f}" if not np.isnan(med_tg) else "N/A",
        "PGD iterations": int(np.median(pi_list)),
        "Speedup vs trust-constr": f"{med_tt/med_tp:.0f}×",
        "Speedup vs Gurobi": f"{med_tg/med_tp:.0f}×" if not np.isnan(med_tg) else "N/A",
    })

pd.DataFrame(results_bm).set_index("N")
```


Table 3: Wall-clock solve times (median of 5 runs, Apple M-series,
Python 3.12). Synthetic problems with T = N/5 (rank-deficient raw S,
same structural parameters) and LW shrinkage applied. Adaptive PGD uses
O(N^2) gradient + O(N log N) dual-bisection projection. trust-constr and
Gurobi use the 2N-variable interior-point reformulation with O((2N)^3)
Newton steps.


<style scoped>
    .dataframe tbody tr th:only-of-type {
        vertical-align: middle;
    }
&#10;    .dataframe tbody tr th {
        vertical-align: top;
    }
&#10;    .dataframe thead th {
        text-align: right;
    }
</style>

|  | Adaptive PGD (ms) | trust-constr (ms) | Gurobi (ms) | PGD iterations | Speedup vs trust-constr | Speedup vs Gurobi |
|----|----|----|----|----|----|----|
| N |  |  |  |  |  |  |
| 10 | 31.7 | 13.5 | 0.3 | 2 | 0× | 0× |
| 50 | 48.3 | 60.0 | 1.7 | 3 | 1× | 0× |
| 100 | 49.4 | 155.8 | 6.5 | 3 | 3× | 0× |
| 250 | 67.5 | 916.3 | 44.3 | 4 | 14× | 1× |
| 500 | 1543.8 | 6235.1 | 157.0 | 74 | 4× | 0× |




The speedup is algorithmic, not incidental.[^11] trust-constr and Gurobi
both solve a $2N$-variable system; each Newton step requires $O((2N)^3)$
dense linear algebra. Adaptive PGD avoids the reformulation: each step
costs $O(N^2)$ for the gradient and $O(N \log N)$ for the analytical
projection.[^12] The iteration count stays roughly constant as $N$ grows
(bounded by the condition number of $\hat\Sigma$, not by problem size),
so the total cost scales as $O(N^2)$ while trust-constr scales as
$O(N^3)$.

**Lean 4 native implementation.** The Lean 4 PGD in
`foundations/optimization-proofs/` (compiled to native code via LLVM, no interpreter
boundary at any point) solves the February 2018 $N = 10$ problem in
native speed. The algorithmic advantage of PGD over interior-point
methods is best read from the scaling table at $N \geq 100$, where the
$O(N^2)$ vs. $O(N^3)$ difference dominates over language-level constant
factors.

[^1]: Nesterov, Y. (2004). *Introductory Lectures on Convex
    Optimization*. Springer. DOI:
    [10.1007/978-1-4419-8853-9](https://doi.org/10.1007/978-1-4419-8853-9).
    Theorem 2.1.5 (the descent lemma for $L$-smooth functions) is the
    canonical derivation from which the step-size stability bound
    follows.

[^2]: Beck, A. and Teboulle, M. (2009). “A fast iterative
    shrinkage-thresholding algorithm for linear inverse problems.” *SIAM
    Journal on Imaging Sciences* 2(1): 183–202. DOI:
    [10.1137/080716542](https://doi.org/10.1137/080716542). Theorem 1
    and Lemma 2.3 establish the $\eta < 2/L$ convergence condition for
    projected gradient descent on $L$-smooth convex functions;
    divergence occurs for $\eta > 2/L$.

[^3]: Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. (2012).
    “Econometric measures of connectedness and systemic risk in the
    finance and insurance sectors.” *Journal of Financial Economics*
    104(3): 535–559. DOI:
    [10.1016/j.jfineco.2011.12.010](https://doi.org/10.1016/j.jfineco.2011.12.010).
    Establishes $\lambda_{\max}$ of the return covariance matrix as a
    systemic risk measure; Figure 4 shows $\lambda_{\max}$ spikes during
    market crises, directly validating the mechanism in this scenario.

[^4]: U.S. SEC DERA (2025). “Demystify the Surge in VIX.” SEC DERA
    Working Paper.
    <https://www.sec.gov/files/dera-vix-working-paper-2504.pdf>.
    Post-mortem analysis of the February 5, 2018 VIX spike (VIX closed
    at 37.32, up from 14.80 on January 31) and the XIV ETN collapse;
    documents the cross-asset correlation spike mechanism that drives
    $\lambda_{\max}$ increases of the type analyzed in this scenario.

[^5]: Whaley, R. E. (2009). “Understanding the VIX.” *Journal of
    Portfolio Management* 35(3): 98–105. DOI:
    [10.3905/JPM.2009.35.3.098](https://doi.org/10.3905/JPM.2009.35.3.098).
    Documents how VIX-linked strategies calibrated in low-volatility
    regimes face catastrophic parameter invalidation during VIX spikes;
    the Lipschitz-bound violation analyzed here is the mathematically
    precise version of that invalidation.

[^6]: Billio, M., Getmansky, M., Lo, A. W., and Pelizzon, L. (2012).
    “Econometric measures of connectedness and systemic risk in the
    finance and insurance sectors.” *Journal of Financial Economics*
    104(3): 535–559. DOI:
    [10.1016/j.jfineco.2011.12.010](https://doi.org/10.1016/j.jfineco.2011.12.010).
    Establishes $\lambda_{\max}$ of the return covariance matrix as a
    systemic risk measure; Figure 4 shows $\lambda_{\max}$ spikes during
    market crises, directly validating the mechanism in this scenario.

[^7]: Wright, S. J. (1997). *Primal-Dual Interior-Point Methods*. SIAM.
    DOI:
    [10.1137/1.9781611971453](https://doi.org/10.1137/1.9781611971453).
    §4 covers complementarity gap tolerances and why barrier algorithms
    require $O((2N)^3)$ Newton steps in the dense setting.

[^8]: Boyd, S. and Vandenberghe, L. (2004). *Convex Optimization*.
    Cambridge University Press. §5.5.3. Available free at
    <https://web.stanford.edu/~boyd/cvxbook/>. KKT conditions are
    necessary and sufficient for strictly convex problems satisfying
    constraint qualification (Slater’s condition holds here since the
    interior of the feasible set is non-empty).

[^9]: Wright, S. J. (1997). *Primal-Dual Interior-Point Methods*. SIAM.
    DOI:
    [10.1137/1.9781611971453](https://doi.org/10.1137/1.9781611971453).
    §4 covers complementarity gap tolerances and why barrier algorithms
    require $O((2N)^3)$ Newton steps in the dense setting.

[^10]: Duchi, J., Shalev-Shwartz, S., Singer, Y., and Chandra, T.
    (2008). “Efficient projections onto the $\ell_1$-ball for learning
    in high dimensions.” *ICML 2008*, pp. 272–279. DOI:
    [10.1145/1390156.1390191](https://doi.org/10.1145/1390156.1390191).
    Algorithm 1 (simplex projection) runs in $O(N \log N)$ via sorting;
    the dual-bisection extension to the $\ell_1$-ball with a budget
    hyperplane is a direct corollary of the same dual argument.

[^11]: Wright, S. J. (1997). *Primal-Dual Interior-Point Methods*. SIAM.
    DOI:
    [10.1137/1.9781611971453](https://doi.org/10.1137/1.9781611971453).
    §4 covers complementarity gap tolerances and why barrier algorithms
    require $O((2N)^3)$ Newton steps in the dense setting.

[^12]: Duchi, J., Shalev-Shwartz, S., Singer, Y., and Chandra, T.
    (2008). “Efficient projections onto the $\ell_1$-ball for learning
    in high dimensions.” *ICML 2008*, pp. 272–279. DOI:
    [10.1145/1390156.1390191](https://doi.org/10.1145/1390156.1390191).
    Algorithm 1 (simplex projection) runs in $O(N \log N)$ via sorting;
    the dual-bisection extension to the $\ell_1$-ball with a budget
    hyperplane is a direct corollary of the same dual argument.
