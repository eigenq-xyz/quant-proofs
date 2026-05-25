import numpy as np
import pandas as pd
from scipy.optimize import minimize

print("=" * 80)
print(
    " SCENARIO 1: Cholesky Crash (Non-PSD Covariance Matrix) ".center(80, "=")
)
print(" PROVIDER: SciPy SLSQP (Active-Set SQP) ".center(80, "="))
print("=" * 80)

# Setup singular returns data: N=10 assets, T=5 days (lookback < assets)
np.random.seed(42)
N_sectors, T_days = 10, 5
returns_singular = np.random.normal(
    loc=0.0005, scale=0.02, size=(T_days, N_sectors)
)
S_singular = pd.DataFrame(returns_singular).cov().to_numpy()
mu_singular = pd.DataFrame(returns_singular).mean().to_numpy()

min_eig = np.min(np.linalg.eigvals(S_singular))
print(f"Number of Assets (N): {N_sectors} | Lookback Days (T): {T_days}")
print(
    f"Estimated Covariance Rank: {np.linalg.matrix_rank(S_singular)} (Rank Deficient)"
)
print(f"Minimum Eigenvalue: {min_eig:.8e} (Non-strictly Positive Definite)")


# Optimization Formulation
def objective(w):
    return 0.5 * np.dot(w.T, np.dot(S_singular, w)) - np.dot(mu_singular, w)


leverage_cap = 1.5
constraints = [
    {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
    {"type": "ineq", "fun": lambda w: leverage_cap - np.sum(np.abs(w))},
]
bounds = [(-1.0, 1.0) for _ in range(N_sectors)]
w0 = np.ones(N_sectors) / N_sectors

print("\nRunning SciPy SLSQP solver on singular covariance matrix...")
res = minimize(
    objective,
    w0,
    method="SLSQP",
    bounds=bounds,
    constraints=constraints,
    tol=1e-12,
)

print("\n--- SLSQP SOLVER OUTPUT ---")
print(f"Solver Converged: {res.success}")
print(f"Solver Message: {res.message}")
print(f"Iterations: {res.nit}")
print(f"Optimal weights: {res.x}")

if not res.success:
    print(
        "\n❌ SUCCESSFUL REPLICATION: SciPy SLSQP failed to converge due to rank-deficiency of the stressed covariance matrix!"
    )
else:
    print("\n⚠️ Solver unexpectedly converged, check conditioning parameters.")
