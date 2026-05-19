# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Formally verified options portfolio backtesting and hedging engine. Lean 4 implements the
accounting kernel (portfolio value, trades, option settlement, proofs). Python handles data
engineering, pricing, simulation, and orchestration. They communicate via compiled Cython FFI.
Currently at v0.4 (accounting kernel + option settlement + Cython FFI + delta-hedging
backtester + BS pricer/Greeks in Python).

## Build & Test Commands

### Full project (from repo root)

- `make setup` — install Lean (elan) + Python (uv) dependencies
- `make build` — build Lean proofs + Python package
- `make test` — run all Lean + Python tests
- `make lint` — ruff lint + mypy typecheck on Python
- `make clean` — remove all build artifacts

### Lean only (from `lean/` or via root)

- `lake build` — build Lean library and proofs
- `lake build OptionHedge.Tests.UnitTests` — run Lean tests
- `lake build --watch` — rebuild on file changes

### Python only (from `python/`)

- `uv run pytest -v --cov=verified_options_backtest --cov-report=term-missing` — run tests with coverage
- `uv run ruff check src/ tests/` — lint
- `uv run mypy src/` — typecheck (strict mode)
- `uv run ruff format src/ tests/` — format code
- Run a single test: `uv run pytest tests/test_ffi.py -v` or `uv run pytest -k test_name`

## Architecture

### Dual-language monorepo

```text
lean/           — Lean 4 accounting kernel (Lake build system, Mathlib dependency)
python/         — Python package managed by uv (src/verified_options_backtest/)
integration/    — Cross-language integration tests
docs/           — JupyterBook documentation site (builds to GitHub Pages)
notebooks/      — standalone executable notebooks (demo)
data/           — Encrypted market data (git-crypt)
```

### Core design: no code duplication

- **Lean** implements all accounting logic as pure functions (`Portfolio → Trade → Portfolio`).
  The kernel is data-source agnostic — it never touches I/O or makes assumptions about where
  data came from.
- **Python** handles data loading (WRDS, FRED), Black-Scholes pricing, simulation, backtest
  orchestration, and step-certificate emission.
- **Cython FFI** bridges the two: Lean compiles to C via Lake (`@[export]`), Cython wraps the
  C functions, Python calls them. The Cython extension is compiled and live; `ffi/__init__.py`
  pre-loads `libleanrt`/`libuv` before importing `lean_ffi.so`.
- **Basis-point integers** are the only numeric type that crosses the FFI boundary; Lean never
  operates on floats.

### Lean types and functions (`lean/OptionHedge/`)

- `Basic.lean` — core types: `AssetId`, `Position` (with `markPrice_pos` proof),
  `Portfolio` (with `value_valid` proof), `Trade` (with `executionPrice_pos`, `fee_nonneg`),
  `applyTrade`, helpers. Smart constructor `Portfolio.mk'` discharges proof via `rfl`.
- `Accounting.lean` — FFI exports only (`@[export hedge_*]`): `hedge_portfolio_value` (O(1)
  field read), `hedge_mk_portfolio`, `hedge_position_value`, `hedge_sum_position_values`,
  `hedge_get_position`, `hedge_apply_trade`, `hedge_option_payoff`, `hedge_settle_option`.
- `Invariants.lean` — 12 accounting theorems: `valueIdentity`, `mk'_value`, `empty_value`,
  `position_value_def`, `pricesPositive`, `feeNonNegative`, `cashUpdateCorrect`,
  `quantityConservation`, `valueUpdateFormula`, `selfFinancing`, `empty_wellFormed`,
  `applyTrade_wellFormed`.
- `Options.lean` — `OptionKind`, `EuropeanOption` (with `strike_pos`), `callPayoff`,
  `putPayoff`, `optionPayoff`, settlement dispatcher.
- `OptionInvariants.lean` — 14 settlement theorems including `settlement_value_formula`
  (unifies ITM/OTM expiry: ΔPV = qty × (payoff − mark)).
- `Tests/UnitTests.lean` — concrete computation tests via `native_decide`.

### Python package (`python/src/verified_options_backtest/`)

- `pricer/black_scholes.py` — `bs_price`, `bs_greeks` (Black-Scholes pricing + Greeks via
  scipy); `pricer/conventions.py` — `to_bp`, `from_bp` (float ↔ basis-point conversion).
- `etl/wrds_loader.py` — WRDS OptionMetrics loader; `etl/data_types.py` — Pydantic models.
- `simulator/gbm.py` — seeded Geometric Brownian Motion path generator.
- `backtest/runner.py` — `HedgingStrategy` Protocol, `SingleLegStrategy`,
  `PortfolioStrategy`, `run_delta_hedge`, `run_portfolio_hedge`;
  `backtest/audit.py` — `StepCertificate` emission and verification;
  `backtest/scenarios.py` — Hull Table 19.2 / 19.3 reference scenarios.
- `ffi/lean_ffi.pyx` — compiled Cython FFI against Lean C headers (`hedge_*` symbols);
  `ffi/__init__.py` — pre-loads `libleanrt`/`libuv`, then imports the `.so` extension.

## Key Conventions

- **Numeric precision**: All monetary values use **basis points** (×10,000) as `Int`.
  Example: $50.25 = 502,500. Never pass floats across the FFI boundary.
- **Lean toolchain**: v4.27.0-rc1 (pinned in `lean/lean-toolchain`, managed by elan).
- **Python**: 3.12+, managed by uv. Strict mypy, ruff for linting/formatting.
- **Line length**: 79 characters for Python (ruff config in `pyproject.toml`).
- **Ruff rules**: E, W, F, I, B, C4, UP with double-quote style.
- **Pre-commit hooks**: trailing whitespace, ruff, mypy, markdownlint, lean build, pytest.
- **Milestone branches**: `feat/v0.X-name` pattern, PRs to `main`.

## Decision Records

Major design decisions are documented in `DECISIONS.md` with full rationale. Key ADRs:

- **ADR-000**: Lean for accounting, Python for ETL, data-source agnostic kernel
- **ADR-001**: Scaled integer arithmetic (basis points) instead of floats or rationals
- **ADR-002**: JSON certificates with string-encoded decimals (future cross-language verifier)
- **ADR-004**: Monorepo structure with root Makefile orchestration
- **ADR-006**: Cython FFI as the Lean ↔ Python bridge (chose Cython for explicit RC wrappers)
