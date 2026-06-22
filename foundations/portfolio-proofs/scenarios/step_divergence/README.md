# Step Divergence — Lipschitz Bound Violation Under Volatility Shock

Gradient descent on a quadratic portfolio objective diverges to infinity when the
step size exceeds the Lipschitz stability bound $2 / \lambda_{\max}(Q)$, and a
volatility shock that increases $\lambda_{\max}$ can silently push a calibrated
step size past that bound overnight.

---

## What this scenario demonstrates

For the mean-variance objective $f(w) = \tfrac{1}{2} w^T Q w - \mu^T w$, the
gradient $\nabla f(w) = Qw - \mu$ is $L$-Lipschitz with $L = \lambda_{\max}(Q)$
(the spectral norm of $Q$). The descent lemma gives:

$$f\!\left(w - \eta \nabla f(w)\right) \leq f(w) - \eta\!\left(1 - \frac{\eta L}{2}\right)\!\|\nabla f(w)\|^2$$

For the step to reduce the objective, we need $1 - \eta L / 2 > 0$, which
requires:

$$\eta < \frac{2}{\lambda_{\max}(Q)}$$

At $\eta = 2 / \lambda_{\max}$, the algorithm may oscillate. For
$\eta > 2 / \lambda_{\max}$, the error grows geometrically and the iterates
diverge to infinity. The divergence growth factor per step is
$|\eta \lambda_{\max} - 1|$.

**Why this matters in production.** The step size $\eta$ is typically a
once-calibrated tuning parameter. A volatility shock that spikes pairwise
correlations increases $\lambda_{\max}$, potentially doubling it. A solver that
was well-behaved under normal conditions can cross the stability boundary
overnight, and nothing in standard solver logs warns that the Lipschitz condition
has been violated.

---

## Numerical setup

A 3-asset covariance matrix representing a volatility shock (pairwise correlation
0.875, individual variance 0.08):

```python
Sigma = np.array([[0.08, 0.07, 0.07],
                  [0.07, 0.08, 0.07],
                  [0.07, 0.07, 0.08]])
mu = np.array([0.05, 0.02, -0.01])
```

Spectral properties:

| Quantity | Value |
| :--- | :--- |
| $\lambda_{\max}(Q)$ | 0.220000 |
| Stability bound $2 / \lambda_{\max}$ | 9.090909 |
| Unverified step size $\eta$ (5% over limit) | 9.545455 |
| Divergence growth factor $\|\eta \lambda_{\max} - 1\|$ | 1.10 per step |
| Error amplification after 100 steps | $\approx 13{,}780\times$ |

The unconstrained optimum (no portfolio constraints) is
$w^* = \Sigma^{-1} \mu \approx [3.09, 0.09, -2.91]$ with objective $-0.0927$.
The script runs pure unconstrained gradient descent to isolate the divergence
mechanism, with no simplex projection applied.

**Note on failure mode.** Unlike the `boundary_trap` scenario, which produces a
suboptimal result, `step_divergence` produces no result at all. The solver
crashes before reaching any feasible point. The failure is binary: either $\eta$
satisfies the Lipschitz bound and the solver converges, or it does not and the
solver diverges to infinity.

---

## Quick start

From the `foundations/portfolio-proofs/` directory:

```bash
uv run python scenarios/step_divergence/unverified_gd.py
```

Expected output (abbreviated):

```
Maximum Eigenvalue (λ_max):          0.220000
Lipschitz Stability Bound (2/λ_max): 9.090909
Unverified Solver Step Size (η):     9.545455  (Violates Lipschitz Bound)

Step 0   | weights: [0.33333333  0.33333333  0.33333333]
Step 1   | weights: [ 0.11060606 -0.17575758 -0.46212121]
Step 2   | weights: [ 0.92963499  0.38424242 -0.16115014]
Step 5   | weights: [ 0.88382419 -0.29951758 -1.48285934]
Step 10  | weights: [ 2.61961276  0.71969514 -1.18022247]
Step 50  | weights: [31.52940738 28.54929767 25.56918795]
Step 100 | weights: [3343.84528384 3340.84541571 3337.84554759]

DIVERGENCE DETECTED at Step 112!
Weights exploded to: [10487.80961277 10484.80965234 10481.80969190]
```

---

## The verified PGD solution

The verified PGD solver formally proves the theorem `pgd_convergence`: for all
step sizes satisfying $\eta < 2 / \lambda_{\max}(Q)$, the projected gradient
iteration

$$w_{k+1} = \Pi_{\mathcal{C}}\!\left(w_k - \eta \nabla f(w_k)\right)$$

converges to the global minimum. The step size is computed from the spectral
radius of $Q$ (an output of the Ledoit-Wolf shrinkage estimator in
`optimization-proofs`) and bounded at compile time. If a covariance shock
increases $\lambda_{\max}$, the solver recomputes $\eta$ automatically, and the
Lean 4 proof guarantees the Lipschitz bound is respected. There is no runtime
path in which $\eta$ can silently violate the stability condition.

---

## File structure

| File | Purpose |
| :--- | :--- |
| `unverified_gd.py` | Gradient descent with fixed step size; demonstrates divergence when $\eta > 2/\lambda_{\max}$ |
| `README.md` | This file |

---

## Context

This is one of four stress-test scenarios in `foundations/portfolio-proofs/scenarios/`. Each
scenario demonstrates a distinct failure class in standard numerical QP solvers
under stressed market conditions:

| Scenario | Failure class |
| :--- | :--- |
| `cholesky_crash/` | Non-PSD covariance matrix when $T < N$ |
| `boundary_trap/` | Non-differentiable $L_1$ boundary traps active-set solvers |
| `precision_bleed/` | Floating-point drift violates leverage constraints over long rebalance paths |
| `step_divergence/` | Step size exceeds Lipschitz bound after volatility shock (this scenario) |

See `foundations/portfolio-proofs/README.md` for the full problem statement and the
head-to-head benchmark table.

---

## References

- Beck, A. and Teboulle, M. (2009). "A fast iterative shrinkage-thresholding
  algorithm for linear inverse problems." _SIAM Journal on Imaging Sciences_
  2(1): 183-202. DOI: 10.1137/080716542. Theorem 1 and Lemma 2.3 establish the
  $\eta < 2/L$ convergence condition for projected gradient descent on $L$-smooth
  convex functions; divergence occurs for $\eta > 2/L$.
- Nesterov, Y. (2004). _Introductory Lectures on Convex Optimization_. Springer.
  DOI: 10.1007/978-1-4419-8853-9. Theorem 2.1.5 (the descent lemma for $L$-smooth
  functions) is the canonical derivation from which the step-size stability bound
  follows.
- Nocedal, J. and Wright, S. J. (2006). _Numerical Optimization_, 2nd ed. Springer.
  Appendix A (linear algebra review). For a symmetric PSD matrix $Q$, the spectral
  norm $\|Q\|_2 = \lambda_{\max}(Q)$; this is the Lipschitz constant for the
  gradient $\nabla f(w) = Qw - \mu$.
- Whaley, R. E. (2009). "Understanding the VIX." _Journal of Portfolio Management_
  35(3): 98–105. DOI: 10.3905/JPM.2009.35.3.098. History and interpretation of
  the CBOE VIX index.
- Cboe Exchange, Inc. (2019). "Cboe Volatility Index." White Paper. Chicago: Cboe
  Global Markets. <https://cdn.cboe.com/resources/vix/VIX_Methodology.pdf>.
  Documents the VIX index calculation methodology. **Cite this for VIX formula
  and methodology only — not for the February 5, 2018 spike event.**
- U.S. SEC DERA (2025). "Demystify the Surge in VIX." SEC DERA Working Paper.
  <https://www.sec.gov/files/dera-vix-working-paper-2504.pdf>. Post-mortem
  analysis of the February 5, 2018 VIX spike and the XIV ETN collapse.
  **Cite this for the Volmageddon event itself.**
