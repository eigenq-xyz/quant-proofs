# backtest-proofs

Options delta-hedging backtester with a formally verified accounting kernel.

## What it proves

26 theorems in Lean 4, zero `sorry`:

- **valueIdentity** — portfolio value equals the sum of position values plus cash
- **selfFinancing** — net cash flow from a trade is exactly zero
- **settlement_value_formula** — option settlement changes portfolio value by `qty × (payoff − mark)`, unifying ITM and OTM expiry
- And 23 more in `BacktestProofs.Invariants` and `BacktestProofs.OptionInvariants`

## Architecture

```
backtest-proofs/
├── lean/BacktestProofs/   # Formally verified accounting kernel (Lean 4)
│   ├── Basic.lean         # Portfolio, Position, Trade types with invariant proofs
│   ├── Options.lean       # European options, payoff functions
│   ├── Accounting.lean    # FFI exports (@[export hedge_*])
│   ├── Invariants.lean    # 12 accounting theorems
│   └── OptionInvariants.lean  # 14 settlement theorems
└── python/src/backtest_proofs/   # Python execution layer
    ├── ffi/               # Cython bridge to the Lean kernel
    ├── pricer/            # Black-Scholes pricing and Greeks
    ├── etl/               # WRDS OptionMetrics loader
    ├── simulator/         # Geometric Brownian Motion
    └── backtest/          # Strategy runner and audit trail
```

## Building

```bash
# Lean kernel
cd backtest-proofs/lean && lake exe cache get && lake build

# Python + Cython FFI (requires Lean build first)
cd backtest-proofs/python && uv sync --extra dev
uv run python setup_ffi.py build_ext --inplace

# Tests
uv run pytest -v
```

## Key design decision

All monetary values cross the FFI boundary as **basis-point integers** (`int64`). Lean never operates on floats. A wrong unit is a compile-time error (type mismatch), not a silent numerical discrepancy.
