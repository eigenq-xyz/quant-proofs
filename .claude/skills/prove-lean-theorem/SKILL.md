---
name: prove-lean-theorem
description: >
  Authoring assistant for Lean 4 proofs. Given a theorem to prove, searches
  mathlib for relevant lemmas, proposes a proof strategy, iterates on the proof
  state, and verifies the result is sorry-free. Use when starting a new theorem
  or stuck on a proof.
paths:
  - "**/*.lean"
allowed-tools: Bash(lake build *) Bash(lake exe *) Read Grep Glob
---

# Lean Proof — Authoring Assistant

## Process

1. **State the theorem in English** before writing Lean — clarity in English predicts clarity in Lean
2. **Search mathlib first** — `exact?`, `apply?`, or search [leanprover-community.github.io/mathlib4_docs](https://leanprover-community.github.io/mathlib4_docs)
3. **Choose mode**: term mode for short equalities/implications; tactic mode for case analysis, induction, or multi-step proofs
4. **Write and iterate** — read the InfoView goal state at each step
5. **Verify**: `lake build` exits 0, zero sorry
6. **Style check**: `/check-lean-style` before opening a PR

## Useful tactics for this codebase

| Tactic | When to use |
|--------|------------|
| `omega` | Integer/natural number arithmetic goals |
| `ring` | Ring/field equalities (no division) |
| `norm_num` | Specific numeric computations |
| `simp [lemma_name]` | Simplification with specific lemmas — never bare `simp` |
| `exact?` | Search for a proof term that closes the goal |
| `apply?` | Search for a lemma to apply |
| `decide` | Decidable propositions on finite types |
| `constructor` | Split a conjunction or build a structure |
| `cases h` / `rcases h with ⟨a, b⟩` | Case analysis and destructuring |
| `linarith` | Linear arithmetic over ordered fields |
| `push_neg` | Push negation inside quantifiers |

## Namespace rule

New theorems go in the correct namespace:
- `backtest-proofs/lean/` → `namespace BacktestProofs`
- `ftap-proofs/` → `namespace FtapProofs`
- `options-proofs/` → `namespace OptionsProofs`
- `mortgage-proofs/lean/` → `namespace MortgageProofs`

## For mathlib candidates (ftap-proofs, options-proofs)

- Use snake_case for theorem names (`no_arbitrage_iff_emm`, not `noArbitrageIffEmm`)
- Every theorem must have a docstring
- No `import Mathlib` — specific imports only
- Run `/check-lean-style` before opening the mathlib PR

## When stuck

1. `exact?` — searches for a proof term
2. `simp?` — shows which simp lemmas would close the goal
3. Split the goal: prove a helper `have h : ... := ...` first
4. Search mathlib docs for the mathematical concept, not the Lean name
