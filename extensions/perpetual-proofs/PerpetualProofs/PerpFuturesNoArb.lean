import PerpetualProofs.FundingCompatibility

/-!
# The No-Arbitrage Pricing Theorem for Perpetual Futures

The unique no-arbitrage price for a perpetual future is the geometric expectation
of the risk-neutral spot price:

`F₀ = geometricExpectation (κ/(1+r)) (fun k => E^Q[S_k])`

This is the discrete finite-state version of the main result in Ackerer, Hugonnier,
and Jermann (2025), DOI: 10.1111/mafi.70018.

## Contents

- **PR4.1** `no_arb_uniqueness` — any two no-arbitrage prices must be equal
- **PR4.2** `no_arb_existence` — the geometric-expectation price satisfies
  `NoBuyAndHoldArbitrage`
- **PR4.3** `perp_futures_no_arb_price` — **Theorem 2** combining existence and
  uniqueness

## Proof structure

**Uniqueness (PR4.1):** Both prices satisfy `CostlessEntry`. By `ackerer_pv_eq`,
each price must equal `geometricExpectation p (E^Q[S_·])`, so they are equal.
The `spot_density_bdd` helper derives the required boundedness from
`OnePeriodMarket.spot_bounded` plus density ≤ 1 (which follows from
`density_sum_eq_one` and positivity on `Fintype Ω`).

**Existence (PR4.2):** At the geometric-expectation price, `CostlessEntry` holds by
`ackerer_cashflow_satisfies_costless_entry`. The round-trip cash-flow difference
`CF(F₀') − CF(F₀)` simplifies to the constant `F₀' − F₀`, whose geometric
expectation is `F₀' − F₀ ≠ 0` when `F₀' ≠ F₀` (by `geometricExpectation_const`).
-/

namespace PerpetualProofs

open StoppedTimeProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### Auxiliary: spot-density boundedness -/

omit [MeasurableSpace Ω] [MeasurableSingletonClass Ω] in
/-- Derive `‖Q.density ω * market.spot k ω‖ ≤ C` from `market.spot_bounded` and the
fact that each `Q.density ω ≤ 1` (since densities are positive and sum to 1 on `Fintype Ω`).
Used internally by `no_arb_uniqueness` and `no_arb_existence` to satisfy the summability
hypothesis of `ackerer_pv_eq` without threading `hspot_bdd` through the caller. -/
lemma spot_density_bdd (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market) :
    ∃ C : ℝ, ∀ k : ℕ, ∀ ω : Ω, ‖Q.density ω * market.spot k ω‖ ≤ C := by
  obtain ⟨C, hC⟩ := market.spot_bounded
  -- Each density ω ≤ 1 because densities are positive and sum to 1
  have hd_le : ∀ ω : Ω, Q.density ω ≤ 1 := fun ω => by
    have h1 : Q.density ω ≤ ∑ ω' : Ω, Q.density ω' :=
      Finset.single_le_sum (fun ω' _ => (Q.density_pos ω').le) (Finset.mem_univ ω)
    linarith [Q.density_sum_eq_one]
  refine ⟨C, fun k ω => ?_⟩
  rw [norm_mul, Real.norm_of_nonneg (Q.density_pos ω).le,
      Real.norm_of_nonneg (market.spot_pos k ω).le]
  calc Q.density ω * market.spot k ω
      ≤ 1 * market.spot k ω :=
          mul_le_mul_of_nonneg_right (hd_le ω) (market.spot_pos k ω).le
    _ = market.spot k ω := one_mul _
    _ ≤ C := hC k ω

/-! ### PR4.1 — Uniqueness -/

/-- **PR4.1** Any two prices satisfying `NoBuyAndHoldArbitrage` must be equal.

Both `F₀` and `F₀'` satisfy `CostlessEntry`. By `ackerer_pv_eq`, each equals
`geometricExpectation p (E^Q[S_·])`. Since this expression is independent of the
price, `F₀ = F₀'`. -/
lemma no_arb_uniqueness (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (F₀ F₀' : ℝ)
    (h : NoBuyAndHoldArbitrage market Q F₀)
    (h' : NoBuyAndHoldArbitrage market Q F₀') :
    F₀ = F₀' := by
  have hspot_bdd := spot_density_bdd market Q
  -- Both CostlessEntry conditions give F₀ = geomExp(·) and F₀' = geomExp(·)
  have hCE := h.1
  have hCE' := h'.1
  simp only [CostlessEntry] at hCE hCE'
  rw [ackerer_pv_eq market Q F₀ hspot_bdd] at hCE
  rw [ackerer_pv_eq market Q F₀' hspot_bdd] at hCE'
  -- hCE : F₀ − geomExp(E^Q[S_·]) = 0
  -- hCE' : F₀' − geomExp(E^Q[S_·]) = 0
  linarith

/-! ### PR4.2 — Existence -/

/-- **PR4.2** The geometric-expectation price satisfies `NoBuyAndHoldArbitrage`.

The price `F₀ = geometricExpectation p (E^Q[S_·])` satisfies:
1. **CostlessEntry** — by `ackerer_cashflow_satisfies_costless_entry` (Theorem 1a).
2. **No round-trip arbitrage** — the Ackerer cash-flow difference
   `CF(F₀') k ω − CF(F₀) k ω = (F₀' − spot k ω) − (F₀ − spot k ω) = F₀' − F₀`
   is constant, so by `geometricExpectation_const` its geometric expectation equals
   `F₀' − F₀ ≠ 0` whenever `F₀' ≠ F₀`. -/
lemma no_arb_existence (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market) :
    NoBuyAndHoldArbitrage market Q
      (geometricExpectation (market.κ / (1 + market.r))
        (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)) := by
  have hp0 : 0 < market.κ / (1 + market.r) :=
    div_pos market.κ_pos (by linarith [market.r_pos])
  have hp1 : market.κ / (1 + market.r) < 1 := by
    rw [div_lt_one (by linarith [market.r_pos])]; exact market.κ_lt
  have hspot_bdd := spot_density_bdd market Q
  -- Abbreviate F₀ for readability
  set F₀ := geometricExpectation (market.κ / (1 + market.r))
              (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) with hF₀_def
  refine ⟨ackerer_cashflow_satisfies_costless_entry market Q hspot_bdd, fun F₀' hne => ?_⟩
  -- Compute round-trip cash-flow difference: CF(F₀') k ω − CF(F₀) k ω = F₀' − F₀
  have key : ∀ k, ∑ ω : Ω, Q.density ω *
      (ackererCashFlow.cashflow k market F₀' ω - ackererCashFlow.cashflow k market F₀ ω) =
      F₀' - F₀ := by
    intro k
    simp only [ackererCashFlow]
    have : ∀ ω : Ω, Q.density ω * ((F₀' - market.spot k ω) - (F₀ - market.spot k ω)) =
        Q.density ω * (F₀' - F₀) := fun ω => by ring
    simp_rw [this, ← Finset.sum_mul, Q.density_sum_eq_one, one_mul]
  -- Geometric expectation of the constant (F₀' − F₀) equals F₀' − F₀
  simp_rw [key]
  rw [geometricExpectation_const hp0 hp1]
  -- F₀' − F₀ ≠ 0 since F₀' ≠ F₀
  exact sub_ne_zero.mpr hne

/-! ### PR4.3 — Theorem 2 -/

/-- **PR4.3 (Theorem 2)** The unique no-arbitrage price for a perpetual futures
contract is `geometricExpectation (κ/(1+r)) (E^Q[S_·])`.

Combines `no_arb_existence` (the geometric-expectation price is a no-arbitrage price)
and `no_arb_uniqueness` (any two no-arbitrage prices coincide). -/
theorem perp_futures_no_arb_price (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market) :
    let p := market.κ / (1 + market.r)
    let F₀ := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
    NoBuyAndHoldArbitrage market Q F₀ ∧
    ∀ F₀' : ℝ, NoBuyAndHoldArbitrage market Q F₀' → F₀' = F₀ := by
  exact ⟨no_arb_existence market Q,
         fun F₀' h' => (no_arb_uniqueness market Q _ F₀' (no_arb_existence market Q) h').symm⟩

end PerpetualProofs
