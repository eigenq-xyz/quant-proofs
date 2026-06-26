import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Analysis.InnerProductSpace.Basic
import Mathlib.Topology.Order.IntermediateValue
import Mathlib.Data.Real.StarOrdered
import OptimizationProofs.ProblemDefs

/-!
# Dual-Bisection Projection: Correctness (Milestone 3)

Formally verifies that the analytical dual-bisection projection operator
`Π_𝒞 : ℝᴺ → 𝒞` is the Euclidean projection onto the constraint set

    𝒞 = {w ∈ ℝᴺ | ∑ᵢ wᵢ = B, ∑ᵢ |wᵢ| ≤ L}

## Contents

- **P3.1** `primalFromDual` — coordinate-wise KKT primal from dual `(θ, μ)`
- **P3.2** `projection_feasibility` — existence of `(θ, μ)` with feasible output
- **P3.3** `projection_correctness` — KKT conditions imply optimality (proved)

## `projection_correctness` proof sketch

The KKT conditions for `min_{x ∈ 𝒞} ½‖x − y‖²` at candidate `p = primalFromDual y θ μ` are:
- Stationarity: `p i − y i + θ + μ g_i = 0` where `g_i ∈ ∂|p i|`
- Primal feasibility: `∑ p i = B`, `∑|p i| ≤ L`
- Dual feasibility: `μ ≥ 0`
- Complementary slackness: `μ(∑|p i| − L) = 0`

These are encoded in the `hkkt` and `hcs` hypotheses.

From the stationarity condition, `p i − y i + θ = −μ g_i` where `g_i ∈ ∂|p i|`.
The projection inequality `⟨p − y, x − p⟩ ≥ 0` for all `x ∈ 𝒞` follows from:

    ∑ (p i − y i)(x i − p i)
    = ∑ (p i − y i + θ)(x i − p i)         [θ cancels via ∑(x i − p i) = 0]
    = −μ ∑ g_i(x i − p i)
    ≥ −μ ∑ (|x i| − |p i|)                [subgradient inequality for |·|]
    = −μ(∑|x i| − ∑|p i|)
    ≥ 0                                    [CS: μ = 0 or ∑|p i| = L ≤ ∑|x i|... wait]

Actually: ≥ −μ(L − ∑|p i|) ≥ 0 by CS and ∑|x i| ≤ L.
-/

open scoped BigOperators

namespace OptimizationProofs

variable {N : ℕ}

/-! ### P3.1 — Primal solution from dual variables -/

/-- **P3.1** The KKT primal solution for the projection problem at dual point `(θ, μ)`.

    At the optimal dual point `(θ*, μ*)`, each component satisfies:

        xᵢ*(θ, μ) = sign(yᵢ − θ) · max(|yᵢ − θ| − μ, 0)

    This is the soft-thresholding operator shifted by `θ`. -/
noncomputable def primalFromDual (y : Fin N → ℝ) (θ μ : ℝ) : Fin N → ℝ :=
  fun i =>
    let z := y i - θ
    if |z| ≤ μ then 0
    else if z > 0 then z - μ
    else z + μ

/-! ### P3.2 — Projection feasibility -/

-- Helper (IVT): for 0 ≤ μ, pfd = max(a-μ,0) + min(a+μ,0) where a = y i - θ
private theorem pfd_eq_maxmin {μ : ℝ} (hμ : 0 ≤ μ) (y : Fin N → ℝ) (θ : ℝ) (i : Fin N) :
    primalFromDual y θ μ i = max (y i - θ - μ) 0 + min (y i - θ + μ) 0 := by
  simp only [primalFromDual]; set a := y i - θ
  by_cases h1 : |a| ≤ μ
  · simp only [h1, ↓reduceIte, max_eq_right (by linarith [(abs_le.mp h1).2] : a-μ ≤ 0),
      min_eq_right (by linarith [(abs_le.mp h1).1] : 0 ≤ a+μ), add_zero]
  · simp only [h1, ↓reduceIte]
    by_cases h2 : a > 0
    · have hlt : μ < a := by rw [abs_of_pos h2] at h1; exact not_le.mp h1
      simp only [h2, ↓reduceIte, max_eq_left (by linarith : 0 ≤ a-μ),
        min_eq_right (by linarith : 0 ≤ a+μ), add_zero]
    · have hle := not_lt.mp h2
      have hlt : a < -μ := by rw [abs_of_nonpos hle] at h1; linarith [not_le.mp h1]
      simp only [h2, ↓reduceIte, max_eq_right (by linarith : a-μ ≤ 0),
        min_eq_left (by linarith : a+μ ≤ 0), zero_add]

-- Helper (IVT): the budget function ∑ pfd(·, μ) is continuous in θ
private theorem budget_continuous (y : Fin N → ℝ) {μ : ℝ} (hμ : 0 ≤ μ) :
    Continuous (fun θ => ∑ i : Fin N, primalFromDual y θ μ i) := by
  simp_rw [pfd_eq_maxmin hμ]; apply continuous_finsetSum; intro i _; fun_prop

-- Helper: primalFromDual y θ 0 i = y i - θ (soft-threshold with μ = 0 is identity shift)
private theorem primalFromDual_mu_zero (y : Fin N → ℝ) (θ : ℝ) (i : Fin N) :
    primalFromDual y θ 0 i = y i - θ := by
  simp only [primalFromDual]
  split_ifs with h1 h2
  · linarith [abs_nonneg (y i - θ), (abs_le.mp h1).1, (abs_le.mp h1).2]
  · ring
  · ring

-- Helper: budget equals B at the unique budget-fixing θ₀ = (∑ y - B) / N
private theorem budget_at_theta0 [NeZero N] (y : Fin N → ℝ) (B : ℝ) :
    ∑ i, primalFromDual y ((∑ i, y i - B) / ↑N) 0 i = B := by
  simp_rw [primalFromDual_mu_zero]
  have hN : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (NeZero.ne N)
  have : ∑ i : Fin N, (y i - (∑ j, y j - B) / ↑N) = B := by
    rw [Finset.sum_sub_distrib]
    simp [Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
    field_simp; ring
  exact this

-- Helper: all components are 0 when μ ≥ max |y i - θ|
private theorem primalFromDual_all_zero (y : Fin N → ℝ) (θ μ : ℝ)
    (hμ : ∀ i, |y i - θ| ≤ μ) (i : Fin N) : primalFromDual y θ μ i = 0 := by
  simp only [primalFromDual]; exact if_pos (hμ i)

/-- **P3.2** For any `y : Fin N → ℝ` and feasible `(B, L)` with `|B| ≤ L`,
    there exist dual variables `θ*, μ* ≥ 0` such that `primalFromDual y θ* μ*`
    lies in the constraint set `𝒞(B, L)`.

    **Case 1** — μ = 0 suffices: Set `θ₀ = (∑ y − B) / N`. Then
    `primalFromDual y θ₀ 0 i = y i − θ₀` and `∑(y i − θ₀) = B`. If
    `∑|y i − θ₀| ≤ L`, use `(θ₀, 0)`. ✓

    **Case 2a** — μ = 0 leverage > L, B = 0: Use `θ = 0` and
    `μ = ∑|y i| + 1`. All components vanish (Case 1 of soft-threshold), giving
    budget 0 = B and leverage 0 ≤ L. ✓

    **Case 2b** — B ≠ 0 and μ = 0 leverage > L: IVT on the budget-maintaining
    leverage curve `h(μ) = ∑|primalFromDual y (θ(μ)) μ i|` where `θ(μ)` is
    the unique root of the budget equation for each fixed μ.  Witnesses found
    via `intermediate_value_Icc'`; feasibility closed by `linarith`. ✓ -/
theorem projection_feasibility [NeZero N] (B L : ℝ) (hL : 1 ≤ L) (hBL : |B| ≤ L) (y : Fin N → ℝ) :
    ∃ θ μ : ℝ, 0 ≤ μ ∧ IsInConstraintSet B L (primalFromDual y θ μ) := by
  set θ₀ := (∑ i, y i - B) / ↑N with hθ₀_def
  by_cases hlev : ∑ i, |primalFromDual y θ₀ 0 i| ≤ L
  · -- ── Case 1: μ = 0 works ──────────────────────────────────────────────────
    exact ⟨θ₀, 0, le_refl _, budget_at_theta0 y B, hlev⟩
  · push Not at hlev
    by_cases hB : B = 0
    · -- ── Case 2a: B = 0, use large μ to zero all components ───────────────
      subst hB
      -- All |y i - 0| ≤ ∑|y j| + 1
      have habs_bound : ∀ i : Fin N, |y i - 0| ≤ ∑ j, |y j| + 1 := fun i => by
        simp only [sub_zero]
        calc |y i|
            ≤ ∑ j, |y j| := Finset.single_le_sum (f := fun j => |y j|)
                (fun j _ => abs_nonneg _) (Finset.mem_univ i)
          _ ≤ ∑ j, |y j| + 1 := le_add_of_nonneg_right one_pos.le
      have hμ_pos : 0 ≤ ∑ j : Fin N, |y j| + 1 :=
        add_nonneg (Finset.sum_nonneg (fun j _ => abs_nonneg _)) one_pos.le
      have hzero : ∀ i : Fin N, primalFromDual y 0 (∑ j, |y j| + 1) i = 0 :=
        fun i => primalFromDual_all_zero y 0 _ habs_bound i
      refine ⟨0, ∑ i, |y i| + 1, hμ_pos, ?_⟩
      constructor
      · -- Budget = 0 = B = 0
        simp [hzero]
      · -- Leverage = 0 ≤ L
        simp [hzero]; linarith
    · -- ── Case 2b: B ≠ 0, leverage too large at μ = 0 — use IVT ────────────
      -- Strategy (review insight): for μ_big = ∑|y i − θ₀| + 1:
      --   • fμ(θ₀) = 0 (all components thresholded)
      --   • fμ(θ₀ − μ_big) ≥ B (positive components only, sum ≥ B)
      -- By IVT on [θ₀ − μ_big, θ₀], ∃ θ₁ with fμ(θ₁) = B.
      -- At θ₁: no Case 3 components (all y i ≤ θ₀ are Case 1), so leverage = B ≤ L.
      -- WLOG B > 0 (Case B < 0 is symmetric via negating y, B, θ).
      have hN : (N : ℝ) ≠ 0 := Nat.cast_ne_zero.mpr (NeZero.ne N)
      -- Case split: B > 0 or B < 0
      rcases lt_or_gt_of_ne hB with hBneg | hBpos
      · -- B < 0: mirror of B > 0 using the upper IVT endpoint θ₀' + μ_big
        -- fμ(θ₀') = 0 > B, fμ(θ₀' + μ_big) ≤ B (only negative components survive)
        have hBneg : B < 0 := hBneg
        have hBL' : -B ≤ L := by linarith [abs_of_neg hBneg ▸ hBL]
        set θ₀' := (∑ i, y i - B) / N
        have hbudget0 : ∑ i : Fin N, (y i - θ₀') = B := by
          show ∑ i : Fin N, (y i - (∑ j, y j - B) / N) = B
          have h1 : ∑ i : Fin N, (y i - (∑ j, y j - B) / ↑N) =
              ∑ i, y i - ↑N * ((∑ j, y j - B) / ↑N) := by
            rw [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
          rw [h1, mul_div_cancel₀ _ hN]; ring
        set μ_big := ∑ i : Fin N, |y i - θ₀'| + 1
        have hμ_pos : 0 < μ_big :=
          add_pos_of_nonneg_of_pos (Finset.sum_nonneg fun i _ => abs_nonneg _) one_pos
        have hbound : ∀ i : Fin N, |y i - θ₀'| < μ_big := fun i =>
          lt_of_le_of_lt (Finset.single_le_sum (f := fun j => |y j - θ₀'|)
            (fun j _ => abs_nonneg _) (Finset.mem_univ i)) (lt_add_one _)
        let fμ : ℝ → ℝ := fun θ => ∑ i : Fin N, primalFromDual y θ μ_big i
        have hcont : ContinuousOn fμ (Set.Icc θ₀' (θ₀' + μ_big)) :=
          (budget_continuous y (le_of_lt hμ_pos)).continuousOn.mono (Set.subset_univ _)
        -- fμ(θ₀') = 0 (all thresholded)
        have hfθ₀ : fμ θ₀' = 0 := by
          simp [fμ, show ∀ i : Fin N, primalFromDual y θ₀' μ_big i = 0 from
            fun i => by simp [primalFromDual, if_pos (hbound i).le]]
        -- fμ(θ₀' + μ_big) ≤ B < 0: only negative Case 3 components survive
        have hfhi : fμ (θ₀' + μ_big) ≤ B := by
          simp only [fμ]
          have hcomp : ∀ i : Fin N, primalFromDual y (θ₀' + μ_big) μ_big i =
              if y i < θ₀' then y i - θ₀' else 0 := by
            intro i; simp only [primalFromDual]
            have ha : y i - (θ₀' + μ_big) = (y i - θ₀') - μ_big := by ring
            by_cases hi : y i < θ₀'
            · have hneg_c : (y i - θ₀') - μ_big < -μ_big := by linarith
              rw [ha, if_neg (by rw [abs_of_neg (by linarith)]; linarith),
                     if_neg (by linarith), if_pos hi]; ring
            · have hge' := not_lt.mp hi
              have hval : y i - θ₀' < μ_big := by
                have hb := hbound i; rwa [abs_of_nonneg (by linarith : 0 ≤ y i - θ₀')] at hb
              rw [ha, if_pos (by rw [abs_of_nonpos (by linarith)]; linarith), if_neg hi]
          simp_rw [hcomp]
          calc ∑ i : Fin N, (if y i < θ₀' then y i - θ₀' else 0)
              ≤ ∑ i : Fin N, (y i - θ₀') := Finset.sum_le_sum fun i _ => by
                  by_cases h : y i < θ₀'
                  · simp [h]
                  · simp [h]; linarith [not_lt.mp h]
            _ = B := hbudget0
        -- IVT on [θ₀', θ₀' + μ_big]: fμ(θ₀' + μ_big) ≤ B ≤ 0 = fμ(θ₀')
        obtain ⟨θ₁, hθ₁_rng, hθ₁_bud⟩ :=
          intermediate_value_Icc' (by linarith [hμ_pos]) hcont
            ⟨hfhi, by rw [hfθ₀]; exact hBneg.le⟩
        -- At θ₁ ∈ [θ₀', θ₀' + μ_big]: all components ≤ 0 (no Case 2)
        have hle' : ∀ i : Fin N, primalFromDual y θ₁ μ_big i ≤ 0 := fun i => by
          simp only [primalFromDual]
          by_cases h1 : |y i - θ₁| ≤ μ_big
          · rw [if_pos h1]
          · rw [if_neg h1]; by_cases h2 : y i - θ₁ > 0
            · rw [if_pos h2]; exfalso
              -- Case 2: y i - θ₁ > μ_big, but θ₁ ≥ θ₀' so y i - θ₁ ≤ y i - θ₀'
              -- and |y i - θ₀'| < μ_big, contradiction
              have hlt : y i - θ₁ > μ_big := by
                have := not_le.mp h1; rw [abs_of_pos h2] at this; linarith
              linarith [hbound i, hθ₁_rng.1, le_abs_self (y i - θ₀')]
            · -- Case 3: y i - θ₁ ≤ 0 and |y i - θ₁| > μ_big
              rw [if_neg h2]
              have hle2 := not_lt.mp h2
              have hlt1 := not_le.mp h1
              rw [abs_of_nonpos hle2] at hlt1; linarith
        refine ⟨θ₁, μ_big, le_of_lt hμ_pos, hθ₁_bud, ?_⟩
        -- Leverage = -B = |B| ≤ L
        have hlev : ∑ i, |primalFromDual y θ₁ μ_big i| = -B := by
          simp_rw [abs_of_nonpos (hle' _), Finset.sum_neg_distrib]
          linarith [hθ₁_bud]
        linarith [hlev.symm ▸ hBL']
      · -- B > 0: the main IVT construction
        have hBpos : 0 < B := hBpos
        set θ₀' := (∑ i, y i - B) / N
        have hbudget0 : ∑ i : Fin N, (y i - θ₀') = B := by
          show ∑ i : Fin N, (y i - (∑ j, y j - B) / N) = B
          have h1 : ∑ i : Fin N, (y i - (∑ j, y j - B) / ↑N) =
              ∑ i, y i - ↑N * ((∑ j, y j - B) / ↑N) := by
            rw [Finset.sum_sub_distrib, Finset.sum_const, Finset.card_univ, Fintype.card_fin, nsmul_eq_mul]
          rw [h1, mul_div_cancel₀ _ hN]; ring
        set μ_big := ∑ i : Fin N, |y i - θ₀'| + 1
        have hμ_pos : 0 < μ_big :=
          add_pos_of_nonneg_of_pos (Finset.sum_nonneg fun i _ => abs_nonneg _) one_pos
        have hbound : ∀ i : Fin N, |y i - θ₀'| < μ_big := fun i =>
          lt_of_le_of_lt (Finset.single_le_sum (f := fun j => |y j - θ₀'|)
            (fun j _ => abs_nonneg _) (Finset.mem_univ i)) (lt_add_one _)
        let fμ : ℝ → ℝ := fun θ => ∑ i : Fin N, primalFromDual y θ μ_big i
        have hcont : ContinuousOn fμ (Set.Icc (θ₀' - μ_big) θ₀') :=
          (budget_continuous y (le_of_lt hμ_pos)).continuousOn.mono (Set.subset_univ _)
        have hfθ₀ : fμ θ₀' = 0 := by
          simp [fμ, show ∀ i : Fin N, primalFromDual y θ₀' μ_big i = 0 from
            fun i => by simp [primalFromDual, if_pos (hbound i).le]]
        have hflo : fμ (θ₀' - μ_big) ≥ B := by
          simp only [fμ]
          have hcomp : ∀ i : Fin N, primalFromDual y (θ₀' - μ_big) μ_big i =
              if y i > θ₀' then y i - θ₀' else 0 := by
            intro i; simp only [primalFromDual]
            have ha : y i - (θ₀' - μ_big) = (y i - θ₀') + μ_big := by ring
            by_cases hi : y i > θ₀'
            · have hpos : (y i - θ₀') + μ_big > μ_big := by linarith
              rw [ha, if_neg (by rw [abs_of_pos (by linarith)]; linarith),
                     if_pos (by linarith), if_pos hi]; ring
            · have hle := not_lt.mp hi
              have hnn : 0 ≤ (y i - θ₀') + μ_big := by
                linarith [(abs_le.mp (hbound i).le).1]
              rw [ha, if_pos (by rw [abs_of_nonneg hnn]; linarith), if_neg hi]
          simp_rw [hcomp]
          calc ∑ i : Fin N, (if y i > θ₀' then y i - θ₀' else 0)
              ≥ ∑ i : Fin N, (y i - θ₀') := Finset.sum_le_sum fun i _ => by
                  by_cases h : y i > θ₀'
                  · simp [h]
                  · simp [h]; linarith [not_lt.mp h]
            _ = B := hbudget0
        obtain ⟨θ₁, hθ₁_rng, hθ₁_bud⟩ :=
          intermediate_value_Icc' (by linarith [hμ_pos]) hcont
            ⟨by rw [hfθ₀]; exact hBpos.le, hflo⟩
        have hge : ∀ i : Fin N, 0 ≤ primalFromDual y θ₁ μ_big i := fun i => by
          simp only [primalFromDual]
          by_cases h1 : |y i - θ₁| ≤ μ_big
          · rw [if_pos h1]
          · rw [if_neg h1]; by_cases h2 : y i - θ₁ > 0
            · rw [if_pos h2]
              have := not_le.mp h1; rw [abs_of_pos h2] at this; linarith
            · rw [if_neg h2]; exfalso
              have hle := not_lt.mp h2
              have hlt3 : -(y i - θ₁) > μ_big := by
                have := not_le.mp h1; rw [abs_of_nonpos hle] at this; linarith
              linarith [neg_abs_le (y i - θ₀'), hbound i, hθ₁_rng.2]
        refine ⟨θ₁, μ_big, le_of_lt hμ_pos, hθ₁_bud, ?_⟩
        have hlev : ∑ i, |primalFromDual y θ₁ μ_big i| = B := by
          simp_rw [abs_of_nonneg (hge _)]; exact hθ₁_bud
        linarith [hlev.symm ▸ (abs_of_pos hBpos ▸ hBL)]
      -- The leverage h(μ) = ∑|primalFromDual y (θ(μ)) μ i| is continuous in μ,
      -- h(0) > L (by hlev), and h(μ) → |B| ≤ L as μ → ∞.
      -- By IVT, ∃ μ* with h(μ*) ≤ L.  Use (θ(μ*), μ*) as the witness.

/-! ### P3.3 — Projection correctness from KKT conditions -/

/-- **P3.3** If `p = primalFromDual y θ μ` satisfies the KKT conditions for the
    projection problem `min_{x ∈ 𝒞} ½‖x − y‖²`, then `p` minimizes the Euclidean
    distance to `y` over `𝒞`.

    The projection inequality `⟨p − y, x − p⟩ ≥ 0` for all feasible `x` is proved
    by expanding the KKT stationarity condition in each of the three cases
    (`p i = 0`, `p i > 0`, `p i < 0`), applying the subgradient inequality for `|·|`,
    summing over coordinates, and using complementary slackness to conclude. -/
theorem projection_correctness (B L : ℝ) (y x : Fin N → ℝ)
    (hx : IsInConstraintSet B L x) (θ μ : ℝ) (hμ : 0 ≤ μ)
    (hfeas : IsInConstraintSet B L (primalFromDual y θ μ))
    -- KKT stationarity: the primal-from-dual formula satisfies the subdifferential condition
    (hkkt : ∀ i,
      let xi := primalFromDual y θ μ i
      (xi = 0 ∧ |y i - θ| ≤ μ) ∨
      (xi > 0 ∧ y i - θ = xi + μ) ∨
      (xi < 0 ∧ y i - θ = xi - μ))
    -- Complementary slackness for the leverage dual
    (hcs : μ * ((∑ i, |primalFromDual y θ μ i|) - L) = 0) :
    ∑ i, (primalFromDual y θ μ i - y i) ^ 2 ≤ ∑ i, (x i - y i) ^ 2 := by
  -- Abbreviate the candidate projection
  set p := primalFromDual y θ μ with hp_def
  -- ── Step 1: Reduce to the projection inequality ⟨p − y, x − p⟩ ≥ 0 ──────────
  -- Use: ‖x − y‖² = ‖x − p‖² + 2⟨p − y, x − p⟩ + ‖p − y‖²
  suffices hinner : 0 ≤ ∑ i : Fin N, (p i - y i) * (x i - p i) by
    -- Prove ∑(p-y)² ≤ ∑(x-y)² via the identity:
    -- ∑(x-y)² - ∑(p-y)² = ∑(x-p)² + 2·∑(p-y)(x-p) ≥ 0
    have hid : ∑ i : Fin N, (x i - y i) ^ 2 - ∑ i, (p i - y i) ^ 2 =
        ∑ i, (x i - p i) ^ 2 + 2 * ∑ i, (p i - y i) * (x i - p i) := by
      -- Step: rewrite each term pointwise, then split sums
      have step1 : ∑ i : Fin N, ((x i - y i)^2 - (p i - y i)^2) =
          ∑ i, ((x i - p i)^2 + 2*(p i - y i)*(x i - p i)) :=
        Finset.sum_congr rfl (fun i _ => by ring)
      have step2 : ∑ i : Fin N, ((x i - y i)^2 - (p i - y i)^2) =
          ∑ i, (x i - y i)^2 - ∑ i, (p i - y i)^2 :=
        Finset.sum_sub_distrib (f := fun i => (x i - y i)^2) (g := fun i => (p i - y i)^2)
      have step3 : ∑ i : Fin N, ((x i - p i)^2 + 2*(p i - y i)*(x i - p i)) =
          ∑ i, (x i - p i)^2 + ∑ i, 2*(p i - y i)*(x i - p i) :=
        Finset.sum_add_distrib
      have step4 : ∑ i : Fin N, 2*(p i - y i)*(x i - p i) =
          2 * ∑ i, (p i - y i)*(x i - p i) := by
        have : ∀ i : Fin N, 2*(p i - y i)*(x i - p i) = (2:ℝ) * ((p i - y i)*(x i - p i)) :=
          fun i => by ring
        simp_rw [this, ← Finset.mul_sum]
      linarith [step1, step2, step3, step4]
    linarith [Finset.sum_nonneg (fun i (_ : i ∈ Finset.univ) => sq_nonneg (x i - p i))]
  -- ── Step 2: Budget cancellation — the θ multiplier vanishes ─────────────────
  -- The sum ∑(xᵢ − pᵢ) = 0 since both x and p satisfy the budget constraint.
  have hsum_xp : ∑ i : Fin N, (x i - p i) = 0 := by
    rw [Finset.sum_sub_distrib]; linarith [hx.1, hfeas.1]
  -- Therefore ∑(p i − y i)(x i − p i) = ∑(p i − y i + θ)(x i − p i)
  have hbudget : ∑ i : Fin N, (p i - y i) * (x i - p i) =
      ∑ i : Fin N, (p i - y i + θ) * (x i - p i) := by
    have hrw : ∑ i : Fin N, (p i - y i + θ) * (x i - p i) =
        ∑ i, (p i - y i) * (x i - p i) + θ * ∑ i, (x i - p i) := by
      simp [add_mul, Finset.sum_add_distrib, ← Finset.mul_sum]
    rw [hrw, hsum_xp, mul_zero, add_zero]
  rw [hbudget]
  -- ── Step 3: Pointwise KKT bound ─────────────────────────────────────────────
  -- For each i: (p i − y i + θ)(x i − p i) ≥ −μ(|x i| − |p i|)
  -- This follows from the KKT stationarity condition, which encodes p i − y i + θ = −μ gᵢ
  -- where gᵢ ∈ ∂|p i|, combined with the subgradient inequality |x i| ≥ |p i| + gᵢ(x i − p i).
  have hpw : ∀ i : Fin N, -μ * (|x i| - |p i|) ≤ (p i - y i + θ) * (x i - p i) := by
    intro i
    -- `let xi := p i` in hkkt is definitionally p i; rcases unfolds it directly
    rcases hkkt i with ⟨hp0, habs⟩ | ⟨hpos, heq⟩ | ⟨hneg, heq⟩
    · -- Case 1: p i = 0, |y i − θ| ≤ μ
      -- KKT: p i − y i + θ = θ − y i with |θ − y i| ≤ μ
      -- Bound: (θ − y i) * x i ≥ −|θ − y i| * |x i| ≥ −μ * |x i|
      simp only [hp0, abs_zero, sub_zero, zero_sub]
      -- Goal: -μ * |x i| ≤ (θ - y i) * x i
      have habs' : |θ - y i| ≤ μ := by rwa [abs_sub_comm]
      nlinarith [abs_nonneg (x i), neg_abs_le ((θ - y i) * x i),
                 abs_mul (θ - y i) (x i),
                 mul_le_mul_of_nonneg_right habs' (abs_nonneg (x i))]
    · -- Case 2: p i > 0, y i − θ = p i + μ
      -- KKT: p i − y i + θ = −μ  (coefficient of subgradient g i = 1)
      -- Bound: −μ(x i − p i) ≥ −μ(|x i| − p i)  since |x i| ≥ x i
      have hcoeff : p i - y i + θ = -μ := by linarith
      rw [hcoeff, abs_of_pos hpos]
      nlinarith [le_abs_self (x i)]
    · -- Case 3: p i < 0, y i − θ = p i − μ
      -- KKT: p i − y i + θ = μ  (coefficient of subgradient g i = −1)
      -- Bound: μ(x i − p i) ≥ −μ(|x i| + p i)  since x i ≥ −|x i|
      have hcoeff : p i - y i + θ = μ := by linarith
      rw [hcoeff, abs_of_neg hneg]
      nlinarith [neg_abs_le (x i), abs_nonneg (x i)]
  -- ── Step 4: Sum the pointwise bounds ────────────────────────────────────────
  have hsum_lower : ∑ i : Fin N, -μ * (|x i| - |p i|) ≤
      ∑ i, (p i - y i + θ) * (x i - p i) :=
    Finset.sum_le_sum (fun i _ => hpw i)
  -- Rewrite: ∑ −μ(|x i| − |p i|) = −μ(∑|x i| − ∑|p i|)
  have hrw_lower : ∑ i : Fin N, -μ * (|x i| - |p i|) =
      -μ * (∑ i, |x i| - ∑ i, |p i|) := by
    rw [← Finset.mul_sum]
    congr 1
    simp [Finset.sum_sub_distrib]
  rw [hrw_lower] at hsum_lower
  -- ── Step 5: Conclude using complementary slackness ──────────────────────────
  rcases eq_or_ne μ 0 with rfl | hμne
  · -- μ = 0: the lower bound is 0
    simp at hsum_lower; linarith
  · -- μ > 0: from complementary slackness, ∑|p i| = L
    have hμpos : 0 < μ := lt_of_le_of_ne hμ (Ne.symm hμne)
    have hpL : ∑ i : Fin N, |p i| = L := by
      have h := hcs
      have hne : (∑ i, |p i|) - L = 0 :=
        (mul_eq_zero.mp h).resolve_left (ne_of_gt hμpos)
      linarith
    -- Now: −μ(∑|x i| − L) ≤ ∑(p i − y i + θ)(x i − p i)
    -- And: ∑|x i| ≤ L, so −μ(∑|x i| − L) ≥ 0
    rw [hpL] at hsum_lower
    -- hsum_lower : -μ * (∑|x i| - L) ≤ ∑(...)
    -- hx.2 : ∑|x i| ≤ L → ∑|x i| - L ≤ 0 → -μ*(∑|x i| - L) ≥ 0
    nlinarith [hx.2]

end OptimizationProofs
