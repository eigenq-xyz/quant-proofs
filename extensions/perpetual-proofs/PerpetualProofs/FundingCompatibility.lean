import PerpetualProofs.CashFlow
import StoppedTimeProofs.GeomExpectation

/-!
# Funding Compatibility

This module contains the `FundingCompatibility` result: the Ackerer-Hugonnier-Jermann
cash flow specification satisfies costless entry, while the original
He-Manela-Ross-von Wachter specification does not.

## Contents

- **F3.1** `ackerer_pv_eq` — the Ackerer cash flow present value equals `F₀ − E^Q[S_τ]`
- **F3.2** `ackerer_cashflow_satisfies_costless_entry` — **Theorem 1a**
- **F3.3** `he_manela_pv_eq` — the He et al. cash flow present value equals `S₀ − F₀`
- **F3.4** `he_manela_violates_costless_entry` — **Theorem 1b** (explicit counterexample)

## The He et al. error

The original He et al. specification has a constant payment `S₀ − F₀` at every
funding date. By `geometricExpectation_const`, this stream has present value `S₀ − F₀`.
Setting this to zero requires `S₀ = F₀`, which is not a consequence of the no-arbitrage
condition in general. The counterexample in Theorem 1b takes `S₀ = 1`, `F₀ = 2`,
`κ = 1/10`, `r = 1/20`, and verifies that `1 − 2 = −1 ≠ 0`.

## Reference

Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing." *Mathematical
Finance*, 2025. DOI: 10.1111/mafi.70018. The error is documented on p. 1 of the
Introduction.
-/

namespace PerpetualProofs

open StoppedTimeProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### F3.1 — Ackerer present value computation -/

/-- **F3.1** The geometric expectation of the Ackerer cash flow equals `F₀ − E^Q[S_τ]`.

The Ackerer cash flow at date `k` in state `ω` is `F₀ − spot k ω`. Weighting by
`Q.density ω` and summing over `Ω`:
  `∑ ω, density ω * (F₀ − spot k ω) = F₀ · ∑ ω, density ω − ∑ ω, density ω * spot k ω`
  `= F₀ − ∑ ω, density ω * spot k ω`   (by `density_sum_eq_one`)

Taking the geometric expectation in `k` and using `geometricExpectation_const` on the
constant `F₀` term yields the result. -/
lemma ackerer_pv_eq (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (F₀ : ℝ)
    (hspot_bdd : ∃ C : ℝ, ∀ k : ℕ, ∀ ω : Ω, ‖Q.density ω * market.spot k ω‖ ≤ C) :
    geometricExpectation (p := market.κ / (1 + market.r))
      (fun k => ∑ ω : Ω, Q.density ω * ackererCashFlow.cashflow k market F₀ ω) =
    F₀ - geometricExpectation (p := market.κ / (1 + market.r))
             (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω) := by
  have hp0 : 0 < market.κ / (1 + market.r) :=
    div_pos market.κ_pos (by linarith [market.r_pos])
  have hp1 : market.κ / (1 + market.r) < 1 := by
    rw [div_lt_one (by linarith [market.r_pos])]; exact market.κ_lt
  -- Step 1: simplify the integrand using ackererCashFlow definition
  have key : ∀ k, ∑ ω : Ω, Q.density ω * ackererCashFlow.cashflow k market F₀ ω =
      F₀ - ∑ ω : Ω, Q.density ω * market.spot k ω := by
    intro k
    simp only [ackererCashFlow, mul_sub]
    rw [Finset.sum_sub_distrib, ← Finset.sum_mul, Q.density_sum_eq_one, one_mul]
  simp_rw [key]
  -- Step 2: compute geometric expectation of (F₀ - g k) via Summable.tsum_sub
  simp only [geometricExpectation, mul_sub]
  -- Set up summability hypotheses
  have hF₀_sum : Summable (fun k : ℕ =>
      geomPMF (market.κ / (1 + market.r)) k * F₀) :=
    geometricExpectation_summable hp0 hp1 ⟨‖F₀‖, fun _ => le_refl _⟩
  obtain ⟨C, hC⟩ := hspot_bdd
  have hbdd : ∃ D, ∀ k, ‖∑ ω : Ω, Q.density ω * market.spot k ω‖ ≤ D := by
    refine ⟨Fintype.card Ω * C, fun k => ?_⟩
    calc ‖∑ ω : Ω, Q.density ω * market.spot k ω‖
        ≤ ∑ ω : Ω, ‖Q.density ω * market.spot k ω‖ := norm_sum_le _ _
      _ ≤ ∑ ω : Ω, C := Finset.sum_le_sum (fun ω _ => hC k ω)
      _ = Fintype.card Ω * C := by simp [Finset.sum_const, Finset.card_univ]
  have hg_sum : Summable (fun k : ℕ =>
      geomPMF (market.κ / (1 + market.r)) k *
      ∑ ω : Ω, Q.density ω * market.spot k ω) :=
    geometricExpectation_summable hp0 hp1 hbdd
  -- Apply Summable.tsum_sub: ∑' (f - g) = ∑' f - ∑' g
  rw [hF₀_sum.tsum_sub hg_sum, tsum_mul_right, geomPMF_tsum_eq_one hp0 hp1, one_mul]

/-! ### F3.2 — Theorem 1a -/

/-- **F3.2 (Theorem 1a)** The Ackerer cash flow satisfies costless entry when
`F₀ = geometricExpectation p (E^Q[S_·])`.

By `ackerer_pv_eq`, the present value equals `F₀ − geometricExpectation p (E^Q[S_·])`.
Setting `F₀ := geometricExpectation p (E^Q[S_·])` makes this `F₀ − F₀ = 0`. -/
theorem ackerer_cashflow_satisfies_costless_entry
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (hspot_bdd : ∃ C : ℝ, ∀ k : ℕ, ∀ ω : Ω, ‖Q.density ω * market.spot k ω‖ ≤ C) :
    let p := market.κ / (1 + market.r)
    let F₀ := geometricExpectation p (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
    CostlessEntry ackererCashFlow market Q F₀ := by
  simp only [CostlessEntry]
  rw [ackerer_pv_eq market Q _ hspot_bdd]
  ring

/-! ### F3.3 — He et al. present value computation -/

/-- **F3.3** The geometric expectation of the He-Manela cash flow equals `S₀ − F₀`.

The He-Manela cash flow is constant in both `k` and `ω`:
  `heManelaCashFlow.cashflow k market F₀ ω = (∑ ω, spot 0 ω) / card Ω − F₀`

Hence `∑ ω, density ω * (S₀_avg − F₀) = (S₀_avg − F₀) * ∑ ω, density ω = S₀_avg − F₀`
(by `density_sum_eq_one`). The geometric expectation of a constant equals the constant
(by `geometricExpectation_const`). -/
lemma he_manela_pv_eq (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (F₀ : ℝ) :
    geometricExpectation (p := market.κ / (1 + market.r))
      (fun k => ∑ ω : Ω, Q.density ω * heManelaCashFlow.cashflow k market F₀ ω) =
    (∑ ω : Ω, market.spot 0 ω) / Fintype.card Ω - F₀ := by
  have hp0 : 0 < market.κ / (1 + market.r) :=
    div_pos market.κ_pos (by linarith [market.r_pos])
  have hp1 : market.κ / (1 + market.r) < 1 := by
    rw [div_lt_one (by linarith [market.r_pos])]; exact market.κ_lt
  -- heManelaCashFlow.cashflow is constant in k and ω
  have key : ∀ k, ∑ ω : Ω, Q.density ω * heManelaCashFlow.cashflow k market F₀ ω =
      (∑ ω : Ω, market.spot 0 ω) / Fintype.card Ω - F₀ := by
    intro k
    simp only [heManelaCashFlow]
    rw [← Finset.sum_mul, Q.density_sum_eq_one, one_mul]
  simp_rw [key]
  exact geometricExpectation_const hp0 hp1 _

/-! ### F3.4 — Theorem 1b: explicit counterexample -/

/-- **F3.4 (Theorem 1b)** The He-Manela cash flow does not satisfy costless entry
in general.

Explicit counterexample: Ω = `Fin 2`, spot = 1 (constant), F₀ = 2, κ = 1/10, r = 1/20,
Q.density = 1/2 (uniform). Then `S₀_avg = 1` and the He-Manela present value equals
`1 − 2 = −1 ≠ 0`. Closed by `norm_num`. -/
theorem he_manela_violates_costless_entry :
    ∃ (Ω' : Type) (_ : MeasurableSpace Ω') (_ : Fintype Ω') (_ : MeasurableSingletonClass Ω')
      (market : OnePeriodMarket Ω') (Q : OnePeriodEMM Ω' market) (F₀ : ℝ),
      ¬ CostlessEntry (Ω := Ω') heManelaCashFlow market Q F₀ := by
  -- Ω = Fin 2 (two states)
  refine ⟨Fin 2, inferInstance, inferInstance, inferInstance, ?_, ?_, 2, ?_⟩
  · -- market: spot = 1, κ = 1/10, r = 1/20
    exact {
      spot := fun _k _ω => 1
      κ := 1 / 10
      r := 1 / 20
      κ_pos := by norm_num
      r_pos := by norm_num
      κ_lt := by norm_num
      spot_pos := fun _k _ω => by norm_num
      spot_bounded := ⟨1, fun _k _ω => le_refl _⟩
    }
  · -- Q: uniform density 1/2
    exact {
      density := fun _ω => 1 / 2
      density_pos := fun _ω => by norm_num
      density_sum_eq_one := by simp [Finset.sum_const, Fintype.card_fin]
      spot_expectation_const := fun k k' => by simp
    }
  · -- ¬ CostlessEntry: present value = 1 - 2 = -1 ≠ 0
    -- Use he_manela_pv_eq to compute the present value
    have pv_eq := he_manela_pv_eq
      (Ω := Fin 2)
      (market := { spot := fun _k _ω => 1, κ := 1/10, r := 1/20,
                   κ_pos := by norm_num, r_pos := by norm_num, κ_lt := by norm_num,
                   spot_pos := fun _k _ω => by norm_num,
                   spot_bounded := ⟨1, fun _k _ω => le_refl _⟩ })
      (Q := { density := fun _ω => 1/2, density_pos := fun _ω => by norm_num,
              density_sum_eq_one := by simp [Finset.sum_const, Fintype.card_fin],
              spot_expectation_const := fun k k' => by simp })
      2
    simp only [CostlessEntry] at *
    intro h
    -- pv_eq gives: geometricExpectation p (...) = (∑ ω : Fin 2, 1) / 2 - 2
    -- = 2 / 2 - 2 = 1 - 2 = -1
    rw [pv_eq] at h
    simp [Finset.sum_const, Fintype.card_fin] at h
    norm_num at h

end PerpetualProofs
