# Development Guide

Deep technical reference for verified-options-backtest development.

---

## Table of Contents

1. [Makefile Reference](#makefile-reference)
2. [Lean Project Structure](#lean-project-structure)
3. [Python Package Architecture](#python-package-architecture)
4. [Numeric Precision Pattern](#numeric-precision-pattern)
5. [Certificate Schema Evolution](#certificate-schema-evolution)
6. [Adding New Invariants](#adding-new-invariants)
7. [CI Pipeline Details](#ci-pipeline-details)
8. [Performance Profiling](#performance-profiling)
9. [ADR Template](#adr-template)

---

## Makefile Reference

### Root Makefile

All targets orchestrate operations across `lean/` and `python/` subdirectories.

| Target | Description | Dependencies |
| --- | --- | --- |
| `make help` | Show available targets | None |
| `make setup` | Install Lean + Python deps | elan, uv |
| `make build` | Compile proofs + Python pkg | setup |
| `make test` | Run all tests | build |
| `make lint` | Lint + typecheck Python | setup |
| `make clean` | Remove build artifacts | None |
| `make docs-build` | Build JupyterBook | setup |
| `make docs-serve` | Serve docs on :8000 | docs-build |
| `make integration` | Run cross-language test | build |
| `make watch-lean` | Auto-rebuild Lean | setup |
| `make ci-local` | Simulate CI with `act` | act installed |

### Lean Makefile (`lean/Makefile`)

| Target | Command | Notes |
| --- | --- | --- |
| `setup` | Install elan | Downloads Lean toolchain |
| `build` | `lake build` | Compiles all Lean files |
| `test` | `lake build OptionHedge.Tests.UnitTests` | Runs test suites |
| `clean` | `lake clean` | Removes build/ |
| `watch` | `lake build --watch` | Continuous compilation |

### Python Makefile (`python/Makefile`)

| Target | Command | Notes |
| --- | --- | --- |
| `setup` | `uv sync` | Installs from uv.lock |
| `build` | `uv build` | Creates wheel/sdist |
| `test` | `uv run pytest` | With coverage |
| `lint` | `uv run ruff check` | Code quality |
| `typecheck` | `uv run mypy` | Type validation |
| `format` | `uv run ruff format` | Auto-format code |
| `clean` | Remove caches | .venv, .pytest_cache, etc. |

---

## Lean Project Structure

### Lean Directory Layout

```text
lean/
├── lakefile.lean          # Lake build configuration
├── lean-toolchain         # Lean version pin (v4.27.0-rc1)
├── Makefile               # Lean-specific targets
└── OptionHedge/
    ├── Basic.lean         # AssetId, Position (markPrice_pos), Portfolio (value_valid),
    │                      # Trade (executionPrice_pos, fee_nonneg), applyTrade
    ├── Accounting.lean    # @[export hedge_*] FFI symbols only
    ├── Invariants.lean    # 12 accounting theorems (valueIdentity → applyTrade_wellFormed)
    ├── Options.lean       # OptionKind, EuropeanOption (strike_pos), payoff functions,
    │                      # settlement dispatcher
    ├── OptionInvariants.lean  # 14 option theorems (callPayoff_nonneg → settlement_value_formula)
    └── Tests/
        └── UnitTests.lean # Concrete native_decide examples
```

### lakefile.lean Structure

```lean
import Lake
open Lake DSL

package «verified-options-backtest» where
  -- Package configuration

lean_lib OptionHedge where
  -- Library: all OptionHedge.* modules

@[default_target]
lean_lib OptionHedge
```

The `OptionHedge` namespace is the module hierarchy name (not the package name). All imports
use `import OptionHedge.Basic`, `import OptionHedge.Invariants`, etc.

### Proof Workflow

Proofs live inline in `Invariants.lean` and `OptionInvariants.lean` — there is no separate
`Proofs/` directory. The workflow is:

1. **State theorem** in `Invariants.lean`:

   ```lean
   theorem valueIdentity (p : Portfolio) :
       p.portfolioValue = p.cash + sumPositionValues p.positions :=
     p.value_valid
   ```

2. **Prove inline** using `rfl` / `simp` / `omega` / `native_decide` as appropriate.
   `rfl` suffices when the equality is definitional; `omega` handles linear integer
   arithmetic; `simp` with lemmas for list operations.

3. **Add concrete test** to `Tests/UnitTests.lean`:

   ```lean
   import OptionHedge.Accounting
   example : some_computable_expression = expected := by native_decide
   ```

The zero-`sorry` invariant is enforced by CI: `lake build` fails if any `sorry` is present.

---

## Python Package Architecture

### Python Directory Layout

```text
python/
├── pyproject.toml              # Project metadata + dependencies
├── uv.lock                     # Locked dependency versions
├── .python-version             # Python version (3.12)
├── Makefile                    # Python-specific targets
├── setup_ffi.py                # Cython extension build script
├── src/
│   └── verified_options_backtest/
│       ├── __init__.py
│       ├── pricer/
│       │   ├── black_scholes.py   # bs_price, bs_greeks (scipy)
│       │   └── conventions.py     # to_bp, from_bp
│       ├── etl/
│       │   ├── wrds_loader.py     # WRDS OptionMetrics CSV → DataFrame
│       │   └── data_types.py      # Pydantic models for raw data
│       ├── simulator/
│       │   └── gbm.py             # Seeded GBM path generator
│       ├── backtest/
│       │   ├── runner.py          # HedgingStrategy Protocol, SingleLegStrategy,
│       │   │                      # PortfolioStrategy, run_delta_hedge
│       │   ├── audit.py           # StepCertificate dataclass + emission
│       │   ├── data_types.py      # BacktestResult, HedgeStep
│       │   └── scenarios.py       # Hull 19.2/19.3 reference scenarios
│       └── ffi/
│           ├── lean_ffi.pyx       # Cython declarations against Lean C headers
│           └── __init__.py        # Loads compiled lean_ffi.so; re-exports apply_trade,
│                                  # settle_option, portfolio_value
└── tests/
    ├── conftest.py            # pytest fixtures
    ├── test_ffi.py            # FFI round-trip tests
    ├── test_pricer.py         # BS price/greeks vs. reference vectors
    ├── test_backtest.py       # Hull 19.2 replication, real-data, holdout
    ├── test_audit.py          # StepCertificate emission
    ├── test_etl.py            # WRDS CSV loading + filtering
    └── test_edge_cases.py     # Boundary conditions
```

### Cython FFI

The Cython extension `lean_ffi.pyx` is compiled and live — there is no Python stub fallback.
It wraps the `@[export hedge_*]` symbols compiled from Lean via `libleanrt` and `libuv`.

Build the extension:

```bash
cd python
uv run python setup_ffi.py build_ext --inplace
```

The compiled `lean_ffi.so` lands in `src/verified_options_backtest/ffi/`. CI builds Lean
first (`make build-lean`), then the Cython extension, then runs Python tests.

---

## Numeric Precision Pattern

All monetary values use **basis points** (×10,000) as `Int`. Floats are computed in Python
(BS pricing, Greeks) and converted at the FFI boundary.

```python
# verified_options_backtest/pricer/conventions.py
def to_bp(value: float) -> int:
    """Convert a dollar float to basis-point integer (×10,000)."""
    return round(value * 10_000)

def from_bp(value: int) -> float:
    """Convert a basis-point integer back to a dollar float."""
    return value / 10_000
```

The FFI functions only accept and return `int` (basis points). Lean never receives floats.

```python
from verified_options_backtest.pricer.conventions import to_bp, from_bp
from verified_options_backtest.ffi import apply_trade

result = apply_trade(
    cash=to_bp(100_000.00),
    positions=[],
    asset_id="SPY",
    delta_quantity=100,
    execution_price=to_bp(450.25),
    fee=to_bp(1.00),
)
nav = from_bp(result["portfolio_value"])  # back to dollars
```

---

## Certificate Schema Evolution

*Planned for v0.5+. See ADR-002 in [DECISIONS.md](DECISIONS.md).*

The v0.4 backtester uses an in-process `StepCertificate` Python dataclass
(`backtest/audit.py`) rather than JSON certificates. Cross-language JSON certificate
interchange with a Lean-side verifier is the planned v0.5 feature.

When JSON certificates ship, versioning will follow `major.minor` (e.g., "1.0", "1.1").
Major bumps are breaking; minor bumps add optional fields only.

---

## Adding New Invariants

Complete workflow for adding a new formally verified invariant.

### Step 1: Document Rationale

Add to [DECISIONS.md](DECISIONS.md) or a comment in `Invariants.lean` explaining why
the invariant matters and what economic property it captures.

### Step 2: Define Lean Theorem

In `OptionHedge/Invariants.lean` (or `OptionInvariants.lean` for options-specific theorems):

```lean
/-- All transaction fees must be non-negative -/
theorem feeNonNegative (t : Trade) : 0 ≤ t.fee :=
  t.fee_nonneg
```

### Step 3: Implement Proof Inline

The proof lives immediately after the theorem statement. Use `omega` for linear integer
goals, `simp` for definitional unfolding, `rfl` when the goal is definitionally equal,
and `cases` for algebraic decomposition.

```lean
theorem cashUpdateCorrect (p : Portfolio) (t : Trade) :
    (applyTrade p t).cash = p.cash - t.executionPrice * t.deltaQuantity - t.fee := by
  simp [applyTrade]
```

### Step 4: Add Concrete Test

In `Tests/UnitTests.lean`:

```lean
import OptionHedge.Accounting

-- Verify at a concrete input via native_decide
example : (some concrete expression) = expected_value := by native_decide
```

### Step 5: Test in Python

If the invariant has a Python-observable consequence, add a test in `tests/test_ffi.py`
or `tests/test_backtest.py`:

```python
def test_fee_nonneg_enforced():
    """Lean kernel refuses negative fees at the type level."""
    # The proof field fee_nonneg on Trade makes this a compile-time guarantee;
    # the FFI accepts only valid (non-negative) fee values.
    result = apply_trade(cash=to_bp(10_000), positions=[], asset_id="SPY",
                         delta_quantity=1, execution_price=to_bp(100), fee=to_bp(0))
    assert result["portfolio_value"] >= 0
```

---

## CI Pipeline Details

Refer to the actual workflow files in `.github/workflows/` for authoritative YAML.
The workflows in summary:

**`.github/workflows/lean.yml`** — runs on every push. Installs elan, caches
`~/.elan` and `lean/build` by `lakefile.lean` hash, runs `lake build`. Any `sorry`
causes a compile error (CI fails automatically). Checks `grep -r "sorry" lean/OptionHedge`
count is zero.

**`.github/workflows/python.yml`** — runs on every push. Installs uv, builds the Lean
library and Cython extension, then runs `uv run pytest --cov=verified_options_backtest
--cov-fail-under=80` and `uv run mypy src/verified_options_backtest`. Matrix covers
`ubuntu-latest` and `macos-latest`.

**`.github/workflows/docs.yml`** — runs on pushes to `main`. Builds JupyterBook
(`make docs-build`) and deploys to GitHub Pages.

### Local CI Simulation

```bash
# Install act (GitHub Actions local runner)
brew install act  # macOS

# Run specific job
act -j lean-build

# Run all jobs
act
```

---

## Performance Profiling

### Python Profiling

```python
import cProfile
import pstats
from verified_options_backtest.backtest.runner import run_delta_hedge
from verified_options_backtest.backtest.scenarios import hull_192_path, HULL_192_K

def profile_backtest():
    profiler = cProfile.Profile()
    profiler.enable()
    run_delta_hedge(path=hull_192_path(), K=HULL_192_K, r=0.05,
                    sigma=0.20, n_contracts=1)
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats("cumtime")
    stats.print_stats(20)
```

```bash
uv run python -c "from tests.test_performance import profile_backtest; profile_backtest()"
```

### Benchmark Targets

| Component | Target | Notes |
| --- | --- | --- |
| FFI call (`apply_trade`) | < 1 ms | Profile in v0.6 |
| BS pricing (1 option) | < 0.1 ms | Already fast via scipy |
| Backtest (20 weekly steps) | < 1 s | Hull 19.2 scale |
| Full GBM run (500 paths × 20 steps) | < 60 s | Monte Carlo convergence test |

---

## ADR Template

For new architectural decisions, add to [DECISIONS.md](DECISIONS.md):

```markdown
## ADR-XXX: [Title]

**Status:** ✅ Accepted / 🔄 Proposed / ❌ Rejected
**Date:** YYYY-MM-DD
**Implementation:** vX.Y

**Context:** [One-paragraph description of the problem and constraints.]

**Decision:** [Describe the chosen solution.]

**Rationale:**

1. [Reason 1]
2. [Reason 2]

**Alternatives:**

- [Alternative A]: [Why rejected]
- [Alternative B]: [Why rejected]
```

---

## Debugging Tips

### Lean Debugging

```lean
-- Show type of expression
#check applyTrade

-- Evaluate at concrete inputs
#eval applyTrade somePortfolio someTrade

-- Use sorry during exploration, replace before committing
theorem myTheorem : ... := by
  sorry  -- TODO: prove using omega after unfolding applyTrade
```

### Python Debugging

```python
# Use ipdb for interactive debugging
import ipdb; ipdb.set_trace()

# Or use pytest with pdb
# pytest --pdb  # Drop into debugger on failure

# Inspect basis-point values
from verified_options_backtest.pricer.conventions import from_bp
print(from_bp(result["portfolio_value"]))
```

---

## Further Reading

- [Lean 4 Manual](https://leanprover.github.io/lean4/doc/)
- [Mathlib4 Docs](https://leanprover-community.github.io/mathlib4_docs/)
- [uv Documentation](https://docs.astral.sh/uv/)
- [JupyterBook Guide](https://jupyterbook.org/)

---

**Last Updated:** 2026-05-09 (v0.4)
