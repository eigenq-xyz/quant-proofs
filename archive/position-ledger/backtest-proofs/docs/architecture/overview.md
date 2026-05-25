# Architecture Overview

**Current version**: v0.5-quant-core

## Core Principle

**Lean** and **Python** have distinct, non-overlapping responsibilities:

- **Lean**: Accounting module + formal proofs (pure functions, data-source agnostic)
- **Python**: Black-Scholes pricing, GBM simulation, backtest runner, ETL, certificates
- **Cython FFI**: Bridge between the two (compiled Lean → C → Cython → Python)

## System Diagram

```text
quant_core (Python: Black-Scholes, GBM, PricePath)
    │
    └─▶ backtest_proofs.pricer / .simulator  (thin re-exports)

Python (ETL, simulation, backtest runner)
    │
    ├─ bs_price / bs_greeks  (via quant_core — float → int via to_bp)
    ├─ simulate_gbm          (via quant_core — seeded GBM path generator)
    ├─ run_delta_hedge        (source-agnostic backtest runner)
    │
    └─▶ Lean accounting module (via compiled Cython FFI)
            │
            ├─ hedge_apply_trade      (applyTrade + valueUpdateFormula)
            ├─ hedge_settle_option    (applySettlement + settlement_value_formula)
            └─ hedge_portfolio_value  (O(1) field read — value_valid proof)
```

## Lean Module Dependency Graph

```text
quant-core/lean/QuantCore/
    Option.lean             — EuropeanOption, AssetId, callPayoff, putPayoff, optionPayoff
    OptionInvariants.lean   — 8 payoff theorems
        │
        └─▶ backtest-proofs/lean/BacktestProofs/
                Basic.lean              — Portfolio, Position, Trade (imports QuantCore.Option)
                    └─▶ Accounting.lean         — FFI exports (hedge_*)
                    └─▶ Invariants.lean         — 12 accounting theorems
                    └─▶ Settlement.lean          — settlementITM, abandonPosition, applySettlement
                            └─▶ SettlementInvariants.lean — 6 settlement theorems
```

## Numeric Precision

All monetary values use **basis points** (×10,000) as `Int`:

```python
to_bp(50.25) = 502_500
from_bp(502_500) = 50.25
```

Floats are computed in Python (BS pricing, Greeks), converted to integers at the boundary,
and the integer is the only thing that crosses into the Lean accounting module. Lean never operates on floats.

## FFI Boundary

The Cython extension `backtest_proofs/ffi/lean_ffi.pyx` is the live FFI path.
It loads `libleanrt` + `libuv`, manages Lean's deterministic reference counting, and wraps
each `@[export hedge_*]` symbol. Key functions exposed to Python:

```python
# python/src/backtest_proofs/ffi/__init__.py  (imports from lean_ffi.so)

apply_trade(cash, positions, asset_id, delta_quantity, execution_price, fee)
    # returns: {"cash": int, "positions": list[dict], "portfolio_value": int}

settle_option(cash, positions, option_asset_id, option_kind, strike_bp, spot_bp)
    # returns: {"cash": int, "positions": list[dict], "portfolio_value": int}
```

All values are basis-point integers (×10,000). Lean never receives floats.

## Step Certificates

At each backtest step, the runner emits a `StepCertificate`:

```python
@dataclass(frozen=True)
class StepCertificate:
    step: int
    portfolio_value_before: int   # basis points
    portfolio_value_after: int    # basis points
    delta_pv: int                 # after − before
    expected_delta_pv: int        # qty × (exec_price − mark) − fee
    invariant_holds: bool         # delta_pv == expected_delta_pv
```

`invariant_holds = False` raises `ValueError` immediately; the runner cannot continue
with a violated accounting invariant.

## Interest Accrual

Interest accrual is handled in Python only:

```python
def _apply_interest(portfolio, rate_per_step):
    new_cash = int(old_cash * rate_per_step) + old_cash
    ...
```

The Lean accounting module is stateless about time. `valueUpdateFormula` certifies individual
trades, not time evolution. Interest is a between-trade event and never belongs in
the module.

## Key Design Decisions

See [DECISIONS.md](https://github.com/eigenq-xyz/backtest-proofs/blob/main/DECISIONS.md) for full ADR documentation:

- **ADR-000**: Lean for accounting, Python for ETL, data-source agnostic module
- **ADR-001**: Scaled integer arithmetic (basis points) instead of floats or rationals
- **ADR-002**: JSON certificates with string-encoded decimals
- **ADR-004**: Monorepo structure with root Makefile orchestration
