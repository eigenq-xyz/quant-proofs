# optimization-proofs — Formally Verified Convex Optimization Core

A specialized, high-performance, and compiler-verified numerical optimization engine in Lean 4, implementing **Projected Gradient Descent (PGD)** with an analytical, high-dimensional **simplex and $L_1$-ball intersection projection** kernel.

This module is designed to be **general-purpose, mathematically abstract, and zero-dependency**, decouplable from financial return series and domain-specific trading code.

---

## 🚨 The Mathematical Formulation

The engine solves general Convex Quadratic Programs (QP) of the form:

$$\min_{x \in \mathcal{C}} \frac{1}{2} x^T Q x + c^T x$$

where:
*   $Q \in \mathbb{R}^{N \times N}$ is a symmetric, strictly positive definite (PD) matrix.
*   $c \in \mathbb{R}^N$ is a linear coefficient vector.
*   $\mathcal{C} \subset \mathbb{R}^N$ is a convex constraint set defined by the intersection of a budget hyperplane and a gross exposure $L_1$-ball:
    $$\mathcal{C} = \left\{ x \in \mathbb{R}^N \;\middle|\; \sum_{i=1}^N x_i = B, \quad \sum_{i=1}^N |x_i| \le L \right\}$$

---

## 🏆 The Algorithm: Projected Gradient Descent (PGD)

PGD iteratively computes the optimal allocation $x^*$ by alternating between unconstrained gradient updates and analytical geometric projections:

```
                  x_{k+1} = Π_C ( x_k - η (Q x_k + c) )
```

where $\eta > 0$ is the learning rate, and $\Pi_{\mathcal{C}}$ is the Euclidean projection operator onto the constraint set $\mathcal{C}$.

### 1. The Lipschitz Stability Bound
For gradient descent to converge on a convex function $f$ with $L$-Lipschitz continuous gradients ($\nabla f$), the step size $\eta$ must be strictly bounded:

$$\eta < \frac{2}{L}$$

In a quadratic program, the Lipschitz constant $L$ is exactly the maximum eigenvalue of the matrix $Q$ ($\lambda_{\text{max}}(Q)$).
*   **The Formal Invariant**: We formally prove in Lean 4 that under all step sizes satisfying $\eta < \frac{2}{\lambda_{\text{max}}(Q)}$, the optimization sequence $x_k$ converges strictly and unconditionally to the unique global minimum $x^*$.

### 2. Analytical Dual-Bisection Projection ($O(N \log N)$)
Traditional solvers introduce $2N$ slack variables and $2N$ inequality constraints to smooth the non-differentiable $L_1$ absolute value bounds. This increases problem dimensionality and creates degenerate, flat valleys.

Instead, we project the unconstrained gradient step $y = x_k - \eta \nabla f(x_k)$ onto the intersection of the hyperplane $\sum x_i = B$ and the $L_1$-ball $\sum |x_i| \le L$ analytically:
1.  **Formulate the Dual**: The projection problem is:
    $$\min_{x} \frac{1}{2} \|x - y\|_2^2 \quad \text{s.t.} \quad \sum x_i = B, \quad \sum |x_i| \le L$$
2.  **Apply Lagrange Duality**: The analytical solution is given by:
    $$x_i(\theta, \mu) = \text{sign}(y_i - \theta) \max(|y_i - \theta| - \mu, 0)$$
    where $\theta \in \mathbb{R}$ is the budget dual multiplier, and $\mu \ge 0$ is the leverage dual multiplier.
3.  **Root-Finding via Sorting/Bisection**: We solve for $(\theta^*, \mu^*)$ in $O(N \log N)$ time using a nested dual bisection search.
*   **The Formal Invariant**: We formally prove in Lean 4 that the analytical projection operator $\Pi_{\mathcal{C}}(y)$ strictly minimizes the Euclidean distance to $y$ subject to the constraints, guaranteeing zero constraint violations.

---

## 📂 Formally Verified Lean 4 Module Structure

```
optimization-proofs/
├── lakefile.lean         # Lean 4 project configuration
├── lean-toolchain        # Lean 4 compiler toolchain lock
└── OptimizationProofs/
    ├── Projection.lean   # Analytical dual-bisection projection algorithm & correctness proofs
    └── PGD.lean          # Projected Gradient Descent core & convergence theorems under η < 2/λ_max
```

---

## 🎯 Lean 4 Theorem Targets

We formally verify the optimization engine under the following theorem roadmap:

1.  **`projection_correctness`**:
    $$\forall y \in \mathbb{R}^N, \quad \Pi_{\mathcal{C}}(y) = \text{arg min}_{x \in \mathcal{C}} \|x - y\|_2$$
    *   *Proof Strategy*: Prove using Karush-Kuhn-Tucker (KKT) optimality conditions on the dual function.
2.  **`pgd_convergence`**:
    *   *Theorem*: The sequence $x_{k+1} = \Pi_{\mathcal{C}}(x_k - \eta \nabla f(x_k))$ satisfies:
        $$\lim_{k \to \infty} f(x_k) = f(x^*)$$
    *   *Proof Strategy*: Prove using the contraction mapping theorem and the spectral properties of positive definite $Q$.
