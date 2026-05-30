import OptionsProofs.Tree
import FtapProofs.MartingaleMeasure

/-!
# The Cox-Ross-Rubinstein Risk-Neutral Measure (measure + equivalence)

This module constructs the risk-neutral probability measure of the Cox-Ross-Rubinstein
(CRR) binomial market and proves that it is **equivalent** to the uniform reference
measure (both have full support, so the equivalence is immediate once both are shown to
be probability measures). The remaining half of the equivalent-martingale-measure (EMM)
condition, the martingale property of the discounted price, is a *separate* later step
and is **not** addressed here.

## Risk-neutral parameters

Fix up/down factors `u d : ℝ` and a per-period rate `r : ℝ` inside the no-arbitrage band

  `0 < d < 1 + r < u`.

The **up-move risk-neutral probability** is

  `q := (1 + r - d) / (u - d)`,

which lies strictly in `(0, 1)` exactly because of the band. The risk-neutral density of a
path `ω : CRRState T` is the binomial weight

  `crrRNDensity ω := q ^ (ups T ω) * (1 - q) ^ (T - ups T ω)`,

and the risk-neutral measure is the `PMF` with that density. Sum-to-one is the binomial
theorem `(q + (1 - q)) ^ T = 1`, proved here by factoring the density as a product over
coordinates and applying `Finset.sum_prod_piFinset`.

## Contents

- `riskNeutralProb`, `riskNeutralProb_mem` (`0 < q < 1`).
- `crrRNDensity`, `crrRNDensity_pos`, `crrRNDensity_eq_prod`, `crrRNDensity_sum_eq_one`.
- `crrRNMeasure`, its `IsProbabilityMeasure` instance.
- `crrRNMeasure_singleton`, `crrRNMeasure_pos`.
- `crrRNMeasure_equiv` — the O2a goal: the risk-neutral measure is equivalent to the CRR
  reference measure.
-/

namespace OptionsProofs

open MeasureTheory
open scoped BigOperators

variable {T : ℕ}

/-! ### The up-move risk-neutral probability -/

/-- The CRR up-move risk-neutral probability `q = (1 + r - d) / (u - d)`. -/
noncomputable def riskNeutralProb (u d r : ℝ) : ℝ := (1 + r - d) / (u - d)

/-- Inside the no-arbitrage band `0 < d < 1 + r < u`, the risk-neutral probability lies
strictly in `(0, 1)`. -/
lemma riskNeutralProb_mem {u d r : ℝ} (_hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    0 < riskNeutralProb u d r ∧ riskNeutralProb u d r < 1 := by
  have hud : 0 < u - d := by linarith
  refine ⟨?_, ?_⟩
  · exact div_pos (by linarith) hud
  · rw [riskNeutralProb, div_lt_one hud]; linarith

/-! ### The risk-neutral density -/

/-- The risk-neutral density of a path: the binomial weight
`q ^ (#up-moves) * (1 - q) ^ (#down-moves)`. -/
noncomputable def crrRNDensity (u d r : ℝ) (ω : CRRState T) : ℝ :=
  riskNeutralProb u d r ^ (ups T ω) * (1 - riskNeutralProb u d r) ^ (T - ups T ω)

/-- The risk-neutral density is strictly positive. -/
lemma crrRNDensity_pos {u d r : ℝ} (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u)
    (ω : CRRState T) : 0 < crrRNDensity u d r ω := by
  obtain ⟨hq0, hq1⟩ := riskNeutralProb_mem hd hdr hru
  exact mul_pos (pow_pos hq0 _) (pow_pos (by linarith) _)

/-- The up-count equals the number of `true` coordinates: the `↑j < T` constraint in `ups`
is vacuous on the index type `Fin T`. -/
lemma ups_eq_card_true (ω : CRRState T) :
    ups T ω = (Finset.univ.filter (fun j : Fin T => ω j = true)).card := by
  unfold ups
  congr 1
  apply Finset.filter_congr
  intro j _
  simp only [and_iff_right_iff_imp]
  intro _
  exact j.isLt

/-- The density factors as a product over coordinates:
`q ^ (ups) * (1 - q) ^ (T - ups) = ∏ j, (if ω j then q else 1 - q)`. -/
lemma crrRNDensity_eq_prod (u d r : ℝ) (ω : CRRState T) :
    crrRNDensity u d r ω =
      ∏ j : Fin T, (if ω j = true then riskNeutralProb u d r else 1 - riskNeutralProb u d r) := by
  classical
  set q := riskNeutralProb u d r with hq
  rw [Finset.prod_ite (f := fun _ => q) (g := fun _ => 1 - q)]
  simp only [Finset.prod_const]
  rw [crrRNDensity, ← hq, ups_eq_card_true ω]
  -- The down-count `#{j : ω j ≠ true}` equals `T - #{j : ω j = true}`.
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

/-- **Sum-to-one for the risk-neutral density.** The binomial weights sum to `1`:
`∑_ω q ^ (ups ω) * (1 - q) ^ (T - ups ω) = (q + (1 - q)) ^ T = 1`. -/
lemma crrRNDensity_sum_eq_one (u d r : ℝ) :
    ∑ ω : CRRState T, crrRNDensity u d r ω = 1 := by
  classical
  set q := riskNeutralProb u d r with hq
  -- Rewrite each density as a product over coordinates.
  have heach : ∀ ω : CRRState T, crrRNDensity u d r ω =
      ∏ j : Fin T, (if ω j = true then q else 1 - q) := fun ω => by
    rw [crrRNDensity_eq_prod, hq]
  rw [Finset.sum_congr rfl (fun ω _ => heach ω)]
  -- `Fin T → Bool` is the `piFinset` of full `Bool` factors, so the sum-of-products
  -- collapses to a product-of-sums over each coordinate.
  have hpi : (Finset.univ : Finset (CRRState T)) =
      Fintype.piFinset (fun _ : Fin T => (Finset.univ : Finset Bool)) := by
    rw [Fintype.piFinset_univ]
  rw [hpi, Finset.sum_prod_piFinset (Finset.univ : Finset Bool)
        (fun (_ : Fin T) b => if b = true then q else 1 - q)]
  -- Each coordinate sum is `q + (1 - q) = 1`, and `∏ 1 = 1`.
  have hcoord : ∀ _i : Fin T,
      (∑ b : Bool, if b = true then q else 1 - q) = 1 := by
    intro _i
    rw [Fintype.sum_bool]
    simp
  rw [Finset.prod_congr rfl (fun i _ => hcoord i)]
  simp

/-! ### The risk-neutral measure -/

/-- The risk-neutral measure of the CRR market: the `PMF` whose mass at `ω` is the binomial
weight `crrRNDensity ω`. -/
noncomputable def crrRNMeasure (T : ℕ) (u d r : ℝ)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) : Measure (CRRState T) :=
  (PMF.ofFintype (fun ω => ENNReal.ofReal (crrRNDensity u d r ω)) (by
    rw [← ENNReal.ofReal_sum_of_nonneg
          (fun ω _ => (crrRNDensity_pos hd hdr hru ω).le),
      crrRNDensity_sum_eq_one, ENNReal.ofReal_one])).toMeasure

/-- The risk-neutral measure is a probability measure. -/
instance crrRNMeasure_prob (T : ℕ) (u d r : ℝ)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    IsProbabilityMeasure (crrRNMeasure T u d r hd hdr hru) := by
  unfold crrRNMeasure
  infer_instance

/-- The risk-neutral measure of a singleton is the binomial weight at that path. -/
lemma crrRNMeasure_singleton {u d r : ℝ}
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) (ω : CRRState T) :
    (crrRNMeasure T u d r hd hdr hru) {ω} = ENNReal.ofReal (crrRNDensity u d r ω) := by
  unfold crrRNMeasure
  rw [PMF.toMeasure_apply_singleton _ ω (measurableSet_singleton ω), PMF.ofFintype_apply]

/-- The risk-neutral measure assigns strictly positive mass to every singleton. -/
lemma crrRNMeasure_pos {u d r : ℝ}
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) (ω : CRRState T) :
    0 < (crrRNMeasure T u d r hd hdr hru) {ω} := by
  rw [crrRNMeasure_singleton hd hdr hru ω]
  exact ENNReal.ofReal_pos.mpr (crrRNDensity_pos hd hdr hru ω)

/-! ### Reference-measure full support -/

/-- The uniform reference measure assigns strictly positive mass to every singleton. -/
lemma crrMeasure_pos (T : ℕ) (ω : CRRState T) : 0 < crrMeasure T {ω} := by
  unfold crrMeasure
  rw [PMF.toMeasure_apply_singleton _ ω (measurableSet_singleton ω),
    PMF.uniformOfFintype_apply]
  simp only [ENNReal.inv_pos, ne_eq]
  exact ENNReal.natCast_ne_top _

/-! ### Equivalence (the O2a goal) -/

section Equivalence

variable {S₀ u d r : ℝ}

/-- **O2a.** The CRR risk-neutral measure is equivalent to the CRR reference measure: both
are probability measures and both have full support, so they agree on which singletons have
positive mass. -/
theorem crrRNMeasure_equiv (T : ℕ) (hS₀ : 0 < S₀)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    FtapProofs.EquivalentMeasure
      (crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith))
      (crrRNMeasure T u d r hd hdr hru) := by
  refine ⟨crrRNMeasure_prob T u d r hd hdr hru, fun ω => ?_⟩
  -- The market's reference measure is `crrMeasure`; both sides are always positive.
  show 0 < crrMeasure T {ω} ↔ 0 < (crrRNMeasure T u d r hd hdr hru) {ω}
  exact ⟨fun _ => crrRNMeasure_pos hd hdr hru ω, fun _ => crrMeasure_pos T ω⟩

end Equivalence

end OptionsProofs
