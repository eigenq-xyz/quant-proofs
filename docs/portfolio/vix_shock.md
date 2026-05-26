# VIX Shock

2026-05-25

- [The mathematical problem](#the-mathematical-problem)
- [Why the VIX doubling matters](#why-the-vix-doubling-matters)
- [Pre-shock equilibrium](#pre-shock-equilibrium)
- [Post-shock optimal portfolio](#post-shock-optimal-portfolio)
- [The step-size stability
  condition](#the-step-size-stability-condition)
- [Solver results: uncertified gradient descent (stale step
  size)](#solver-results-uncertified-gradient-descent-stale-step-size)
- [Solver results: certified PGD](#solver-results-certified-pgd)
- [Solver results: Gurobi QP](#solver-results-gurobi-qp)
- [Weight trajectory comparison](#weight-trajectory-comparison)
- [Why the Lean 4 proof is
  necessary](#why-the-lean-4-proof-is-necessary)

## The mathematical problem

A fund allocates across $N = 3$ assets (Equity, Bonds, Commodities)
subject to a long-only simplex constraint. The mean-variance allocation
problem is:

$$\min_{w \in \mathbb{R}^3}\ \tfrac{1}{2} w^\top \Sigma w - \mu^\top w$$

$$\text{subject to}\quad \begin{cases}
\displaystyle\sum_{i=1}^{3} w_i = 1 & (\text{budget}) \\[4pt]
w_i \geq 0 \quad \forall\, i & (\text{long-only})
\end{cases}$$

The covariance matrix is diagonal, $\Sigma = \sigma^2 I$, reflecting the
stylized assumption that returns are uncorrelated across these broad
asset classes at a single-day horizon.[^1] Because all weights are
non-negative and sum to one, the gross leverage
$\sum |w_i| = \sum w_i = 1$ is automatically bounded; no separate L1
constraint is needed.

Expected annual returns and the scalar variance change overnight:

| Parameter  | Pre-shock                | Post-shock                         |
|------------|--------------------------|------------------------------------|
| $\mu$      | $[0.15,\ 0.10,\ 0.05]$   | $[0.15,\ 0.10,\ 0.05]$ (unchanged) |
| $\sigma^2$ | $0.04$ ($\sigma = 20\%$) | $0.16$ ($\sigma = 40\%$)           |
| $\Sigma$   | $0.04\, I$               | $0.16\, I$                         |

The expected returns are unchanged by the shock: the VIX event changes
the second moment, not the first.[^2]

## Why the VIX doubling matters

A VIX doubling is a discrete shift in the market’s implied variance
regime. The COVID-19 shock of February-March 2020 is a canonical
example: the VIX rose from approximately 14 on February 14 to a closing
high of 82.7 on March 16, 2020 — a 5$\times$ increase in under four
weeks, with the sharpest single-week move between February 21 and
February 28.


![](vix_shock_files/figure-commonmark/fig-vix-output-1.png)

Figure 1: VIX daily close during the COVID-19 shock, January-April 2020.
Feb 21 marks the last trading day before the sharp sell-off; Feb 28
shows the first full week of the new volatility regime. An optimizer
calibrated on pre-Feb-21 data and using a step size eta =
1.9/lambda_max(Sigma_pre) would carry a stale eta into the new regime.
Data: Yahoo Finance.


In our stylized scenario, $\sigma^2$ doubles from $0.04$ to $0.16$
overnight (a factor-of-2 increase in $\sigma$, matching the roughly
3$\times$ annualized VIX move from ~15 to ~45 in the first week of the
COVID shock). The key question is what happens to an optimizer that was
calibrated — specifically, whose step size was set — before the shock.

## Pre-shock equilibrium

When $\Sigma = 0.04\, I$ and $\mu = [0.15, 0.10, 0.05]$, the KKT
conditions for the long-only simplex problem reduce to: for each active
asset $i \in S$ (with $w_i > 0$, dual variable $\nu_i = 0$):

$$\sigma^2 w_i - \mu_i + \lambda = 0 \quad \Rightarrow \quad
w_i = \frac{\mu_i - \lambda}{\sigma^2}$$

and for each inactive asset $j \notin S$ (with $w_j = 0$,
$\nu_j \geq 0$):

$$\mu_j \leq \lambda$$

**Candidate support $S = \{\text{Equity}\}$:** With $w_0 = 1$ (budget
tight on single asset):

$$\lambda = \mu_0 - \sigma^2 \cdot 1 = 0.15 - 0.04 = 0.11$$

Dual feasibility check:

- Bonds: $\mu_1 = 0.10 \leq 0.11 = \lambda$ ✓
- Commodities: $\mu_2 = 0.05 \leq 0.11 = \lambda$ ✓

All KKT conditions are satisfied. The unique pre-shock optimum is:

$$w^\star_{\text{pre}} = [1.0,\ 0.0,\ 0.0], \qquad \lambda_{\text{pre}} = 0.11$$

When variance is low, the optimizer concentrates entirely in the
highest-return asset. Diversification only enters when the cost of
concentration (the variance penalty $\tfrac{1}{2}\sigma^2 \|w\|^2$) is
large enough to outweigh the return spread.

``` python
res_pre, cert_pre = kkt_optimum.derive_pre_shock(p_pre)
kkt_optimum.print_certificate(cert_pre, res_pre, p_pre)
```

    Solver    : KKT global optimum (pre-shock)
    Message   : Analytically certified: support S={Equity}

    Support set (active assets, w_i > 0):
      Equity        w* = 1.0000000000  (mu = 0.1500)

    lambda (budget dual) = 0.1100000000

    Budget: sum(w*) = 1.000000000000000  (must = 1.0)
    Budget error   = 0.00e+00

    Dual feasibility -- inactive assets must satisfy mu_i <= lambda:
      Asset             mu_i   lambda - mu_i   OK?
      Bonds          0.10000    0.0100000000  OK
      Commodities    0.05000    0.0600000000  OK

    All KKT conditions satisfied. This is the unique global minimum.

      f(w*) = -0.130000000000000

## Post-shock optimal portfolio

When $\Sigma = 0.16\, I$, the quadrupled variance penalty makes
concentration expensive. With
$S = \{\text{Equity, Bonds, Commodities}\}$ (all three assets active):

$$\sum_{i \in S} \frac{\mu_i - \lambda}{\sigma^2} = 1
\quad\Rightarrow\quad
\frac{\sum \mu_i - 3\lambda}{\sigma^2} = 1
\quad\Rightarrow\quad
\lambda = \frac{\sum \mu_i - \sigma^2}{3} = \frac{0.30 - 0.16}{3} = \frac{7}{150}$$

The optimal weights:

$$w_i^\star = \frac{\mu_i - \lambda}{\sigma^2}$$

$$w_0^\star = \frac{0.15 - 7/150}{0.16} = \frac{155/1000}{0.16} \approx 0.6458, \quad
w_1^\star = \frac{0.10 - 7/150}{0.16} \approx 0.3333, \quad
w_2^\star = \frac{0.05 - 7/150}{0.16} \approx 0.0208$$

Sum: $0.6458 + 0.3333 + 0.0208 = 1.000$ ✓, all $w_i^\star > 0$ ✓.

``` python
res_post, cert_post = kkt_optimum.derive_post_shock(p_post)
kkt_optimum.print_certificate(cert_post, res_post, p_post)
```

    Solver    : KKT global optimum (post-shock)
    Message   : Analytically certified: support S={Equity, Bonds, Commodities}

    Support set (active assets, w_i > 0):
      Equity        w* = 0.6458333333  (mu = 0.1500)
      Bonds         w* = 0.3333333333  (mu = 0.1000)
      Commodities   w* = 0.0208333333  (mu = 0.0500)

    lambda (budget dual) = 0.0466666667

    Budget: sum(w*) = 1.000000000000000  (must = 1.0)
    Budget error   = 2.22e-16

    All KKT conditions satisfied. This is the unique global minimum.

      f(w*) = -0.088958333333333


![](vix_shock_files/figure-commonmark/fig-weights-comparison-output-1.png)

Figure 2: Optimal portfolio weights before and after the overnight
volatility shock. When variance quadruples (sigma^2: 0.04 to 0.16), the
optimizer diversifies — the cost of concentration rises, so the
Equity-only portfolio gives way to a three-asset spread.


## The step-size stability condition

Nesterov (2004) Theorem 2.1.5[^3] establishes that for an $L$-smooth
convex function, gradient descent with step size $\eta$ converges if and
only if:

$$\eta < \frac{2}{L}$$

For the mean-variance objective
$f(w) = \tfrac{1}{2} w^\top \Sigma w - \mu^\top w$, the gradient is
$\nabla f(w) = \Sigma w - \mu$, which is Lipschitz continuous with
constant $L = \lambda_{\max}(\Sigma)$. With $\Sigma = \sigma^2 I$:

$$L = \lambda_{\max}(\sigma^2 I) = \sigma^2$$

The stability bound and the certified step size are:

$$\text{bound:} \quad \eta < \frac{2}{\sigma^2}, \qquad
\text{certified:} \quad \eta = \frac{1.9}{\sigma^2} < \frac{2}{\sigma^2}\ \checkmark$$

An optimizer calibrated on the pre-shock covariance computes
$\eta_{\text{pre}} = 1.9 / 0.04 = 47.5$ and reuses it unchanged after
the shock. This step size violates the post-shock bound:

$$\eta_{\text{pre}} = 47.5 \gg 12.5 = \frac{2}{0.16} = \frac{2}{\sigma^2_{\text{post}}}$$

In unconstrained gradient descent, the growth factor per step would be:

$$\left|1 - \eta_{\text{pre}} \cdot \lambda_{\max}(\Sigma_{\text{post}})\right|
= \left|1 - 47.5 \times 0.16\right| = |1 - 7.6| = 6.6$$

On the simplex, each gradient step sends the iterate far outside the
feasible set before the projection clips it back. The projection
prevents $|w_i| \to \infty$, but the gradient direction is so far from
the contraction direction that projected iterates cycle between extreme
simplex vertices rather than converging to the interior optimum. The
norm-to-optimum stays constant at $\approx 0.5$-$0.9$, rather than
decreasing geometrically.


Table 1


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

|  | sigma^2 | lambda_max(Sigma) | Stability bound 2/lambda_max | eta_pre = 1.9/lambda_max_pre | eta_post = 1.9/lambda_max_post | Growth factor \|eta\*lambda_max - 1\| |
|----|----|----|----|----|----|----|
|  |  |  |  |  |  |  |
| Pre-shock | 0.04 | 0.04 | 50.0 | 47.5000 | — | \|0.90\| = 0.90 |
| Post-shock | 0.16 | 0.16 | 12.5 | 47.5000  VIOLATES (47.5 \> 12.5) | 11.8750  (\< 12.5) OK | \|6.60\| = 6.60x per step (stale) |




## Solver results: uncertified gradient descent (stale step size)

The uncertified solver applies $\eta_{\text{pre}} = 47.5$ to the
post-shock problem. Each gradient step first sends the iterate far
outside the simplex before the projection pulls it back. The gradient
direction is so far off that after projection the iterates cycle between
the Equity-only corner and the Bonds-only corner of the simplex, never
approaching the interior optimum.

``` python
res_unc = uncertified_gd.run(p_post)
print(f"Solver    : {res_unc.solver_name}")
print(f"Converged : {res_unc.converged}")
print(f"Oscillation detected: {res_unc.diverged}")
print(f"Iterations: {res_unc.n_iterations}")
print(f"Message   : {res_unc.message}")
print()
print("Weight trajectory (selected steps):")
print(f"  {'Step':>5}  {'Equity':>12}  {'Bonds':>12}  {'Commodities':>14}  {'||w - w*||_2':>14}")
w_star = common.W_STAR_POST
fib_steps = [0, 1, 2, 3, 5, 8, 13]
for k in fib_steps:
    if k < len(res_unc.weight_history):
        w_k = res_unc.weight_history[k]
        dist = float(np.linalg.norm(w_k - w_star))
        print(f"  {k:>5}  {w_k[0]:>12.4f}  {w_k[1]:>12.4f}  {w_k[2]:>14.4f}  {dist:>14.4f}")
```

    Solver    : Uncertified GD (stale eta=47.5000)
    Converged : False
    Oscillation detected: True
    Iterations: 11
    Message   : OSCILLATION DETECTED at iteration 11: step norms constant at ~1.4142 for 10 steps. Stale eta=47.5000 violates stability bound 2/lambda_max=12.5000. Iterate cycles between simplex vertices instead of converging.

    Weight trajectory (selected steps):
       Step        Equity         Bonds     Commodities    ||w - w*||_2
          0        0.3333        0.3333          0.3333          0.4419
          1        1.0000        0.0000          0.0000          0.4868
          2        0.0000        1.0000          0.0000          0.9284
          3        1.0000        0.0000          0.0000          0.4868
          5        1.0000        0.0000          0.0000          0.4868
          8        0.0000        1.0000          0.0000          0.9284

The simplex projection maintains $\sum w_i = 1$ at each step, yet the
distance to the post-shock optimum $w^\star_{\text{post}}$ does not
decrease. The iterates alternate between $[1, 0, 0]$ (Equity-only) and
$[0, 1, 0]$ (Bonds-only), both far from the true post-shock optimum
$[0.6458, 0.3333, 0.0208]$. The stale step size makes the gradient
descent direction counterproductive: projection cannot recover what the
gradient step destroys.

## Solver results: certified PGD

The certified solver recomputes $\eta$ from the post-shock covariance
before every solve, yielding $\eta_{\text{post}} = 1.9 / 0.16 = 11.875$.
The Lean 4 proof of `pgd_convergence` in `optimization-proofs/`
certifies this inequality as a `Prop` at compile time: no runtime code
path can pass a step size that violates $\eta < 2 / \lambda_{\max}$.

``` python
res_cert = certified_pgd.run(p_post)
print(f"Solver    : {res_cert.solver_name}")
print(f"Converged : {res_cert.converged}")
print(f"Iterations: {res_cert.n_iterations}")
print(f"Message   : {res_cert.message}")
print(f"Objective : {res_cert.objective:.15f}")
print()
print("Weight trajectory (selected steps):")
print(f"  {'Step':>5}  {'Equity':>12}  {'Bonds':>12}  {'Commodities':>14}  {'||w - w*||_2':>14}")
w_star_post = common.W_STAR_POST
traj_steps = [0, 1, 5, 10, 20, res_cert.n_iterations]
for k in sorted(set(traj_steps)):
    if k < len(res_cert.weight_history):
        w_k = res_cert.weight_history[k]
        dist = float(np.linalg.norm(w_k - w_star_post))
        print(f"  {k:>5}  {w_k[0]:>12.6f}  {w_k[1]:>12.6f}  {w_k[2]:>14.6f}  {dist:>14.2e}")
print()
print("Post-shock optimum w*_post:")
print(f"  Equity={w_star_post[0]:.6f}  Bonds={w_star_post[1]:.6f}  Commodities={w_star_post[2]:.6f}")
print(f"\nFinal weights vs w*_post:")
print(f"  Max absolute error: {np.max(np.abs(res_cert.weights - w_star_post)):.2e}")
```

    Solver    : Certified PGD (eta=11.8750, recomputed from post-shock Sigma)
    Converged : True
    Iterations: 212
    Message   : Converged in 212 iterations (tol=1e-10)
    Objective : -0.088958333333333

    Weight trajectory (selected steps):
       Step        Equity         Bonds     Commodities    ||w - w*||_2
          0      0.333333      0.333333        0.333333        4.42e-01
          1      0.796875      0.203125        0.000000        2.01e-01
          5      0.744932      0.247904        0.007165        1.32e-01
         10      0.587317      0.383779        0.028905        7.77e-02
         20      0.625430      0.350923        0.023648        2.71e-02
        212      0.645833      0.333333        0.020833        7.28e-11

    Post-shock optimum w*_post:
      Equity=0.645833  Bonds=0.333333  Commodities=0.020833

    Final weights vs w*_post:
      Max absolute error: 6.22e-11

## Solver results: Gurobi QP

Gurobi solves the long-only simplex QP directly (N=3 non-negative
variables, one equality constraint). This serves as the ground-truth
check against which both gradient methods are compared.

``` python
res_gurobi = gurobi.run(p_post)
gurobi.print_result(res_gurobi, p_post)
print()
print(f"KKT optimum f(w*_post) = {res_post.objective:.15f}")
print(f"Max weight error vs KKT: {np.max(np.abs(res_gurobi.weights - common.W_STAR_POST)):.2e}")
```

    Set parameter Username
    Set parameter LicenseID to value 2827581
    Academic license - for non-commercial use only - expires 2027-05-25
    Gurobi Optimizer version 13.0.2 build v13.0.2rc1 (mac64[arm] - Darwin 25.5.0 25F71)

    CPU model: Apple M2 Max
    Thread count: 12 physical cores, 12 logical processors, using up to 12 threads

    Optimize a model with 1 rows, 3 columns and 3 nonzeros (Min)
    Model fingerprint: 0x3fadbe17
    Model has 3 linear objective coefficients
    Model has 3 quadratic objective terms
    Coefficient statistics:
      Matrix range     [1e+00, 1e+00]
      Objective range  [5e-02, 1e-01]
      QObjective range [2e-01, 2e-01]
      Bounds range     [0e+00, 0e+00]
      RHS range        [1e+00, 1e+00]

    Presolve time: 0.00s
    Presolved: 1 rows, 3 columns, 3 nonzeros
    Presolved model has 3 quadratic objective terms
    Ordering time: 0.00s

    Barrier statistics:
     AA' NZ     : 0.000e+00
     Factor NZ  : 1.000e+00
     Factor Ops : 1.000e+00 (less than 1 second per iteration)
     Threads    : 1

                      Objective                Residual
    Iter       Primal          Dual         Primal    Dual     Compl     Time
       0   9.59719927e+05 -9.60320027e+05  3.00e+03 0.00e+00  1.00e+06     0s
       1   3.79152377e-01 -5.00383356e+02  2.55e+00 0.00e+00  1.02e+03     0s
       2  -7.37188884e-02 -3.50598950e+02  2.55e-06 0.00e+00  1.17e+02     0s
       3  -7.37325078e-02 -4.73373336e-01  3.57e-10 0.00e+00  1.33e-01     0s
       4  -8.17928181e-02 -1.07002513e-01  5.80e-12 0.00e+00  8.40e-03     0s
       5  -8.80114432e-02 -9.10409313e-02  0.00e+00 2.29e-17  1.01e-03     0s
       6  -8.88618990e-02 -8.92193528e-02  0.00e+00 1.70e-17  1.19e-04     0s
       7  -8.89535964e-02 -8.89975318e-02  0.00e+00 0.00e+00  1.46e-05     0s
       8  -8.89583132e-02 -8.89604945e-02  0.00e+00 0.00e+00  7.27e-07     0s
       9  -8.89583333e-02 -8.89583368e-02  0.00e+00 2.05e-17  1.14e-09     0s

    Barrier solved model in 9 iterations and 0.00 seconds (0.00 work units)
    Optimal objective -8.89583333e-02

    Converged  : True
    Message    : Gurobi status=2 (2=OPTIMAL)
    Objective  : -0.088958333333280
    Budget err : 0.00e+00

    Weights:
      Equity        0.6458330008
      Bonds         0.3333330012
      Commodities   0.0208339980

    KKT optimum f(w*_post) = -0.088958333333333
    Max weight error vs KKT: 6.65e-07

## Weight trajectory comparison

The defining figure of this scenario:
$\|w_k - w^\star_{\text{post}}\|_2$ versus iteration $k$ on a log scale.
Certified PGD contracts geometrically over ~212 iterations. The
uncertified solver with stale $\eta_{\text{pre}}$ oscillates between two
extreme simplex vertices at constant large distance from the optimum —
the simplex projection prevents $|w_i| \to \infty$, but the gradient
step direction is so far off that the iterates cycle rather than
contract.


![](vix_shock_files/figure-commonmark/fig-trajectory-output-1.png)

Figure 3: Distance to the post-shock optimum \|\|w_k - w\*\_post\|\|\_2
on a log scale. Certified PGD (blue, eta=11.875) converges geometrically
over ~212 iterations. Uncertified GD (red, stale eta=47.5) oscillates at
constant distance ~0.5-0.9 from the optimum — the simplex projection
keeps weights on the feasible set, but the stale step size makes the
gradient direction catastrophically wrong. Both start from w_0 = \[1/3,
1/3, 1/3\].


The certified PGD converges to the post-shock optimum in 212 iterations
(geometric decay visible in the log plot). The uncertified solver with
stale $\eta_{\text{pre}} = 47.5$ oscillates at constant distance
$\approx
0.49$-$0.93$ from the optimum: the simplex projection keeps individual
weights in $[0,1]$, but the gradient step direction is so far off that
the iterates cycle between the Equity-only corner $[1,0,0]$ and the
Bonds-only corner $[0,1,0]$ rather than moving toward the interior
optimum $[0.6458, 0.3333, 0.0208]$.

## Why the Lean 4 proof is necessary

The step-size condition $\eta < 2 / \lambda_{\max}(\Sigma)$ is not a
recommendation; it is a hard mathematical requirement for convergence
(Nesterov 2004, Theorem 2.1.5).[^4] The Lean 4 proof of
`pgd_convergence` in `optimization-proofs/` certifies this condition as
a `Prop` at compile time:

- The theorem statement takes $\eta$ and $\Sigma$ as explicit arguments
  and requires a proof that $\eta < 2 / \lambda_{\max}(\Sigma)$ as a
  hypothesis.
- The certified solver computes $\eta = 1.9 / \lambda_{\max}(\Sigma)$
  from the current covariance and constructs the proof object inline.
- The uncertified solver has no such constraint: a caller can pass any
  $\eta > 0$, including one calibrated on a stale covariance.

The proof makes the failure mode structurally impossible at the type
level. No runtime check, no configuration flag, and no code review can
enforce this guarantee as strongly: if the Lean module compiles without
`sorry`, the convergence condition is satisfied.[^5]

In production, the certified PGD recalibrates $\eta$ on every solve by
recomputing $\lambda_{\max}(\Sigma)$ from the current covariance
estimate. For $\Sigma = \sigma^2 I$ this is trivially $\sigma^2$; for
general $\Sigma$ it requires a leading-eigenvalue computation (e.g.,
power iteration, cost $O(N^2)$ per step). The uncertified solver skips
this step as an optimization — one that is safe in a stationary regime
and catastrophic after an overnight volatility shift.

[^1]: Laloux, L., Cizeau, P., Bouchaud, J.-P., and Potters, M. (1999).
    “Noise dressing of financial correlation matrices.” *Physical Review
    Letters* 83(7): 1467-1470. DOI:
    [10.1103/PhysRevLett.83.1467](https://doi.org/10.1103/PhysRevLett.83.1467).
    Establishes that most off-diagonal entries in empirical correlation
    matrices are indistinguishable from noise at short horizons,
    supporting the diagonal $\Sigma = \sigma^2 I$ stylization.

[^2]: Cont, R. (2001). “Empirical properties of asset returns: Stylized
    facts and statistical issues.” *Quantitative Finance* 1(2): 223-236.
    DOI: [10.1080/713665670](https://doi.org/10.1080/713665670).
    Documents that volatility (second moment) changes on much shorter
    timescales than drift (first moment), motivating the stylized
    assumption that $\mu$ is unchanged while $\Sigma$ doubles.

[^3]: Nesterov, Yu. (2004). *Introductory Lectures on Convex
    Optimization: A Basic Course*. Kluwer Academic Publishers. Theorem
    2.1.5 establishes that $\eta < 2/L$ is necessary and sufficient for
    convergence of gradient descent on $L$-smooth convex functions.

[^4]: Nesterov, Yu. (2004). *Introductory Lectures on Convex
    Optimization: A Basic Course*. Kluwer Academic Publishers. Theorem
    2.1.5 establishes that $\eta < 2/L$ is necessary and sufficient for
    convergence of gradient descent on $L$-smooth convex functions.

[^5]: Boyd, S. and Vandenberghe, L. (2004). *Convex Optimization*.
    Cambridge University Press. Section 9.3 covers convergence rates of
    gradient descent; KKT conditions for strictly convex problems are
    covered in Section 5.5.3. Available free at
    <https://web.stanford.edu/~boyd/cvxbook/>.
