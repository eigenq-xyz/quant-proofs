import Mathlib.LinearAlgebra.Matrix.PosDef
import Mathlib.Analysis.InnerProductSpace.Basic
import OptimizationProofs.ProblemDefs

/-!
# Dual-Bisection Projection: Correctness (Milestone 3)

Formally verifies that the analytical dual-bisection projection operator
`Π_𝒞 : ℝᴺ → 𝒞` is the Euclidean projection onto the constraint set

    𝒞 = {w ∈ ℝᴺ | ∑ᵢ wᵢ = B, ∑ᵢ |wᵢ| ≤ L}

This module contains:

- **P3.1** `primalFromDual` — abstract form of the KKT primal solution
- **P3.2** `projection_feasibility` — output satisfies both constraints (TODO: prove)
- **P3.3** `projection_correctness` — output minimises ‖· − y‖₂² over 𝒞 (TODO: prove)

## Proof strategy (for future completion)

The projection problem is:

    min_{x ∈ 𝒞} ½ ‖x − y‖₂²

By strong duality (the constraint set is convex and closed), the KKT conditions
are necessary and sufficient.  The Lagrangian is:

    L(x, θ, μ) = ½ ‖x − y‖₂² + θ(∑ xᵢ − B) + μ(∑ |xᵢ| − L)

with dual variables `θ ∈ ℝ` (budget) and `μ ≥ 0` (leverage).

The closed-form primal solution is:

    xᵢ*(θ, μ) = sign(yᵢ − θ) · max(|yᵢ − θ| − μ, 0)

The proof plan is:

1. Show that `xᵢ*(θ, μ)` satisfies the subdifferential inclusion of the
   Lagrangian (Step 1: pointwise KKT for the `|xᵢ|` term via
   `ConvexOn.subdifferential_add`).

2. Show that bisecting `θ` to enforce `∑ xᵢ*(θ, μ) = B` finds the unique root
   (Step 2: monotonicity of `θ ↦ ∑ xᵢ*(θ, μ)` from `Antitone.iSup_eq`-style
   reasoning).

3. Show that bisecting `μ` to enforce the complementary slackness condition
   `μ(∑|xᵢ*| − L) = 0` finds the global optimum (Step 3: from strong duality
   for the bounded L₁-ball, `ConvexDual` in mathlib).

4. Combine: the solution to the nested bisection is the Euclidean projection.

**Status**: Proof obligations stubs.  The structure is correct; individual steps
require `Mathlib.Analysis.Convex.Duality` and `Mathlib.Optimization.LinearCombination`.
Remove `sorry` after completing Milestone 3.
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

/-- **P3.2** The projection `Π_𝒞(y)` is always feasible: it lies in `𝒞(B, L)`.

    Formally: for any `y`, there exist dual variables `θ* ∈ ℝ`, `μ* ≥ 0` such
    that `primalFromDual y θ* μ*` satisfies both constraints.

    **Proof outline**:
    - Budget: `∑ xᵢ(θ*, μ*) = B` holds by construction of `θ*` via bisection.
    - Leverage: `∑ |xᵢ(θ*, μ*)| ≤ L` holds by complementary slackness.

    **Status**: `sorry`.  Full proof requires reasoning about the bisection
    algorithm's fixed point and the budget-feasible root existence (by the
    Intermediate Value Theorem on the strictly decreasing function
    `θ ↦ ∑ xᵢ(θ, μ)`). -/
theorem projection_feasibility (B L : ℝ) (hL : 1 ≤ L) (y : Fin N → ℝ) :
    ∃ θ μ : ℝ, 0 ≤ μ ∧ IsInConstraintSet B L (primalFromDual y θ μ) := by
  sorry
  -- TODO (Milestone 3, Step 2–3):
  --   1. Apply IVT to `h(θ) = ∑ xᵢ(θ, 0) - B` to find θ₀ with h(θ₀) = 0 (μ = 0 case).
  --   2. If `∑|xᵢ(θ₀, 0)| ≤ L`, take (θ*, μ*) = (θ₀, 0).
  --   3. Otherwise, solve the nested bisection over μ ≥ 0 to enforce complementary slackness.
  --   Key lemmas: `StrictAntiOn` for the budget sum, `ContinuousOn` for the leverage sum.

/-! ### P3.3 — Projection correctness (Euclidean distance minimisation) -/

/-- **P3.3** The projection `Π_𝒞(y)` minimises the Euclidean distance to `y` over `𝒞`.

    Formally: `primalFromDual y θ* μ*` (with the optimal dual variables from
    `projection_feasibility`) satisfies the characterisation

        ∀ x ∈ 𝒞, ‖Π_𝒞(y) − y‖₂² ≤ ‖x − y‖₂²

    equivalently (by the projection theorem for convex sets):

        ∀ x ∈ 𝒞, ⟨Π_𝒞(y) − y, x − Π_𝒞(y)⟩ ≥ 0

    **Proof outline**:
    Prove the KKT conditions hold at `(xᵢ*, θ*, μ*)`:
    - Stationarity: `0 ∈ ∂_{xᵢ}(½|xᵢ−yᵢ|² + θ xᵢ + μ |xᵢ|)` at `xᵢ*`
    - Primal feasibility: from `projection_feasibility`
    - Dual feasibility: `μ* ≥ 0`
    - Complementary slackness: `μ*(∑|xᵢ*| − L) = 0`
    These KKT conditions are sufficient (strong duality from convexity of 𝒞).

    **Status**: `sorry`.  Full proof requires `Mathlib.Analysis.Convex.Duality`
    and the subdifferential calculus for the absolute value. -/
theorem projection_correctness (B L : ℝ) (hL : 1 ≤ L) (y x : Fin N → ℝ)
    (hx : IsInConstraintSet B L x) (θ μ : ℝ) (hμ : 0 ≤ μ)
    (hfeas : IsInConstraintSet B L (primalFromDual y θ μ))
    -- KKT stationarity: at each coordinate, the primal-from-dual formula
    -- satisfies the subdifferential condition
    (hkkt : ∀ i,
      let xi := primalFromDual y θ μ i
      (xi = 0 ∧ |y i - θ| ≤ μ) ∨
      (xi > 0 ∧ y i - θ = xi + μ) ∨
      (xi < 0 ∧ y i - θ = xi - μ))
    -- Complementary slackness for the leverage dual
    (hcs : μ * ((∑ i, |primalFromDual y θ μ i|) - L) = 0) :
    ∑ i, (primalFromDual y θ μ i - y i) ^ 2 ≤ ∑ i, (x i - y i) ^ 2 := by
  sorry
  -- TODO (Milestone 3, Step 4):
  --   Use the projection theorem for closed convex sets:
  --     ⟨Π y − y, x − Π y⟩ ≥ 0  ∀ x ∈ 𝒞
  --   This follows from the KKT conditions above by expanding the inner product
  --   and summing over coordinates.
  --   Key lemmas: `inner_sub_left`, `Finset.sum_nonneg`, case-analysis on `hkkt i`.

end OptimizationProofs
