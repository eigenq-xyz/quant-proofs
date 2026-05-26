import FtapProofs.Strategy
import Mathlib.Probability.Martingale.Basic
import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic
import Mathlib.MeasureTheory.Function.ConditionalExpectation.PullOut

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
- **Q4.5** `risk_neutral_pricing` — `Ṽ 0 θ = E^Q [Ṽ T θ]` under any EMM

## Sorry ledger

- **Q4.4** (StronglyAdapted): `∑_i θ.holdings i t · discountedPrice m i t` is
  `ℱ t`-strongly measurable — needs measurability of a sum of products of a
  `ℱ t`-adapted process (holdings, predictable hence adapted) and the adapted
  discounted price. Tactic: `Finset.stronglyMeasurable_sum + StronglyMeasurable.mul`.

- **Q4.4** (condExp): `condExp (ℱ t) Q (Ṽ (t+1) θ) = Ṽ t θ` a.e. — requires
  linearity of condExp over the sum, pulling out the predictable factor
  (`condExp_smul_of_aestronglyMeasurable_left`), and the tower property
  (`condExp_condExp_of_le (h : ℱ t ≤ ℱ (t+1))`).

- **Q4.5**: follows from Q4.4 via `Martingale.condExp` at times `0 ≤ T`.
-/

namespace FtapProofs

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

    **Proof sketch:**
    - *StronglyAdapted*: `Ṽ t θ ω = ∑_i θ.holdings i t ω * discountedPrice m i t ω`.
      The holdings are predictable (hence `ℱ t`-measurable by adaptedness one step forward),
      and `discountedPrice m i t` is `ℱ t`-measurable by `m.S_adapted`. The sum of products
      is `ℱ t`-measurable.
    - *condExp*: For any `t`, using `selfFinancing m θ` we have
      `Ṽ (t+1) θ = ∑_i θ.holdings i (t+1) * discountedPrice m i (t+1)`.
      Taking `E^Q[· | ℱ t]` and using that `θ.holdings i (t+1)` is `ℱ t`-predictable
      (pull out via `condExp_smul_of_aestronglyMeasurable_left`) together with the
      martingale property of `discountedPrice m i` gives the result. -/
theorem discountedValue_martingale_of_emm (m : FinancialMarket Ω)
    (θ : TradingStrategy m) (hθ : selfFinancing m θ)
    (Q : MeasureTheory.Measure Ω) (hQ : EquivalentMartingaleMeasure m Q) :
    MeasureTheory.Martingale (discountedValueProcess m θ) m.𝒻 Q := by
  constructor
  · -- StronglyAdapted: Ṽ t θ is ℱ t-measurable
    intro t
    sorry
    -- Tactic path:
    -- show StronglyMeasurable[m.𝒻 t] (discountedValueProcess m θ t)
    -- unfold discountedValueProcess; simp only
    -- apply Finset.stronglyMeasurable_sum
    -- intro i _
    -- apply StronglyMeasurable.mul
    -- · -- holdings: θ.predictable gives ℱ_{prevTime t}-measurability.
    --   -- Need to lift to ℱ_t via filtration monotonicity:
    --   -- (θ.predictable i t).mono (m.𝒻.mono (Fin.castSucc_le_succ t) Ω rfl)
    --   --   or more precisely: StronglyMeasurable.mono with the comap argument.
    -- · exact (m.S_adapted i t).stronglyMeasurable    -- S adapted → ℱ_t-meas for discountedPrice
  · -- condExp property: E^Q[Ṽ (t+1) θ | ℱ t] = Ṽ t θ a.e.
    intro t ht
    sorry
    -- Tactic path: use selfFinancing to rewrite Ṽ (t+1) in terms of holdings at t+1
    -- then use linearity of condExp over sum, predictability of holdings,
    -- and martingale property of discountedPrice m i under Q.

/-! ### Q4.5 Risk-neutral pricing formula -/

/-- **Risk-neutral pricing**: Under any EMM `Q`, the discounted initial value equals
    the `Q`-expectation of the discounted terminal payoff:
    `E^Q [Ṽ T θ] = Ṽ 0 θ ω` for any `ω`.

    This follows from `discountedValue_martingale_of_emm` via the optional sampling /
    martingale property at times `0 ≤ T`. -/
theorem risk_neutral_pricing (m : FinancialMarket Ω)
    (θ : TradingStrategy m) (hθ : selfFinancing m θ)
    (Q : MeasureTheory.Measure Ω) (hQ : EquivalentMartingaleMeasure m Q)
    (ω₀ : Ω) :
    MeasureTheory.integral Q (discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩) =
    discountedValueProcess m θ ⟨0, Nat.zero_lt_succ m.T⟩ ω₀ := by
  sorry
  -- Tactic path:
  -- have hmart := discountedValue_martingale_of_emm m θ hθ Q hQ
  -- Since Ṽ 0 θ is constant (same for all ω), use integral_const.
  -- Apply hmart.condExp with le_refl together with integral_condExp
  -- to get ∫ Ṽ T θ dQ = ∫ Ṽ 0 θ dQ = Ṽ 0 θ ω₀.

end FtapProofs
