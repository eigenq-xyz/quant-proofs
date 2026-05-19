# Architectural Decision Records

**Purpose:** Document significant design decisions for future reference and consultation.

**Last Updated:** 2026-05-09
**Status:** Work in Progress (v0.4)

---

## ADR-000: Architecture — Lean for Accounting, Python for ETL

**Status:** ✅ Accepted
**Date:** 2026-01-18
**Implementation:** All milestones

**Context:** Need clear separation of concerns between Lean (verification + implementation) and Python
(data engineering). Must support both historical backtests AND future MCMC simulations
without architectural changes.

**Decision:** Two distinct subprojects with no code duplication:

1. **Accounting Kernel (100% Lean) — Data Source Agnostic**
   - Lean implements ALL portfolio accounting (NAV, trades, cash, positions, settlement)
   - Pure functions: `state + action → new state`
   - No I/O: kernel never touches databases, files, or data sources
   - Lean proves formal invariants about accounting logic
   - Lean code compiled to C via Lake, exposed with `@[export]`
   - Called from Python via Cython FFI (see ADR-006)

2. **Data Pipeline (Python) — Multiple Sources**
   - Historical backtests: Python loads WRDS OptionMetrics and FRED data
   - Simulations: Python generates stochastic paths (GBM)
   - Python emits `StepCertificate` at each backtest step
   - Lean does NOT care about data source — just validates the accounting call

**Rationale:**

1. No duplication: each language does exactly one job
2. Lean strengths: formal verification + compiled performance for critical accounting
3. Python strengths: data wrangling, rich ecosystem (pandas, numpy, scipy)
4. Clear interfaces: FFI for accounting calls, step certificates for audit trail
5. Data source flexibility: kernel works for historical data, simulations, live feeds

**Consequences (positive):**

- Zero duplicate code between Lean and Python
- Accounting kernel is fully formally verified
- Data pipeline has flexibility while maintaining guarantees

**Consequences (negative):**

- FFI complexity (Lean → C → Cython → Python)
- Certificate schema must be kept in sync

**Design Principles (do):**

- Accounting functions are pure: `Portfolio → Trade → Portfolio`
- Accept prices/quantities as inputs (data source is irrelevant to the kernel)
- Keep time-stepping logic in Python (can be historical or simulated)

**Design Principles (don't):**

- Hard-code WRDS-specific logic in Lean
- Embed data loading in accounting kernel
- Assume data frequency (daily vs. intraday vs. tick)

**Consultation Points:**

- FFI performance: Is overhead acceptable for backtest throughput? → Profile in v0.6
- Certificate granularity: Per-row or batched? → Start batched, refine if needed

---

## ADR-001: Scaled Integer Arithmetic for Financial Precision

**Status:** ✅ Accepted
**Date:** 2026-01-18
**Implementation:** v0.2-numeric; **Actual delivery:** v0.4

**Context:** Need exact decimal arithmetic for portfolio accounting (cash, prices, NAV) to enable
formal verification. Lean implements all accounting logic (per ADR-000).

**Decision:** Use scaled integer arithmetic (basis points) as canonical representation.

In Lean — raw `Int` with semantic convention (not a separate type):

```lean
-- $50.25 is represented as 502500 (× 10,000)
def positionValue (qty markPrice : Int) : Int := qty * markPrice
```

In Python — convert at the boundary using `to_bp` / `from_bp`:

```python
# backtest_proofs/pricer/conventions.py
def to_bp(value: float) -> int:
    return round(value * 10_000)

def from_bp(value: int) -> float:
    return value / 10_000
```

FFI boundary: pass integers (basis points), never floats.

**Rationale:**

1. Exactness: no binary floating-point rounding errors
2. Provability: integer arithmetic in Lean is fully decidable and easily proved
3. Performance: fast integer operations vs. `Rat`'s GCD overhead
4. Industry standard: matches Java `BigDecimal`, SQL `DECIMAL`, financial systems
5. Determinism: same inputs always produce identical outputs

**Alternatives Considered:**

- `Rat` everywhere: exact fractions, but denominators grow unpredictably (GCD overhead).
- `Float` everywhere: fast but non-exact, rounding errors accumulate.
- `Real` (Lean type): proof-only, not computable.

**Consultation Points:**

- Is 4 decimal places sufficient for option prices? (Some may need 6)
- How do production systems handle Greeks (float vs. decimal)?

**References:**

- Mathlib: `Data.Rat.Basic`
- [Martin Fowler on Money Pattern](https://martinfowler.com/eaaCatalog/money.html)

---

## ADR-002: JSON Certificates with String-Encoded Decimals

**Status:** ❌ Abandoned — Lean-side verifier not being built
**Date:** 2026-01-18
**Implementation:** N/A. Kept as a record of the design considered and why we chose in-process Python `StepCertificate` instead.

**v0.4 update:** The current backtester uses an in-process `StepCertificate` Python
dataclass (`backtest/audit.py`) rather than JSON certificates. Cross-language JSON
certificates remain planned for a future Lean-side verifier; this ADR describes that
future state.

**Context:** Need interchange format for Python → Lean verification when calling Lean as a
separate process. Must preserve decimal precision.

**Decision:** Use JSON with decimals encoded as strings:

```json
{
  "cash": "105234.5000",
  "price": "123.4567",
  "precision_decimals": 4
}
```

Lean parses strings to `Int` (multiply by 10^precision).

**Rationale:**

- JSON numbers are floats (imprecise)
- String preserves exact decimal representation

**Alternatives:**

- Binary format (MessagePack): more efficient, harder to debug. Defer unless perf critical.
- JSON numbers: loses precision in parsing.

---

## ADR-003: Epsilon-Tolerance Verification (1 Basis Point)

**Status:** ❌ Abandoned — Lean-side verifier not being built
**Date:** 2026-01-18
**Implementation:** N/A. The in-process `StepCertificate` uses exact integer equality; no epsilon is needed.

**v0.4 update:** The Python-level verifier uses exact integer comparison
(`invariant_holds = delta_pv == expected_delta_pv`). The parameterised epsilon
described here is not yet implemented; it describes the future Lean-side verifier.

**Context:** Conversion from float-based pricers to integer-based accounting may introduce
rounding at the `to_bp` boundary.

**Decision:** Lean verifier accepts `epsilon = 0.0001` (1 basis point) tolerance.

**Rationale:**

- Balances exactness with practical numerical stability
- 1bp is negligible for portfolio-level accounting
- Prevents spurious failures from final-digit rounding

**Future Review:**

- v0.11: profile actual errors, tighten to 0.1bp if feasible
- Consider variable epsilon by invariant (strict for cash, looser for Greeks)

---

## ADR-004: Monorepo with Lean + Python + Docs

**Status:** ✅ Accepted
**Date:** 2026-01-18
**Implementation:** v0.1-scaffold

**Context:** Need to co-locate Lean proofs, Python implementation, and JupyterBook docs.

**Decision:** Single repository with subdirectories:

- `lean/` — Lake project
- `python/` — uv-managed package
- `docs/` — JupyterBook (renamed from `book/` in v0.4)
- Root `Makefile` orchestrates all

**Rationale:**

- Easier to keep schemas in sync (same PR updates both)
- Unified CI (test both sides together)
- Atomic changes (Lean + Python + docs in one commit)

**Alternatives:**

- Separate repos: schema sync harder, but cleaner separation. Rejected for v1.0.

---

## ADR-005: Tag-Based Development Milestones

**Status:** ✅ Accepted
**Date:** 2026-01-18
**Implementation:** v0.1-scaffold

**Context:** Need development methodology suitable for solo academic project with incremental
progress.

**Decision:** Use semantic version tags (`v0.X-name`) for milestones. Each tag represents a
complete, demo-able feature. GitHub is the single source of truth.

**Rationale:**

- Academic rigor: each milestone is verifiable
- Flexibility: can adapt based on what proves difficult
- Documentation: git history preserves research process
- Candid: milestones reflect actual progress, not aspirational timelines

---

## ADR-006: Cython FFI as the Lean ↔ Python Bridge

**Status:** ✅ Accepted
**Date:** 2026-03-07
**Implementation:** v0.4

**Context:** Needed a bridge between the Lean-compiled C objects and the Python backtesting
layer. Alternatives were CFFI (C Foreign Function Interface) and ctypes.

**Decision:** Use Cython (`lean_ffi.pyx`) to wrap the Lean C IR directly.

**Rationale:**

- Cython generates explicit C-level wrappers that handle Lean's deterministic reference
  counting (RC) discipline (`lean_inc` / `lean_dec`) correctly.
- CFFI and ctypes don't have a good story for managing RC; manual RC in Python is
  error-prone.
- Cython's `cdef extern from "lean/lean.h"` maps cleanly to the Lean header's types.
- Build integration: `setup.py build_ext --inplace` fits naturally into the Lake + uv
  monorepo workflow.

**Consequences (positive):**

- Correct RC management enforced at the C level
- Full access to Lean's `lean_object *` API

**Consequences (negative):**

- Cython adds a build step; CI must build Lean first, then Cython
- macOS-only for now (libleanrt.a on Linux uses non-PIC TLS)

---

## ADR-007: Extract QuantCore Shared Library

**Status:** ✅ Accepted
**Date:** 2026-05-19
**Implementation:** v0.5

**Context:** `backtest-proofs` and `options-proofs` both needed `EuropeanOption`, `OptionKind`,
`callPayoff`, `putPayoff`, and the 8 payoff theorems. Prior to v0.5 these lived in
`backtest-proofs/lean/BacktestProofs/Options.lean` and `OptionInvariants.lean`. As
`options-proofs` began to develop, duplication became unavoidable.

**Decision:** Extract a `quant-core/` subdir (Lean 4 `QuantCore` namespace; Python `quant_core`
package) as the canonical home for types and theorems that are independent of any specific
backtester or pipeline.

- `quant-core/lean/QuantCore/Option.lean` — types, payoff functions
- `quant-core/lean/QuantCore/OptionInvariants.lean` — 8 payoff theorems
- `quant-core/python/` — `bs_price`, `bs_greeks`, `PricePath`, `simulate_gbm`

`backtest-proofs` and `options-proofs` declare `require «quant-core» from "..."` (path
dependency) in their lakefiles. Python packages declare `quant-core` as a path dependency
in `pyproject.toml`.

`backtest-proofs` retains all settlement logic: `Settlement.lean` (functions) and
`SettlementInvariants.lean` (6 theorems including the crown-jewel `settlement_value_formula`).
These are portfolio-specific and do not belong in the shared library.

**Rationale:**

1. Single definition: `EuropeanOption` has one canonical type, not two that can drift apart.
2. Enables `options-proofs` to build on proven payoff theorems without re-proving them.
3. Cleanly separates "option math" (QuantCore) from "portfolio accounting" (BacktestProofs).
4. Python side mirrors the Lean structure: `quant_core.pricer` / `.simulator` have no
   backtester dependencies, so they can be tested in isolation without building Cython.

**Consequences (positive):**

- Zero duplication: payoff theorems proved once, imported everywhere.
- `options-proofs` starts with 8 proven lemmas for free.
- `quant-core` Python tests run on Ubuntu (no FFI); `backtest-proofs` tests remain macOS-only.

**Consequences (negative):**

- Path dependency means both subdirs must be present on disk; a standalone `lake build`
  of `backtest-proofs` requires `quant-core/lean/` to exist at `../../quant-core/lean`.
- CI matrix grows: one more Lean job, one more Python job.

## Future ADRs (Pending)

The accounting kernel is complete at v0.4. Future ADRs will cover credibility and
validation work rather than proof extensions:

- ADR-008: QuantLib A-B comparison methodology — credibility lever 3
- ADR-009: WRDS stress-run data pipeline — credibility lever 4
- ADR-010: Data Encryption Strategy (git-crypt key rotation)
