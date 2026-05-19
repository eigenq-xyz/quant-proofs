# Writing Lean 4 proofs — Examples

## Example 1: Well-documented theorem (BacktestProofs style)

This is the style to follow for all exported theorems.

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

What makes this good:
- Docstring explains the theorem in English, then symbolically, then its role.
- Named simp lemmas (not bare `simp`).
- Namespace is properly opened and closed.
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

What makes this good:
- Named induction cases (`zero`, `succ n ih`).
- Hypothesis extracted with `have`, then arithmetic closed by `linarith`.
- `rw` + `linarith` is clearer than a large `simp` call.

---

## Example 3: Short term-mode proof

For obvious equalities, term mode is acceptable and cleaner:

```lean
/-- The empty portfolio has zero value. -/
theorem emptyPortfolio_value_zero : portfolioValue emptyPortfolio = 0 :=
  Finset.sum_empty
```

One line, no `by`. This is appropriate here because `Finset.sum_empty` closes the goal directly.

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
1. No `/-- ... -/` docstring.
2. `simp` without lemma list — fragile, will break if simp set changes.
3. `sorry` — this theorem is unproven. Blocked from `main`.

Fixed version:

```lean
/-- Adding zero to a real number is an identity.
    This follows directly from the additive identity axiom. -/
theorem real_add_zero (x : ℝ) : x + 0 = x :=
  add_zero x
```

---

## Exercise: Add a new theorem to BacktestProofs

Suppose you want to prove that a portfolio with a single option position has
value equal to that option's Black-Scholes price at expiry.

Before writing:

1. Check InfoView goal at the `by`:
   ```
   ⊢ portfolioValue (singleOption opt) = optionPayoff opt S
   ```

2. Run `exact?` — does mathlib have it? Almost certainly not (domain-specific).

3. Unfold definitions manually:
   ```lean
   simp only [portfolioValue, singleOption, Finset.sum_singleton]
   ```

4. The remaining goal should be `optionPayoff opt S = optionPayoff opt S` → `rfl`.

Full proof:
```lean
/-- A single-option portfolio has value equal to that option's payoff.
    Formally: V({opt}) = max(S − K, 0) for a call with strike K. -/
theorem singleOption_value_eq_payoff (opt : Option) (S : ℝ) :
    portfolioValue (singleOption opt) = optionPayoff opt S := by
  simp only [portfolioValue, singleOption, Finset.sum_singleton, positionValue_option]
```
