---
name: verify-property
description: >
  Level 3 verification: hypothesis property-based tests verifying mathematical
  properties across thousands of random inputs. Bridges the gap between Lean
  proofs (exact arithmetic) and Python execution (floating-point). Runs after
  verify-unit passes.
paths:
  - "**/*.py"
  - "tests/property/**"
allowed-tools: Bash(uv run pytest *)
---

# Verify Property — Level 3

Property tests check mathematical guarantees across arbitrary inputs, not just unit-test fixtures.

## Command (when infrastructure exists)

```bash
uv run pytest tests/property/ -v --hypothesis-seed=0
```

## Target properties

### BacktestProofs (extensions/hedge-proofs — Lean only, no Python bindings exist yet; these
properties are proved directly as Lean theorems in `Invariants.lean`/`SettlementInvariants.lean`,
not exercised via Hypothesis today)

- **valueIdentity**: `portfolio_value(cash, positions) == cash + sum(qty * price for each position)` — verified for any integer cash and any list of positions
- **selfFinancing**: applying a trade then reversing it returns the exact same portfolio value
- **settlementBounds**: option payoff is non-negative for any spot price

### OptionsProofs (options-proofs — when Python bindings exist)

- **putCallParity**: `C - P ≈ S - K * exp(-r*T)` within floating-point tolerance for any (S > 0, K > 0, r, T > 0, sigma > 0)
- **callMonotonicity**: call price is non-decreasing in S and non-increasing in K

### MortgageProofs (mortgage-proofs)

- **traceInvariant**: any routing decision that passes Python validators also passes `lake exe verify-trace`
- **dtiBound**: any application with DTI > threshold is never routed to underwriter without a compliance flag

## Interpreting a falsifying example

Hypothesis outputs the minimal input that breaks the property:
```
Falsifying example: portfolio_value(cash=-1, positions=[...])
```
This is the bridge to the Lean proof. A falsifying input means either (a) the Python
implementation has a bug relative to the Lean model, or (b) the property test is
over-specified. Check the Lean theorem first.

## Current status

`tests/property/` does not exist yet. Create it before running this skill.
Implementation priority order:
1. `tests/property/test_backtest_properties.py` — valueIdentity, selfFinancing (needs Python
   bindings for `extensions/hedge-proofs`, which do not exist yet — only the Lean `@[export]`
   FFI surface in `BacktestProofs/Accounting.lean` is defined today)
2. `tests/property/test_mortgage_trace.py` — traceInvariant
3. `tests/property/test_options_parity.py` — putCallParity (needs OptionsProofs Python bindings)
