import numpy as np

print("=" * 80)
print(" SCENARIO 4: Step-Size Divergence (Lipschitz Bound Violations) ".center(80, "="))
print(" PROVIDER: Unverified Gradient Descent (Fixed learning rate η) ".center(80, "="))
print("=" * 80)

# Stressed covariance matrix during a liquidity freeze (volatility shock)
Sigma = np.array([[0.08, 0.07, 0.07], [0.07, 0.08, 0.07], [0.07, 0.07, 0.08]])
mu = np.array([0.05, 0.02, -0.01])

# Lipschitz constant is the maximum eigenvalue
eigvals = np.linalg.eigvals(Sigma)
lambda_max = np.max(eigvals)
lipschitz_bound = 2.0 / lambda_max

print(f"Maximum Eigenvalue (λ_max): {lambda_max:.6f}")
print(f"Lipschitz Stability Bound (2/λ_max): {lipschitz_bound:.6f}")

# Unverified Solver: Step size chosen slightly over the bound (due to a float error or tuning bug)
lr_unverified = lipschitz_bound * 1.05  # 5% over the limit
print(
    f"Unverified Solver Step Size (η): {lr_unverified:.6f} (Violates Lipschitz Bound)"
)

w = np.ones(3) / 3.0
print(f"\nStep 0 | weights: {w}")

# Run Gradient Descent steps
diverged = False
for k in range(1, 151):
    grad = np.dot(Sigma, w) - mu
    w = w - lr_unverified * grad

    if k in [1, 2, 5, 10, 50, 100, 150]:
        print(f"Step {k:<3} | weights: {w}")
    if np.any(np.isnan(w)) or np.any(np.abs(w) > 1e4):
        print(f"\n❌ DIVERGENCE DETECTED at Step {k}!")
        print(f"Weights exploded to: {w}")
        diverged = True
        break

if diverged:
    print(
        "\n❌ SUCCESSFUL REPLICATION: Unverified solver diverged completely under volatility shock!"
    )
    print(
        "Without a compiler-verified compile-time upper bound on η (η < 2/λ_max), standard gradient updates explode under covariance shocks."
    )
else:
    print(
        "\n⚠️ Solver stabilized. Adjust learning rate or covariance to force divergence."
    )
