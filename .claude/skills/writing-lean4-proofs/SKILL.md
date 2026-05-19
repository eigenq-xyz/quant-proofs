---
name: writing-lean4-proofs
description: >
  Lean 4 proof style and idioms following mathlib conventions.
  Use when writing or reviewing Lean 4 proofs, choosing tactics,
  naming theorems, or writing proof docstrings. Also use when
  adding a new theorem to BacktestProofs, FtapProofs, OptionsProofs,
  or MortgageProofs.
paths:
  - "**/*.lean"
allowed-tools: >
  Bash(lake build *)
  Bash(lake exe *)
  Read
  Grep
  Glob
---

# Writing Lean 4 proofs

## Naming conventions

| Item | Convention | Example |
|------|-----------|---------|
| Theorems and lemmas | `snake_case` | `portfolio_value_nonneg` |
| Types and structures | `PascalCase` | `Portfolio`, `DecisionRecord` |
| Namespaces | `PascalCase` | `BacktestProofs`, `FtapProofs` |
| Local variables | short `camelCase` or Greek letters | `hPos`, `ε`, `n` |
| Simp lemma sets | `@[simp]` attribute on the right lemmas | see REFERENCE.md |

Follow mathlib naming conventions precisely if targeting a mathlib PR (`ftap-proofs`):
the theorem name encodes the conclusion, e.g., `add_comm`, `Finset.sum_empty`.

## Tactic mode vs term mode

- **Tactic mode** (`by ...`): use for all but the simplest proofs.
- **Term mode**: use when the proof is a one-liner constructor application or
  a direct lemma reference, e.g., `exact Nat.zero_add n`.
- Never silently switch between the two mid-proof. If a term-mode proof needs
  a tactic block, use `show goal_type; by tactic` or restructure.

Prefer tactic mode when in doubt — it is easier to read, diff, and extend.

## Docstrings

Every exported theorem needs a `/-- ... -/` docstring. The docstring must:

1. State the theorem in plain English for a reader who does not know Lean.
2. Give the mathematical statement symbolically if it is non-trivial.
3. Note its significance or where it fits in the larger proof architecture.

```lean
/-- The market value of a portfolio equals the sum of its position values.
    Formally: V(Π) = Σᵢ qᵢ · Sᵢ.
    This is the accounting identity that grounds the PnL attribution proofs. -/
theorem valueIdentity (π : Portfolio) : portfolioValue π = π.positions.sum positionValue := by
  ...
```

Internal `private` lemmas do not need docstrings, but a one-line comment helps.

## The no-sorry rule

`sorry` is banned on `main`. It compiles but marks the theorem as unproven, which
means the FFI compiled kernel in `backtest-proofs` is not actually verified.
CI (`grep -rn sorry --include="*.lean"`) enforces this.

On feature branches, `sorry` is fine as scaffolding:

```lean
theorem hard_lemma : ... := by
  sorry  -- TODO: prove this
```

Remove all `sorry` before opening a PR.

## Import discipline

```lean
-- CORRECT — imports only what you need
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

-- WRONG — triggers full mathlib rebuild, rejected upstream
import Mathlib
```

When adding a new import, search mathlib4 docs first to confirm the module path.
See REFERENCE.md for common import patterns.

## Pre-proof checklist

Before writing a proof from scratch:

1. **Read the statement** — is it actually true? Check edge cases.
2. **Search mathlib** — `exact?` or `apply?` at the goal, or search loogle.lean-lang.org.
3. **Pick the right tactic**:
   - Integer/natural number arithmetic → `omega`
   - Ring equalities → `ring`
   - Decidable propositions → `decide` (only for small finite cases)
   - Everything else → `simp [specific_lemmas]`, `linarith`, or build up by hand
4. **Name hypotheses** — use `intro h`, `obtain ⟨a, ha⟩ := h`, `rcases` rather than
   anonymous `intro` followed by `rename_i`.
5. **Verify incrementally** — after each tactic, check the goal in InfoView.

## Module structure

Every `.lean` file in this repo follows this structure:

```lean
-- 1. Imports (specific, not `import Mathlib`)
import Mathlib.Data.Finset.Basic

-- 2. Namespace open
namespace BacktestProofs

-- 3. Exported definitions and theorems (with docstrings)
/-- ... -/
theorem my_theorem : ... := by
  ...

-- 4. End namespace
end BacktestProofs
```

See REFERENCE.md for the full module convention and EXAMPLES.md for annotated examples.

## Where to put a new theorem or type

| Content | Where it goes |
|---|---|
| Shared across ≥2 subdirs (e.g., a new option type, a utility lemma) | `quant-core/lean/QuantCore/` |
| Specific to portfolio accounting or FFI | `backtest-proofs/lean/BacktestProofs/` |
| Pricing theory (CRR, BSM, replication cost) | `options-proofs/` (imports quant-core) |
| FTAP / no-arbitrage / EMM | `ftap-proofs/` |
| Mortgage routing invariants | `mortgage-proofs/lean/MortgageProofs/` |

When in doubt: start in the leaf project. Move to `quant-core` only when a second project actually needs it.

## Verifying your work

After writing or editing a proof:

```bash
# From the subproject root (directory with lakefile.toml)
lake build

# Confirm no sorry
grep -rn sorry --include="*.lean" .
```

Both must succeed before pushing.
