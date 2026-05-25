import numpy as np
import pandas as pd
from scipy.optimize import minimize

print("=" * 80)
print(" SCENARIO 2: Boundary Trap (Non-Differentiable L1 Bounds) ".center(80, "="))
print(" PROVIDER: SciPy SLSQP (Active-Set SQP) ".center(80, "="))
print("=" * 80)

# Setup singular returns data: N=10 assets, T=5 days (lookback < assets)
np.random.seed(42)
N_sectors, T_days = 10, 5
returns_singular = np.random.normal(loc=0.0005, scale=0.02, size=(T_days, N_sectors))
S_singular = pd.DataFrame(returns_singular).cov().to_numpy()
mu_singular = pd.DataFrame(returns_singular).mean().to_numpy()

# Shrink singular matrix to make it strictly PSD but highly ill-conditioned
tr = np.trace(S_singular)
F = (tr / N_sectors) * np.eye(N_sectors)
Sigma_shrink = 0.1 * F + 0.9 * S_singular
min_eig = np.min(np.linalg.eigvals(Sigma_shrink))

print(f"Shrinked Covariance Minimum Eigenvalue: {min_eig:.8e} (Positive Definite)")
print("This matrix is strictly positive definite but highly ill-conditioned.")


# Optimization Formulation
def objective(w):
    return 0.5 * np.dot(w.T, np.dot(Sigma_shrink, w)) - np.dot(mu_singular, w)


leverage_cap = 1.5
constraints = [
    {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
    {"type": "ineq", "fun": lambda w: leverage_cap - np.sum(np.abs(w))},
]
bounds = [(-1.0, 1.0) for _ in range(N_sectors)]
w0 = np.ones(N_sectors) / N_sectors

print("\nRunning SciPy SLSQP solver on ill-conditioned covariance matrix...")
res = minimize(
    objective, w0, method="SLSQP", bounds=bounds, constraints=constraints, tol=1e-12
)

print("\n--- SLSQP SOLVER OUTPUT ---")
print(f"Solver Converged: {res.success}")
print(f"Solver Message: {res.message}")
print(f"Iterations: {res.nit}")
print(f"Objective Value: {res.fun:.12f}")
print(f"Leverage Violation: {max(0, np.sum(np.abs(res.x)) - 1.5):.2e}")

if not res.success:
    print(
        "\n❌ SUCCESSFUL REPLICATION: SciPy SLSQP failed to converge due to non-differentiable absolute value L1 bounds!"
    )
    print(
        "SLSQP's active-set search gets trapped in infinite boundary oscillation loops."
    )
else:
    print("\n⚠️ Solver unexpectedly converged, check conditioning parameters.")
