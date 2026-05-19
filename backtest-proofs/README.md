# backtest-proofs

[![Lean CI](https://github.com/eigenq-xyz/backtest-proofs/actions/workflows/lean.yml/badge.svg)](https://github.com/eigenq-xyz/backtest-proofs/actions/workflows/lean.yml)
[![Python CI](https://github.com/eigenq-xyz/backtest-proofs/actions/workflows/python.yml/badge.svg)](https://github.com/eigenq-xyz/backtest-proofs/actions/workflows/python.yml)
[![codecov](https://codecov.io/gh/eigenq-xyz/backtest-proofs/branch/main/graph/badge.svg)](https://codecov.io/gh/eigenq-xyz/backtest-proofs)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/eigenq-xyz/backtest-proofs/main.svg)](https://results.pre-commit.ci/latest/github/eigenq-xyz/backtest-proofs/main)

> **Educational use only.** Research software, not production trading infrastructure. See [DISCLAIMER.md](DISCLAIMER.md).

Formally verified accounting invariants for options portfolio backtesting.

> As AI accelerates model development in quantitative finance, the bottleneck shifts from building models to ensuring they are correct. This project applies formal verification to the accounting layer that every backtesting engine depends on.

## What is verified

The following invariants are proved as Lean 4 theorems — not tested, *proved*. Checked by the Lean kernel on every commit via CI. Zero `sorry`, zero `axiom`.

| Invariant | Statement | Theorem |
| --- | --- | --- |
| NAV identity | Portfolio value = cash + Σ(quantity × mark price), at every step | `valueIdentity` |
| Trade accounting | ΔPV = qty × (exec − mark) − fee; cash and quantity update correctly | `valueUpdateFormula`, `cashUpdateCorrect`, `quantityConservation` |
| Self-financing | Trading at the mark price changes PV only by the fee | `selfFinancing` |
| Settlement | At expiry ΔPV = qty × (payoff − mark), unifying ITM and OTM | `settlement_value_formula` |

26 theorems total across [`Invariants.lean`](lean/BacktestProofs/Invariants.lean) (12) and [`OptionInvariants.lean`](lean/BacktestProofs/OptionInvariants.lean) (14). See [docs/formal_guarantees.md](docs/formal_guarantees.md) for the full list.

## Status

| Component | Status |
| --- | --- |
| Accounting invariants (NAV, self-financing, conservation, well-formedness) | ✅ Complete |
| European option settlement (ITM ∪ OTM unified) | ✅ Complete |
| Cython FFI bridge (Lean → C → Python) | ✅ Complete |
| Python/Cython backtesting execution layer | ✅ Complete |
| Delta-hedging strategy (single-leg + portfolio) | ✅ Complete |
| Black-Scholes pricing formalization in Lean | 🔧 In progress (currently Python only) |
| Greeks (delta, gamma) as Lean 4 theorems | 📋 Planned |
| Multi-period GBM convergence theorem | 📋 Planned (requires Mathlib real analysis) |

## What is not verified

The pricing layer (Black-Scholes, Greeks), the delta-hedging strategy logic, the simulator, ETL, and the backtesting orchestration are conventional Python — not formally verified. The formal proofs cover the **accounting layer**: the invariants that must hold regardless of which strategy or pricing model sits on top.

## Validation

Numerical results that confirm the engine behaves correctly on externally verifiable benchmarks. Full detail in [docs/validation.md](docs/validation.md).

- **Black-Scholes pricer** matches Hull/DerivaGem reference vectors within `abs=0.01` on price, `abs=0.001` on delta.
- **Monte Carlo convergence**: over 500 seeded GBM paths × 20 weekly steps, mean discrete-hedge cost is within ±3% of the BS price. All 10,000 step certificates pass `valueUpdateFormula`.
- **BKL (2000) variance scaling**: `std(10 steps) / std(20 steps) ≈ √2`.
- **Carr-Madan (1998) decomposition**: `corr(hedge_cost, gamma_pnl) > 0.70` across 200 seeded paths.

## Repository structure

```text
backtest-proofs/
├── lean/
│   ├── lakefile.lean
│   └── BacktestProofs/
│       ├── Basic.lean              # Portfolio, Position, Trade
│       ├── Accounting.lean         # @[export hedge_*] FFI exports
│       ├── Invariants.lean         # accounting theorems
│       ├── Options.lean            # EuropeanOption, payoffs
│       ├── OptionInvariants.lean   # settlement theorems
│       └── Tests/UnitTests.lean
├── python/
│   ├── pyproject.toml
│   └── src/backtest_proofs/
│       ├── pricer/                 # Black-Scholes + Greeks
│       ├── etl/                    # WRDS OptionMetrics loaders
│       ├── simulator/              # seeded GBM
│       ├── backtest/               # delta-hedge runner, certificates
│       └── ffi/                    # compiled Cython bridge to Lean
├── docs/                           # JupyterBook → GitHub Pages
├── notebooks/                      # delta_hedge_demo.ipynb
└── data/                           # WRDS / FRED (git-crypt)
```

## Prerequisites

- Lean 4 v4.27.0-rc1 (installed via `elan` by `make setup`)
- Python 3.12+ (managed by `uv`)
- Make

## Setup

```bash
git clone https://github.com/eigenq-xyz/backtest-proofs
cd backtest-proofs
make setup      # elan + uv + Mathlib cache (~5 min first run)
make test       # Lean proofs + Python tests
```

## Running the proofs

```bash
cd lean && lake build
```

Any `sorry` would cause a compile error; the build succeeding is the audit.

## Running a backtest

```python
from backtest_proofs.backtest.runner import run_delta_hedge
from backtest_proofs.backtest.scenarios import (
    hull_192_path, HULL_192_K, HULL_192_R, HULL_192_SIGMA, HULL_192_N_CONTRACTS,
)

result = run_delta_hedge(
    path=hull_192_path(),
    K=HULL_192_K, r=HULL_192_R, sigma=HULL_192_SIGMA,
    n_contracts=HULL_192_N_CONTRACTS,
)
print(f"Hedging cost: ${result.total_hedging_cost:,.0f}")
print(f"Certificates passed: {all(c.invariant_holds for c in result.certificates)}")
```

## Motivation

A unit test checks one input. A Lean proof checks all inputs. For accounting invariants — *after any trade, portfolio value equals cash plus mark-to-market positions* — a proof is qualitatively stronger than any finite test suite.

This matters as AI-generated trading code becomes common. A model that produces plausible-looking results can still contain an accounting error that compounds silently over months. Machine-checked proofs eliminate this class of error entirely. The project also explores a development pattern in which the human reviews theorem statements while the AI produces implementations that must discharge them ([docs/human_ai.md](docs/human_ai.md)).

## Roadmap

- **v0.4** — Discrete delta-hedging backtest + Python stack (current)
- **v0.5** — `binomial_replication_cost` theorem: single-period replication cost = risk-neutral price (integer arithmetic)
- **v0.6+** — Multi-period GBM convergence theorem (Mathlib-level real analysis)

## References

- Hull, *Options, Futures, and Other Derivatives*, 9th Global ed. (2014), Tables 19.2 and 19.3
- [Bertsimas, Kogan & Lo (2000)](https://doi.org/10.1016/S0304-405X(99)00048-6), *JFE* 55(2): discrete hedging variance
- [Carr & Madan (1998)](https://ssrn.com/abstract=1691942): realized P&L decomposition via dollar gamma
- [de Moura & Ullrich (2021)](https://doi.org/10.1007/978-3-030-79876-5_37): Lean 4 theorem prover

---

Apache 2.0. See [LICENSE](LICENSE). Research software — not production trading infrastructure.
