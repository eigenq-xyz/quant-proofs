import ResearchPipeline.NoLookahead
import ResearchPipeline.Measurability

/-!
# Bridge: measure-theoretic adaptedness implies pointwise non-anticipation

`NoLookahead` states no-look-ahead **pointwise** (outcomes that agree on the observed
history up to `t` produce the same value at `t`); `Measurability` states it
**measure-theoretically** (the signal process is `Adapted` to the natural price
filtration, citing `ftap-proofs`). This module connects the two: the measure-theoretic
notion is the stronger one, and it *implies* the pointwise notion.

The forward direction proved here makes pointwise non-anticipation a corollary of
adaptedness. Concretely: if a real process is `𝓕ₜ`-measurable against the natural
filtration of the price observations, then it cannot tell apart two outcomes whose price
history agrees up to `t`. The reverse direction (pointwise dependence implies
measurability) needs a Doob-Dynkin factorization plus a measurable-dependence hypothesis
and is deliberately left out of scope.

The key sublemma `agreeUpTo_indistinguishable` is a `generateFrom` induction: the family of
events that cannot separate two history-agreeing outcomes contains every price-coordinate
preimage and is closed under complement and countable union, hence contains all of `𝓕ₜ`.
-/

open MeasureTheory MeasurableSpace

namespace ResearchPipeline

variable {Ω : Type*} [MeasurableSpace Ω]

/-- Two outcomes agree on the price history through time `t`: every observation `price s`
with `s ≤ t` takes the same value on both. This is the `Ω`-level form of
`ResearchPipeline.AgreeUpTo` (which is stated on explicit paths). -/
def AgreeUpToΩ (price : ℕ → Ω → ℝ) (ω ω' : Ω) (t : ℕ) : Prop :=
  ∀ s ≤ t, price s ω = price s ω'

/-- The σ-algebra of events that cannot separate two fixed outcomes `ω`, `ω'` (those `B` with
`ω ∈ B ↔ ω' ∈ B`). It is the upper bound used to constrain the natural filtration below. -/
@[reducible]
def indistinguishableSpace (ω ω' : Ω) : MeasurableSpace Ω where
  MeasurableSet' B := ω ∈ B ↔ ω' ∈ B
  measurableSet_empty := by simp
  measurableSet_compl B hB := by simp only [Set.mem_compl_iff]; exact not_congr hB
  measurableSet_iUnion f hf := by simp only [Set.mem_iUnion]; exact exists_congr hf

/-- **History-agreeing outcomes are indistinguishable by any `𝓕ₜ` event.** If `ω` and `ω'`
share the price history up to `t`, then they lie in exactly the same sets of the natural
filtration at time `t`. It suffices to show the natural filtration at `t` is no finer than
`indistinguishableSpace ω ω'`, which reduces over the `⨆` to each price coordinate `s ≤ t`,
where `price s ω = price s ω'` makes every preimage non-separating. -/
theorem agreeUpTo_indistinguishable
    (price : ℕ → Ω → ℝ) (hp : ∀ t, StronglyMeasurable (price t))
    {ω ω' : Ω} {t : ℕ} (h : AgreeUpToΩ price ω ω' t)
    {A : Set Ω} (hA : MeasurableSet[naturalFiltration price hp t] A) :
    ω ∈ A ↔ ω' ∈ A := by
  have hcoord : ∀ s, s ≤ t →
      MeasurableSpace.comap (price s) (inferInstance : MeasurableSpace ℝ)
        ≤ indistinguishableSpace ω ω' := by
    intro s hs B hB
    obtain ⟨C, _hC, rfl⟩ := hB
    show ω ∈ (price s) ⁻¹' C ↔ ω' ∈ (price s) ⁻¹' C
    rw [Set.mem_preimage, Set.mem_preimage, h s hs]
  have hle : naturalFiltration price hp t ≤ indistinguishableSpace ω ω' := by
    show ⨆ j, ⨆ (_ : j ≤ t), MeasurableSpace.comap (price j) _ ≤ indistinguishableSpace ω ω'
    exact iSup₂_le hcoord
  exact hle A hA

/-- **Forward bridge: a `𝓕ₜ`-adapted real process is pointwise non-anticipating.** If `X` is
adapted to the natural filtration of the price observations, then its value at time `t`
agrees on any two outcomes that share the price history up to `t`. This is the
measure-theoretic guarantee of `Measurability` discharging the pointwise guarantee of
`NoLookahead`. -/
theorem adapted_pointwise_nonAnticipating
    (price : ℕ → Ω → ℝ) (hp : ∀ t, StronglyMeasurable (price t))
    (X : ℕ → Ω → ℝ) (hX : Adapted (naturalFiltration price hp) X)
    {ω ω' : Ω} {t : ℕ} (h : AgreeUpToΩ price ω ω' t) :
    X t ω = X t ω' := by
  -- `X t` is `𝓕ₜ`-measurable, so its level set `{η | X t η = X t ω}` is a `𝓕ₜ` event. It
  -- contains `ω`, and by `agreeUpTo_indistinguishable` it then contains `ω'`, forcing equality.
  have hmeas : Measurable[naturalFiltration price hp t] (X t) := hX t
  have hA : MeasurableSet[naturalFiltration price hp t] ((X t) ⁻¹' {X t ω}) :=
    hmeas (measurableSet_singleton (X t ω))
  have hmem : ω' ∈ (X t) ⁻¹' {X t ω} :=
    (agreeUpTo_indistinguishable price hp h hA).mp rfl
  exact (hmem).symm

/-- **The momentum signal is pointwise non-anticipating**, obtained from its adaptedness
(`momentumSignal_adapted`) through the forward bridge. The measure-theoretic proof in
`Measurability` thus subsumes the pointwise no-look-ahead guarantee for the concrete signal
the pipeline uses. -/
theorem momentumSignal_pointwise_nonAnticipating
    (price : ℕ → Ω → ℝ) (hp : ∀ t, StronglyMeasurable (price t))
    (skip lookback : ℕ) {g : ℝ → ℝ → ℝ} (hg : Measurable g.uncurry)
    {ω ω' : Ω} {t : ℕ} (h : AgreeUpToΩ price ω ω' t) :
    momentumSignal price skip lookback g t ω = momentumSignal price skip lookback g t ω' :=
  adapted_pointwise_nonAnticipating price hp _ (momentumSignal_adapted price hp skip lookback hg) h

end ResearchPipeline
