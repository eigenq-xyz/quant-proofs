import OptionsProofs.Tree
import FtapProofs.MartingaleMeasure
import FtapProofs.Theorem
import Mathlib.Probability.ProbabilityMassFunction.Integrals
import Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic
import Mathlib.Logic.Equiv.Prod

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

/-- The integral against the risk-neutral measure is the density-weighted finite sum:
`∫ f ∂Q = ∑ ω, crrRNDensity ω * f ω`. -/
lemma crrRNMeasure_integral_eq_sum {u d r : ℝ}
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) (f : CRRState T → ℝ) :
    ∫ ω, f ω ∂(crrRNMeasure T u d r hd hdr hru) =
      ∑ ω : CRRState T, crrRNDensity u d r ω * f ω := by
  unfold crrRNMeasure
  rw [PMF.integral_eq_sum]
  apply Finset.sum_congr rfl
  intro ω _
  rw [PMF.ofFintype_apply, smul_eq_mul,
    ENNReal.toReal_ofReal (crrRNDensity_pos hd hdr hru ω).le]

/-! ### Reference-measure full support -/

/-- The uniform reference measure assigns strictly positive mass to every singleton. -/
lemma crrMeasure_pos (T : ℕ) (ω : CRRState T) : 0 < crrMeasure T {ω} := by
  unfold crrMeasure
  rw [PMF.toMeasure_apply_singleton _ ω (measurableSet_singleton ω),
    PMF.uniformOfFintype_apply]
  simp only [ENNReal.inv_pos, ne_eq]
  exact ENNReal.natCast_ne_top _

/-! ### The drift identity -/

/-- **The defining drift identity of the risk-neutral probability.** With
`q = (1 + r - d) / (u - d)`, the one-step expected gross return under `q` is exactly the
risk-free factor: `q * u + (1 - q) * d = 1 + r`. This is the algebraic heart of the
martingale property. Requires `d < u` so that `u - d ≠ 0`. -/
lemma riskNeutralProb_drift {u d r : ℝ} (hdu : d < u) :
    riskNeutralProb u d r * u + (1 - riskNeutralProb u d r) * d = 1 + r := by
  have hud : u - d ≠ 0 := by linarith
  rw [riskNeutralProb]
  field_simp
  ring

/-! ### The one-step price recursion -/

/-- The up-count increases by one exactly when the `t`-th move (coordinate `t`) is up:
`ups (t + 1) ω = ups t ω + (if ω ⟨t, _⟩ then 1 else 0)`. The new coordinate available at
time `t + 1` relative to time `t` is index `t`, whose constraint `↑j < t + 1` is the only
new admission to the up-set. -/
lemma ups_succ {T : ℕ} (t : Fin T) (ω : CRRState T) :
    ups (t.val + 1) ω = ups t.val ω + (if ω ⟨t.val, t.isLt⟩ = true then 1 else 0) := by
  classical
  unfold ups
  -- The filter at time `t+1` is the filter at time `t` plus possibly coordinate `t`.
  have hsplit :
      (Finset.univ.filter (fun j : Fin T => (j : ℕ) < t.val + 1 ∧ ω j = true)) =
      (Finset.univ.filter (fun j : Fin T => (j : ℕ) < t.val ∧ ω j = true)) ∪
      (Finset.univ.filter (fun j : Fin T => (j : ℕ) = t.val ∧ ω j = true)) := by
    ext j
    simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_union]
    constructor
    · rintro ⟨hjlt, hjt⟩
      rcases Nat.lt_succ_iff_lt_or_eq.mp hjlt with h | h
      · exact Or.inl ⟨h, hjt⟩
      · exact Or.inr ⟨h, hjt⟩
    · rintro (⟨hjlt, hjt⟩ | ⟨hjeq, hjt⟩)
      · exact ⟨Nat.lt_succ_of_lt hjlt, hjt⟩
      · exact ⟨by omega, hjt⟩
  rw [hsplit, Finset.card_union_of_disjoint]
  · congr 1
    -- The second piece is `{⟨t, _⟩}` if `ω ⟨t,_⟩` is true, else empty.
    by_cases hb : ω ⟨t.val, t.isLt⟩ = true
    · rw [if_pos hb]
      rw [show (Finset.univ.filter (fun j : Fin T => (j : ℕ) = t.val ∧ ω j = true)) =
            {(⟨t.val, t.isLt⟩ : Fin T)} from ?_]
      · simp
      · ext j
        simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.mem_singleton]
        constructor
        · rintro ⟨hjv, _⟩; exact Fin.ext hjv
        · rintro rfl; exact ⟨rfl, hb⟩
    · rw [if_neg hb]
      rw [show (Finset.univ.filter (fun j : Fin T => (j : ℕ) = t.val ∧ ω j = true)) = ∅ from ?_]
      · simp
      · ext j
        simp only [Finset.mem_filter, Finset.mem_univ, true_and, Finset.notMem_empty, iff_false]
        rintro ⟨hjv, hjt⟩
        exact hb (by rw [show (⟨t.val, t.isLt⟩ : Fin T) = j from Fin.ext hjv.symm]; exact hjt)
  · rw [Finset.disjoint_left]
    intro j hj1 hj2
    simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hj1 hj2
    omega

/-- **The one-step price recursion.** Moving from time `t` to time `t + 1`, the risky-asset
price is multiplied by `u` if the `t`-th move is up and by `d` if it is down:
`crrPrice (t + 1) ω = crrPrice t ω * (if ω ⟨t, _⟩ then u else d)`. -/
lemma crrPrice_succ {T : ℕ} (S₀ u d : ℝ) (t : Fin T) (ω : CRRState T) :
    crrPrice T S₀ u d t.succ ω =
      crrPrice T S₀ u d t.castSucc ω * (if ω ⟨t.val, t.isLt⟩ = true then u else d) := by
  classical
  simp only [crrPrice, Fin.val_succ, Fin.val_castSucc]
  rw [ups_succ t ω]
  have hle : ups t.val ω ≤ t.val := ups_le_time t.val ω
  by_cases hb : ω ⟨t.val, t.isLt⟩ = true
  · -- Up-move: the up-exponent gains 1, the down-exponent is unchanged.
    rw [if_pos hb, if_pos hb]
    have hdown : t.val + 1 - (ups t.val ω + 1) = t.val - ups t.val ω := by omega
    rw [hdown, pow_succ]
    ring
  · -- Down-move: the down-exponent gains 1, the up-exponent is unchanged.
    rw [if_neg hb, if_neg hb, add_zero]
    have hdown : t.val + 1 - ups t.val ω = (t.val - ups t.val ω) + 1 := by omega
    rw [hdown, pow_succ]
    ring

/-! ### The discounted-price one-step recursion -/

section Discounted

variable {S₀ u d r : ℝ}

/-- The market's discounted risky price `crrPrice t ω / (1 + r) ^ t`, written without the
`Fin m.n` index so that the `crrMarket.n = 1` index synthesis does not interfere. -/
noncomputable def crrDiscounted (T : ℕ) (S₀ u d r : ℝ) (t : Fin (T + 1)) (ω : CRRState T) : ℝ :=
  crrPrice T S₀ u d t ω / (1 + r) ^ (t : ℕ)

/-- The market's discounted price of the single risky asset is `crrDiscounted`. -/
lemma crrDiscountedPrice_eq (T : ℕ) (hS₀ : 0 < S₀) (hd : 0 < d) (hud : d < u) (hr : -1 < r)
    (i : Fin (crrMarket T S₀ u d r hS₀ hd hud hr).n) (t : Fin (T + 1)) (ω : CRRState T) :
    FtapProofs.discountedPrice (crrMarket T S₀ u d r hS₀ hd hud hr) i t ω =
      crrDiscounted T S₀ u d r t ω := by
  rfl

/-- **The discounted-price one-step recursion under the CRR numeraire.** Dividing the price
recursion by the numeraire growth `(1 + r)`:
`D (t + 1) ω = D t ω * (if ω ⟨t, _⟩ then u else d) / (1 + r)`. -/
lemma crrDiscounted_succ (T : ℕ) (S₀ u d r : ℝ) (hr : -1 < r) (t : Fin T) (ω : CRRState T) :
    crrDiscounted T S₀ u d r t.succ ω =
      crrDiscounted T S₀ u d r t.castSucc ω *
        ((if ω ⟨t.val, t.isLt⟩ = true then u else d) / (1 + r)) := by
  have hr0 : (0 : ℝ) < 1 + r := by linarith
  simp only [crrDiscounted]
  rw [crrPrice_succ S₀ u d t ω, Fin.val_succ, Fin.val_castSucc, pow_succ]
  field_simp

end Discounted

/-! ### The one-step martingale sum identity (the crux) -/

section OneStepSum

variable {S₀ u d r : ℝ}

/-- **The crux: the one-step martingale identity, stated as a finite sum.**

For any "weight" function `w : CRRState T → ℝ` that does **not** depend on coordinate `s`
(this is the role played by an `crrFiltration s.castSucc`-measurable indicator times the
coordinate-`s`-independent discounted price `crrDiscounted s.castSucc`), the risk-neutral
average of the *next* discounted price equals that of the *current* one:

  `∑ ω, ρ(ω) · w ω · crrDiscounted (s.succ) ω = ∑ ω, ρ(ω) · w ω · crrDiscounted (s.castSucc) ω`

where `ρ = crrRNDensity`. The proof splits each path at coordinate `s` via
`Equiv.funSplitAt`, summing the two Bernoulli branches; the density factors as
`q` (resp. `1 - q`) times a common remainder, the coordinate-`s`-independent factors come
out, and what is left is exactly the drift identity `q·u + (1-q)·d = 1 + r` divided by
`(1 + r)`, i.e. `q·(u/(1+r)) + (1-q)·(d/(1+r)) = 1`. -/
lemma crrRNMeasure_one_step_sum (T : ℕ) (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u)
    (s : Fin T) (w : CRRState T → ℝ)
    (hw : ∀ ω : CRRState T, w (Function.update ω ⟨s.val, s.isLt⟩ (! ω ⟨s.val, s.isLt⟩)) = w ω) :
    ∑ ω : CRRState T,
        crrRNDensity u d r ω * w ω * crrDiscounted T S₀ u d r s.succ ω =
      ∑ ω : CRRState T,
        crrRNDensity u d r ω * w ω * crrDiscounted T S₀ u d r s.castSucc ω := by
  classical
  set q := riskNeutralProb u d r with hq
  set sidx : Fin T := ⟨s.val, s.isLt⟩ with hsidx
  -- `crrDiscounted` at `s.castSucc` does not depend on coordinate `sidx` (it only sees the
  -- first `s` coordinates); the same therefore holds for `w` (by `hw`) and for the product.
  -- The next price factors through the previous one times the coordinate-`sidx` move.
  -- Reindex the whole sum by splitting coordinate `sidx`.
  set e := (Equiv.funSplitAt sidx Bool).trans (Equiv.prodComm Bool ({j // j ≠ sidx} → Bool))
    with he
  -- The density factorization: at a reconstructed path, the coordinate-`sidx` Bernoulli
  -- weight separates from the product over the remaining coordinates.
  have hud : (0:ℝ) < u - d := by linarith
  have hr0 : (0:ℝ) < 1 + r := by linarith
  -- The "down-price-independent-of-sidx" facts, packaged for both branches.
  -- castSucc value: crrDiscounted s.castSucc depends only on coords < s.val, hence not on sidx.
  have hcast_indep : ∀ ω : CRRState T,
      crrDiscounted T S₀ u d r s.castSucc (Function.update ω sidx (! ω sidx)) =
      crrDiscounted T S₀ u d r s.castSucc ω := by
    intro ω
    simp only [crrDiscounted, crrPrice, Fin.val_castSucc]
    have hups : ups s.val (Function.update ω sidx (! ω sidx)) = ups s.val ω := by
      unfold ups
      apply Finset.card_bij' (fun j _ => j) (fun j _ => j)
      · intro j hj
        simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hj ⊢
        refine ⟨hj.1, ?_⟩
        rw [Function.update_of_ne (by exact Fin.ne_of_val_ne (by simp [hsidx]; omega))] at hj
        exact hj.2
      · intro j hj
        simp only [Finset.mem_filter, Finset.mem_univ, true_and] at hj ⊢
        refine ⟨hj.1, ?_⟩
        rw [Function.update_of_ne (by exact Fin.ne_of_val_ne (by simp [hsidx]; omega))]
        exact hj.2
      · intro j _; rfl
      · intro j _; rfl
    rw [hups]
  -- The succ price is the castSucc price times the move factor at sidx.
  have hsucc_eq : ∀ ω : CRRState T,
      crrDiscounted T S₀ u d r s.succ ω =
      crrDiscounted T S₀ u d r s.castSucc ω * ((if ω sidx = true then u else d) / (1 + r)) :=
    fun ω => crrDiscounted_succ T S₀ u d r (by linarith) s ω
  -- Reindex both sums by `e`, then split the product type, summing the `Bool` coordinate.
  rw [← Equiv.sum_comp e.symm
        (fun ω => crrRNDensity u d r ω * w ω * crrDiscounted T S₀ u d r s.succ ω),
    ← Equiv.sum_comp e.symm
        (fun ω => crrRNDensity u d r ω * w ω * crrDiscounted T S₀ u d r s.castSucc ω)]
  rw [Fintype.sum_prod_type, Fintype.sum_prod_type]
  -- For each `rest`, sum the two Bool branches and use the drift identity.
  apply Finset.sum_congr rfl
  intro rest _
  -- Expand the inner sum over `Bool` into its two branches.
  rw [Fintype.sum_bool, Fintype.sum_bool]
  -- Abbreviations for the reconstructed paths at the two branches.
  set ωF : CRRState T := e.symm (rest, false) with hωF
  set ωT : CRRState T := e.symm (rest, true) with hωT
  -- The two paths differ only at `sidx`: `ωT = update ωF sidx true`, `ωF = update ωT sidx false`.
  have hωF_sidx : ωF sidx = false := by
    simp [hωF, he, Equiv.funSplitAt, Equiv.piSplitAt]
  have hωT_sidx : ωT sidx = true := by
    simp [hωT, he, Equiv.funSplitAt, Equiv.piSplitAt]
  have hupdate : ωT = Function.update ωF sidx (! ωF sidx) := by
    funext j
    by_cases hj : j = sidx
    · subst hj; rw [Function.update_self, hωF_sidx]; simp [hωT_sidx]
    · rw [Function.update_of_ne hj, hωF, hωT, he]
      simp [Equiv.funSplitAt, Equiv.piSplitAt, hj]
  -- `w` agrees on both branches.
  have hw_eq : w ωT = w ωF := by rw [hupdate]; exact hw ωF
  -- `crrDiscounted s.castSucc` agrees on both branches.
  have hcast_eq : crrDiscounted T S₀ u d r s.castSucc ωT =
      crrDiscounted T S₀ u d r s.castSucc ωF := by rw [hupdate]; exact hcast_indep ωF
  -- The density factorization: ρ(ωT) = q · R, ρ(ωF) = (1-q) · R for a common R.
  -- Use `crrRNDensity_eq_prod` and pull out coordinate `sidx`.
  set R : ℝ := ∏ j ∈ (Finset.univ.erase sidx),
      (if ωF j = true then q else 1 - q) with hR
  have hρF : crrRNDensity u d r ωF = (1 - q) * R := by
    rw [crrRNDensity_eq_prod, ← hq]
    rw [Fintype.prod_eq_mul_prod_compl sidx (fun j => if ωF j = true then q else 1 - q)]
    rw [hωF_sidx]
    simp only [Bool.false_eq_true, if_false]
    congr 1
    rw [hR]
    rw [Finset.compl_eq_univ_sdiff, Finset.sdiff_singleton_eq_erase]
  have hρT : crrRNDensity u d r ωT = q * R := by
    rw [crrRNDensity_eq_prod, ← hq]
    rw [Fintype.prod_eq_mul_prod_compl sidx (fun j => if ωT j = true then q else 1 - q)]
    rw [hωT_sidx]
    simp only [if_true]
    congr 1
    rw [hR, Finset.compl_eq_univ_sdiff, Finset.sdiff_singleton_eq_erase]
    apply Finset.prod_congr rfl
    intro j hj
    have hjne : j ≠ sidx := Finset.ne_of_mem_erase hj
    rw [show ωT j = ωF j from by rw [hupdate, Function.update_of_ne hjne]]
  -- The common coordinate-independent factor and the move factors.
  set c : ℝ := w ωF * crrDiscounted T S₀ u d r s.castSucc ωF with hc
  -- Expand both branch sums using hsucc_eq and the equalities above.
  rw [hsucc_eq ωF, hsucc_eq ωT, hωF_sidx, hωT_sidx, hw_eq, hcast_eq, hρF, hρT]
  simp only [Bool.false_eq_true, if_false, if_true]
  -- Goal: (qR)·w(ωF)·(D·(u/(1+r))) + ((1-q)R)·w(ωF)·(D·(d/(1+r)))
  --     = (qR)·w(ωF)·D + ((1-q)R)·w(ωF)·D
  -- Factor out R·c and apply the drift identity.
  have hdrift : q * (u / (1 + r)) + (1 - q) * (d / (1 + r)) = 1 := by
    have hdr := riskNeutralProb_drift (u := u) (d := d) (r := r) (show d < u by linarith)
    rw [← hq] at hdr
    rw [mul_div_assoc', mul_div_assoc', ← add_div, hdr, div_self (ne_of_gt hr0)]
  -- Algebraic rearrangement: both sides equal R · c.
  have hlhs : q * R * w ωF * (crrDiscounted T S₀ u d r s.castSucc ωF * (u / (1 + r))) +
      (1 - q) * R * w ωF * (crrDiscounted T S₀ u d r s.castSucc ωF * (d / (1 + r))) =
      R * c * (q * (u / (1 + r)) + (1 - q) * (d / (1 + r))) := by rw [hc]; ring
  have hrhs : q * R * w ωF * crrDiscounted T S₀ u d r s.castSucc ωF +
      (1 - q) * R * w ωF * crrDiscounted T S₀ u d r s.castSucc ωF =
      R * c * 1 := by rw [hc]; ring
  rw [hlhs, hrhs, hdrift]

/-- A set measurable with respect to `crrFiltration (s.castSucc)` is determined by the first
`s` coordinates, hence its indicator is invariant under toggling coordinate `s`. -/
lemma crrFiltration_indicator_update_invariant {T : ℕ} (s : Fin T) {s_set : Set (CRRState T)}
    (hs_set : MeasurableSet[(crrFiltration T) s.castSucc] s_set) (ω : CRRState T) :
    s_set.indicator (fun _ => (1 : ℝ)) (Function.update ω ⟨s.val, s.isLt⟩ (! ω ⟨s.val, s.isLt⟩)) =
      s_set.indicator (fun _ => (1 : ℝ)) ω := by
  classical
  -- `crrFiltration (s.castSucc) = comap (truncate s.val) ⊤`, so `s_set = truncate s.val ⁻¹' A`.
  obtain ⟨A, _, hA⟩ := hs_set
  set sidx : Fin T := ⟨s.val, s.isLt⟩
  -- Toggling coordinate `sidx` does not change `truncate s.val`, since it only reads
  -- coordinates with index `< s.val`.
  have htrunc : truncate (T := T) s.val (Function.update ω sidx (! ω sidx)) =
      truncate (T := T) s.val ω := by
    funext j
    simp only [truncate]
    rw [Function.update_of_ne]
    -- The read index `castLE j` has value `< min s.val T ≤ s.val`, so it is ≠ sidx (value s.val).
    refine Fin.ne_of_val_ne ?_
    have hj : (j : ℕ) < min s.val T := j.isLt
    simp only [Fin.val_castLE, sidx]
    omega
  -- Membership is preserved, hence the indicator value: `s_set = truncate s.val ⁻¹' A`.
  have hset_eq : s_set = truncate (T := T) s.val ⁻¹' A := hA.symm
  have hmem : (Function.update ω sidx (! ω sidx)) ∈ s_set ↔ ω ∈ s_set := by
    rw [hset_eq, Set.mem_preimage, Set.mem_preimage, htrunc]
  by_cases hω : ω ∈ s_set
  · rw [Set.indicator_of_mem hω, Set.indicator_of_mem (hmem.mpr hω)]
  · rw [Set.indicator_of_notMem hω, Set.indicator_of_notMem (fun h => hω (hmem.mp h))]

end OneStepSum

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

/-! ### The martingale property and no-arbitrage (the O2b goal) -/

section Martingale

open MeasureTheory

variable {S₀ u d r : ℝ}

/-- **O2b — the martingale property of the CRR risk-neutral measure.** Under `crrRNMeasure`,
the discounted price of the single risky asset is a martingale with respect to the natural
filtration. The one-step conditional-expectation identity is reduced, via the set-integral
characterization `ae_eq_condExp_of_forall_setIntegral_eq`, to the finite Bernoulli sum
`crrRNMeasure_one_step_sum`, which is in turn the drift identity `q·u + (1-q)·d = 1 + r`. The
general time gap is handled by induction using the tower property, mirroring the FTAP T5.3. -/
theorem crrRNMeasure_martingale (T : ℕ) (hS₀ : 0 < S₀)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    FtapProofs.IsMartingaleMeasure
      (crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith))
      (crrRNMeasure T u d r hd hdr hru) := by
  set m := crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith) with hm
  set Q := crrRNMeasure T u d r hd hdr hru with hQ
  haveI : IsProbabilityMeasure Q := crrRNMeasure_prob T u d r hd hdr hru
  haveI : IsFiniteMeasure Q := inferInstance
  -- `m.n = 1`: reduce the single asset index to `0`.
  intro i₀
  refine ⟨fun t => (FtapProofs.discountedPrice_adapted m i₀ t).stronglyMeasurable,
    fun s_time t_time hst => ?_⟩
  -- Induction on the time gap (mirrors FTAP T5.3).
  suffices key : ∀ (k : ℕ) (j : Fin (m.T + 1)), j.val = s_time.val + k →
      Q[FtapProofs.discountedPrice m i₀ j | m.𝒻 s_time] =ᵐ[Q]
      FtapProofs.discountedPrice m i₀ s_time from
    key (t_time.val - s_time.val) t_time (by omega)
  intro k
  induction k with
  | zero =>
    intro j hj
    have hjs : j = s_time := Fin.ext (by omega)
    rw [hjs]
    exact Filter.EventuallyEq.of_eq
      (MeasureTheory.condExp_of_stronglyMeasurable (m.𝒻.le s_time)
        (FtapProofs.discountedPrice_adapted m i₀ s_time).stronglyMeasurable
        (MeasureTheory.Integrable.of_finite (μ := Q)))
  | succ k ih =>
    intro j hj
    have hklt : s_time.val + k < m.T := by have := j.isLt; omega
    -- Here `m.T = T`, so `mid : Fin T`.
    have hmT : m.T = T := rfl
    let mid : Fin m.T := ⟨s_time.val + k, hklt⟩
    have hjmid : j = mid.succ := Fin.ext (by simp [mid]; omega)
    have hs_le_mid : s_time ≤ mid.castSucc := by
      simp only [Fin.le_def, Fin.val_castSucc, mid]; omega
    rw [hjmid]
    -- `m.T = T` definitionally, so `mid : Fin m.T` doubles as a `Fin T` index of a coordinate.
    -- One-step: Q[D(mid+1) | ℱ_mid] =ᵐ D(mid)
    have one_step : Q[FtapProofs.discountedPrice m i₀ mid.succ | m.𝒻 mid.castSucc] =ᵐ[Q]
        FtapProofs.discountedPrice m i₀ mid.castSucc := by
      haveI : SigmaFinite (Q.trim (m.𝒻.le mid.castSucc)) := inferInstance
      have hgm := (FtapProofs.discountedPrice_adapted m i₀ mid.castSucc).stronglyMeasurable.aestronglyMeasurable
        (μ := Q)
      apply (MeasureTheory.ae_eq_condExp_of_forall_setIntegral_eq (m.𝒻.le mid.castSucc)
        (MeasureTheory.Integrable.of_finite (μ := Q))
        (fun _ _ _ => MeasureTheory.Integrable.of_finite.integrableOn) _ hgm).symm
      intro s_set hs_set _
      -- Convert both set integrals to density-weighted sums.
      have hint_eq : ∀ (F : CRRState T → ℝ),
          ∫ ω in s_set, F ω ∂Q =
          ∑ ω : CRRState T, crrRNDensity u d r ω * s_set.indicator F ω := fun F => by
        rw [← MeasureTheory.integral_indicator ((m.𝒻.le mid.castSucc) s_set hs_set),
          crrRNMeasure_integral_eq_sum hd hdr hru]
      rw [hint_eq, hint_eq]
      -- The two discounted prices are `crrDiscounted` at `mid.castSucc` / `mid.succ`.
      -- Identify the market discounted price with `crrDiscounted`.
      have hDcast : ∀ ω, FtapProofs.discountedPrice m i₀ mid.castSucc ω =
          crrDiscounted T S₀ u d r mid.castSucc ω := fun ω =>
        crrDiscountedPrice_eq T hS₀ hd (by linarith) (by linarith) i₀ mid.castSucc ω
      have hDsucc : ∀ ω, FtapProofs.discountedPrice m i₀ mid.succ ω =
          crrDiscounted T S₀ u d r mid.succ ω := fun ω =>
        crrDiscountedPrice_eq T hS₀ hd (by linarith) (by linarith) i₀ mid.succ ω
      -- Indicator of a coordinate-independent function: pull indicator through.
      have hindF : ∀ (D : CRRState T → ℝ) ω,
          s_set.indicator D ω = s_set.indicator (fun _ => (1:ℝ)) ω * D ω := fun D ω => by
        by_cases hω : ω ∈ s_set
        · rw [Set.indicator_of_mem hω, Set.indicator_of_mem hω, one_mul]
        · rw [Set.indicator_of_notMem hω, Set.indicator_of_notMem hω, zero_mul]
      -- Apply the crux with the indicator weight.
      have hw_inv : ∀ ω : CRRState T,
          s_set.indicator (fun _ => (1:ℝ))
            (Function.update ω ⟨mid.val, mid.isLt⟩ (! ω ⟨mid.val, mid.isLt⟩)) =
          s_set.indicator (fun _ => (1:ℝ)) ω := fun ω =>
        crrFiltration_indicator_update_invariant mid hs_set ω
      have hsum := crrRNMeasure_one_step_sum (S₀ := S₀) T hd hdr hru mid
        (s_set.indicator (fun _ => (1:ℝ))) hw_inv
      -- Rewrite both sides into the form of `hsum`.
      calc ∑ ω : CRRState T, crrRNDensity u d r ω * s_set.indicator
              (FtapProofs.discountedPrice m i₀ mid.castSucc) ω
          = ∑ ω : CRRState T, crrRNDensity u d r ω *
              s_set.indicator (fun _ => (1:ℝ)) ω * crrDiscounted T S₀ u d r mid.castSucc ω := by
            apply Finset.sum_congr rfl; intro ω _
            rw [hindF (FtapProofs.discountedPrice m i₀ mid.castSucc) ω, hDcast ω]; ring
        _ = ∑ ω : CRRState T, crrRNDensity u d r ω *
              s_set.indicator (fun _ => (1:ℝ)) ω * crrDiscounted T S₀ u d r mid.succ ω :=
            hsum.symm
        _ = ∑ ω : CRRState T, crrRNDensity u d r ω * s_set.indicator
              (FtapProofs.discountedPrice m i₀ mid.succ) ω := by
            apply Finset.sum_congr rfl; intro ω _
            rw [hindF (FtapProofs.discountedPrice m i₀ mid.succ) ω, hDsucc ω]; ring
    calc Q[FtapProofs.discountedPrice m i₀ mid.succ | m.𝒻 s_time]
        =ᵐ[Q]
          Q[Q[FtapProofs.discountedPrice m i₀ mid.succ | m.𝒻 mid.castSucc] | m.𝒻 s_time] :=
          (MeasureTheory.Filtration.condExp_condExp _ m.𝒻 hs_le_mid).symm
      _ =ᵐ[Q] Q[FtapProofs.discountedPrice m i₀ mid.castSucc | m.𝒻 s_time] :=
          MeasureTheory.condExp_congr_ae one_step
      _ =ᵐ[Q] FtapProofs.discountedPrice m i₀ s_time :=
          ih mid.castSucc (by simp [mid])

/-- **O2b — the CRR risk-neutral measure is an equivalent martingale measure.** Combines the
equivalence (O2a, `crrRNMeasure_equiv`) with the martingale property
(`crrRNMeasure_martingale`). -/
theorem crrRNMeasure_emm (T : ℕ) (hS₀ : 0 < S₀)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    FtapProofs.EquivalentMartingaleMeasure
      (crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith))
      (crrRNMeasure T u d r hd hdr hru) :=
  ⟨crrRNMeasure_equiv T hS₀ hd hdr hru, crrRNMeasure_martingale T hS₀ hd hdr hru⟩

/-- **O2b — the CRR binomial market is arbitrage-free.** With `0 < d < 1 + r < u`, the
explicit risk-neutral measure is an equivalent martingale measure, so the FTAP easy direction
(`emm_implies_no_arbitrage`) yields no-arbitrage. The full-support hypothesis is discharged by
`crrMeasure_pos` (the uniform reference measure has full support). -/
theorem crr_no_arbitrage (T : ℕ) (hS₀ : 0 < S₀)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    FtapProofs.NoArbitrage (crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith)) :=
  FtapProofs.emm_implies_no_arbitrage _
    (fun ω => crrMeasure_pos T ω)
    (crrRNMeasure T u d r hd hdr hru)
    (crrRNMeasure_emm T hS₀ hd hdr hru)

end Martingale

end OptionsProofs
