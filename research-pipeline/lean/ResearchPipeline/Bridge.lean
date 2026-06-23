import ResearchPipeline.NoLookahead
import ResearchPipeline.Measurability

/-!
# Bridge: measure-theoretic adaptedness implies pointwise non-anticipation

`NoLookahead` states no-look-ahead **pointwise** (outcomes that agree on the observed
history up to `t` produce the same value at `t`); `Measurability` states it
**measure-theoretically** (the signal process is `Adapted` to the natural price
filtration, citing `ftap-proofs`). This module connects them in the forward direction.

Two layers are proved, both forward (measure-theoretic implies pointwise):

1. *Outcome level* (`adapted_pointwise_nonAnticipating`): if a real process is `𝓕ₜ`-measurable
   against the natural filtration of the price observations, it cannot tell apart two outcomes
   `ω, ω' : Ω` whose price history agrees up to `t`.
2. *`NonAnticipating` itself* (`nonAnticipating_of_coordMeasurable`): instantiating the bridge on
   the canonical path space `Ω := Path Asset ℝ` with the coordinate maps `p ↦ p s a` as the
   observations, a process adapted to the coordinate filtration satisfies
   `NoLookahead.NonAnticipating` in full, asset dimension included. So the measure-theoretic
   guarantee formally entails the pointwise predicate `NoLookahead` defines.

What is **not** proved: the reverse direction (pointwise dependence implies measurability), which
needs a Doob-Dynkin factorization plus a measurable-dependence hypothesis and is out of scope.

The key sublemmas (`agreeUpTo_indistinguishable`, `agree_coordSpace_indistinguishable`) bound the
generating filtration above by `indistinguishableSpace`, the σ-algebra of events that cannot
separate two history-agreeing points, reduced over the `⨆` to each coordinate.
-/

open MeasureTheory MeasurableSpace

namespace ResearchPipeline

variable {Ω : Type*} [MeasurableSpace Ω]

/-- Two outcomes agree on the price history through time `t`: every observation `price s`
with `s ≤ t` takes the same value on both. This is the outcome-level rendering of
`ResearchPipeline.AgreeUpTo`, specialized to a single scalar observation per time (the path's
asset dimension is dropped; the momentum signal is single-asset). -/
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

/-! ### Encoding `NoLookahead.NonAnticipating` itself (multi-asset path space)

The lemmas above act on outcomes `ω : Ω`. `NoLookahead.NonAnticipating` is instead stated over
the explicit multi-asset path space `Path Asset V → Time → Asset → W`. This section closes that
gap: it instantiates the bridge on the canonical path space `Ω := Path Asset ℝ` (with the
coordinate maps `p ↦ p s a` as the observations), so a process adapted to the coordinate
filtration genuinely satisfies `NonAnticipating`. The asset dimension dropped by `AgreeUpToΩ` is
restored here. -/

/-- The coordinate filtration on the path space `Path Asset ℝ`: at time `t`, the σ-algebra
generated by every coordinate `p ↦ p s a` with `s ≤ t` (all assets `a`). This is the natural
information set `𝓕ₜ` for a process living on paths. -/
@[reducible]
noncomputable def coordSpace (Asset : Type) (t : ℕ) : MeasurableSpace (Path Asset ℝ) :=
  ⨆ s, ⨆ (_ : s ≤ t), ⨆ a, MeasurableSpace.comap (fun p : Path Asset ℝ => p s a) inferInstance

/-- Two paths that agree on every coordinate up to time `t` lie in the same `coordSpace t`
events. Same argument as `agreeUpTo_indistinguishable`, now over the coordinate family
`{p ↦ p s a : s ≤ t, a}`. -/
theorem agree_coordSpace_indistinguishable {Asset : Type} (t : ℕ) {p q : Path Asset ℝ}
    (hpq : ∀ s ≤ t, ∀ a, p s a = q s a)
    {A : Set (Path Asset ℝ)} (hA : MeasurableSet[coordSpace Asset t] A) :
    p ∈ A ↔ q ∈ A := by
  have hle : coordSpace Asset t ≤ indistinguishableSpace p q := by
    show ⨆ s, ⨆ (_ : s ≤ t), ⨆ a, MeasurableSpace.comap (fun p : Path Asset ℝ => p s a) _
        ≤ indistinguishableSpace p q
    refine iSup_le fun s => iSup_le fun hs => iSup_le fun a => ?_
    intro B hB
    obtain ⟨C, _hC, rfl⟩ := hB
    show p ∈ (fun p : Path Asset ℝ => p s a) ⁻¹' C ↔ q ∈ (fun p : Path Asset ℝ => p s a) ⁻¹' C
    rw [Set.mem_preimage, Set.mem_preimage, hpq s hs a]
  exact hle A hA

/-- **Adaptedness to the coordinate filtration implies `NoLookahead.NonAnticipating`.** If each
per-asset map `X a t` is `𝓕ₜ`-measurable on the path space, then the signal `fun p t a => X a t p`
is non-anticipating in the exact sense of `NoLookahead`: on any two paths agreeing up to `t`, its
time-`t` cross-section is identical. This is the formal collapse of the two no-look-ahead
formulations — the measure-theoretic notion entails the pointwise predicate, asset dimension and
all. (`momentumSignal_adapted` supplies the measurability hypothesis in the single-asset case.) -/
theorem nonAnticipating_of_coordMeasurable {Asset W : Type}
    [MeasurableSpace W] [MeasurableSingletonClass W]
    (X : Asset → ℕ → Path Asset ℝ → W)
    (hX : ∀ a t, Measurable[coordSpace Asset t] (X a t)) :
    NonAnticipating (fun (p : Path Asset ℝ) (t : Time) (a : Asset) => X a t p) := by
  intro p q t hpq a
  show X a t p = X a t q
  have hA : MeasurableSet[coordSpace Asset t] ((X a t) ⁻¹' {X a t p}) :=
    (hX a t) (measurableSet_singleton (X a t p))
  have hmem : q ∈ (X a t) ⁻¹' {X a t p} :=
    (agree_coordSpace_indistinguishable t hpq hA).mp rfl
  exact (Set.mem_singleton_iff.mp hmem).symm

end ResearchPipeline
