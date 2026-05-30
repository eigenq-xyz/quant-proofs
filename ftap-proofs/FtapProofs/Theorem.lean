import FtapProofs.Arbitrage
import FtapProofs.MartingaleMeasure
import Mathlib.MeasureTheory.Integral.Bochner.Basic
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Probability.ProbabilityMassFunction.Constructions
import Mathlib.Probability.ProbabilityMassFunction.Basic
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.MeasureTheory.Integral.Bochner.Set
import Mathlib.MeasureTheory.Integral.Bochner.SumMeasure

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

open scoped MeasureTheory

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
    - **Measure construction (proved):** Define `Q ω = q ω / Z` where `Z = ∑ ω, q ω > 0`,
      as a probability measure via `PMF.ofFintype`. `Q ~ P` follows since `q ω > 0` and
      `P {ω} > 0` for all `ω`.
    - **Martingale property (pending, structural limitation):** The full one-step condition
      `E^Q[g · (D_i(t+1) − D_i(t))] = 0` for all ℱ_t-measurable `g` requires "bond-funded
      buy-and-hold" strategies: hold `g` units of asset `i` from time `t+1` to `T` while
      shorting `g · D_i(t)` units of the bond. These are not in `attainablePayoffs m` because
      `TradingStrategy` has no bond-holding field — it covers risky assets only.
      **Fix required:** Extend `TradingStrategy` with an explicit bond component (constant
      discounted price 1) so that `attainablePayoffs` spans all predictable stochastic integrals. -/
private theorem state_prices_to_emm (m : FinancialMarket Ω)
    (hP_full : ∀ ω : Ω, 0 < m.P {ω})
    (q : Ω → ℝ) (hq_pos : ∀ ω : Ω, 0 < q ω)
    (hq_vanish : ∀ f ∈ attainablePayoffs m, ∑ ω : Ω, q ω * f ω = 0) :
    ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q := by
  -- Ω is nonempty (m.P is a probability measure, so m.P univ = 1 ≠ 0 = m.P ∅)
  haveI hΩ : Nonempty Ω := by
    have huniv : (Set.univ : Set Ω).Nonempty := by
      rw [Set.nonempty_iff_ne_empty]
      intro he
      have hmeas := m.P_prob.measure_univ
      simp [he] at hmeas
    obtain ⟨ω, _⟩ := huniv
    exact ⟨ω⟩
  -- Step 1: Normalizing constant Z = ∑ ω, q ω (positive since each q ω > 0)
  let Z : ℝ := ∑ ω : Ω, q ω
  have hZ_pos : 0 < Z :=
    Finset.sum_pos (fun ω _ => hq_pos ω) Finset.univ_nonempty
  -- Step 2: ENNReal density f ω = ENNReal.ofReal (q ω / Z)
  let f : Ω → ENNReal := fun ω => ENNReal.ofReal (q ω / Z)
  -- The density sums to 1 (so it defines a PMF)
  have hfsum : ∑ ω : Ω, f ω = 1 := by
    simp only [f]
    rw [← ENNReal.ofReal_sum_of_nonneg (fun ω _ =>
        div_nonneg (le_of_lt (hq_pos ω)) (le_of_lt hZ_pos))]
    rw [← Finset.sum_div, div_self (ne_of_gt hZ_pos), ENNReal.ofReal_one]
  -- Step 3: Build Q as the PMF measure with Q {ω} = q ω / Z
  let pmf : PMF Ω := PMF.ofFintype f hfsum
  have hQprob : MeasureTheory.IsProbabilityMeasure pmf.toMeasure :=
    PMF.toMeasure.isProbabilityMeasure pmf
  -- Q {ω} equals the density at each singleton
  have hQsing : ∀ ω : Ω, pmf.toMeasure {ω} = ENNReal.ofReal (q ω / Z) := fun ω => by
    rw [pmf.toMeasure_apply_singleton ω (measurableSet_singleton ω)]
    simp only [pmf, PMF.ofFintype_apply]
    -- f ω := ENNReal.ofReal (q ω / Z) by definition of the let binding
    rfl
  -- Step 4: Q {ω} > 0 for all ω (since q ω > 0, Z > 0)
  have hQpos : ∀ ω : Ω, 0 < pmf.toMeasure {ω} := fun ω => by
    rw [hQsing ω]
    exact ENNReal.ofReal_pos.mpr (div_pos (hq_pos ω) hZ_pos)
  -- Provide the EMM witness
  refine ⟨pmf.toMeasure, ⟨hQprob, fun ω => ⟨fun _ => hQpos ω, fun _ => hP_full ω⟩⟩, ?_⟩
  -- Step 5: IsMartingaleMeasure
  haveI : MeasureTheory.IsFiniteMeasure pmf.toMeasure := inferInstance
  -- (pmf ω).toReal = q ω / Z
  have hpmf_val : ∀ ω : Ω, (pmf ω).toReal = q ω / Z := fun ω => by
    simp only [pmf, PMF.ofFintype_apply, f]
    exact ENNReal.toReal_ofReal (div_nonneg (le_of_lt (hq_pos ω)) (le_of_lt hZ_pos))
  -- Key one-step vanishing: ∑_ω q ω * g ω * (D_i(t₀+1,ω) − D_i(t₀,ω)) = 0
  -- for any ℱ_{t₀}-measurable g, via the bond-funded buy-and-hold strategy.
  have hq_step : ∀ (i₀ : Fin m.n) (t₀ : Fin m.T) (g : Ω → ℝ)
      (_ : @Measurable Ω ℝ (m.𝒻 t₀.castSucc) _ g),
      ∑ ω : Ω, q ω * g ω *
        (discountedPrice m i₀ t₀.succ ω - discountedPrice m i₀ t₀.castSucc ω) = 0 :=
      fun i₀ t₀ g hg => by
    -- Bond-funded buy-and-hold TradingStrategy:
    --   hold g units of asset i₀ at time t₀+1, financed by bond at t₀+1
    --   lock gains g*(D_i₀(t₀+1)−D_i₀(t₀)) in bond from t₀+2 onwards
    let θbh : TradingStrategy m := {
      holdings := fun i t ω => if i = i₀ ∧ t = t₀.succ then g ω else 0
      predictable := fun i t => by
        rcases Classical.em (i = i₀ ∧ t = t₀.succ) with ⟨rfl, rfl⟩ | hne
        · simp only [and_self, if_true]; rw [FtapProofs.prevTime_succ]; exact hg
        · have : (fun ω : Ω => if i = i₀ ∧ t = t₀.succ then g ω else (0 : ℝ)) = 0 :=
            funext fun ω => if_neg hne
          exact this ▸ measurable_const
      bondHolding := fun t ω =>
        if t = t₀.succ then -(g ω * discountedPrice m i₀ t₀.castSucc ω)
        else if t₀.val + 1 < t.val then
          g ω * (discountedPrice m i₀ t₀.succ ω - discountedPrice m i₀ t₀.castSucc ω)
        else 0
      bondPredictable := fun t => by
        by_cases h1 : t = t₀.succ
        · subst h1; simp only [if_true]; rw [FtapProofs.prevTime_succ]
          exact (hg.mul (discountedPrice_adapted m i₀ t₀.castSucc)).neg
        · simp only [if_neg h1]
          by_cases h2 : t₀.val + 1 < t.val
          · simp only [if_pos h2]
            have hprev : t₀.succ ≤ FtapProofs.prevTime t := by
              simp only [Fin.le_def, FtapProofs.prevTime, Fin.val_succ, Nat.pred_eq_sub_one]
              omega
            have hcprev : t₀.castSucc ≤ FtapProofs.prevTime t :=
              le_trans (Fin.castSucc_le_succ t₀) hprev
            exact (hg.mono (m.𝒻.mono hcprev) le_rfl).mul
              (((discountedPrice_adapted m i₀ t₀.succ).mono (m.𝒻.mono hprev) le_rfl).sub
                ((discountedPrice_adapted m i₀ t₀.castSucc).mono (m.𝒻.mono hcprev) le_rfl))
          · simp only [if_neg h2]; exact measurable_const }
    -- Self-financing
    have θbh_sf : selfFinancing m θbh := fun t ω => by
      simp only [θbh]
      by_cases hsu : t.succ = t₀.succ
      · -- t.val = t₀.val: step t₀→t₀+1
        have htval : t.val = t₀.val := by
          have := congrArg Fin.val hsu; simpa [Fin.val_succ] using this
        have hcs_ne : t.castSucc ≠ t₀.succ :=
          Fin.ne_of_val_ne (by simp [Fin.val_castSucc, Fin.val_succ]; omega)
        have hcs_eq : t.castSucc = t₀.castSucc :=
          Fin.ext (by simp [Fin.val_castSucc]; omega)
        have hsu_simp : ∀ i, (if i = i₀ ∧ t.succ = t₀.succ then g ω else (0:ℝ)) =
            if i = i₀ then g ω else 0 := fun i => by simp [hsu]
        have hcs_simp : ∀ i, (if i = i₀ ∧ t.castSucc = t₀.succ then g ω else (0:ℝ)) = 0 :=
          fun i => if_neg (fun h => hcs_ne h.2)
        have hcs_bond : ¬ (t₀.val + 1 < t.castSucc.val) := by simp [Fin.val_castSucc]; omega
        simp only [hsu_simp, hcs_simp, ite_mul, zero_mul,
          Finset.sum_ite_eq', Finset.mem_univ, ite_true, Finset.sum_const_zero,
          if_pos hsu, if_neg hcs_ne, if_neg hcs_bond, add_zero]
        rw [hcs_eq]; ring
      · by_cases hcs : t.castSucc = t₀.succ
        · -- t.val = t₀.val + 1: step t₀+1→t₀+2
          have hsu_simp : ∀ i, (if i = i₀ ∧ t.succ = t₀.succ then g ω else (0:ℝ)) = 0 :=
            fun i => if_neg (fun h => hsu h.2)
          have hcs_simp : ∀ i, (if i = i₀ ∧ t.castSucc = t₀.succ then g ω else (0:ℝ)) =
              if i = i₀ then g ω else 0 := fun i => by simp [hcs]
          have hcsv : t.val = t₀.val + 1 := by
            have := congrArg Fin.val hcs; simpa [Fin.val_succ, Fin.val_castSucc] using this
          have hgt : t₀.val + 1 < t.succ.val := by simp [Fin.val_succ]; omega
          simp only [hsu_simp, hcs_simp, ite_mul, zero_mul,
            Finset.sum_const_zero, zero_add, Finset.sum_ite_eq', Finset.mem_univ, ite_true,
            if_neg hsu, if_pos hcs, if_pos hgt]
          rw [hcs]; ring
        · -- t.val ≠ t₀.val and t.val ≠ t₀.val + 1
          have hsu_simp : ∀ i, (if i = i₀ ∧ t.succ = t₀.succ then g ω else (0:ℝ)) = 0 :=
            fun i => if_neg (fun h => hsu h.2)
          have hcs_simp : ∀ i, (if i = i₀ ∧ t.castSucc = t₀.succ then g ω else (0:ℝ)) = 0 :=
            fun i => if_neg (fun h => hcs h.2)
          simp only [hsu_simp, hcs_simp, if_neg hsu, if_neg hcs]
          have hsucc_val : t.succ.val = t.val + 1 := Fin.val_succ t
          have hcast_val : t.castSucc.val = t.val := Fin.val_castSucc t
          have hsu_v : t.val ≠ t₀.val := fun h => hsu (Fin.ext (by simp [Fin.val_succ, h]))
          have hcs_v : t.val ≠ t₀.val + 1 := fun h =>
            hcs (Fin.ext (by simp [Fin.val_castSucc, Fin.val_succ, h]))
          by_cases h3 : t₀.val + 1 < t.val
          · rw [if_pos (by rw [hsucc_val]; omega : t₀.val + 1 < t.succ.val),
              if_pos (by rw [hcast_val]; omega : t₀.val + 1 < t.castSucc.val)]
          · rw [if_neg (by rw [hsucc_val]; omega : ¬(t₀.val + 1 < t.succ.val)),
              if_neg (by rw [hcast_val]; omega : ¬(t₀.val + 1 < t.castSucc.val))]
    -- Zero initial cost
    have θbh_zc : ∀ ω : Ω, discountedValueProcess m θbh ⟨0, Nat.zero_lt_succ m.T⟩ ω = 0 := fun ω => by
      have hz_ne : (⟨0, Nat.zero_lt_succ m.T⟩ : Fin (m.T+1)) ≠ t₀.succ :=
        Fin.ne_of_val_ne (by simp [Fin.val_succ])
      have hz_hold : ∀ x : Fin m.n,
          (if x = i₀ ∧ (⟨0, Nat.zero_lt_succ m.T⟩ : Fin (m.T+1)) = t₀.succ then g ω else (0:ℝ)) = 0 :=
        fun x => if_neg (fun h => hz_ne h.2)
      simp only [θbh, discountedValueProcess, hz_hold,
        zero_mul, Finset.sum_const_zero, zero_add,
        if_neg hz_ne,
        if_neg (show ¬(t₀.val + 1 < (⟨0, Nat.zero_lt_succ m.T⟩ : Fin (m.T+1)).val) from by simp)]
    -- Terminal value = g * (D_i₀(t₀+1) − D_i₀(t₀))
    have θbh_terminal : ∀ ω : Ω,
        discountedValueProcess m θbh ⟨m.T, Nat.lt_succ_self m.T⟩ ω =
        g ω * (discountedPrice m i₀ t₀.succ ω - discountedPrice m i₀ t₀.castSucc ω) := fun ω => by
      simp only [θbh, discountedValueProcess]
      by_cases hTsucc : (⟨m.T, Nat.lt_succ_self m.T⟩ : Fin (m.T+1)) = t₀.succ
      · -- t₀.val = m.T - 1: holdings at T = g, bond = -(g * D_i₀(t₀.castSucc))
        simp only [hTsucc, and_true, ite_mul, zero_mul,
          Finset.sum_ite_eq', Finset.mem_univ, if_true]
        ring
      · -- t₀.val + 1 < m.T: holdings at T = 0, bond = g*(D_i₀(t₀+1)−D_i₀(t₀))
        have hT_ne : t₀.val + 1 ≠ m.T := fun h =>
          hTsucc (Fin.ext (by simp [Fin.val_succ]; omega))
        have hTgt : t₀.val + 1 < (⟨m.T, Nat.lt_succ_self m.T⟩ : Fin (m.T+1)).val := by
          show t₀.val + 1 < m.T; have := t₀.isLt; omega
        have hT_hold : ∀ x : Fin m.n,
            (if x = i₀ ∧ (⟨m.T, Nat.lt_succ_self m.T⟩ : Fin (m.T+1)) = t₀.succ
              then g ω else (0:ℝ)) = 0 :=
          fun x => if_neg (fun h => hTsucc h.2)
        simp only [hT_hold, zero_mul, Finset.sum_const_zero, zero_add,
          if_neg hTsucc, if_pos hTgt]
    -- θbh is in attainablePayoffs
    have θbh_attain : (fun ω => g ω * (discountedPrice m i₀ t₀.succ ω -
        discountedPrice m i₀ t₀.castSucc ω)) ∈ attainablePayoffs m :=
      ⟨θbh, θbh_sf, θbh_zc, funext fun ω => (θbh_terminal ω).symm⟩
    -- Apply hq_vanish and reorganize: the attainable payoff is g·(D_succ − D_cast),
    -- so ∑ q·(g·(D_succ − D_cast)) = 0; rewrite termwise to the goal's grouping via ring.
    have hv := hq_vanish _ θbh_attain
    rw [← hv]
    exact Finset.sum_congr rfl (fun ω _ => by ring)
  -- Now build the martingale for each asset
  intro i₀
  refine ⟨fun t => (discountedPrice_adapted m i₀ t).stronglyMeasurable, fun s_time t_time hst => ?_⟩
  -- Induction on the time gap (mirrors Q4.4-b)
  suffices key : ∀ (k : ℕ) (j : Fin (m.T + 1)), j.val = s_time.val + k →
      pmf.toMeasure[discountedPrice m i₀ j | m.𝒻 s_time] =ᵐ[pmf.toMeasure]
      discountedPrice m i₀ s_time from
    key (t_time.val - s_time.val) t_time (by omega)
  intro k
  induction k with
  | zero =>
    intro j hj
    have hjs : j = s_time := Fin.ext (by omega)
    rw [hjs]
    have heq : pmf.toMeasure[discountedPrice m i₀ s_time | m.𝒻 s_time] =
        discountedPrice m i₀ s_time :=
      MeasureTheory.condExp_of_stronglyMeasurable (m.𝒻.le s_time)
        (discountedPrice_adapted m i₀ s_time).stronglyMeasurable
        (MeasureTheory.Integrable.of_finite (μ := pmf.toMeasure))
    exact Filter.EventuallyEq.of_eq heq
  | succ k ih =>
    intro j hj
    have hklt : s_time.val + k < m.T := by have := j.isLt; omega
    let mid : Fin m.T := ⟨s_time.val + k, hklt⟩
    have hjmid : j = mid.succ := Fin.ext (by simp [mid]; omega)
    have hs_le_mid : s_time ≤ mid.castSucc := by
      simp only [Fin.le_def, Fin.val_castSucc, mid]; omega
    rw [hjmid]
    -- One-step: Q[D_i₀(mid+1) | ℱ_mid] =ᵐ D_i₀(mid)
    have one_step : pmf.toMeasure[discountedPrice m i₀ mid.succ | m.𝒻 mid.castSucc] =ᵐ[pmf.toMeasure]
        discountedPrice m i₀ mid.castSucc := by
      haveI : MeasureTheory.SigmaFinite
          (pmf.toMeasure.trim (m.𝒻.le mid.castSucc)) := inferInstance
      -- Use ae_eq_condExp_of_forall_setIntegral_eq: D_i₀(mid) is the condExp of D_i₀(mid+1)
      have hgm := (discountedPrice_adapted m i₀ mid.castSucc).stronglyMeasurable.aestronglyMeasurable
        (μ := pmf.toMeasure)
      apply (MeasureTheory.ae_eq_condExp_of_forall_setIntegral_eq (m.𝒻.le mid.castSucc)
        (MeasureTheory.Integrable.of_finite (μ := pmf.toMeasure))
        (fun _ _ _ => MeasureTheory.Integrable.of_finite.integrableOn)
        _ hgm).symm
      -- Set integral condition: ∫_{s_set} D_i₀(mid) ∂Q = ∫_{s_set} D_i₀(mid+1) ∂Q
      intro s_set hs_set _
      have hs_global : MeasurableSet s_set := (m.𝒻.le mid.castSucc) s_set hs_set
      -- Indicator measurability with respect to m.𝒻 mid.castSucc
      have hg_meas : @Measurable Ω ℝ (m.𝒻 mid.castSucc) _ (s_set.indicator (fun _ => (1:ℝ))) :=
        Measurable.indicator
          (@measurable_const ℝ Ω _ (m.𝒻 mid.castSucc) (1:ℝ)) hs_set
      -- Apply hq_step with g = 1_{s_set}
      have hstep := hq_step i₀ mid (s_set.indicator (fun _ => 1)) hg_meas
      -- Convert ∑ q * 1_s * (D_succ − D_cast) = 0 to set integrals equal
      -- ∫_{s_set} F ∂Q = ∑_ω (q ω / Z) * (s_set.indicator F ω)
      have hint_eq : ∀ (F : Ω → ℝ),
          ∫ ω in s_set, F ω ∂pmf.toMeasure =
          ∑ ω : Ω, (q ω / Z) * s_set.indicator F ω := fun F => by
        rw [← MeasureTheory.integral_indicator hs_global]
        rw [PMF.integral_eq_sum]
        congr 1; ext ω
        rw [hpmf_val]; simp [smul_eq_mul]
      rw [hint_eq, hint_eq]
      -- Now both sides are ∑ (q/Z) * 1_s * D; use hstep to equate them
      -- hstep : ∑ ω, q ω * 1_s ω * (D_succ ω - D_cast ω) = 0
      have key : ∀ ω : Ω,
          q ω * s_set.indicator (fun _ => (1:ℝ)) ω *
          (discountedPrice m i₀ mid.succ ω - discountedPrice m i₀ mid.castSucc ω) =
          q ω * s_set.indicator (discountedPrice m i₀ mid.succ) ω -
          q ω * s_set.indicator (discountedPrice m i₀ mid.castSucc) ω := fun ω => by
        by_cases hω : ω ∈ s_set
        · simp only [Set.indicator_of_mem hω]; ring
        · simp only [Set.indicator_of_notMem hω]; ring
      have hstep' : ∑ ω : Ω, (q ω * s_set.indicator (discountedPrice m i₀ mid.succ) ω -
          q ω * s_set.indicator (discountedPrice m i₀ mid.castSucc) ω) = 0 := by
        simp_rw [← key]; exact hstep
      rw [Finset.sum_sub_distrib] at hstep'
      have hinner : ∑ ω : Ω, q ω * s_set.indicator (discountedPrice m i₀ mid.castSucc) ω =
          ∑ ω : Ω, q ω * s_set.indicator (discountedPrice m i₀ mid.succ) ω := by linarith
      -- Divide both sides by Z (factor out 1/Z from each term).
      calc ∑ ω : Ω, (q ω / Z) * s_set.indicator (discountedPrice m i₀ mid.castSucc) ω
          = (∑ ω : Ω, q ω * s_set.indicator (discountedPrice m i₀ mid.castSucc) ω) / Z := by
            rw [Finset.sum_div]; apply Finset.sum_congr rfl; intro ω _; ring
        _ = (∑ ω : Ω, q ω * s_set.indicator (discountedPrice m i₀ mid.succ) ω) / Z := by rw [hinner]
        _ = ∑ ω : Ω, (q ω / Z) * s_set.indicator (discountedPrice m i₀ mid.succ) ω := by
            rw [Finset.sum_div]; apply Finset.sum_congr rfl; intro ω _; ring
    calc pmf.toMeasure[discountedPrice m i₀ mid.succ | m.𝒻 s_time]
        =ᵐ[pmf.toMeasure]
          pmf.toMeasure[pmf.toMeasure[discountedPrice m i₀ mid.succ | m.𝒻 mid.castSucc] | m.𝒻 s_time] :=
          (MeasureTheory.Filtration.condExp_condExp _ m.𝒻 hs_le_mid).symm
      _ =ᵐ[pmf.toMeasure] pmf.toMeasure[discountedPrice m i₀ mid.castSucc | m.𝒻 s_time] :=
          MeasureTheory.condExp_congr_ae one_step
      _ =ᵐ[pmf.toMeasure] discountedPrice m i₀ s_time :=
          ih mid.castSucc (by simp [mid])

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
