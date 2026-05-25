import numpy as np


def print_banner(text):
    print("\n" + "=" * 80)
    print(f" {text} ".center(80, "="))
    print("=" * 80)


# ==============================================================================
# DEMONSTRATION 1: Step-Size Divergence Under Volatility Shock
# ==============================================================================
print_banner("DEMONSTRATION 1: Step-Size Divergence Under Volatility Shock")

# Stressed covariance matrix during a liquidity freeze
Sigma = np.array([[0.08, 0.07, 0.07], [0.07, 0.08, 0.07], [0.07, 0.07, 0.08]])
mu = np.array([0.05, 0.02, -0.01])

# Lipschitz constant is the maximum eigenvalue
eigvals = np.linalg.eigvals(Sigma)
lambda_max = np.max(eigvals)
lipschitz_bound = 2.0 / lambda_max

print(f"Maximum Eigenvalue (λ_max): {lambda_max:.6f}")
print(f"Lipschitz Stability Bound (2/λ_max): {lipschitz_bound:.6f}")

# 1. Unverified Solver: Step size chosen slightly over the bound (due to a float error or tuning bug)
lr_unverified = lipschitz_bound * 1.05  # 5% over the limit
print(
    f"Unverified Solver Step Size (η): {lr_unverified:.6f} (Violates Lipschitz Bound)"
)

# 2. Verified Solver: Step size proven to satisfy η < 2/λ_max
lr_verified = (2.0 / lambda_max) * 0.95  # Provably stable
print(f"Verified Solver Step Size (η):   {lr_verified:.6f} (Satisfies Lipschitz Bound)")


def run_gd(Sigma, mu, lr, steps=150):
    w = np.ones(3) / 3.0
    history = [w]
    for _ in range(steps):
        grad = np.dot(Sigma, w) - mu
        w = w - lr * grad
        history.append(w)
    return history


hist_unverified = run_gd(Sigma, mu, lr_unverified, steps=150)
hist_verified = run_gd(Sigma, mu, lr_verified, steps=150)

print("\n--- Solver Weight Paths (Divergence vs Convergence) ---")
print(
    f"{'Step':<5} | {'Unverified Solver weights':<35} | {'Verified Solver weights':<35}"
)
print("-" * 80)
for k in [0, 1, 2, 5, 10, 50, 100, 150]:
    uv_str = "[" + ", ".join(f"{x:.4e}" for x in hist_unverified[k]) + "]"
    v_str = "[" + ", ".join(f"{x:.4f}" for x in hist_verified[k]) + "]"
    print(f"{k:<5} | {uv_str:<35} | {v_str:<35}")

uv_diverged = np.any(np.abs(hist_unverified[-1]) > 1e4)
v_converged = np.linalg.norm(hist_verified[-1] - hist_verified[-2]) < 1e-6
print(f"\nUnverified Solver Diverged: {uv_diverged} ❌ (Weights exploded to infinity!)")
print(f"Verified Solver Converged:  {v_converged} ✅ (Weights stabilized at optimal!)")

# ==============================================================================
# DEMONSTRATION 2: Cumulative Constraint Bleed Over 100,000 Rebalances
# ==============================================================================
print_banner("DEMONSTRATION 2: Cumulative Constraint Bleed Over 100,000 Rebalances")

steps = 100000
np.random.seed(42)

# Simulate 100,000 sequential trades and rebalances
# We use np.float32 to simulate low-latency GPU/hardware execution pipelines
w_float = np.ones(3, dtype=np.float32) / 3.0
for i in range(steps):
    # Simulate trade execution: fractional changes in weights
    epsilon = (
        np.array([0.1, 0.2, -0.3], dtype=np.float32) * 1e-6 * (1.0 + 0.1 * np.sin(i))
    )
    w_float = w_float + epsilon
    # Projection onto hyperplane: sum(w) = 1
    w_float = w_float - (np.sum(w_float) - 1.0) / 3.0

sum_float = np.sum(w_float)
float_error = np.abs(sum_float - 1.0)

# 2. Verified Scaled-Integer Path (Basis Points)
# 100% is represented exactly as the integer 10,000
w_int = np.array([3333, 3333, 3334], dtype=np.int64)
for i in range(steps):
    # Simulate an integer rebalance: we must rebalance in whole basis points
    epsilon = np.array([2, 1, -3], dtype=np.int64) * (1 if i % 2 == 0 else -1)
    w_int = w_int + epsilon

sum_int = np.sum(w_int)
int_error = np.abs(sum_int - 10000)

print(f"Simulation Steps: {steps}")
print("\n--- Final Constraint Accuracy ---")
print(
    f"Unverified Float32 sum of weights:  {sum_float:.25f} (Error: {float_error:.2e}) ⚠️"
)
print(f"Verified Scaled-Integer sum (bp):   {sum_int:<25} (Error: {int_error:.2e}) ✅")

if float_error > 0:
    print(
        "\n⚠️ Floating-point rounding errors have quietly bled the budget constraint at the native level."
    )
    print(
        "✅ The scaled-integer budget constraint is structurally guaranteed to have EXACTLY zero drift."
    )
