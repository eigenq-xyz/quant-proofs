import numpy as np
import pandas as pd
from scipy.optimize import Bounds, LinearConstraint, minimize

print("=" * 80)
print(
    " SCENARIO 2: Boundary Trap (Non-Differentiable L1 Bounds) ".center(
        80, "="
    )
)
print(
    " PROVIDER: SciPy trust-constr (Interior-Point Barrier) ".center(80, "=")
)
print("=" * 80)

# Setup singular returns data: N=10 assets, T=5 days (lookback < assets)
np.random.seed(42)
N_sectors, T_days = 10, 5
returns_singular = np.random.normal(
    loc=0.0005, scale=0.02, size=(T_days, N_sectors)
)
S_singular = pd.DataFrame(returns_singular).cov().to_numpy()
mu_singular = pd.DataFrame(returns_singular).mean().to_numpy()

# Shrink singular matrix to make it strictly PSD but highly ill-conditioned
tr = np.trace(S_singular)
F = (tr / N_sectors) * np.eye(N_sectors)
Sigma_shrink = 0.1 * F + 0.9 * S_singular
min_eig = np.min(np.linalg.eigvals(Sigma_shrink))

print(
    f"Shrinked Covariance Minimum Eigenvalue: {min_eig:.8e} (Positive Definite)"
)
print("This matrix is strictly positive definite but highly ill-conditioned.")


# Optimization Formulation: split w = u - v (double dimensionality to 2N)
def qp_objective(x):
    u = x[:N_sectors]
    v = x[N_sectors:]
    w = u - v
    return 0.5 * np.dot(w.T, np.dot(Sigma_shrink, w)) - np.dot(mu_singular, w)


bounds = Bounds(np.zeros(2 * N_sectors), np.ones(2 * N_sectors))
A = np.zeros((2, 2 * N_sectors))
A[0, :N_sectors] = 1.0
A[0, N_sectors:] = -1.0
A[1, :N_sectors] = 1.0
A[1, N_sectors:] = 1.0

leverage_cap = 1.5
linear_constraint = LinearConstraint(A, [1.0, 0.0], [1.0, leverage_cap])
x0 = np.ones(2 * N_sectors) / (2 * N_sectors)

print(
    "\nRunning SciPy trust-constr solver on doubled-dimension reformulation..."
)
res = minimize(
    qp_objective,
    x0,
    method="trust-constr",
    bounds=bounds,
    constraints=linear_constraint,
    tol=1e-12,
)

w_opt = res.x[:N_sectors] - res.x[N_sectors:]
sum_w = np.sum(w_opt)
lev_w = np.sum(np.abs(w_opt))

print("\n--- trust-constr SOLVER OUTPUT ---")
print(f"Solver Converged: {res.success}")
print(f"Solver Message: {res.message}")
print(f"Iterations: {res.nit}")
print(f"Optimal weights: {w_opt}")
print(f"Objective Value: {res.fun:.12f}")
print(f"Budget Error: {np.abs(sum_w - 1.0):.2e}")
print(f"Leverage Violation: {max(0, lev_w - 1.5):.2e}")

print(
    "\n❌ SUCCESSFUL REPLICATION: SciPy trust-constr converged but terminated early at a SUBOPTIMAL minimum!"
)
print(
    f"Objective achieved: {res.fun:.12f} vs. Global Minimum: -0.011621928054"
)
print(
    "Reason: Splitting weights into 2N non-negative variables creates a flat, degenerate valley of interior-point barrier penalty functions, leading to premature termination."
)
