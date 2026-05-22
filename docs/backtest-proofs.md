# backtest-proofs

Options delta-hedging backtester with a Lean 4 accounting module and proof-checked invariants.

## What it proves

27 theorems total across BacktestProofs and QuantCore, zero `sorry`:

- **valueIdentity** — portfolio value equals the sum of position values plus cash
- **selfFinancing** — net cash flow from a trade is exactly zero
- **settlement_value_formula** — option settlement changes portfolio value by `qty × (payoff − mark)`, unifying ITM and OTM expiry
- 16 more in `BacktestProofs.Invariants` (13) and `BacktestProofs.SettlementInvariants` (6 supporting `settlement_value_formula`)
- 8 payoff theorems in `QuantCore.OptionInvariants` (non-negativity, ITM/OTM characterization, integer payoff identity)

## Architecture

```
quant-core/lean/QuantCore/         # Shared option types and payoff theorems
├── Option.lean                    # EuropeanOption, callPayoff, putPayoff, optionPayoff
└── OptionInvariants.lean          # 8 payoff theorems

backtest-proofs/
├── lean/BacktestProofs/           # Accounting module (Lean 4)
│   ├── Basic.lean                 # Portfolio, Position, Trade types with invariant proofs
│   ├── Accounting.lean            # FFI exports (@[export hedge_*])
│   ├── Invariants.lean            # 12 accounting theorems
│   ├── Settlement.lean            # Settlement functions (ITM trade / OTM abandon)
│   └── SettlementInvariants.lean  # 6 settlement theorems
└── python/src/backtest_proofs/    # Python execution layer
    ├── ffi/                       # Cython bridge to the Lean accounting module
    ├── pricer/                    # Re-exports quant_core.pricer (Black-Scholes + Greeks)
    ├── etl/                       # WRDS OptionMetrics loader
    ├── simulator/                 # Re-exports quant_core.simulator (GBM)
    └── backtest/                  # Strategy runner and audit trail
```

## Building

```bash
# Lean accounting module
cd backtest-proofs/lean && lake exe cache get && lake build

# Python + Cython FFI (requires Lean build first)
cd backtest-proofs/python && uv sync --extra dev
uv run python setup_ffi.py build_ext --inplace

# Tests
uv run pytest -v
```

## Key design decision

All monetary values cross the FFI boundary as **basis-point integers** (`int64`). Lean never operates on floats. A wrong unit is a compile-time error (type mismatch), not a silent numerical discrepancy.
