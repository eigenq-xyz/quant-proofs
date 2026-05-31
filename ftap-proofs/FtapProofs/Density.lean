import FtapProofs.MartingaleMeasure

/-!
# EMM → density bridge

On a finite state space `Ω`, every measure `Q` is determined by its values on singletons.
This module turns an abstract `EquivalentMartingaleMeasure` into the concrete, computable
**density** data `Ω → ℝ` that downstream finite-state pricing arguments consume:

- `emmDensity Q ω = (Q {ω}).toReal` — the risk-neutral weight of state `ω`.
- `emmDensity_pos` — strict positivity, under measure equivalence with a full-support
  reference measure (`Q ~ P` and `P {ω} > 0` for all `ω`).
- `emmDensity_sum_eq_one` — the weights sum to one (`Q` is a probability measure).
- `integral_eq_sum_emmDensity` — the `Q`-integral is the density-weighted finite sum
  `∫ f ∂Q = ∑ ω, emmDensity Q ω * f ω`.
- `emm_integral_discountedPrice_const` / `emm_discountedPrice_expectation_const` — under an
  EMM, the `Q`-expectation of each discounted price is constant across time. This is the
  martingale condition in the form a finite-state model can use directly.

## Why this exists

`perpetual-proofs` carries a placeholder `OnePeriodEMM` structure (a density with
`density_pos`, `density_sum_eq_one`, and a constant-spot-expectation field) precisely because
the FTAP layer did not yet expose these facts. The lemmas here are the reusable bridge that
lets that placeholder be discharged from the genuine `EquivalentMartingaleMeasure`.

## Contents

- **Q5.1** `emmDensity` — the singleton density of `Q`
- **Q5.2** `emmDensity_nonneg`, `emmDensity_pos` — nonnegativity / strict positivity
- **Q5.3** `emmDensity_sum_eq_one` — densities sum to one
- **Q5.4** `integral_eq_sum_emmDensity` — integral as a density-weighted sum
- **Q5.5** `emm_integral_discountedPrice_const` — constant discounted-price expectation
- **Q5.6** `emm_discountedPrice_expectation_const` — the same, in density-weighted-sum form
-/

namespace FtapProofs

open scoped MeasureTheory
open MeasureTheory

variable {Ω : Type*} [Fintype Ω] [MeasurableSpace Ω] [MeasurableSingletonClass Ω]

/-! ### Q5.1 The singleton density -/

/-- The **density** of a measure `Q` on a finite state space: `emmDensity Q ω = (Q {ω}).toReal`.
On a finite space `Q` is determined by these singleton weights. -/
noncomputable def emmDensity (Q : Measure Ω) (ω : Ω) : ℝ := (Q {ω}).toReal

/-! ### Q5.2 Positivity -/

omit [Fintype Ω] [MeasurableSingletonClass Ω] in
/-- The density is nonnegative. -/
lemma emmDensity_nonneg (Q : Measure Ω) (ω : Ω) : 0 ≤ emmDensity Q ω :=
  ENNReal.toReal_nonneg

/-- Under measure equivalence `Q ~ P` with a full-support reference measure `P`, the density
is strictly positive at every state. Finiteness of `Q` comes from `EquivalentMeasure` itself
(it carries `IsProbabilityMeasure Q`), so it need not be assumed separately. -/
lemma emmDensity_pos (m : FinancialMarket Ω) (Q : Measure Ω)
    (hequiv : EquivalentMeasure m Q) (hP : ∀ ω, 0 < m.P {ω}) (ω : Ω) :
    0 < emmDensity Q ω := by
  haveI : IsProbabilityMeasure Q := hequiv.1
  have hQpos : 0 < Q {ω} := (hequiv.2 ω).mp (hP ω)
  rw [emmDensity, ENNReal.toReal_pos_iff]
  exact ⟨hQpos, measure_lt_top Q {ω}⟩

/-! ### Q5.3 Integral as a density-weighted sum -/

/-- The `Q`-integral of any real function on a finite space is the density-weighted sum
`∫ f ∂Q = ∑ ω, emmDensity Q ω * f ω`. -/
lemma integral_eq_sum_emmDensity (Q : Measure Ω) [IsFiniteMeasure Q] (f : Ω → ℝ) :
    ∫ ω, f ω ∂Q = ∑ ω : Ω, emmDensity Q ω * f ω := by
  rw [integral_fintype (μ := Q) (f := f) Integrable.of_finite]
  exact Finset.sum_congr rfl fun ω _ => by
    simp only [emmDensity, measureReal_def, smul_eq_mul]

/-! ### Q5.4 Densities sum to one -/

/-- For a probability measure on a finite space, the singleton densities sum to one. -/
lemma emmDensity_sum_eq_one (Q : Measure Ω) [IsProbabilityMeasure Q] :
    ∑ ω : Ω, emmDensity Q ω = 1 := by
  have h := integral_eq_sum_emmDensity Q (fun _ => (1 : ℝ))
  simp only [mul_one] at h
  rw [← h]
  simp

/-! ### Q5.5 Constant discounted-price expectation under an EMM -/

/-- Under an EMM `Q`, the `Q`-expectation of each discounted asset price is constant across
time: `∫ S̃ i t ∂Q = ∫ S̃ i t' ∂Q` for all times `t, t'`.

**Proof.** It suffices to show every `∫ S̃ i t ∂Q` equals the value at time `0`. For `0 ≤ t`,
the martingale property gives `Q[S̃ i t | ℱ_0] =ᵐ S̃ i 0`, and `integral_condExp` turns the
conditional-expectation identity into equality of integrals. -/
lemma emm_integral_discountedPrice_const (m : FinancialMarket Ω) (Q : Measure Ω)
    (hQ : EquivalentMartingaleMeasure m Q) (i : Fin m.n) (t t' : Fin (m.T + 1)) :
    ∫ ω, discountedPrice m i t ω ∂Q = ∫ ω, discountedPrice m i t' ω ∂Q := by
  haveI : IsProbabilityMeasure Q := hQ.1.1
  haveI : IsFiniteMeasure Q := inferInstance
  haveI : SigmaFiniteFiltration Q m.𝒻 := inferInstance
  have hmart := hQ.2 i
  -- Anchor every time at 0: `∫ S̃ i s ∂Q = ∫ S̃ i 0 ∂Q`.
  have anchor : ∀ s : Fin (m.T + 1),
      ∫ ω, discountedPrice m i s ω ∂Q = ∫ ω, discountedPrice m i ⟨0, Nat.zero_lt_succ m.T⟩ ω ∂Q := by
    intro s
    have hcondexp := hmart.condExp_ae_eq (Fin.zero_le s)
    have hintcondexp := integral_condExp (hm := m.𝒻.le ⟨0, Nat.zero_lt_succ m.T⟩)
      (f := discountedPrice m i s) (μ := Q)
    rw [← hintcondexp]
    exact integral_congr_ae hcondexp
  rw [anchor t, anchor t']

/-! ### Q5.6 Constant discounted-price expectation in density-weighted form -/

/-- Under an EMM `Q`, the density-weighted discounted-price sum is constant across time:
`∑ ω, emmDensity Q ω * S̃ i t ω = ∑ ω, emmDensity Q ω * S̃ i t' ω`.

This is `emm_integral_discountedPrice_const` rewritten through `integral_eq_sum_emmDensity`,
giving the explicit finite-sum form a finite-state model consumes directly. -/
lemma emm_discountedPrice_expectation_const (m : FinancialMarket Ω) (Q : Measure Ω)
    (hQ : EquivalentMartingaleMeasure m Q) (i : Fin m.n) (t t' : Fin (m.T + 1)) :
    ∑ ω : Ω, emmDensity Q ω * discountedPrice m i t ω =
    ∑ ω : Ω, emmDensity Q ω * discountedPrice m i t' ω := by
  haveI : IsProbabilityMeasure Q := hQ.1.1
  haveI : IsFiniteMeasure Q := inferInstance
  rw [← integral_eq_sum_emmDensity Q (discountedPrice m i t),
    ← integral_eq_sum_emmDensity Q (discountedPrice m i t')]
  exact emm_integral_discountedPrice_const m Q hQ i t t'

end FtapProofs
