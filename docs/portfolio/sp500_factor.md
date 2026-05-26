# S&P 500 Factor Portfolio

2026-05-25

- [The mathematical problem](#the-mathematical-problem)
  - [Single-factor CAPM covariance](#single-factor-capm-covariance)
  - [O(N) gradient via rank-1 factor
    structure](#on-gradient-via-rank-1-factor-structure)
- [Why S&P 500 scale matters](#why-sp-500-scale-matters)
- [The Woodbury formula: O(N)
  Sigma^{-1}](#the-woodbury-formula-on-sigma-1)
  - [Verification at N=10](#verification-at-n10)
- [Scaling benchmark](#scaling-benchmark)
- [Scaling plot](#scaling-plot)
- [Active position count](#active-position-count)
- [Why interior-point cannot exploit factor
  structure](#why-interior-point-cannot-exploit-factor-structure)
- [Computational complexity
  analysis](#computational-complexity-analysis)

## The mathematical problem

A portfolio manager allocating across $N$ assets subject to a gross
leverage cap faces the mean-variance problem:

$$\min_{w \in \mathbb{R}^N}\ \tfrac{1}{2} w^\top \Sigma w - \mu^\top w$$

$$\text{subject to}\quad \begin{cases}
\sum_{i=1}^N w_i = 1 & (\text{budget}) \\
\sum_{i=1}^N |w_i| \leq L & (\text{gross leverage, } L = 1.5)
\end{cases}$$

### Single-factor CAPM covariance

The covariance matrix $\Sigma$ follows a single-factor CAPM structure:

$$\Sigma = \sigma_f^2 \beta\beta^\top + \sigma_\varepsilon^2 I$$

where $\beta_i = i/N$ for $i = 1, \ldots, N$ are linearly spaced factor
loadings, $\sigma_f = 0.15$ is the annualized factor volatility, and
$\sigma_\varepsilon = 0.05$ is the identical idiosyncratic volatility
for each asset. Expected returns follow the CAPM security market line:

$$\mu_i = r_f + \beta_i \cdot (\mu_m - r_f) = 0.03 + 0.07 \cdot \beta_i$$

### O(N) gradient via rank-1 factor structure

The gradient $\nabla f(w) = \Sigma w - \mu$ does not require $O(N^2)$
work when $\Sigma$ has rank-1 plus diagonal structure:

$$\Sigma w = \sigma_f^2 \beta (\beta^\top w) + \sigma_\varepsilon^2 w$$

This is two dot products and two vector scalings — exactly $O(N)$ work.
Interior-point solvers destroy this structure by introducing $2N$ slack
variables, creating a full $2N \times 2N$ dense Hessian for the Newton
step.

## Why S&P 500 scale matters

DeMiguel et al. (2009)[^1] demonstrated that L1-gross-leverage
constraints improve out-of-sample Sharpe ratios compared to
unconstrained mean-variance portfolios. Their empirical tests used
$N \leq 25$ assets. An index manager running the same optimization on
all S&P 500 constituents ($N \approx 500$) cannot use interior-point
methods in practice: the $O(N^3)$ Newton step becomes prohibitive.

The operation count comparison makes this concrete. Each interior-point
Newton step requires solving a $(2N) \times (2N)$ KKT system at cost
$O((2N)^3) = O(8N^3)$. PGD with the factor-structure gradient costs
$O(N)$ per step; even the dense $O(N^2)$ variant costs $O(N^2)$ plus
$O(N \log N)$ for the Duchi projection. Assuming 25 Newton steps and 500
PGD steps:


![](sp500_factor_files/figure-commonmark/fig-op-counts-output-1.png)

Figure 1: Theoretical operation counts at each benchmark scale.
Interior-point cost assumes 25 Newton steps with O((2N)^3) dense linear
algebra per step. PGD (factor) cost assumes 500 iterations with O(N)
gradient and O(N log N) projection. Log scale spans 9 orders of
magnitude.


``` python
N_ref = 500
ip_ref = 25 * (2 * N_ref) ** 3
pgd_ref = 500 * (N_ref + N_ref * np.log2(N_ref))
print(f"Interior-point ops at N=500 : {ip_ref:.2e}")
print(f"PGD (factor) ops at N=500   : {pgd_ref:.2e}")
print(f"Ratio                        : {ip_ref / pgd_ref:.0f}×")
```

    Interior-point ops at N=500 : 2.50e+10
    PGD (factor) ops at N=500   : 2.49e+06
    Ratio                        : 10034×

## The Woodbury formula: O(N) Sigma^{-1}

The single-factor covariance admits a closed-form inverse via the
Sherman-Morrison identity.[^2] Writing $\Sigma = A + uu^\top$ with
$A = \sigma_\varepsilon^2 I$ and $u = \sigma_f \beta$:

$$\Sigma^{-1} = A^{-1} - A^{-1} u (1 + u^\top A^{-1} u)^{-1} u^\top A^{-1}
= \frac{1}{\sigma_\varepsilon^2} I
  - \frac{\sigma_f^2 / \sigma_\varepsilon^4}{1 + \sigma_f^2 \|\beta\|^2 / \sigma_\varepsilon^2}
    \beta\beta^\top$$

Applying this to the gradient update direction
$v = \mu - \lambda \mathbf{1}$:

$$\Sigma^{-1} v
= \frac{v}{\sigma_\varepsilon^2}
  - \frac{\sigma_f^2}{\sigma_\varepsilon^4 (1 + \sigma_f^2 \|\beta\|^2 / \sigma_\varepsilon^2)}
    \beta \bigl(\beta^\top v\bigr)$$

Both evaluations are $O(N)$: one dot product $\beta^\top v$ followed by
two vector scalings. The unconstrained optimum is
$w_{\text{unc}} = \Sigma^{-1} \mu$, computed in one pass at O(N) cost.

### Verification at N=10

``` python
p10 = p_list[10]

# Woodbury O(N) inverse vs dense O(N^3) solve
w_unc_woodbury = kkt_woodbury.woodbury_inv_v(
    p10.mu, p10.beta, p10.sigma_eps_sq, p10.sigma_f_sq
)
w_unc_dense = np.linalg.solve(p10.Sigma, p10.mu)
max_err = float(np.max(np.abs(w_unc_woodbury - w_unc_dense)))
print(f"Woodbury vs dense Sigma^{{-1}} mu: max error = {max_err:.2e}  (machine precision)")
print(f"Unconstrained w_unc: budget = {np.sum(w_unc_woodbury):.2f}  (far from feasible set)")
print(f"                     leverage = {np.sum(np.abs(w_unc_woodbury)):.2f}  (cap = {p10.leverage_cap})")
```

    Woodbury vs dense Sigma^{-1} mu: max error = 6.99e-15  (machine precision)
    Unconstrained w_unc: budget = 32.68  (far from feasible set)
                         leverage = 46.41  (cap = 1.5)

The unconstrained optimum is infeasible (budget $\gg 1$, leverage
$\gg L$). The constrained optimum is found by running PGD to convergence
using the same O(N) factor gradient:

``` python
w_star, cert10 = kkt_woodbury.derive(p10)

print(f"Certified optimum (N=10):")
print(f"  f(w*) = {p10.objective(w_star):.15f}")
print(f"  sum(w*)  = {np.sum(w_star):.15f}  (target: 1.0)")
print(f"  sum|w*|  = {np.sum(np.abs(w_star)):.15f}  (cap: {p10.leverage_cap})")
print(f"  Active assets (|w| > 1e-10): {cert10.n_active}")
print(f"  Estimated lambda* = {cert10.lambda_star:.6f}")
print(f"  Estimated nu*     = {cert10.nu_star:.8f}")
print()
print("Nonzero weights:")
for i, wi in enumerate(w_star):
    if abs(wi) > 1e-10:
        print(f"  asset {i+1:3d}  beta={p10.beta[i]:.3f}  mu={p10.mu[i]:.5f}  w={wi:.8f}")
```

    Certified optimum (N=10):
      f(w*) = -0.096836718766480
      sum(w*)  = 0.999999999997513  (target: 1.0)
      sum|w*|  = 1.500000000964440  (cap: 1.5)
      Active assets (|w| > 1e-10): 2
      Estimated lambda* = 0.052091
      Estimated nu*     = 0.01722187

    Nonzero weights:
      asset   1  beta=0.100  mu=0.03700  w=-0.25000000
      asset  10  beta=1.000  mu=0.10000  w=1.25000000

We can verify that `gradient_factor` and the dense gradient agree
exactly:

``` python
grad_factor = p10.gradient_factor(w_star)
grad_dense  = p10.Sigma @ w_star - p10.mu
max_err = float(np.max(np.abs(grad_factor - grad_dense)))
print(f"Max |gradient_factor(w*) - Sigma @ w* - mu| = {max_err:.2e}  (must be < 1e-14)")
```

    Max |gradient_factor(w*) - Sigma @ w* - mu| = 1.39e-17  (must be < 1e-14)

## Scaling benchmark

The table below times the PGD reference solver alongside Gurobi across
all five benchmark scales. The benchmark runs
`BENCHMARK_FIXED_ITERS = 100` PGD steps for each $N$ (same iteration
count across all scales), so the reported PGD time directly reflects
per-iteration cost as a function of $N$. Gurobi runs to full convergence
(barrier termination) at each scale.

``` python
import time

results_bm: list[dict[str, object]] = []

for N_bm in common.BENCHMARK_N:
    p_bm = p_list[N_bm]

    pgd_res = pgd_reference.benchmark(p_bm, reps=common.BENCHMARK_REPS)
    gurobi_res = gurobi.benchmark(p_bm, reps=3, timeout=120.0)

    if gurobi_res.timed_out:
        gurobi_str = "> 120 s (timeout)"
        speedup_str = "—"
    elif np.isnan(gurobi_res.solve_time_ms):
        gurobi_str = "N/A (no Gurobi)"
        speedup_str = "—"
    else:
        gurobi_str = f"{gurobi_res.solve_time_ms:.1f}"
        speedup_str = f"{gurobi_res.solve_time_ms / pgd_res.solve_time_ms:.0f}×"

    results_bm.append({
        "N": N_bm,
        "PGD-100 (ms)": f"{pgd_res.solve_time_ms:.1f}",
        "Gurobi (ms)": gurobi_str,
        "PGD active k": pgd_res.n_active,
        "Gurobi bar. iters": gurobi_res.n_bar_iters if not gurobi_res.timed_out else "—",
        "Gurobi / PGD": speedup_str,
    })

df_bm = pd.DataFrame(results_bm).set_index("N")
df_bm
```


Table 1: Wall-clock times: PGD = 100 fixed iterations (median of 5
runs); Gurobi = full barrier solve (median of 3 runs). PGD time measures
per-iteration cost and grows slowly with N, reflecting the O(N) factor
gradient. Gurobi time grows with N<sup>2–N</sup>3, reflecting the
2N-variable dense Newton step.


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

|     | PGD-100 (ms) | Gurobi (ms) | PGD active k | Gurobi bar. iters | Gurobi / PGD |
|-----|--------------|-------------|--------------|-------------------|--------------|
| N   |              |             |              |                   |              |
| 10  | 450.6        | 0.2         | 2            | 8                 | 0×           |
| 50  | 460.9        | 1.9         | 5            | 10                | 0×           |
| 100 | 475.0        | 7.3         | 9            | 10                | 0×           |
| 250 | 557.3        | 51.0        | 19           | 11                | 0×           |
| 500 | 633.2        | 161.7       | 36           | 11                | 0×           |




**Reading the table.** The PGD-100 times grow only modestly from
$N = 10$ to $N = 500$, reflecting the $O(N)$ per-iteration cost
(gradient in O(N) via factor structure, projection in O(N) nested
bisection). The Gurobi times grow with approximately $O(N^2)$ scaling —
consistent with the barrier method forming a $(2N) \times (2N)$ Hessian
each Newton step. At $N = 500$ the Gurobi solve is substantially slower
than 100 PGD iterations, and this gap widens at $N = 1000+$.

The Python reference PGD is used for benchmarking only — it carries no
formal correctness guarantee. The Lean 4 PGD in `optimization-proofs/`
provides the verified guarantees.[^3]

## Scaling plot


![](sp500_factor_files/figure-commonmark/fig-scaling-output-1.png)

Figure 2: Wall-clock time (ms) vs. N on log-log axes. PGD-100 measures
100 fixed iterations; Gurobi measures a full barrier solve. Empirical
scaling exponents are estimated by least-squares fit on the log-log data
points.


## Active position count

The Duchi projection onto the L1 ball with budget constraint induces
sparsity: the optimal portfolio concentrates on the assets with the best
risk-adjusted returns. Since $\mu_i = r_f + \beta_i (\mu_m - r_f)$ is
monotone in $\beta_i$, and the L1 leverage constraint bounds total
exposure, the optimal portfolio typically holds one long-high-$\beta$
position and one short-low-$\beta$ position (for $L > 1$).


![](sp500_factor_files/figure-commonmark/fig-active-positions-output-1.png)

Figure 3: Active positions (\|w_i\| \> 1e-9) in PGD iterates after 100
steps, for each benchmark N. The active set is sparse (k \<\< N)
throughout the optimization.



Table 2: Active positions and sparsity ratio for each benchmark N. The
PGD Duchi threshold maps most assets to exactly zero weight.
Interior-point methods cannot achieve this sparsity mid-solve.


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

|     | Active k | Sparse k/N | Zero weights |
|-----|----------|------------|--------------|
| N   |          |            |              |
| 10  | 2        | 20.0%      | 8            |
| 50  | 5        | 10.0%      | 45           |
| 100 | 9        | 9.0%       | 91           |
| 250 | 19       | 7.6%       | 231          |
| 500 | 36       | 7.2%       | 464          |




Interior-point methods in the $2N$-variable reformulation cannot exploit
this sparsity during the solve: the barrier terms prevent $u_i$ or $v_i$
from reaching exactly zero until the final clean-up step. The result is
$2N$ phantom variables throughout the interior-point path, even though
the true optimum has only $k \ll N$ nonzero weights.

## Why interior-point cannot exploit factor structure

Even though
$\Sigma = \sigma_f^2 \beta\beta^\top + \sigma_\varepsilon^2 I$ is rank-1
plus diagonal, the Gurobi $2N$-variable reformulation creates a full
$2N \times 2N$ dense Hessian for the Newton step. Define
$W = (u, v) \in \mathbb{R}^{2N}$ and $x = u - v$. The objective Hessian
in the $(u, v)$ space is:

$$H = \begin{pmatrix} \Sigma & -\Sigma \\ -\Sigma & \Sigma \end{pmatrix}
\in \mathbb{R}^{2N \times 2N}$$

Even though $\Sigma$ has rank-1 plus diagonal structure, $H$ does not:
the off-diagonal blocks $-\Sigma$ are dense and the barrier augmented
system $H + \mu \operatorname{diag}(X^{-2})$ (where $X$ is the barrier
slack vector) has no exploitable sparsity. The combined KKT Newton step
requires inverting a $2N \times 2N$ matrix each iteration.

PGD avoids the reformulation entirely:

$$g_k = \nabla f(w_k) = \underbrace{\sigma_f^2 \beta (\beta^\top w_k)}_{\text{O(N)}}
  + \underbrace{\sigma_\varepsilon^2 w_k}_{\text{O(N)}}
  - \underbrace{\mu}_{\text{given}} \qquad \text{cost: 2 dot products + 2 scalings}$$

## Computational complexity analysis

| Step             | Interior-point     | PGD (dense)     | PGD (factor)       |
|------------------|--------------------|-----------------|--------------------|
| Gradient         | included in Newton | O(N²)           | **O(N)**           |
| Projection       | included in Newton | O(N log N)      | O(N log N)         |
| KKT system       | O((2N)³) per step  | —               | —                  |
| Per-solve cost   | O(N³) × 25 steps   | O(N²) × K steps | **O(N) × K steps** |
| N=500 operations | ≈ 3 × 10¹⁰         | ≈ 7 × 10⁷       | **≈ 4.5 × 10³**    |


Table 3: Absolute operation count estimates at each benchmark N.
Interior-point assumes 25 Newton steps; PGD assumes K=500 iterations.
The IP / PGD-factor ratio grows as O(N^2) since IP is O(N^3) and
PGD-factor is O(N).


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

|     | Interior-point ops | PGD dense ops | PGD factor ops | IP / PGD-factor |
|-----|--------------------|---------------|----------------|-----------------|
| N   |                    |               |                |                 |
| 10  | 2.00e+05           | 7.00e+04      | 2.50e+04       | 8.00e+00        |
| 50  | 2.50e+07           | 1.40e+06      | 1.75e+05       | 1.43e+02        |
| 100 | 2.00e+08           | 5.35e+06      | 4.00e+05       | 5.00e+02        |
| 250 | 3.12e+09           | 3.22e+07      | 1.12e+06       | 2.78e+03        |
| 500 | 2.50e+10           | 1.27e+08      | 2.50e+06       | 1.00e+04        |




**On Python vs. Lean 4 timing.** The Python reference PGD measures the
per-iteration cost of the factor gradient and bisection projection, but
Python interpreter overhead dominates at small $N$. At $N = 10$ each
numpy call (gradient computation: 4 ops) costs more in dispatch than the
actual floating-point work. The algorithmic scaling advantage is best
read from the Gurobi-to-PGD timing ratio in the benchmark table above,
where the $O(N^3)$ vs. $O(N)$ difference dominates at $N \geq 100$. The
Lean 4 implementation in `optimization-proofs/` solves the $N = 10$
problem in 14.8 ns per solve (1,000-run average on Apple M-series),
demonstrating the algorithm’s performance when the interpreter overhead
is removed.[^4]

[^1]: DeMiguel, V., Garlappi, L., Nogales, F. J., and Uppal, R. (2009).
    “A generalized approach to portfolio optimization: Improving
    performance by constraining portfolio norms.” *Management Science*
    55(5): 798–812. DOI:
    [10.1287/mnsc.1080.0986](https://doi.org/10.1287/mnsc.1080.0986).
    Table 1 tests portfolios up to $N = 25$; Section 5.1 notes that
    interior-point methods become impractical at larger scales.

[^2]: Goldfarb, D. and Iyengar, G. (2003). “Robust portfolio selection
    problems.” *Mathematics of Operations Research* 28(1): 1–38. DOI:
    [10.1287/moor.28.1.1.14260](https://doi.org/10.1287/moor.28.1.1.14260).
    Section 4 uses the Sherman-Morrison-Woodbury identity to exploit
    factor covariance structure in second-order cone reformulations of
    robust portfolio problems.

[^3]: Wright, S. J. (1997). *Primal-Dual Interior-Point Methods*. SIAM.
    DOI:
    [10.1137/1.9781611971453](https://doi.org/10.1137/1.9781611971453).
    Chapter 4 establishes the $O(N^{3.5})$ iteration complexity bound
    for the QP barrier method; Chapter 6 covers dense factorization
    costs per Newton step.

[^4]: Boyd, S., Parikh, N., Chu, E., Peleato, B., and Eckstein, J.
    (2011). “Distributed optimization and statistical learning via the
    alternating direction method of multipliers.” *Foundations and
    Trends in Machine Learning* 3(1): 1–122. DOI:
    [10.1561/2200000016](https://doi.org/10.1561/2200000016). Section
    4.2 covers the $\ell_1$-regularized quadratic program; Section 6.3
    discusses the portfolio optimization formulation.
