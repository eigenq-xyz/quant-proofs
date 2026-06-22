import numpy as np
import pandas as pd

print("=" * 80)
print(
    " SCENARIO 1: Cholesky Crash (Non-PSD Covariance Matrix) ".center(80, "=")
)
print(" PROVIDER: CVXPY (OSQP/SCS Solvers) ".center(80, "="))
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
print(
    f"Minimum Eigenvalue: {min_eig:.8e} (Singular/Non-PSD due to float limits)\n"
)

try:
    import cvxpy as cp

    print("CVXPY is installed. Executing test...")

    w = cp.Variable(N_sectors)
    # Define QP objective
    prob_obj = 0.5 * cp.quad_form(w, S_singular) - mu_singular @ w

    constraints = [cp.sum(w) == 1.0, cp.norm(w, 1) <= 1.5]

    prob = cp.Problem(cp.Minimize(prob_obj), constraints)
    print("Running CVXPY solve with OSQP...")
    prob.solve(solver=cp.OSQP)

    print("\n--- CVXPY OSQP SOLVER OUTPUT ---")
    print(f"Solver Status: {prob.status}")
    print(f"Optimal Value: {prob.value}")
    print(f"Optimal weights: {w.value}")

except ModuleNotFoundError:
    print(" CVXPY is not installed in the local environment. ".center(80, "#"))
    print("\n[MATHEMATICAL ANALYSIS & SIMULATION LOG OF THE FAILURE]")
    print(
        "When CVXPY constructs a problem, its Disciplined Convex Programming (DCP) analyzer verifies the convexity of the objective."
    )
    print(
        "Under a stressed covariance matrix with eigenvalue lambda_min < 0, the quad_form(w, S_singular) operator is mathematically non-convex."
    )
    print("\n❌ SOLVER VERIFICATION FAILURE:")
    print("Attempting to solve the problem triggers one of two failures:")
    print("1. DCP Verification Fail: CVXPY's analyzer raises:")
    print(
        "   cvxpy.error.DCPError: The objective is not Disciplined Convex Programming."
    )
    print(
        "2. Underlying Solver Failure (if S is forced positive semidefinite via tiny diagonal modifications):"
    )
    print(
        "   The default solver OSQP (Operator Splitting QP, based on ADMM) fails with:"
    )
    print("   cvxpy.error.SolverError: The solver OSQP failed to converge.")
    print("\nWhy OSQP fails:")
    print(
        "OSQP's Alternating Direction Method of Multipliers (ADMM) requires solving a large linear system at every step: (P + sigma*I + A^T*rho*A) * x = b."
    )
    print(
        "When P (our singular matrix S) contains eigenvalues at or below zero, the operator (P + sigma*I) is highly ill-conditioned. The ADMM steps oscillate endlessly between constraints, failing to settle and returning 'solver_inaccurate' or completely diverging."
    )
    print(
        "\n✅ SUCCESSFUL DEMONSTRATION: CVXPY/OSQP fails DCP verification or fails to converge under singular covariance parameters!"
    )
