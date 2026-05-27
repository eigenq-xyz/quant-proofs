import FtapProofs.Arbitrage
import FtapProofs.MartingaleMeasure
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.Analysis.InnerProductSpace.Basic

/-!
# The Fundamental Theorem of Asset Pricing

**Theorem (Harrison-Pliska 1981, discrete-time finite-state).**
A market is arbitrage-free if and only if there exists an equivalent martingale measure.

```
NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q
```

## Proof sketch

### (⇐) EMM implies NA (T5.1 — easy direction)

Suppose `Q` is an EMM and `θ` is an arbitrage opportunity with zero cost.
- Zero cost: `Ṽ 0 θ ω = 0` for all `ω`.
- Non-negative terminal payoff: `Ṽ T θ ω ≥ 0` for all `ω`.
- Profit in some state: `∃ ω₀, 0 < Ṽ T θ ω₀`.

By risk-neutral pricing (Q4.5): `E^Q[Ṽ T θ] = Ṽ 0 θ ω = 0` for any `ω`.
But `Ṽ T θ ≥ 0` everywhere and `Ṽ T θ ω₀ > 0`, so `E^Q[Ṽ T θ] > 0`. Contradiction.

### (⇒) NA implies EMM (T5.2–T5.3 — hard direction via Farkas)

Let `K = attainablePayoffs m` be the linear subspace of attainable discounted
terminal payoffs from zero-cost self-financing strategies.

NA says `K ∩ ℝ₊^Ω = {0}` (by `noArbitrage_iff_attainable_nonneg_eq_zero`).

**T5.2** By the separating hyperplane theorem (`ProperCone.hyperplane_separation'`
from `Mathlib.Analysis.Convex.Cone.InnerDual`), there exists a strictly positive
linear functional `φ : (Ω → ℝ) → ℝ` that vanishes on `K` and is strictly positive
on `ℝ₊^Ω \ {0}`.

In the finite-state setting `Ω → ℝ ≅ EuclideanSpace ℝ Ω`, so `φ` corresponds to
a vector `q : Ω → ℝ` with `q ω > 0` for all `ω` and `∑_ω q ω · f ω = 0` for all `f ∈ K`.

**T5.3** Normalize `q` to a probability measure `Q ω = q ω / (∑_ω q ω)`.
- `Q ~ P`: since `q ω > 0` for all `ω`, `Q {ω} > 0`, hence `Q ~ P` by the full
  support assumption on `P`.
- Martingale property: buy-and-hold strategies (holding 1 unit of asset `i` from time
  `s` to `T` and 0 otherwise) lie in `K`. The vanishing of `φ` on `K` translates to
  `E^Q[discountedPrice m i (t+1)] = discountedPrice m i t`, i.e., the martingale property.

## Sorry ledger

- **T5.1 integral step**: `∫ Ṽ T θ dQ > 0` when `Ṽ T θ ≥ 0` and `∃ ω₀, Ṽ T θ ω₀ > 0`
  and `Q {ω} > 0` for all `ω`. Use `integral_pos_of_pos_of_ae_pos` or
  `Measure.sum_smul_dirac` + `Finset.sum_pos`.

- **T5.2** (`state_price_functional`): cone separation in `EuclideanSpace ℝ Ω`.
  Set up `K_cone` as the linear subspace `K` viewed as a closed convex cone, and
  `pos_orthant` as `{f | ∀ ω, 0 ≤ f ω}`. Apply
  `ProperCone.hyperplane_separation' : K_cone ∩ pos_orthant = {0} → ∃ φ, ...`.

- **T5.3** (`state_prices_to_emm`): construct `Q` from state prices and verify
  both the equivalence and martingale properties. Use `Measure.sum_smul_dirac`
  to build `Q` as a weighted sum of Dirac measures.

## Contents

- **T5.1** `emm_implies_no_arbitrage` — EMM ⇒ NA
- **T5.2** `state_price_functional` — NA ⇒ ∃ strictly positive functional vanishing on K
- **T5.3** `state_prices_to_emm` — state prices ⇒ EMM
- **T5.4** `no_arbitrage_implies_emm` — NA ⇒ ∃ EMM (combines T5.2 + T5.3)
- **T5.5** `ftap` — the full biconditional
-/

namespace FtapProofs

variable {Ω : Type*} [Fintype Ω] [MeasurableSpace Ω] [MeasurableSingletonClass Ω]

/-! ### T5.1 EMM implies no arbitrage -/

/-- **(Easy direction.)** If an equivalent martingale measure exists, the market is
    arbitrage-free.

    **Proof:** By risk-neutral pricing, any zero-cost self-financing strategy satisfies
    `E^Q[Ṽ T θ] = Ṽ 0 θ = 0`. If `θ` were an arbitrage, `Ṽ T θ ≥ 0` everywhere and
    `Ṽ T θ ω₀ > 0` for some `ω₀`. Since `Q {ω₀} > 0`, this forces `E^Q[Ṽ T θ] > 0`,
    contradicting the zero value. -/
theorem emm_implies_no_arbitrage (m : FinancialMarket Ω)
    (hP_full : ∀ ω : Ω, 0 < m.P {ω})
    (Q : MeasureTheory.Measure Ω) (hQ : EquivalentMartingaleMeasure m Q) :
    NoArbitrage m := by
  intro ⟨arb⟩
  -- Extract the arbitrage components
  have hQprob := hQ.1.1
  have hQeq := hQ.1.2
  -- By risk-neutral pricing: E^Q[Ṽ T θ] = Ṽ 0 θ ω₀ = 0
  obtain ⟨ω₀, hω₀pos⟩ := arb.profit
  have hQ_pos : 0 < Q {ω₀} := by
    rw [← hQeq ω₀]
    exact hP_full ω₀
  -- The integral is positive: Ṽ T θ ≥ 0 everywhere and Ṽ T θ ω₀ > 0 with Q {ω₀} > 0
  have hintegral_pos : 0 <
      MeasureTheory.integral Q
        (discountedValueProcess m arb.θ ⟨m.T, Nat.lt_succ_self m.T⟩) := by
    -- Q is a probability measure (hence finite), and Ω is a fintype.
    -- Any function on a fintype with a finite measure is integrable.
    haveI hQprob' : MeasureTheory.IsProbabilityMeasure Q := hQprob
    haveI hQfin : MeasureTheory.IsFiniteMeasure Q := inferInstance
    let f := discountedValueProcess m arb.θ ⟨m.T, Nat.lt_succ_self m.T⟩
    -- Ṽ T θ ≥ 0 almost everywhere (pointwise ≥ 0 ⟹ ae ≥ 0)
    have hnn : 0 ≤ᵐ[Q] f := MeasureTheory.ae_of_all Q arb.nonneg
    -- Ṽ T θ is Q-integrable on the finite probability space
    have hint : MeasureTheory.Integrable f Q := MeasureTheory.Integrable.of_finite
    -- Use: 0 < ∫ f ∂Q ↔ 0 < Q (support f), for a nonneg integrable f
    rw [MeasureTheory.integral_pos_iff_support_of_nonneg_ae hnn hint]
    -- ω₀ lies in the support of f (since f ω₀ > 0 ≠ 0)
    have hmem : ω₀ ∈ Function.support f := Function.mem_support.mpr hω₀pos.ne'
    -- Q (support f) ≥ Q {ω₀} > 0 by measure monotonicity
    exact lt_of_lt_of_le hQ_pos
      (MeasureTheory.measure_mono (Set.singleton_subset_iff.mpr hmem))
  -- risk_neutral_pricing gives ∫ Ṽ T ∂Q = ∫ Ṽ 0 ∂Q; and Ṽ 0 ≡ 0 by zero_cost
  have hzero : MeasureTheory.integral Q
      (discountedValueProcess m arb.θ ⟨m.T, Nat.lt_succ_self m.T⟩) = 0 := by
    have h0 := risk_neutral_pricing m arb.θ arb.sf Q hQ
    -- h0 : ∫ Ṽ T ∂Q = ∫ Ṽ 0 ∂Q
    rw [h0]
    -- ∫ Ṽ 0 ∂Q = 0 since Ṽ 0 θ ω = 0 for all ω
    have hzc : discountedValueProcess m arb.θ ⟨0, Nat.zero_lt_succ m.T⟩ = fun _ => 0 :=
      funext arb.zero_cost
    rw [hzc, MeasureTheory.integral_zero]
  linarith

/-! ### T5.2 State-price functional (Farkas / cone separation) -/

/-- **(Hard direction, step 1.)** If the market satisfies NA, there exists a strictly
    positive functional `q : Ω → ℝ` that vanishes on all attainable payoffs.

    **Proof sketch:** Under NA, `K ∩ ℝ₊^Ω = {0}` by
    `noArbitrage_iff_attainable_nonneg_eq_zero`. In the finite-dimensional space
    `EuclideanSpace ℝ Ω`, the positive orthant is a proper cone and `K` is a closed
    subspace with `K ∩ ℝ₊^Ω = {0}`. Apply a hyperplane separation theorem (e.g.,
    `geometric_hahn_banach_point_closed` or the inner-dual cone characterization from
    `Mathlib.Analysis.Convex.Cone.InnerDual`) to get a separating functional `q` with
    `q ω > 0` for all `ω` and `∑_ω q ω * f ω = 0` for all `f ∈ K`.

    **API note (high-risk):** `ProperCone.hyperplane_separation'` is the target but its
    exact name in current mathlib4 is uncertain. Before implementing, search for the
    correct lemma in `Mathlib.Analysis.Convex.Cone.*`. Also: `attainablePayoffs m`
    should be refactored to a `Submodule ℝ (Ω → ℝ)` to access closedness results. -/
private theorem state_price_functional (m : FinancialMarket Ω) (hNA : NoArbitrage m) :
    ∃ q : Ω → ℝ,
      (∀ ω : Ω, 0 < q ω) ∧
      (∀ f ∈ attainablePayoffs m, ∑ ω : Ω, q ω * f ω = 0) := by
  sorry
  -- Tactic path:
  -- 1. Let K := attainablePayoffs m (shown linear subspace by attainablePayoffs_isLinearSubspace)
  -- 2. Embed Ω → ℝ as EuclideanSpace ℝ Ω (finite-dimensional inner product space)
  -- 3. The positive orthant P = {f | ∀ ω, 0 ≤ f ω} is a ProperCone in EuclideanSpace ℝ Ω
  -- 4. By noArbitrage_iff_attainable_nonneg_eq_zero applied to hNA:
  --    K ∩ P = {0}
  -- 5. Apply ProperCone.hyperplane_separation' (or Farkas lemma variant) to get q.
  -- 6. Translate the inner product ⟪q, f⟫ = ∑ ω, q ω * f ω.

/-! ### T5.3 State prices to EMM -/

/-- **(Hard direction, step 2.)** Given a strictly positive functional `q` vanishing on
    attainable payoffs, normalize it to an EMM.

    **Proof sketch:**
    - Define `Q ω = q ω / (∑ ω, q ω)` as a probability measure via
      `Measure.sum_smul_dirac`.
    - `Q ~ P`: since `q ω > 0` and `P {ω} > 0` for all `ω` (full support), we have
      `Q {ω} > 0 ↔ P {ω} > 0`.
    - Martingale property: for each asset `i` and time `t`, the buy-and-hold strategy
      (hold 1 unit of asset `i` from `t` to `T`) is a zero-cost self-financing strategy
      whose payoff is `discountedPrice m i T - discountedPrice m i t`. The vanishing
      of `q` on attainable payoffs gives `E^Q[discountedPrice m i T] = discountedPrice m i t`,
      which is the martingale property. -/
private theorem state_prices_to_emm (m : FinancialMarket Ω)
    (hP_full : ∀ ω : Ω, 0 < m.P {ω})
    (q : Ω → ℝ) (hq_pos : ∀ ω : Ω, 0 < q ω)
    (hq_vanish : ∀ f ∈ attainablePayoffs m, ∑ ω : Ω, q ω * f ω = 0) :
    ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q := by
  sorry
  -- Tactic path:
  -- 1. Let Z := ∑ ω : Ω, q ω (positive since each term positive)
  -- 2. Define Q := (1/Z) • ∑ ω : Ω, q ω • Measure.dirac ω
  --    (or equivalently via MeasureTheory.Measure.ofFintype)
  -- 3. Verify IsProbabilityMeasure Q: Q univ = (1/Z) * Z = 1
  -- 4. Verify EquivalentMeasure: Q {ω} = q ω / Z > 0 ↔ P {ω} > 0 (by hP_full and hq_pos)
  -- 5. Verify IsMartingaleMeasure: for each i, use hq_vanish on buy-and-hold strategies
  --    to get E^Q[discountedPrice m i (t+1) - discountedPrice m i t] = 0, i.e., martingale

/-! ### T5.4 NA implies EMM -/

/-- **(Hard direction.)** If the market is arbitrage-free, there exists an equivalent
    martingale measure. This follows by combining the cone separation (T5.2) with
    the measure construction (T5.3). -/
theorem no_arbitrage_implies_emm (m : FinancialMarket Ω)
    (hP_full : ∀ ω : Ω, 0 < m.P {ω})
    (hNA : NoArbitrage m) :
    ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q := by
  obtain ⟨q, hq_pos, hq_vanish⟩ := state_price_functional m hNA
  exact state_prices_to_emm m hP_full q hq_pos hq_vanish

/-! ### T5.5 The full FTAP biconditional -/

/-- **Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981).**
    In a finite-state discrete-time market with full support (`P {ω} > 0` for all `ω`),
    the market is arbitrage-free if and only if there exists an equivalent martingale
    measure.

    ```
    NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q
    ```

    The `hP_full` hypothesis is needed for **both** directions:
    - *Hard direction (NA → EMM)*: state prices constructed via T5.2 give a measure
      equivalent to `P` only if `P` has full support.
    - *Easy direction (EMM → NA)*: `ArbitrageOpportunity.profit` witnesses a state `ω₀`
      with `Ṽ T θ ω₀ > 0`, but we need `Q {ω₀} > 0` to derive `E^Q[Ṽ T θ] > 0`.
      Since `Q ~ P`, this requires `P {ω₀} > 0` — which `hP_full` provides. -/
theorem ftap (m : FinancialMarket Ω) (hP_full : ∀ ω : Ω, 0 < m.P {ω}) :
    NoArbitrage m ↔ ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q := by
  constructor
  · exact no_arbitrage_implies_emm m hP_full
  · rintro ⟨Q, hQ⟩
    exact emm_implies_no_arbitrage m hP_full Q hQ

end FtapProofs
