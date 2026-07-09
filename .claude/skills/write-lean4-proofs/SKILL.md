---
name: write-lean4-proofs
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

Zero `sorry` on `main`. Specific imports only. Every exported theorem gets a docstring.
Full detail: REFERENCE.md (naming/tactics/imports), EXAMPLES.md (worked proofs),
ANTI_PATTERNS.md (common mistakes).

## Naming quick reference

| Item | Convention | Example |
|------|-----------|---------|
| Theorems and lemmas | `snake_case` | `portfolio_value_nonneg` |
| Types and structures | `PascalCase` | `Portfolio`, `DecisionRecord` |
| Namespaces | `PascalCase` | `BacktestProofs`, `FtapProofs` |
| Local variables | short `camelCase` or Greek letters | `hPos`, `ε`, `n` |

Targeting a mathlib PR (`ftap-proofs`): follow mathlib naming precisely — the
theorem name encodes the conclusion (`add_comm`, `Finset.sum_empty`). Full scheme
in REFERENCE.md.

## Tactic mode vs term mode

- **Tactic mode** (`by ...`) for all but the simplest proofs.
- **Term mode** for one-liners: a constructor application or direct lemma reference,
  e.g., `exact Nat.zero_add n`.
- Never switch modes silently mid-proof.
- Default to tactic mode — easier to read, diff, extend.

## Docstrings

Every exported theorem needs `/-- ... -/`. Three parts: plain-English statement
(no Lean knowledge required), symbolic statement if non-trivial, where it fits in
the proof architecture. Worked example in EXAMPLES.md #1.

`private` lemmas skip the docstring; a one-line comment still helps.

## The no-sorry rule

`sorry` is **banned on `main`**. It compiles but leaves the theorem unproven — the
FFI-exported kernel in `extensions/hedge-proofs` is not actually verified if it
contains one. CI enforces this: `grep -rn sorry --include="*.lean"`.

Fine as scaffolding on a feature branch:

```lean
theorem hard_lemma : ... := by
  sorry  -- TODO: prove this
```

Remove every `sorry` before opening a PR.

## Import discipline

```lean
-- CORRECT — imports only what you need
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

-- WRONG — triggers full mathlib rebuild, rejected upstream
import Mathlib
```

Confirm the module path in mathlib4 docs first. Common import patterns in REFERENCE.md.

## Pre-proof checklist

1. **Read the statement** — is it true? Check edge cases.
2. **Search mathlib** — `exact?`/`apply?` at the goal, or loogle.lean-lang.org.
3. **Pick the tactic** — integer/nat arithmetic → `omega`; ring equalities → `ring`;
   small decidable cases → `decide`; else `simp [specific_lemmas]`, `linarith`, or build by hand.
4. **Name hypotheses** — `intro h`, `obtain ⟨a, ha⟩ := h`, `rcases`, not anonymous
   `intro` + `rename_i`.
5. **Verify incrementally** — check InfoView after each tactic.

## Module structure

Every `.lean` file: specific imports, then `namespace X`, then docstringed
definitions/theorems, then `end X`. Full template in REFERENCE.md; annotated
examples in EXAMPLES.md.

## Where to put a new theorem or type

| Content | Where it goes |
|---|---|
| Shared across ≥2 subdirs (e.g., a new option type, a utility lemma) | `foundations/quant-core/lean/QuantCore/` |
| Specific to portfolio accounting or FFI | `extensions/hedge-proofs/BacktestProofs/` |
| Pricing theory (CRR, BSM, replication cost) | `foundations/options-proofs/` (imports quant-core) |
| FTAP / no-arbitrage / EMM | `foundations/ftap-proofs/` |
| Mortgage routing invariants | `extensions/mortgage-proofs/lean/MortgageProofs/` |

Default to the leaf project. Move to `quant-core` only once a second project needs it.

## Verifying your work

```bash
# From the subproject root (directory with lakefile.toml)
lake build

# Confirm no sorry
grep -rn sorry --include="*.lean" .
```

Both must pass before pushing.
