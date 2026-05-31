import OptionsProofs.RiskNeutral
import QuantCore.Option

/-!
# Put-call parity in the CRR binomial model

The headline options result. In the Cox-Ross-Rubinstein market (O1) with its explicit
risk-neutral equivalent martingale measure (O2), the risk-neutral prices of a European call
and put with strike `K` and expiry `T` satisfy

`C - P = S₀ - K / (1 + r) ^ T`.

The proof is risk-neutral pricing plus linearity of expectation:

- the payoff identity `(S_T - K)⁺ - (K - S_T)⁺ = S_T - K` (pointwise, over `ℝ`);
- linearity of the `Q`-integral splits `∫ (call - put) = ∫ S_T - K`;
- the martingale property of the discounted price gives `∫ S_T / (1+r)^T = S₀` (the discounted
  terminal price has the same `Q`-expectation as the discounted initial price, which is the
  constant `S₀` since `B 0 = 1`).

## Contents

- **O4.1** `callPayoffReal`, `putPayoffReal` — real-valued European payoffs
- **O4.2** `payoff_parity` — `(S-K)⁺ - (K-S)⁺ = S - K`
- **O4.3** `rnPrice` — risk-neutral price of a terminal claim (discounted `Q`-expectation)
- **O4.4** `terminalSpot` — the time-`T` CRR price
- **O4.5** `callPrice`, `putPrice` — risk-neutral option prices
- **O4.6** `discounted_terminal_expectation` — `∫ S̃_T ∂Q = S₀`
- **O4.7** `put_call_parity` — `C - P = S₀ - K / (1+r)^T`
-/

namespace OptionsProofs

open scoped MeasureTheory
open MeasureTheory

variable {T : ℕ} {S₀ u d r K : ℝ}

/-! ### O4.1 Real-valued payoffs -/

/-- European call payoff at expiry: `(spot - K)⁺ = max 0 (spot - K)`. -/
def callPayoffReal (spot K : ℝ) : ℝ := max 0 (spot - K)

/-- European put payoff at expiry: `(K - spot)⁺ = max 0 (K - spot)`. -/
def putPayoffReal (spot K : ℝ) : ℝ := max 0 (K - spot)

/-! ### O4.2 The payoff parity identity -/

/-- The real-valued payoff identity underlying put-call parity:
`(spot - K)⁺ - (K - spot)⁺ = spot - K`. -/
lemma payoff_parity (spot K : ℝ) :
    callPayoffReal spot K - putPayoffReal spot K = spot - K := by
  unfold callPayoffReal putPayoffReal
  rcases le_total spot K with h | h
  · rw [max_eq_left (sub_nonpos.mpr h), max_eq_right (sub_nonneg.mpr h)]; ring
  · rw [max_eq_right (sub_nonneg.mpr h), max_eq_left (sub_nonpos.mpr h)]; ring

/-! ### O4.3 Risk-neutral pricing -/

/-- The risk-neutral price of a terminal claim `X` is its discounted `Q`-expectation
`(∫ X ∂Q) / (1 + r) ^ T`, where `Q` is the CRR risk-neutral measure. -/
noncomputable def rnPrice (T : ℕ) (u d r : ℝ)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) (X : CRRState T → ℝ) : ℝ :=
  (∫ ω, X ω ∂(crrRNMeasure T u d r hd hdr hru)) / (1 + r) ^ T

/-! ### O4.4 Terminal spot price -/

/-- The CRR spot price at expiry `T` (the last time index). -/
noncomputable def terminalSpot (T : ℕ) (S₀ u d : ℝ) (ω : CRRState T) : ℝ :=
  crrPrice T S₀ u d (Fin.last T) ω

/-! ### O4.5 Option prices -/

/-- Risk-neutral price of the European call with strike `K`, expiry `T`. -/
noncomputable def callPrice (T : ℕ) (S₀ u d r K : ℝ)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) : ℝ :=
  rnPrice T u d r hd hdr hru (fun ω => callPayoffReal (terminalSpot T S₀ u d ω) K)

/-- Risk-neutral price of the European put with strike `K`, expiry `T`. -/
noncomputable def putPrice (T : ℕ) (S₀ u d r K : ℝ)
    (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) : ℝ :=
  rnPrice T u d r hd hdr hru (fun ω => putPayoffReal (terminalSpot T S₀ u d ω) K)

/-! ### O4.6 The discounted terminal price has expectation `S₀` -/

/-- `ups 0 ω = 0`: no coordinate index is below time `0`. -/
lemma ups_zero (ω : CRRState T) : ups (0 : ℕ) ω = 0 := by
  simp [ups]

/-- The discounted initial price is the constant `S₀`. -/
lemma crrDiscounted_zero_eq (S₀ u d r : ℝ) (ω : CRRState T) :
    crrDiscounted T S₀ u d r ⟨0, Nat.zero_lt_succ T⟩ ω = S₀ := by
  simp [crrDiscounted, crrPrice, ups_zero]

/-- **The risk-neutral expectation of the discounted terminal price is `S₀`.**
Because the discounted price is a `Q`-martingale (O2), its time-`T` `Q`-expectation equals its
time-`0` value, which is the constant `S₀` (the numeraire starts at `1`). Equivalently
`(∫ S_T ∂Q) / (1+r)^T = S₀`. -/
lemma discounted_terminal_expectation (T : ℕ) (S₀ u d r : ℝ)
    (hS₀ : 0 < S₀) (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    (∫ ω, terminalSpot T S₀ u d ω ∂(crrRNMeasure T u d r hd hdr hru)) / (1 + r) ^ T = S₀ := by
  set Q := crrRNMeasure T u d r hd hdr hru with hQ
  haveI : IsProbabilityMeasure Q := crrRNMeasure_prob T u d r hd hdr hru
  haveI : IsFiniteMeasure Q := inferInstance
  set m := crrMarket T S₀ u d r hS₀ hd (by linarith) (by linarith) with hm
  haveI : SigmaFiniteFiltration Q m.𝒻 := inferInstance
  -- The single risky asset index (`m.n = 1`).
  let i : Fin m.n := ⟨0, Nat.one_pos⟩
  -- Identify the discounted terminal price with `discountedPrice m i (Fin.last T)`.
  have hlast : ∀ ω, terminalSpot T S₀ u d ω / (1 + r) ^ T =
      FtapProofs.discountedPrice m i (Fin.last T) ω := by
    intro ω
    rw [crrDiscountedPrice_eq T hS₀ hd (by linarith) (by linarith)]
    simp [crrDiscounted, terminalSpot, Fin.val_last]
  -- Martingale anchoring: ∫ disc (last) = ∫ disc 0.
  have hmart := (crrRNMeasure_martingale T hS₀ hd hdr hru) i
  have hcondexp := hmart.condExp_ae_eq (Fin.zero_le (Fin.last T))
  have hintcondexp := integral_condExp (hm := m.𝒻.le ⟨0, Nat.zero_lt_succ m.T⟩)
    (f := FtapProofs.discountedPrice m i (Fin.last T)) (μ := Q)
  -- ∫ disc 0 = ∫ S₀ = S₀.
  have hdisc0 : ∀ ω, FtapProofs.discountedPrice m i ⟨0, Nat.zero_lt_succ m.T⟩ ω = S₀ := by
    intro ω
    rw [crrDiscountedPrice_eq T hS₀ hd (by linarith) (by linarith)]
    exact crrDiscounted_zero_eq S₀ u d r ω
  calc (∫ ω, terminalSpot T S₀ u d ω ∂Q) / (1 + r) ^ T
      = ∫ ω, terminalSpot T S₀ u d ω / (1 + r) ^ T ∂Q := (integral_div _ _).symm
    _ = ∫ ω, FtapProofs.discountedPrice m i (Fin.last T) ω ∂Q :=
        integral_congr_ae (Filter.Eventually.of_forall hlast)
    _ = ∫ ω, FtapProofs.discountedPrice m i ⟨0, Nat.zero_lt_succ m.T⟩ ω ∂Q := by
        rw [← hintcondexp]; exact integral_congr_ae hcondexp
    _ = ∫ _ω, S₀ ∂Q := integral_congr_ae (Filter.Eventually.of_forall hdisc0)
    _ = S₀ := by rw [integral_const, probReal_univ, one_smul]

/-! ### O4.7 Put-call parity -/

/-- **Put-call parity in the CRR model.** With `0 < d < 1 + r < u`, the risk-neutral call and
put prices with strike `K` and expiry `T` satisfy `C - P = S₀ - K / (1 + r) ^ T`. -/
theorem put_call_parity (T : ℕ) (S₀ u d r K : ℝ)
    (hS₀ : 0 < S₀) (hd : 0 < d) (hdr : d < 1 + r) (hru : 1 + r < u) :
    callPrice T S₀ u d r K hd hdr hru - putPrice T S₀ u d r K hd hdr hru =
      S₀ - K / (1 + r) ^ T := by
  haveI : IsProbabilityMeasure (crrRNMeasure T u d r hd hdr hru) :=
    crrRNMeasure_prob T u d r hd hdr hru
  -- `C - P = (∫ call - ∫ put)/(1+r)^T`.
  rw [callPrice, putPrice, rnPrice, rnPrice, div_sub_div_same]
  -- `∫ call - ∫ put = ∫ (call - put) = ∫ (S_T - K)`.
  rw [← integral_sub (.of_finite) (.of_finite)]
  have hpoint : ∀ ω, callPayoffReal (terminalSpot T S₀ u d ω) K -
      putPayoffReal (terminalSpot T S₀ u d ω) K = terminalSpot T S₀ u d ω - K :=
    fun ω => payoff_parity _ _
  rw [integral_congr_ae (Filter.Eventually.of_forall hpoint)]
  -- `∫ (S_T - K) = ∫ S_T - K`.
  rw [integral_sub (.of_finite) (.of_finite), integral_const, probReal_univ, one_smul]
  -- `(∫ S_T - K)/(1+r)^T = (∫ S_T)/(1+r)^T - K/(1+r)^T = S₀ - K/(1+r)^T`.
  rw [sub_div, discounted_terminal_expectation T S₀ u d r hS₀ hd hdr hru]

end OptionsProofs
