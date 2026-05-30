import FtapProofs.Strategy
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Fin
import Mathlib.MeasureTheory.Measure.MeasureSpace

/-!
# No-Arbitrage

An **arbitrage opportunity** is a self-financing strategy that:
1. Costs nothing to initiate: `Ṽ 0 θ ω = 0` for all `ω`
2. Cannot lose money: `Ṽ T θ ω ≥ 0` for all `ω`
3. Has a strict profit in some state: `∃ ω, Ṽ T θ ω > 0`

In the finite-state setting, almost-sure qualifiers reduce to pointwise conditions.

## Contents

- **A3.1** `ArbitrageOpportunity` — a self-financing strategy violating NA
- **A3.2** `NoArbitrage` — the NA condition: no `ArbitrageOpportunity` exists
- **A3.3** `attainablePayoffs` — the set K of discounted terminal payoffs from zero-cost
           self-financing strategies
- **A3.4** `attainablePayoffs_isLinearSubspace` — K is a linear subspace of `Ω → ℝ`
           (zero, add, and scalar-multiple closure stated as a conjunction)
- **A3.5** `noArbitrage_iff_attainable_nonneg_eq_zero` — NA ↔ K ∩ ℝ₊^Ω = {0}
-/

namespace FtapProofs

open BigOperators

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### A3.1 Arbitrage opportunity -/

/-- **A3.1** An **arbitrage opportunity** is a self-financing trading strategy that:
- costs nothing at time 0 (zero initial discounted value),
- cannot lose money at time T (non-negative discounted terminal value everywhere), and
- has a strictly positive payoff in at least one state.

This is a "free lottery ticket": the strategy cannot lose and can win. -/
structure ArbitrageOpportunity (m : FinancialMarket Ω) where
  /-- The underlying trading strategy -/
  θ : TradingStrategy m
  /-- The strategy is self-financing (no external cash injections) -/
  sf : selfFinancing m θ
  /-- Zero initial cost: `Ṽ 0 θ ω = 0` for all `ω` -/
  zero_cost : ∀ ω : Ω,
    discountedValueProcess m θ ⟨0, Nat.zero_lt_succ m.T⟩ ω = 0
  /-- Cannot lose money: `Ṽ T θ ω ≥ 0` for all `ω` -/
  nonneg : ∀ ω : Ω,
    0 ≤ discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω
  /-- Positive profit in some state: `∃ ω, Ṽ T θ ω > 0` -/
  profit : ∃ ω : Ω,
    0 < discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω

/-! ### A3.2 No-arbitrage condition -/

/-- **A3.2** A market satisfies **no-arbitrage (NA)** if no arbitrage opportunity exists. -/
def NoArbitrage (m : FinancialMarket Ω) : Prop :=
  ¬Nonempty (ArbitrageOpportunity m)

/-! ### A3.3 Attainable payoffs -/

/-- **A3.3** The set `K` of **attainable discounted terminal payoffs** from zero-cost
    self-financing strategies:
    ```
    K = { f : Ω → ℝ | ∃ θ, selfFinancing θ ∧ Ṽ 0 θ = 0 ∧ f = Ṽ T θ }
    ```
    By A3.4, `K` is a linear subspace of `Ω → ℝ`. The FTAP characterization (A3.5)
    says NA is equivalent to `K ∩ ℝ₊^Ω = {0}`. -/
def attainablePayoffs (m : FinancialMarket Ω) : Set (Ω → ℝ) :=
  {f | ∃ θ : TradingStrategy m,
      selfFinancing m θ ∧
      (∀ ω : Ω, discountedValueProcess m θ ⟨0, Nat.zero_lt_succ m.T⟩ ω = 0) ∧
      f = fun ω => discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω}

/-! ### Helper strategies for subspace proofs -/

/-- The zero strategy: hold 0 units of every asset and 0 units of the bond at every time. -/
private def zeroStrategy (m : FinancialMarket Ω) : TradingStrategy m where
  holdings _ _ _ := 0
  predictable _ _ := measurable_const
  bondHolding _ _ := 0
  bondPredictable _ := measurable_const

/-- Self-financing property of the zero strategy. -/
private lemma sf_zeroStrategy (m : FinancialMarket Ω) :
    selfFinancing m (zeroStrategy m) := by
  intro t ω
  simp [zeroStrategy]

/-- The zero strategy has zero discounted value at all times. -/
private lemma dvp_zeroStrategy_eq_zero (m : FinancialMarket Ω) (t : Fin (m.T + 1)) (ω : Ω) :
    discountedValueProcess m (zeroStrategy m) t ω = 0 := by
  simp [discountedValueProcess, zeroStrategy]

/-- Sum of two strategies: add risky asset holdings and bond holdings pointwise. -/
private def sumStrategy (m : FinancialMarket Ω) (θ₁ θ₂ : TradingStrategy m) :
    TradingStrategy m where
  holdings i t ω := θ₁.holdings i t ω + θ₂.holdings i t ω
  predictable i t := (θ₁.predictable i t).add (θ₂.predictable i t)
  bondHolding t ω := θ₁.bondHolding t ω + θ₂.bondHolding t ω
  bondPredictable t := (θ₁.bondPredictable t).add (θ₂.bondPredictable t)

/-- Self-financing is preserved under addition of strategies. -/
private lemma sf_sumStrategy (m : FinancialMarket Ω) (θ₁ θ₂ : TradingStrategy m)
    (h₁ : selfFinancing m θ₁) (h₂ : selfFinancing m θ₂) :
    selfFinancing m (sumStrategy m θ₁ θ₂) := by
  intro t ω
  simp only [sumStrategy, add_mul, Finset.sum_add_distrib]
  linarith [h₁ t ω, h₂ t ω]

/-- The discounted value process of a sum is the sum of discounted value processes. -/
private lemma dvp_sumStrategy (m : FinancialMarket Ω) (θ₁ θ₂ : TradingStrategy m)
    (t : Fin (m.T + 1)) (ω : Ω) :
    discountedValueProcess m (sumStrategy m θ₁ θ₂) t ω =
    discountedValueProcess m θ₁ t ω + discountedValueProcess m θ₂ t ω := by
  simp only [discountedValueProcess, sumStrategy, add_mul, Finset.sum_add_distrib]
  ring

/-- Scalar multiple of a strategy. -/
private def smulStrategy (m : FinancialMarket Ω) (c : ℝ) (θ : TradingStrategy m) :
    TradingStrategy m where
  holdings i t ω := c * θ.holdings i t ω
  predictable i t := (θ.predictable i t).const_smul c
  bondHolding t ω := c * θ.bondHolding t ω
  bondPredictable t := (θ.bondPredictable t).const_smul c

/-- Self-financing is preserved under scalar multiplication of strategies. -/
private lemma sf_smulStrategy (m : FinancialMarket Ω) (c : ℝ) (θ : TradingStrategy m)
    (h : selfFinancing m θ) :
    selfFinancing m (smulStrategy m c θ) := by
  intro t ω
  simp only [smulStrategy, selfFinancing] at *
  -- Goal: ∑ i, c * θ_i(t+1) * D_i(t) + c * bondHolding(t+1) =
  --       ∑ i, c * θ_i(t)   * D_i(t) + c * bondHolding(t)
  -- h: ∑ i, θ_i(t+1) * D_i(t) + bondHolding(t+1) = ∑ i, θ_i(t) * D_i(t) + bondHolding(t)
  simp only [mul_assoc, ← Finset.mul_sum, ← mul_add]
  congr 1
  exact h t ω

/-- The discounted value process of a scalar multiple is the scalar multiple of the process. -/
private lemma dvp_smulStrategy (m : FinancialMarket Ω) (c : ℝ) (θ : TradingStrategy m)
    (t : Fin (m.T + 1)) (ω : Ω) :
    discountedValueProcess m (smulStrategy m c θ) t ω =
    c * discountedValueProcess m θ t ω := by
  simp only [discountedValueProcess, smulStrategy, mul_assoc, ← Finset.mul_sum, mul_add]

/-! ### A3.4 Attainable payoffs form a linear subspace -/

/-- **A3.4** The set `K = attainablePayoffs m` is a linear subspace of `Ω → ℝ`:
    it contains zero, is closed under pointwise addition, and closed under scalar
    multiplication.

    **Proof:** Closure follows from the corresponding helper strategies:
    - *Zero*: the zero strategy `zeroStrategy m` witnesses `0 ∈ K`.
    - *Addition*: `sumStrategy m θ₁ θ₂` witnesses `f + g ∈ K` when `θ₁` witnesses `f`
      and `θ₂` witnesses `g`.
    - *Scalar multiple*: `smulStrategy m c θ` witnesses `c • f ∈ K` when `θ` witnesses `f`. -/
theorem attainablePayoffs_isLinearSubspace (m : FinancialMarket Ω) :
    (0 : Ω → ℝ) ∈ attainablePayoffs m ∧
    (∀ f g : Ω → ℝ, f ∈ attainablePayoffs m → g ∈ attainablePayoffs m →
        f + g ∈ attainablePayoffs m) ∧
    (∀ (c : ℝ) (f : Ω → ℝ), f ∈ attainablePayoffs m → c • f ∈ attainablePayoffs m) := by
  refine ⟨?_, ?_, ?_⟩
  · -- Zero: the zero strategy witnesses 0 ∈ K
    exact ⟨zeroStrategy m, sf_zeroStrategy m,
      fun ω => dvp_zeroStrategy_eq_zero m _ ω,
      funext fun ω => (dvp_zeroStrategy_eq_zero m ⟨m.T, Nat.lt_succ_self m.T⟩ ω).symm⟩
  · -- Addition: sumStrategy m θ₁ θ₂ witnesses f + g ∈ K
    rintro f g ⟨θ₁, hsf₁, hzc₁, hf⟩ ⟨θ₂, hsf₂, hzc₂, hg⟩
    refine ⟨sumStrategy m θ₁ θ₂, sf_sumStrategy m θ₁ θ₂ hsf₁ hsf₂,
      fun ω => by
        have h := dvp_sumStrategy m θ₁ θ₂ ⟨0, Nat.zero_lt_succ m.T⟩ ω
        linarith [hzc₁ ω, hzc₂ ω],
      funext fun ω => ?_⟩
    simp only [Pi.add_apply, dvp_sumStrategy]
    exact congr_arg₂ (· + ·) (congr_fun hf ω) (congr_fun hg ω)
  · -- Scalar multiplication: smulStrategy m c θ witnesses c • f ∈ K
    rintro c f ⟨θ, hsf, hzc, hf⟩
    refine ⟨smulStrategy m c θ, sf_smulStrategy m c θ hsf,
      fun ω => by
        have h := dvp_smulStrategy m c θ ⟨0, Nat.zero_lt_succ m.T⟩ ω
        rw [h, hzc ω, mul_zero],
      funext fun ω => ?_⟩
    simp only [Pi.smul_apply, smul_eq_mul, dvp_smulStrategy]
    congr 1
    exact congr_fun hf ω

/-! ### A3.5 NA is equivalent to K ∩ ℝ₊^Ω = {0} -/

/-- **A3.5** The market is arbitrage-free if and only if the only attainable payoff that
    is everywhere non-negative is the zero payoff.

    **Proof:**
    - (→) If NA holds and `f ∈ K` with `f ω ≥ 0` for all `ω`, suppose for contradiction
      that `f ≠ 0`. Then `∃ ω₀, f ω₀ > 0`. But the strategy `θ` realizing `f` is an
      arbitrage opportunity, contradicting NA.
    - (←) If the only non-negative attainable payoff is zero, suppose `θ` is an arbitrage.
      Then `Ṽ T θ ∈ K`, `Ṽ T θ ≥ 0` everywhere, and `Ṽ T θ ≠ 0`. Contradiction. -/
theorem noArbitrage_iff_attainable_nonneg_eq_zero (m : FinancialMarket Ω) :
    NoArbitrage m ↔
    ∀ f ∈ attainablePayoffs m, (∀ ω : Ω, 0 ≤ f ω) → f = fun _ => 0 := by
  constructor
  · -- (→) NA → K ∩ ℝ₊^Ω = {0}
    intro hNA f ⟨θ, hsf, hzc, hf⟩ hnn
    by_contra hf_ne
    -- f is not identically zero, so some ω₀ has f ω₀ > 0
    have hexists : ∃ ω₀ : Ω, f ω₀ > 0 := by
      by_contra hall
      push Not at hall
      apply hf_ne
      funext ω
      exact le_antisymm (hall ω) (hnn ω)
    obtain ⟨ω₀, hω₀⟩ := hexists
    -- Build an ArbitrageOpportunity from θ
    apply hNA
    refine ⟨⟨θ, hsf, hzc, fun ω => ?_, ⟨ω₀, ?_⟩⟩⟩
    · have heq : f ω = discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω :=
        congr_fun hf ω
      linarith [hnn ω]
    · have heq : f ω₀ = discountedValueProcess m θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω₀ :=
        congr_fun hf ω₀
      linarith
  · -- (←) K ∩ ℝ₊^Ω = {0} → NA
    intro hK ⟨arb⟩
    -- The terminal payoff of arb is in K and is non-negative
    have hf_in_K : (fun ω => discountedValueProcess m arb.θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω)
        ∈ attainablePayoffs m :=
      ⟨arb.θ, arb.sf, arb.zero_cost, rfl⟩
    -- By hypothesis, the payoff must be zero everywhere
    have hf_zero := hK _ hf_in_K arb.nonneg
    -- But arb has profit in some state
    obtain ⟨ω₀, hω₀⟩ := arb.profit
    -- Contradiction: hf_zero says f ω₀ = 0 but hω₀ says f ω₀ > 0
    have : discountedValueProcess m arb.θ ⟨m.T, Nat.lt_succ_self m.T⟩ ω₀ = 0 :=
      congr_fun hf_zero ω₀
    linarith

end FtapProofs
