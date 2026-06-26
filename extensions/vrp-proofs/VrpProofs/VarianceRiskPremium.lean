import VrpProofs.Replication

/-!
# The variance risk premium sign theorem (CLAIM 2)

This module adds a **physical** probability measure to the CRR setup (the existing
`OptionsProofs` structure carries only the risk-neutral measure `Q`) and proves the
discrete decomposition of the **variance risk premium** (VRP).

We work directly with binomial expectations. For an up-probability `p ∈ [0, 1]`, the
*binomial expectation* of a terminal-price functional `G` is

  `binomExp p G = ∑_ω p^(ups ω) · (1-p)^(T - ups ω) · G(S_N(ω))`,

the expectation of `G(S_N)` when each of the `T` moves is independently up with probability
`p`. Specialising `p = q = riskNeutralProb u d r` recovers the risk-neutral expectation; a
different physical `p` gives the physical expectation.

The **risk-neutral price** of the claim is the discounted risk-neutral expectation
`price = binomExp q G / (1+r)^T` (this is exactly `OptionsProofs.rnPrice`, the no-arbitrage
price). The **variance risk premium** is

  `vrp = price − binomExp p G / (1+r)^T`,

the price of the claim minus its discounted *physical* expectation. The headline result is

  `vrp = (binomExp q G − binomExp p G) / (1+r)^T`   (`vrp_decomposition`),

which is `> 0` exactly when `Q` values the payoff above `P` (`vrp_pos_of_lt`,
`vrp_nonneg_of_le`). Source: the variance-risk-premium literature; the discrete CRR mechanics
of Cox-Ross-Rubinstein 1979.

## Contents

- `binomExp` — the binomial expectation of a terminal-price functional under up-probability `p`.
- `binomDensity`, `binomDensity_sum_eq_one` — the underlying path weights (sum to one).
- `rnExp_eq_binomExp` — the risk-neutral binomial expectation matches `binomExp q`.
- `claimPrice`, `physicalPV`, `vrp` — the price, the discounted physical value, and the VRP.
- `vrp_decomposition` — **CLAIM 2 (decomposition)**: `vrp = (E^Q − E^P)/(1+r)^T`.
- `vrp_nonneg_of_le`, `vrp_pos_of_lt`, `vrp_pos_iff` — **CLAIM 2 (sign)**: the VRP inherits the
  sign of the `Q`-vs-`P` expectation gap, and is positive *iff* that gap is positive.

Everything in this module is fully proved, with no proof gaps. A naive "convex payoff" bridge of the
form `q ≤ p ∧ G convex ⟹ E^P ≤ E^Q` is **false** for a single fixed tree (see the closing note
at the end of the file), so it is deliberately not asserted; the sharp true criterion is the
expectation gap itself.
-/

namespace VrpProofs

open OptionsProofs
open scoped BigOperators

variable {T : ℕ}

/-! ### The binomial path density under an arbitrary up-probability -/

/-- The binomial path weight under up-probability `p`:
`p^(#up-moves) · (1-p)^(#down-moves)`. This is `crrRNDensity` with `p` in place of `q`. -/
noncomputable def binomDensity (p : ℝ) (ω : CRRState T) : ℝ :=
  p ^ (ups T ω) * (1 - p) ^ (T - ups T ω)

/-- The binomial weights factor as a product over the `T` coordinates. (Same argument as
`OptionsProofs.crrRNDensity_eq_prod`, generalised to an arbitrary `p`.) -/
lemma binomDensity_eq_prod (p : ℝ) (ω : CRRState T) :
    binomDensity p ω = ∏ j : Fin T, (if ω j = true then p else 1 - p) := by
  classical
  rw [Finset.prod_ite (f := fun _ => p) (g := fun _ => 1 - p)]
  simp only [Finset.prod_const]
  rw [binomDensity, ups_eq_card_true ω]
  have hsplit :
      (Finset.univ.filter (fun j : Fin T => ω j = true)).card +
        (Finset.univ.filter (fun j : Fin T => ¬ ω j = true)).card = T := by
    have := Finset.card_filter_add_card_filter_not
      (s := (Finset.univ : Finset (Fin T))) (fun j => ω j = true)
    simpa [Finset.card_univ] using this
  have hdown :
      (Finset.univ.filter (fun j : Fin T => ¬ ω j = true)).card =
        T - (Finset.univ.filter (fun j : Fin T => ω j = true)).card := by omega
  rw [hdown]

/-- The binomial weights sum to one: `∑_ω p^(ups) (1-p)^(T-ups) = (p + (1-p))^T = 1`.
(Same `Finset.sum_prod_piFinset` argument as `OptionsProofs.crrRNDensity_sum_eq_one`.) -/
lemma binomDensity_sum_eq_one (p : ℝ) :
    ∑ ω : CRRState T, binomDensity p ω = 1 := by
  classical
  rw [Finset.sum_congr rfl (fun ω _ => binomDensity_eq_prod p ω)]
  have hpi : (Finset.univ : Finset (CRRState T)) =
      Fintype.piFinset (fun _ : Fin T => (Finset.univ : Finset Bool)) := by
    rw [Fintype.piFinset_univ]
  rw [hpi, Finset.sum_prod_piFinset (Finset.univ : Finset Bool)
        (fun (_ : Fin T) b => if b = true then p else 1 - p)]
  have hcoord : ∀ _i : Fin T,
      (∑ b : Bool, if b = true then p else 1 - p) = 1 := by
    intro _i; rw [Fintype.sum_bool]; simp
  rw [Finset.prod_congr rfl (fun i _ => hcoord i)]
  simp

/-! ### The binomial expectation of a terminal-price functional -/

/-- The binomial expectation under up-probability `p` of a functional `G` of the terminal
price: `∑_ω binomDensity p ω · G (terminalSpot ω)`. -/
noncomputable def binomExp (T : ℕ) (S₀ u d p : ℝ) (G : ℝ → ℝ) : ℝ :=
  ∑ ω : CRRState T, binomDensity p ω * G (terminalSpot T S₀ u d ω)

/-- The risk-neutral expectation, written via the risk-neutral measure `Q`, equals the
binomial expectation under `p = q = riskNeutralProb u d r`. Both are the same density-weighted
finite sum. -/
lemma rnExp_eq_binomExp (T : ℕ) {S₀ u d r : ℝ}
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) (G : ℝ → ℝ) :
    (∫ ω, G (terminalSpot T S₀ u d ω) ∂(crrRNMeasure T u d r hd hdr hru)) =
      binomExp T S₀ u d (riskNeutralProb u d r) G := by
  rw [crrRNMeasure_integral_eq_sum hd hdr hru]
  apply Finset.sum_congr rfl
  intro ω _
  -- `crrRNDensity u d r ω = binomDensity (riskNeutralProb u d r) ω` definitionally.
  rfl

/-! ### Price, physical present value, and the variance risk premium -/

/-- The risk-neutral (no-arbitrage) price of the claim `G(S_N)`: discounted risk-neutral
expectation. By `rnExp_eq_binomExp` this is `binomExp q G / (1+r)^T`. -/
noncomputable def claimPrice (T : ℕ) (S₀ u d r : ℝ) (G : ℝ → ℝ) : ℝ :=
  binomExp T S₀ u d (riskNeutralProb u d r) G / (1 + r) ^ T

/-- The discounted **physical** present value of the claim: `binomExp p G / (1+r)^T`, where
`p` is the physical up-probability (possibly `≠ q`). -/
noncomputable def physicalPV (T : ℕ) (S₀ u d r p : ℝ) (G : ℝ → ℝ) : ℝ :=
  binomExp T S₀ u d p G / (1 + r) ^ T

/-- The **variance risk premium** of the claim: its risk-neutral price minus its discounted
physical expectation. For a short option position this is the expected P&L of the
delta-hedged book (positive when the option is sold rich relative to physical expectation). -/
noncomputable def vrp (T : ℕ) (S₀ u d r p : ℝ) (G : ℝ → ℝ) : ℝ :=
  claimPrice T S₀ u d r G - physicalPV T S₀ u d r p G

/-! ### CLAIM 2 — the decomposition and its sign -/

/-- **CLAIM 2 (decomposition).** The variance risk premium equals the discounted gap between
the risk-neutral and physical expectations of the payoff:

`vrp = (binomExp q G − binomExp p G) / (1 + r) ^ T`.

Pure algebra of the two discounted sums (`sub_div`). -/
theorem vrp_decomposition (T : ℕ) (S₀ u d r p : ℝ) (G : ℝ → ℝ) :
    vrp T S₀ u d r p G =
      (binomExp T S₀ u d (riskNeutralProb u d r) G - binomExp T S₀ u d p G) / (1 + r) ^ T := by
  rw [vrp, claimPrice, physicalPV, sub_div]

/-- **CLAIM 2 (sign, non-strict).** If `Q` values the payoff at least as high as `P`
(`binomExp p G ≤ binomExp q G`) and the discount factor is positive (`-1 < r`), the variance
risk premium is non-negative. Immediate from the decomposition: a non-negative numerator over
a positive denominator. -/
theorem vrp_nonneg_of_le (T : ℕ) {S₀ u d r p : ℝ} {G : ℝ → ℝ} (hr : -1 < r)
    (hle : binomExp T S₀ u d p G ≤ binomExp T S₀ u d (riskNeutralProb u d r) G) :
    0 ≤ vrp T S₀ u d r p G := by
  rw [vrp_decomposition]
  apply div_nonneg (by linarith)
  exact pow_nonneg (by linarith) T

/-- **CLAIM 2 (sign, strict).** If `Q` values the payoff strictly above `P`
(`binomExp p G < binomExp q G`) and `-1 < r`, the variance risk premium is strictly positive.
Immediate from the decomposition. -/
theorem vrp_pos_of_lt (T : ℕ) {S₀ u d r p : ℝ} {G : ℝ → ℝ} (hr : -1 < r)
    (hlt : binomExp T S₀ u d p G < binomExp T S₀ u d (riskNeutralProb u d r) G) :
    0 < vrp T S₀ u d r p G := by
  rw [vrp_decomposition]
  apply div_pos (by linarith)
  exact pow_pos (by linarith) T

/-- **CLAIM 2 (sign, sharp).** The variance risk premium is positive **iff** `Q` values the
payoff strictly above `P`. The expectation gap is therefore the complete, sharp criterion for a
positive VRP.

This is a purely algebraic consequence of `vrp_decomposition` and `(1+r)^T > 0`: it holds for
any `r > -1` and needs no no-arbitrage hypotheses (no `0 < q < 1`, no `d < 1+r < u`). Those
conditions matter for whether `q` is a genuine risk-neutral probability, not for the sign
equivalence itself. -/
theorem vrp_pos_iff (T : ℕ) {S₀ u d r p : ℝ} {G : ℝ → ℝ} (hr : -1 < r) :
    0 < vrp T S₀ u d r p G ↔
      binomExp T S₀ u d p G < binomExp T S₀ u d (riskNeutralProb u d r) G := by
  rw [vrp_decomposition]
  have hpow : (0 : ℝ) < (1 + r) ^ T := pow_pos (by linarith) T
  rw [div_pos_iff]
  constructor
  · rintro (⟨hnum, _⟩ | ⟨_, hden⟩)
    · linarith
    · exact absurd hpow (by linarith)
  · intro hlt
    exact Or.inl ⟨by linarith, hpow⟩

/-! ### A note on the convexity story (why no false bridge is asserted)

It is tempting to add a "convex payoff" bridge of the shape
`q ≤ p ∧ G convex ⟹ binomExp p G ≤ binomExp q G`, so that the VRP sign would follow from a
risk premium on the stock (`q ≤ p`) plus convexity of `G`. **That statement is false.** Holding
`u, d` fixed, a lower up-probability `q` shifts the terminal-price law to *lower* prices
(first-order stochastic dominance), and for an increasing convex payoff such as a call this
*lowers* the expectation, giving `binomExp q G ≤ binomExp p G`, the opposite inequality.
Numerically, with `T = 3, S₀ = 100, u = 1.3, d = 0.8`, a `K = 100` call has `E^Q = 17.8` at
`q = 0.4` versus `E^P = 41.1` at `p = 0.6`.

The genuine variance risk premium is *not* a statement about the same tree under two
probabilities; it compares the price under an **implied** tree (wide `u, d`) against the
physical expectation under a **realized** tree (narrow `u, d`). Capturing that requires two
distinct `(u, d)` pairs and is deliberately left out of scope here. What is proved is the exact,
true content for a single tree: the VRP equals the discounted `E^Q − E^P` gap
(`vrp_decomposition`), and is positive exactly when that gap is positive (`vrp_pos_iff`). The
expectation ordering `binomExp p G < binomExp q G` is the honest, sharp hypothesis. -/

end VrpProofs
