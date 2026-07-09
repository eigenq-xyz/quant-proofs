# Writing Lean 4 proofs — Examples

## Example 1: Well-documented theorem (BacktestProofs style)

```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.BigOperators.Group.Finset

open BigOperators

namespace BacktestProofs

/-- The market value of a portfolio equals the sum of its individual position values.
    Formally: V(Π) = Σᵢ∈Π.positions (qᵢ · Sᵢ).
    This is the accounting identity that grounds all PnL attribution theorems in this library.
    It ensures that the Python backtester's `portfolio_value` function cannot silently miscount
    position weights or prices. -/
theorem valueIdentity (π : Portfolio) :
    portfolioValue π = π.positions.sum positionValue := by
  simp only [portfolioValue, positionValue, Finset.sum_congr rfl]
  rfl

end BacktestProofs
```

Why it's good:
- Docstring: English, then symbolic, then role.
- Named simp lemmas, not bare `simp`.
- Namespace opened/closed properly.
- Import is specific.

---

## Example 2: Inductive proof (FtapProofs style)

```lean
import Mathlib.Data.Finset.Basic
import Mathlib.Algebra.Order.Field.Basic

namespace FtapProofs

/-- A self-financing trading strategy has zero net cash flow at each rebalancing step.
    This is the discrete-time analogue of the self-financing condition dV = θ dS. -/
theorem selfFinancing_net_zero
    (θ : ℕ → Finset.sum_type)
    (S : ℕ → ℝ)
    (hSF : IsSelfFinancing θ S)
    (n : ℕ) :
    netCashFlow θ S n = 0 := by
  induction n with
  | zero => simp [netCashFlow, IsSelfFinancing.at_zero hSF]
  | succ n ih =>
    rw [netCashFlow_succ]
    have := hSF.step n
    linarith

end FtapProofs
```

Why it's good:
- Named induction cases (`zero`, `succ n ih`).
- Hypothesis extracted with `have`, arithmetic closed by `linarith`.
- `rw` + `linarith` beats one large `simp` call.

---

## Example 3: Short term-mode proof

```lean
/-- The empty portfolio has zero value. -/
theorem emptyPortfolio_value_zero : portfolioValue emptyPortfolio = 0 :=
  Finset.sum_empty
```

Term mode: one line, no `by` — `Finset.sum_empty` closes the goal directly.

---

## Example 4: Existential with witness

```lean
/-- Under any no-arbitrage condition, there exists a risk-neutral measure. -/
theorem exists_risk_neutral_measure
    (hNoArb : NoArbitrage market) :
    ∃ Q : ProbabilityMeasure market.Ω, IsRiskNeutral market Q := by
  obtain ⟨Q, hQ⟩ := FarkasSeparation.apply hNoArb
  exact ⟨Q, hQ.toRiskNeutral⟩
```

Pattern: `obtain` destructs the witness, `exact ⟨..., ...⟩` packages the result.

---

## Bad example: what NOT to write

```lean
-- BAD: No docstring, bare simp, sorry on main
theorem thing (x : ℝ) : x + 0 = x := by
  simp
  sorry
```

Problems:
- No `/-- ... -/` docstring.
- `simp` without a lemma list — fragile, breaks if the simp set changes.
- `sorry` — unproven, blocked from `main`.

Fixed version:

```lean
/-- Adding zero to a real number is an identity.
    This follows directly from the additive identity axiom. -/
theorem real_add_zero (x : ℝ) : x + 0 = x :=
  add_zero x
```

---

## Exercise: Add a new theorem to BacktestProofs

Goal: single-option portfolio value = that option's Black-Scholes payoff at expiry.

1. Check the InfoView goal at `by`:
   ```
   ⊢ portfolioValue (singleOption opt) = optionPayoff opt S
   ```

2. Run `exact?` — mathlib almost certainly lacks this; it's domain-specific.

3. Unfold definitions manually:
   ```lean
   simp only [portfolioValue, singleOption, Finset.sum_singleton]
   ```

4. Remaining goal reduces to `optionPayoff opt S = optionPayoff opt S` → `rfl`.

Full proof:
```lean
/-- A single-option portfolio has value equal to that option's payoff.
    Formally: V({opt}) = max(S − K, 0) for a call with strike K. -/
theorem singleOption_value_eq_payoff (opt : Option) (S : ℝ) :
    portfolioValue (singleOption opt) = optionPayoff opt S := by
  simp only [portfolioValue, singleOption, Finset.sum_singleton, positionValue_option]
```
