# Writing Lean 4 proofs — Anti-patterns

The most common Lean 4 mistakes in this repo. Each entry: the bad pattern, why it's
wrong, the fix.

---

## 1. `import Mathlib`

**Wrong:**
```lean
import Mathlib

theorem myTheorem : ... := by ...
```

**Why it's wrong:**
- Imports all of mathlib (~200k lines) — 30-60 minute cold-cache compile.
- Rejected by both mathlib PR review and this repo's CI performance standards.
- Hides which parts of mathlib the theorem actually depends on.

**Correct:**
```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

theorem myTheorem : ... := by ...
```

Search [loogle.lean-lang.org](https://loogle.lean-lang.org) by type signature to find
the right module.

---

## 2. Bare `simp` without a lemma list

**Wrong:**
```lean
theorem portfolio_value_add (π₁ π₂ : Portfolio) :
    portfolioValue (π₁ + π₂) = portfolioValue π₁ + portfolioValue π₂ := by
  simp
```

**Why it's wrong:**
- `simp` applies every `@[simp]`-tagged lemma in scope, including mathlib lemmas that
  change over time. A mathlib update can silently break the proof.
- Hides what the proof actually relies on — hard to audit.
- mathlib PRs reject bare `simp` in most cases.

**Correct:**
```lean
theorem portfolio_value_add (π₁ π₂ : Portfolio) :
    portfolioValue (π₁ + π₂) = portfolioValue π₁ + portfolioValue π₂ := by
  simp only [portfolioValue, Finset.sum_union π₁.disjoint π₂]
```

Use `simp?` interactively to find which lemmas `simp` used, then copy them into
`simp only [...]`.

---

## 3. `sorry` on main

**Wrong:**
```lean
theorem hard_lemma : ArbitrageImpossible market := by
  sorry
```

**Why it's wrong:**
- Asserted, not proven. Lean accepts it, but it's mathematically meaningless.
- In `extensions/hedge-proofs`, the `@[export hedge_*]` FFI surface (`BacktestProofs/Accounting.lean`)
  compiles against the Lean kernel — a `sorry` voids those guarantees, so code calling through
  that FFI isn't actually verified. (Same property for `foundations/portfolio-proofs`'s
  Cython FFI relative to `foundations/optimization-proofs`'s kernel.)
- CI (`grep -rn sorry --include="*.lean"`) fails on `main`.
- A `sorry` in `ftap-proofs` invalidates every `options-proofs` theorem depending on it.

**Correct on a feature branch:**
```lean
theorem hard_lemma : ArbitrageImpossible market := by
  sorry  -- TODO: prove this; sketch: apply FarkasLemma, then construct Q explicitly
```

Remove the `sorry` before opening a PR. If a theorem is genuinely incomplete, leave it
out of the PR until the proof is finished.

---

## 4. `native_decide` for propositions that warrant a real proof

**Wrong:**
```lean
theorem noArb_iff_rnm (market : FiniteMarket) :
    NoArbitrage market ↔ ∃ Q, IsRiskNeutral market Q := by
  native_decide
```

**Why it's wrong:**
- `native_decide` only handles decidable propositions over finite, computable types.
  FTAP ranges over probability measures — not decidable this way.
- Even when it compiles, it's just a computation, no mathematical insight. The point
  of `ftap-proofs` is a human-readable, auditable proof.
- mathlib discourages `native_decide` except for closed, finite enumeration checks.

**Correct:**
Reserve `decide` for small finite propositions like `2 + 2 = 4` or
`Finset.card {1, 2, 3} = 3`. Write a tactic proof for mathematical theorems.

---

## 5. Missing namespace qualification

**Wrong:**
```lean
-- In BacktestProofs/Basic.lean
theorem valueIdentity ... := by ...  -- no namespace
```

**Why it's wrong:**
- Every `BacktestProofs` theorem must live under that namespace. Without it, the
  theorem lands in the root namespace — collisions, ambiguous API surface.
- In `ftap-proofs`, mathlib reviewers reject theorems outside the declared namespace.

**Correct:**
```lean
namespace BacktestProofs

theorem valueIdentity ... := by ...

end BacktestProofs
```

Or, when the namespace stays open for the whole file:
```lean
-- At the top of BacktestProofs/Basic.lean
namespace BacktestProofs

-- ... all theorems ...

end BacktestProofs
```

---

## 6. No docstring on exported theorems

**Wrong:**
```lean
theorem portfolio_value_nonneg (π : Portfolio) (hPos : AllPositive π) :
    0 ≤ portfolioValue π := by
  ...
```

**Why it's wrong:**
- A name alone explains nothing about what the theorem means or why it matters.
- For `ftap-proofs` (mathlib PR), missing docstrings are a review blocker.
- `hedge-proofs` exists for auditable guarantees — a bare name isn't auditable.

**Correct:**
```lean
/-- The value of a portfolio with all non-negative positions is non-negative.
    Formally: if qᵢ ≥ 0 and Sᵢ ≥ 0 for all i, then V(Π) ≥ 0.
    This ensures the accounting kernel cannot report negative portfolio value
    for a long-only position book. -/
theorem portfolio_value_nonneg (π : Portfolio) (hPos : AllPositive π) :
    0 ≤ portfolioValue π := by
  ...
```

---

## 7. Silently reopening a closed namespace in a different file

**Wrong:**
```lean
-- In BacktestProofs/Extra.lean
namespace BacktestProofs

-- Defines `valueIdentity` again, shadowing Basic.lean
theorem valueIdentity ... := by ...

end BacktestProofs
```

**Why it's wrong:** Lean allows reopening namespaces, but duplicate theorem names
across files cause ambiguity and a maintenance hazard. PR reviewers reject duplicates.

**Correct:**
Give the theorem a unique name, or replace the existing one in its original file.
If the new theorem generalizes the old one, rename it and update callers.

---

## 8. Using `omega` or `ring` on goals that need domain knowledge

**Wrong:**
```lean
-- Trying to close a financial no-arbitrage goal with omega
theorem noArb_price_bound : ask ≤ fair_value := by
  omega   -- fails: omega only handles linear arithmetic over ℤ/ℕ
```

**Why it's wrong:** `omega` handles only linear integer/natural-number arithmetic —
it can't reason about real-valued financial quantities. A misapplied closing tactic
wastes time and produces confusing errors.

**Correct tactic selection:**
| Goal type | Tactic |
|-----------|--------|
| `n + m = m + n` (ℕ/ℤ) | `omega` |
| `a * b + c = c + b * a` (ring) | `ring` |
| `(2 : ℝ) > 0` | `norm_num` |
| `x ≤ y → y ≤ z → x ≤ z` | `linarith` |
| `0 ≤ x ^ 2` | `positivity` |
| Anything else | decompose and build up |
