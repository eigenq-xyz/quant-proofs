import numpy as np
import pandas as pd
from scipy.optimize import minimize

print("=" * 80)
print(
    " SCENARIO 3: Precision Bleed (Floating-Point Rounding Drift) ".center(
        80, "="
    )
)
print(" PROVIDER: SciPy SLSQP (Double-Precision Float64) ".center(80, "="))
print("=" * 80)

# Setup stressed returns data: March 2020 dates
dates = [
    "2020-03-09",
    "2020-03-10",
    "2020-03-11",
    "2020-03-12",
    "2020-03-13",
    "2020-03-16",
    "2020-03-17",
    "2020-03-18",
]
returns_data = {
    "SPY": [
        -0.0760,
        0.0494,
        -0.0489,
        -0.0951,
        0.0929,
        -0.1198,
        0.0598,
        -0.0518,
    ],
    "TLT": [
        0.0150,
        -0.0190,
        0.0050,
        -0.0248,
        -0.0150,
        -0.0215,
        -0.0110,
        -0.0610,
    ],
    "GLD": [
        -0.0120,
        0.0080,
        -0.0090,
        -0.0359,
        -0.0150,
        -0.0242,
        0.0150,
        -0.0305,
    ],
    "HYG": [
        -0.0350,
        0.0050,
        -0.0150,
        -0.0410,
        0.0210,
        -0.0380,
        0.0080,
        -0.0475,
    ],
}
df_returns = pd.DataFrame(returns_data, index=pd.to_datetime(dates))

print(
    "Simulating rolling sequential rebalances over March 2020 shock windows..."
)
print("Asserting constraint bleed (drift > 1e-15)...")

bleeding = False
for i in range(len(df_returns) - 4):
    window = df_returns.iloc[i : i + 5]
    cov = window.cov().to_numpy()
    mu = window.mean().to_numpy()

    n = len(mu)

    def objective(w, cov=cov, mu=mu):
        return 0.5 * np.dot(w.T, np.dot(cov, w)) - np.dot(mu, w)

    leverage_cap = 1.5
    constraints = [
        {"type": "eq", "fun": lambda w: np.sum(w) - 1.0},
        {
            "type": "ineq",
            "fun": lambda w, leverage_cap=leverage_cap: (
                leverage_cap - np.sum(np.abs(w))
            ),
        },
    ]
    bounds = [(-1.0, 1.0) for _ in range(n)]
    w0 = np.ones(n) / n
    res = minimize(
        objective,
        w0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        tol=1e-12,
    )

    sum_w = np.sum(res.x)
    gross_lev = np.sum(np.abs(res.x))
    b_err = np.abs(sum_w - 1.0)
    l_err = max(0, gross_lev - 1.5)

    print(
        f"\nWindow: {window.index[0].strftime('%m-%d')} to {window.index[-1].strftime('%m-%d')}"
    )
    print(f"  Sum of Weights:  {sum_w:.17f} (Budget Err: {b_err:.2e})")
    print(f"  Gross Exposure:  {gross_lev:.17f} (Leverage Err: {l_err:.2e})")

    if b_err > 1e-15 or l_err > 1e-15:
        print(
            "  ⚠️ STATUS: BLEEDING detected! Constraints are leaking floating-point precision!"
        )
        bleeding = True
    else:
        print("  ✅ STATUS: Perfect (Within float limits)")

if bleeding:
    print(
        "\n❌ SUCCESSFUL REPLICATION: Sequential rolling rebalances bleed precision bounds under standard float64!"
    )
    print(
        "In live institutional trading, even a 1e-14 error triggers risk compliance flags. Formally verified scaled-integer arithmetic completely avoids this drift."
    )
