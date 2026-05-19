# Writing Lean 4 proofs — Anti-patterns

These are the most common mistakes when writing Lean 4 proofs in this repo.
Each entry shows the problematic pattern, why it is wrong, and the correct alternative.

---

## 1. `import Mathlib`

**Wrong:**
```lean
import Mathlib

theorem myTheorem : ... := by ...
```

**Why it is wrong:**
- Imports the entire mathlib library (~200k lines). Compilation takes 30-60 minutes on a
  cold cache.
- Accepted neither by mathlib PR review nor by this repo's CI performance standards.
- Makes it impossible to tell which parts of mathlib the theorem actually depends on.

**Correct:**
```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

theorem myTheorem : ... := by ...
```

Search [loogle.lean-lang.org](https://loogle.lean-lang.org) by type signature to find the
right module.

---

## 2. Bare `simp` without a lemma list

**Wrong:**
```lean
theorem portfolio_value_add (π₁ π₂ : Portfolio) :
    portfolioValue (π₁ + π₂) = portfolioValue π₁ + portfolioValue π₂ := by
  simp
```

**Why it is wrong:**
- `simp` applies every lemma tagged `@[simp]` in scope, including ones from mathlib that
  change over time. A mathlib update can silently break the proof.
- It hides what the proof actually relies on, making it hard to audit.
- mathlib PRs reject bare `simp` in most cases.

**Correct:**
```lean
theorem portfolio_value_add (π₁ π₂ : Portfolio) :
    portfolioValue (π₁ + π₂) = portfolioValue π₁ + portfolioValue π₂ := by
  simp only [portfolioValue, Finset.sum_union π₁.disjoint π₂]
```

Use `simp?` interactively to discover which lemmas `simp` used, then copy the result
into `simp only [...]`.

---

## 3. `sorry` on main

**Wrong:**
```lean
theorem hard_lemma : ArbitrageImpossible market := by
  sorry
```

**Why it is wrong:**
- The theorem is asserted but unproven. Lean accepts it, but it is mathematically meaningless.
- In `backtest-proofs`, the Cython FFI compiles against the Lean kernel. A `sorry` means the
  kernel guarantees are void — the Python code is not actually verified.
- CI (`grep -rn sorry --include="*.lean"`) fails on `main`.
- A `sorry` in `ftap-proofs` would invalidate every theorem in `options-proofs` that depends
  on the sorry'd result.

**Correct on a feature branch:**
```lean
theorem hard_lemma : ArbitrageImpossible market := by
  sorry  -- TODO: prove this; sketch: apply FarkasLemma, then construct Q explicitly
```

Remove the `sorry` before opening a PR. If a theorem is genuinely incomplete, do not include
it in the PR — wait until the proof is finished.

---

## 4. `native_decide` for propositions that warrant a real proof

**Wrong:**
```lean
theorem noArb_iff_rnm (market : FiniteMarket) :
    NoArbitrage market ↔ ∃ Q, IsRiskNeutral market Q := by
  native_decide
```

**Why it is wrong:**
- `native_decide` works only for decidable propositions over finite, computable types.
  The FTAP statement ranges over probability measures, which are not decidable this way.
- Even when it compiles, `native_decide` produces no mathematical insight — it is just a
  computation. The purpose of `ftap-proofs` is to have a human-readable, auditable proof.
- mathlib strongly discourages `native_decide` except for closed, finite enumeration checks.

**Correct:**
Use `decide` only for small finite propositions like `2 + 2 = 4` or `Finset.card {1, 2, 3} = 3`.
For mathematical theorems, write a tactic proof.

---

## 5. Missing namespace qualification

**Wrong:**
```lean
-- In BacktestProofs/Basic.lean
theorem valueIdentity ... := by ...  -- no namespace
```

**Why it is wrong:**
- Every theorem in `BacktestProofs` must live under the `BacktestProofs` namespace.
  Without it, the theorem is in the root namespace, causing name collisions and making
  the module's API surface ambiguous.
- In `ftap-proofs`, mathlib PR reviewers will reject theorems not in the declared namespace.

**Correct:**
```lean
namespace BacktestProofs

theorem valueIdentity ... := by ...

end BacktestProofs
```

Or, for files where the namespace is open for the whole file:
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

**Why it is wrong:**
- The theorem has a name but no explanation of what it means or why it matters.
- For `ftap-proofs` (mathlib PR), missing docstrings are a review blocker.
- For `backtest-proofs`, the purpose of the library is to provide auditable guarantees
  to a human reviewer. A bare theorem name is not auditable.

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

**Why it is wrong:**
- Lean allows reopening namespaces, but duplicate theorem names across files cause
  ambiguity and are a maintenance hazard.
- PR reviewers will reject duplicate names.

**Correct:**
Give the theorem a unique name, or replace the existing theorem in its original file.
If the new theorem is a generalization, rename it appropriately and update callers.

---

## 8. Using `omega` or `ring` on goals that need domain knowledge

**Wrong:**
```lean
-- Trying to close a financial no-arbitrage goal with omega
theorem noArb_price_bound : ask ≤ fair_value := by
  omega   -- fails: omega only handles linear arithmetic over ℤ/ℕ
```

**Why it is wrong:**
- `omega` handles only linear integer/natural number arithmetic. It cannot reason about
  real-valued financial quantities or mathematical structures.
- Misapplying a closing tactic wastes time and produces confusing error messages.

**Correct tactic selection:**
| Goal type | Tactic |
|-----------|--------|
| `n + m = m + n` (ℕ/ℤ) | `omega` |
| `a * b + c = c + b * a` (ring) | `ring` |
| `(2 : ℝ) > 0` | `norm_num` |
| `x ≤ y → y ≤ z → x ≤ z` | `linarith` |
| `0 ≤ x ^ 2` | `positivity` |
| Anything else | decompose and build up |
