# Writing Lean 4 proofs — Reference

## Naming conventions (detailed)

### Theorem and lemma names

mathlib uses a systematic naming scheme where the theorem name encodes the conclusion.
For `ftap-proofs` (targeting mathlib), follow this precisely.
For `backtest-proofs`, `options-proofs`, `mortgage-proofs`, follow it as a guide.

| Pattern | Example name | Meaning |
|---------|-------------|---------|
| `Type.property` | `Finset.sum_empty` | Property of a type |
| `op_comm` | `add_comm`, `mul_comm` | Commutativity of operation |
| `op_assoc` | `add_assoc` | Associativity |
| `thing_nonneg` | `portfolio_value_nonneg` | Non-negativity |
| `thing_eq_thing` | `value_eq_sum_positions` | Equality between two things |
| `thing_of_thing` | `arbitrage_of_neg_price` | A follows from B |
| `not_thing_of_thing` | `not_arb_of_risk_neutral` | Negation from condition |

Auxiliary lemmas that should not be exported use `private`:

```lean
private lemma sum_split_helper (s : Finset α) : ... := by ...
```

### Structure and type naming

```lean
structure Portfolio where
  positions : Finset Position
  cash : ℝ

structure RiskMeasure where
  value : ℝ
  hNonneg : 0 ≤ value

inductive Decision where
  | approve : Decision
  | deny    : Decision
  | refer   : Decision
```

## Full tactic reference

### Closing tactics (finish the goal)

| Tactic | Goal type | Notes |
|--------|-----------|-------|
| `rfl` | `a = a` | Exact reflexivity, definitionally equal |
| `ring` | Any ring equality | Handles commutativity, distributivity automatically |
| `omega` | Linear arithmetic over ℤ/ℕ | Faster than `linarith` for pure integer goals |
| `linarith` | Linear arithmetic over ordered field | Can use named hypotheses |
| `norm_num` | Numeric computations | `2 ^ 10 = 1024`, `(3 : ℝ) / 4 > 0` |
| `decide` | Decidable proposition | Only for small finite cases; see ANTI_PATTERNS.md |
| `tauto` | Propositional tautology | Classical logic |
| `positivity` | `0 < e` or `0 ≤ e` | Structural positivity reasoning |
| `exact h` | Goal matches hypothesis `h` | Direct proof term |
| `exact?` | Any | Searches for a proof term; use interactively |

### Simplification tactics

| Tactic | Use |
|--------|-----|
| `simp [h1, h2]` | Simplify using named lemmas — always name them |
| `simp only [h1, h2]` | Stricter simp, only uses the listed lemmas |
| `simp?` | Find which lemmas simp would use; copy result to `simp only [...]` |
| `simp_all` | Simplifies everything, including hypotheses — use sparingly |
| `push_simp` | Push simp lemmas into subterms |
| `field_simp` | Clear denominators in field expressions |
| `ring_nf` | Normalize ring expressions without closing the goal |

### Structural tactics

| Tactic | Use |
|--------|-----|
| `intro h` | Introduce a hypothesis or variable |
| `intros` | Introduce multiple at once |
| `constructor` | Split `And` or `Iff` goal into two subgoals |
| `left` / `right` | Choose branch of `Or` goal |
| `cases h` | Case-split on `h : A ∨ B` or an inductive type |
| `rcases h with ⟨a, b⟩` | Destruct products and existentials with pattern |
| `obtain ⟨a, ha⟩ := h` | Destruct and name components |
| `induction n` | Induction on natural numbers or inductives |
| `induction n with \| zero => ... \| succ n ih => ...` | Named induction cases |
| `ext x` | Extensionality: `f = g ↔ ∀ x, f x = g x` |
| `funext x` | Function extensionality |
| `apply h` | Apply lemma `h`, unifying conclusion with goal |
| `apply?` | Search for applicable lemmas; use interactively |
| `refine ⟨?_, ?_⟩` | Provide partial proof term with holes |
| `use a` | Provide witness for `∃ x, P x` |
| `exists a` | Same as `use a` |

### Negation and classical tactics

| Tactic | Use |
|--------|-----|
| `push_neg` | `¬ ∀ x, P x` → `∃ x, ¬ P x` |
| `contrapose` | Switch to contrapositive |
| `contrapose!` | Contrapose and then push_neg |
| `by_contra h` | Introduce `h : ¬ goal`, goal becomes `False` |
| `by_cases h : P` | Case split on decidable `P` |
| `exfalso` | Change goal to `False` when you have a contradiction |

### Arithmetic helpers

| Tactic | Use |
|--------|-----|
| `gcongr` | `a ≤ b → f a ≤ f b` style congruence for inequalities |
| `nlinarith` | Nonlinear arithmetic (polynomial inequalities) |
| `norm_cast` | Normalize coercions (`↑n`, `(n : ℝ)`) |
| `push_cast` | Push coercions inward |
| `rw [h]` | Rewrite goal using `h : a = b` |
| `rw [← h]` | Rewrite right-to-left |
| `conv => ...` | Targeted rewriting inside a subterm |

## Module structure (full template)

```lean
/-!
# Module title

One-paragraph description of what this module proves.
-/

-- Imports: specific, never `import Mathlib`
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

-- Open frequently-used namespaces (sparingly)
open BigOperators

namespace BacktestProofs   -- or FtapProofs, OptionsProofs, MortgageProofs

/-! ## Section heading (optional for large files) -/

/-- One-sentence English statement of what this definition captures. -/
def myDef : Type := ...

/-- English statement of the theorem.
    Mathematical statement: P ↔ Q.
    Where it fits: this is used by `largerTheorem` to establish ... -/
theorem myTheorem (h : Hypothesis) : Conclusion := by
  ...

end BacktestProofs
```

The `/-! ... -/` module docstring (at the top) and section docstrings are optional for
library files but required for files that will be submitted as mathlib PRs.

## Writing mathlib-style proofs

For `ftap-proofs` (targeting a mathlib PR), follow these additional rules:

1. **No `sorry`.** Mathlib CI rejects it unconditionally.
2. **Every definition has a docstring.**
3. **Proofs are term-mode when short** (≤ 3 lines), tactic mode otherwise.
4. **Use `@[simp]` judiciously** — only on lemmas that are genuinely always
   useful for simplification. Over-tagging `@[simp]` pollutes the simp set.
5. **Avoid `classical` when constructive proofs are feasible.**
6. **Namespace exported definitions** — everything lives under `FtapProofs.*`.
7. **Split large proofs into private lemmas** rather than writing one 50-line tactic block.

## Common import patterns for this repo

```lean
-- Finsets and sums
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

-- Real numbers
import Mathlib.Data.Real.Basic
import Mathlib.Analysis.SpecialFunctions.Pow.Real

-- Probability / measure theory
import Mathlib.MeasureTheory.Probability.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpace

-- Linear algebra
import Mathlib.LinearAlgebra.Matrix.Determinant
import Mathlib.LinearAlgebra.Basis

-- Order theory
import Mathlib.Order.Bounds.Basic
import Mathlib.Order.WithBot
```

Finding the right module: search [loogle.lean-lang.org](https://loogle.lean-lang.org)
by the type signature of the lemma you need, then look at its source file header for the
import path.
