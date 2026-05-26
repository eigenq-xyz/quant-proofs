import FtapProofs.Market
import StoppedTimeProofs.GeomExpectation
import Mathlib.MeasureTheory.Measure.MeasureSpace

/-!
# One-Period Perpetual Futures Market Model

Definitions for the one-period market and risk-neutral measure used in the
perpetual futures pricing theorems. All definitions specialize the
`FtapProofs.FinancialMarket` framework to the perpetual futures setting.

## Contents

- **P2.1** `OnePeriodMarket` — market with an infinite spot price sequence,
  funding rate κ, and risk-free rate r
- **P2.2** `OnePeriodEMM` — minimal equivalent martingale measure for the
  one-period model

## Dependency note

`OnePeriodEMM` is defined here as a self-contained structure rather than importing
`FtapProofs.MartingaleMeasure`, which is not yet proved (ftap-proofs Phase 4,
tracked in issue #110). Once Phase 4 is complete, replace `OnePeriodEMM` with
`FtapProofs.MartingaleMeasure.EquivalentMartingaleMeasure` — theorem statements
in `FundingCompatibility.lean`, `PerpFuturesNoArb.lean`, and
`InversePerpCorrection.lean` should not need to change.

## Open question (resolve before Week 3 proofs)

The Ackerer et al. cash flow at date k involves F_k — the perpetual futures price
at date k. In the time-homogeneous (stationary) model, F_k = F₀ for all k.
Confirm this reading against Ackerer et al. §2 before committing `ackererCashFlow`
in `CashFlow.lean`. See SPEC.md Q1.
-/

namespace PerpetualProofs

variable (Ω : Type*) [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### P2.1 — One-period market -/

/-- **P2.1** A one-period perpetual futures market on a finite probability space `Ω`.

The spot price process `spot : ℕ → Ω → ℝ` is indexed by funding date `k ∈ ℕ`,
representing the spot price at each funding interval. The market is characterized by:
- A funding rate `κ > 0` (proportional funding payment per interval)
- A risk-free rate `r > 0` (per funding interval)
- The intensity `p = κ / (1 + r) ∈ (0, 1)` governing the geometric stopping time

All spot prices are strictly positive (`spot_pos`), which is required for the
inverse perpetual convexity adjustment (Theorem 3). `spot_bounded` ensures the
cash-flow tsum converges — see `geometricExpectation_summable` in `stopped-time-proofs`.
Resolves issues #124 and #125. -/
structure OnePeriodMarket where
  /-- Spot price process: `spot k ω` is the spot price at funding date `k` in state `ω` -/
  spot : ℕ → Ω → ℝ
  /-- Funding rate κ > 0 -/
  κ : ℝ
  /-- Risk-free rate r > 0 per funding interval -/
  r : ℝ
  /-- Funding rate is strictly positive -/
  κ_pos : 0 < κ
  /-- Risk-free rate is strictly positive -/
  r_pos : 0 < r
  /-- Funding rate is less than 1 + r (ensures p = κ/(1+r) < 1) -/
  κ_lt : κ < 1 + r
  /-- Spot prices are strictly positive (required for inverse perpetual) -/
  spot_pos : ∀ k ω, 0 < spot k ω
  /-- Spot prices are uniformly bounded above.
  Required for convergence of `geometricExpectation` in `CostlessEntry`: the cash-flow
  tsum `∑' k, geomPMF p k * (F₀ - spot k ω)` is summable only when `spot k ω ≤ C`
  for all `k` and `ω`. Without this, Lean's `tsum` convention (returns 0 for
  non-summable series) makes `CostlessEntry` vacuously satisfiable for unbounded
  spot processes. Resolves issue #124. -/
  spot_bounded : ∃ C : ℝ, ∀ k : ℕ, ∀ ω : Ω, spot k ω ≤ C

/-! ### P2.2 — Equivalent martingale measure -/

/-- **P2.2** A one-period equivalent martingale measure (EMM) for `market`.

A risk-neutral probability measure Q on Ω, represented by a strictly positive
density function. Q is equivalent to the reference measure P (both assign positive
probability to every state) via `density_pos`. The field `spot_expectation_const`
encodes the martingale condition: Q-expected spot prices are constant across all
funding dates. This is the time-homogeneous analogue of the full martingale condition
and is sufficient for all theorems in `perpetual-proofs`.

**TODO:** Replace with `FtapProofs.MartingaleMeasure.EquivalentMartingaleMeasure`
once ftap-proofs Phase 4 (issue #110) is complete. Resolves issue #125. -/
structure OnePeriodEMM (market : OnePeriodMarket Ω) where
  /-- Risk-neutral density: Q({ω}) = density ω -/
  density : Ω → ℝ
  /-- Strictly positive density (Q equivalent to P) -/
  density_pos : ∀ ω, 0 < density ω
  /-- Q is a probability measure: densities sum to 1 -/
  density_sum_eq_one : ∑ ω : Ω, density ω = 1
  /-- Martingale condition: Q-expected spot price is constant across all funding dates.
  In the time-homogeneous model, `E^Q[S_k] = E^Q[S_{k'}]` for all `k`, `k'`. This
  is what allows the geometric expectation in the pricing formula to reduce to a single
  Q-expectation `E^Q[S_τ]`. Required by `no_arb_existence` (PR4.2). -/
  spot_expectation_const : ∀ k k' : ℕ,
    ∑ ω : Ω, density ω * market.spot k ω =
    ∑ ω : Ω, density ω * market.spot k' ω

end PerpetualProofs
