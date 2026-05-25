import Mathlib.Probability.Process.Adapted
import Mathlib.MeasureTheory.Group.Arithmetic

/-!
# Market Model

A finite-state, discrete-time financial market for the discrete FTAP (Harrison-Pliska 1981).

We work with:
- A finite time horizon `T : ℕ` (times run from `0` to `T`)
- `n` risky assets with price processes `S : Fin n → Fin (T+1) → Ω → ℝ`
- A deterministic numeraire `B : Fin (T+1) → ℝ` with `B 0 = 1` and `B t > 0`
- A filtration `𝒻 : MeasureTheory.Filtration (Fin (T+1)) m` encoding information flow
- Discounted prices `S̃ i t ω := S i t ω / B t`

## Contents

- **M1.1** `FinancialMarket` structure
- **M1.2** Measurability (`S_adapted` field)
- **M1.3** `discountedPrice` — discounted price process
- **M1.4** `numeraire_pos` — numeraire is strictly positive
- **M1.5** `discountedPrice_adapted` — discounted prices are `ℱ_t`-measurable
-/

namespace FtapProofs

/-! ### M1.1 — Market structure -/

/-- A discrete-time financial market on a measurable space `(Ω, m)`.

A `FinancialMarket Ω` bundles together all the data of a Harrison-Pliska market:
- A finite time horizon `T` (trading occurs at times `0, 1, …, T`)
- `n` risky assets with adapted price processes `S`
- A deterministic, strictly positive numeraire `B` (the risk-free bond) with `B 0 = 1`
- A filtration `𝒻` on `Ω` encoding the information available at each time

The filtration is indexed by `Fin (T + 1)` so that `𝒻 t : MeasurableSpace Ω` is `ℱ_t`.
Asset prices are adapted: `S i t` is `ℱ_t`-measurable for all assets `i` and times `t`.

**M1.1, M1.2**
-/
structure FinancialMarket (Ω : Type*) [MeasurableSpace Ω] where
  /-- Finite time horizon: trading occurs at times `0, 1, …, T` -/
  T : ℕ
  /-- Number of risky assets -/
  n : ℕ
  /-- Price processes: `S i t ω` is the price of risky asset `i` at time `t` in state `ω` -/
  S : Fin n → Fin (T + 1) → Ω → ℝ
  /-- Numeraire (risk-free bond): deterministic, strictly positive -/
  B : Fin (T + 1) → ℝ
  /-- Filtration: `𝒻 t` is the sigma-algebra `ℱ_t` available at time `t` -/
  𝒻 : MeasureTheory.Filtration (Fin (T + 1)) ‹MeasurableSpace Ω›
  /-- **M1.2** Adaptedness: `S i t` is `ℱ_t`-measurable for all `i`, `t` -/
  S_adapted : ∀ i, MeasureTheory.Adapted 𝒻 (S i)
  /-- Numeraire is strictly positive at all times -/
  B_pos : ∀ t, 0 < B t
  /-- Numeraire starts at 1 (standard normalization) -/
  B_zero : B ⟨0, Nat.zero_lt_succ T⟩ = 1

variable {Ω : Type*} [MeasurableSpace Ω]

/-! ### M1.3 — Discounted prices -/

/-- **M1.3** The discounted price process: `S̃ i t ω = S i t ω / B t`.

Discounting converts asset prices to units of the numeraire (risk-free bond).
All no-arbitrage and martingale arguments in the FTAP use discounted prices.
The discounting is well-defined since `B t > 0` for all `t` (see `numeraire_pos`). -/
noncomputable def discountedPrice (m : FinancialMarket Ω) (i : Fin m.n) (t : Fin (m.T + 1)) (ω : Ω) : ℝ :=
  m.S i t ω / m.B t

/-! ### M1.4 — Numeraire positivity -/

/-- **M1.4** The numeraire is strictly positive at all times.

This ensures discounting is invertible: undiscounted and discounted values carry
the same information, and the self-financing condition is preserved under discounting. -/
lemma numeraire_pos (m : FinancialMarket Ω) (t : Fin (m.T + 1)) : 0 < m.B t :=
  m.B_pos t

/-! ### M1.5 — Measurability of discounted prices -/

/-- **M1.5** Discounted prices are `ℱ_t`-measurable.

Since `S i t` is `ℱ_t`-measurable (by adaptedness) and `B t` is a strictly positive constant,
`S̃ i t = S i t / B t` inherits `ℱ_t`-measurability by `Measurable.div_const`. -/
lemma discountedPrice_adapted (m : FinancialMarket Ω) (i : Fin m.n) (t : Fin (m.T + 1)) :
    @Measurable Ω ℝ (m.𝒻 t) _ (discountedPrice m i t) :=
  (m.S_adapted i t).div_const (m.B t)

end FtapProofs
