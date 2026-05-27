import FtapProofs.Strategy
import Mathlib.Probability.Martingale.Basic
import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic
import Mathlib.MeasureTheory.Function.ConditionalExpectation.PullOut
import Mathlib.Order.Filter.CountableInter

/-!
# Equivalent Martingale Measure

A probability measure `Q` on `(Ω, ℱ)` is an **equivalent martingale measure** (EMM) if:

1. **Equivalence**: `Q ~ P`, meaning `Q A > 0 ↔ P A > 0` for all `A ∈ ℱ`.
   In the finite-state case this means `Q {ω} > 0` for all `ω ∈ Ω`.

2. **Martingale property**: the discounted asset price processes `S̃ i` are
   `Q`-martingales:
   `E^Q [S̃ i (t+1) | ℱ_t] = S̃ i t`  for all `i`, `t`.

## Contents

- **Q4.1** `EquivalentMeasure` — measure equivalence `Q ~ P`
- **Q4.2** `IsMartingaleMeasure` — discounted prices are `Q`-martingales
- **Q4.3** `EquivalentMartingaleMeasure` — the EMM condition
- **Q4.4** `discountedValue_martingale_of_emm` — under an EMM, the discounted value
           process of any self-financing strategy is a `Q`-martingale
- **Q4.5** `risk_neutral_pricing` — `∫ Ṽ T ∂Q = ∫ Ṽ 0 ∂Q` under any EMM

## Proof status

*All proof obligations in this file are fully discharged (no admitted goals).*
-/

namespace FtapProofs

open scoped MeasureTheory

variable {Ω : Type*} [Fintype Ω] [MeasurableSpace Ω] [MeasurableSingletonClass Ω]

/-! ### Q4.1 Equivalent measure -/

/-- A measure `Q` is equivalent to the market measure `P` if they agree on which events
    have positive probability. In the finite-state case this reduces to
    `Q {ω} > 0 ↔ P {ω} > 0` for each `ω`. -/
def EquivalentMeasure (m : FinancialMarket Ω) (Q : MeasureTheory.Measure Ω) : Prop :=
  MeasureTheory.IsProbabilityMeasure Q ∧ ∀ ω : Ω, 0 < m.P {ω} ↔ 0 < Q {ω}

/-! ### Q4.2 Martingale measure -/

/-- A measure `Q` is a martingale measure for market `m` if the discounted price of each
    asset `i` is a `Q`-martingale with respect to the market filtration `𝒻`. -/
def IsMartingaleMeasure (m : FinancialMarket Ω) (Q : MeasureTheory.Measure Ω) : Prop :=
  ∀ i : Fin m.n, MeasureTheory.Martingale (discountedPrice m i) m.𝒻 Q

/-! ### Q4.3 Equivalent martingale measure -/

/-- An **equivalent martingale measure** (EMM) satisfies both `Q ~ P` and the
    martingale property for all discounted asset prices. The FTAP asserts that
    such a `Q` exists if and only if the market is arbitrage-free. -/
def EquivalentMartingaleMeasure (m : FinancialMarket Ω) (Q : MeasureTheory.Measure Ω) : Prop :=
  EquivalentMeasure m Q ∧ IsMartingaleMeasure m Q

/-! ### Q4.4 Value process is a martingale under any EMM -/

/-- Under any EMM `Q`, the discounted value process `Ṽ t θ` of a self-financing strategy
    `θ` is a `Q`-martingale.

    **Proof:**
    - *StronglyAdapted*: `Ṽ t θ = ∑_i θ.holdings i t * discountedPrice m i t`.
      Holdings are predictable (hence `ℱ t`-adapted) and prices are `ℱ t`-adapted;
      the sum of products is `ℱ t`-strongly measurable.
    - *condExp one-step*: `E^Q[Ṽ(t+1) | ℱ t] =ᵐ Ṽ t` by linearity of condExp,
      the pull-out property (holdings are `ℱ t`-predictable), and the martingale
      property of each discounted price; the self-financing condition then identifies
      the result as `Ṽ t`.
    - *General case*: induction on the time gap, using the tower property of condExp. -/
theorem discountedValue_martingale_of_emm (m : FinancialMarket Ω)
    (θ : TradingStrategy m) (hθ : selfFinancing m θ)
    (Q : MeasureTheory.Measure Ω) (hQ : EquivalentMartingaleMeasure m Q) :
    MeasureTheory.Martingale (discountedValueProcess m θ) m.𝒻 Q := by
  have hQprob : MeasureTheory.IsProbabilityMeasure Q := hQ.1.1
  have hQmart : IsMartingaleMeasure m Q := hQ.2
  haveI : MeasureTheory.IsFiniteMeasure Q := inferInstance
  haveI : MeasureTheory.SigmaFiniteFiltration Q m.𝒻 := inferInstance
  -- StronglyAdapted branch
  have hadp : MeasureTheory.StronglyAdapted m.𝒻 (discountedValueProcess m θ) := by
    intro t
    have prevTime_le_t : FtapProofs.prevTime t ≤ t := by
      simp only [FtapProofs.prevTime, Fin.le_def]; exact Nat.pred_le _
    have key := Finset.stronglyMeasurable_sum Finset.univ
      (f := fun i ω => θ.holdings i t ω * discountedPrice m i t ω)
      fun i _ =>
        (((θ.predictable i t).mono (m.𝒻.mono prevTime_le_t) le_rfl).stronglyMeasurable).mul
        (discountedPrice_adapted m i t).stronglyMeasurable
    convert key using 1
    ext ω; simp [discountedValueProcess, Finset.sum_apply]
  constructor
  · exact hadp
  · -- condExp branch: E^Q[Ṽ j | ℱ i] =ᵐ Ṽ i for i ≤ j
    intro i j hij
    -- One-step lemma: E^Q[Ṽ(t+1) | ℱ t] =ᵐ Ṽ t
    have one_step : ∀ (t : Fin m.T),
        Q[discountedValueProcess m θ t.succ | m.𝒻 t.castSucc] =ᵐ[Q]
        discountedValueProcess m θ t.castSucc := fun t => by
      -- Per-asset pull-out: E^Q[θ_a(t+1) * S̃_a(t+1) | ℱ t] =ᵐ θ_a(t+1) * S̃_a t
      have ae_per_asset : ∀ a : Fin m.n,
          Q[fun ω => θ.holdings a t.succ ω * discountedPrice m a t.succ ω |
              m.𝒻 t.castSucc] =ᵐ[Q]
          fun ω => θ.holdings a t.succ ω * discountedPrice m a t.castSucc ω := fun a => by
        -- Holdings at t+1 are ℱ t-measurable by predictability
        have hmeas : StronglyMeasurable[m.𝒻 t.castSucc] (θ.holdings a t.succ) := by
          have h := θ.predictable a t.succ
          rw [FtapProofs.prevTime_succ] at h
          exact h.stronglyMeasurable
        -- Pull out the ℱ t-measurable factor (explicit f/g to help elaboration)
        have hpull := MeasureTheory.condExp_mul_of_stronglyMeasurable_left
          (μ := Q) (m := m.𝒻 t.castSucc)
          (f := θ.holdings a t.succ) (g := discountedPrice m a t.succ)
          hmeas MeasureTheory.Integrable.of_finite MeasureTheory.Integrable.of_finite
        -- Martingale step: E^Q[S̃_a(t+1) | ℱ t] =ᵐ S̃_a t
        have hmart_step := (hQmart a).condExp_ae_eq (Fin.castSucc_le_succ t)
        filter_upwards [hpull, hmart_step] with ω hω1 hω2
        -- hpull uses Pi.mul form; goal uses lambda form. They're definitionally equal.
        change Q[θ.holdings a t.succ * discountedPrice m a t.succ | m.𝒻 t.castSucc] ω =
          θ.holdings a t.succ ω * discountedPrice m a t.castSucc ω
        rw [hω1]
        simp only [Pi.mul_apply, hω2]
      -- Expand Ṽ(t+1) as a Finset sum
      have dvp_eq : discountedValueProcess m θ t.succ =
          ∑ a ∈ Finset.univ,
            (fun ω => θ.holdings a t.succ ω * discountedPrice m a t.succ ω) := by
        ext ω; simp [discountedValueProcess]
      rw [dvp_eq]
      calc Q[∑ a ∈ Finset.univ,
                 (fun ω => θ.holdings a t.succ ω * discountedPrice m a t.succ ω) |
                 m.𝒻 t.castSucc]
          =ᵐ[Q] ∑ a ∈ Finset.univ,
              Q[fun ω => θ.holdings a t.succ ω * discountedPrice m a t.succ ω |
                  m.𝒻 t.castSucc] :=
            MeasureTheory.condExp_finsetSum
              (fun _ _ => MeasureTheory.Integrable.of_finite) (m.𝒻 t.castSucc)
        _ =ᵐ[Q] fun ω => ∑ a : Fin m.n,
              θ.holdings a t.succ ω * discountedPrice m a t.castSucc ω := by
            filter_upwards [eventually_countable_forall.mpr ae_per_asset] with ω hω
            simp only [Finset.sum_apply]
            exact Finset.sum_congr rfl fun a _ => hω a
        _ = discountedValueProcess m θ t.castSucc := by
            -- self-financing: ∑_a holdings(t+1) * S̃_a t = ∑_a holdings_t * S̃_a t = Ṽ t
            ext ω; simp only [discountedValueProcess]; exact hθ t ω
    -- General case: induction on k = j.val - i.val
    suffices key : ∀ (k : ℕ) (j : Fin (m.T + 1)), j.val = i.val + k →
        Q[discountedValueProcess m θ j | m.𝒻 i] =ᵐ[Q] discountedValueProcess m θ i from
      key (j.val - i.val) j (by omega)
    intro k
    induction k with
    | zero =>
      intro j hj
      have hjei : j = i := Fin.ext (by omega)
      rw [hjei, MeasureTheory.condExp_of_stronglyMeasurable (m.𝒻.le i) (hadp i)
        MeasureTheory.Integrable.of_finite]
    | succ k ih =>
      intro j hj
      have hklt : i.val + k < m.T := by have := j.isLt; omega
      let mid : Fin m.T := ⟨i.val + k, hklt⟩
      have hjmid : j = mid.succ := Fin.ext (by simp [mid]; omega)
      have hicmid : i ≤ mid.castSucc := by
        simp only [Fin.le_def, Fin.val_castSucc, mid]; omega
      rw [hjmid]
      calc Q[discountedValueProcess m θ mid.succ | m.𝒻 i]
          =ᵐ[Q] Q[Q[discountedValueProcess m θ mid.succ | m.𝒻 mid.castSucc] | m.𝒻 i] :=
            (MeasureTheory.Filtration.condExp_condExp
              (discountedValueProcess m θ mid.succ) m.𝒻 hicmid).symm
        _ =ᵐ[Q] Q[discountedValueProcess m θ mid.castSucc | m.𝒻 i] :=
            MeasureTheory.condExp_congr_ae (one_step mid)
        _ =ᵐ[Q] discountedValueProcess m θ i :=
            ih mid.castSucc (by simp [mid])

/-! ### Q4.5 Risk-neutral pricing formula -/

/-- **Risk-neutral pricing**: Under any EMM `Q`, the `Q`-expectation of the discounted
    terminal payoff equals the `Q`-expectation of the discounted initial value:
    ```
    ∫ Ṽ T θ ∂Q = ∫ Ṽ 0 θ ∂Q
    ```
    In particular, if `θ` is zero-cost (`Ṽ 0 θ ω = 0` for all `ω`), then
    `∫ Ṽ T θ ∂Q = 0`.

    **Proof:** The discounted value process is a `Q`-martingale by `discountedValue_martingale_of_emm`.
    The martingale condExp equality at times `0 ≤ T` together with `integral_condExp` gives the
    result. -/
theorem risk_neutral_pricing (m : FinancialMarket Ω)
    (θ : TradingStrategy m) (hθ : selfFinancing m θ)
    (Q : MeasureTheory.Measure Ω) (hQ : EquivalentMartingaleMeasure m Q) :
    MeasureTheory.integral Q (discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩) =
    MeasureTheory.integral Q (discountedValueProcess m θ ⟨0, Nat.zero_lt_succ m.T⟩) := by
  haveI : MeasureTheory.IsProbabilityMeasure Q := hQ.1.1
  haveI : MeasureTheory.IsFiniteMeasure Q := inferInstance
  haveI : MeasureTheory.SigmaFiniteFiltration Q m.𝒻 := inferInstance
  have hmart := discountedValue_martingale_of_emm m θ hθ Q hQ
  -- Martingale condExp at times 0 ≤ T: E^Q[Ṽ T | ℱ 0] =ᵐ Ṽ 0
  have hcondexp := hmart.condExp_ae_eq (Fin.zero_le ⟨m.T, Nat.lt_succ_self m.T⟩)
  -- integral_condExp: ∫ E^Q[Ṽ T | ℱ 0] ∂Q = ∫ Ṽ T ∂Q
  have hintcondexp := MeasureTheory.integral_condExp
    (hm := m.𝒻.le ⟨0, Nat.zero_lt_succ m.T⟩)
    (f := discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩) (μ := Q)
  rw [← hintcondexp]
  exact MeasureTheory.integral_congr_ae hcondexp

end FtapProofs
