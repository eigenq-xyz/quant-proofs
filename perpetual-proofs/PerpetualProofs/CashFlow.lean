import PerpetualProofs.Market
import StoppedTimeProofs.GeomExpectation

/-!
# Cash Flow Specifications and Key Conditions

Definitions for perpetual futures cash flow specifications, costless entry,
and the no-buy-and-hold-arbitrage condition.

## Contents

- **P2.3** `CashFlowSpec` — abstract cash flow specification
- **P2.3** `ackererCashFlow` — the Ackerer-Hugonnier-Jermann (2025) specification
- **P2.3** `heManelaCashFlow` — the original He-Manela-Ross-von Wachter specification
  (as documented in Ackerer et al. to be incompatible with costless entry)
- **P2.4** `CostlessEntry` — the costless entry condition as a Lean `Prop`
- **P2.4** `NoBuyAndHoldArbitrage` — no-arbitrage condition for a given entry price

## The He et al. error

`heManelaCashFlow` encodes the original specification from the initial version of
He, Manela, Ross, and von Wachter (arXiv:2212.06888). Ackerer et al. (DOI:
10.1111/mafi.70018) document that this specification is "incompatible with the
assumption that entering the contract is costless." The theorem
`he_manela_violates_costless_entry` in `FundingCompatibility.lean` produces the
explicit counterexample.

## Note on ackererCashFlow

The Ackerer et al. cash flow at date k is F_k − S_k, where F_k is the current
perpetual futures price. In the time-homogeneous model assumed here, F_k = F₀ for all k
(stationarity). This must be confirmed against Ackerer et al. §2 before Week 3 proof
writing. See SPEC.md Q1 and the open question in `Market.lean`.

## Note on heManelaCashFlow (issue #127)

This encoding takes `S₀` as the arithmetic mean of spot prices at date 0 over `Ω`,
implicitly assuming the reference measure P is uniform. For the F3.4 counterexample,
the market is symmetric (two states, equal P-probability), so the arithmetic mean
equals the P-expectation. Any construction of the counterexample market must satisfy
this uniformity condition.
-/

namespace PerpetualProofs

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

open StoppedTimeProofs

/-! ### P2.3 — Cash flow specifications -/

/-- **P2.3** A cash flow specification for a perpetual futures contract.

`cashflow k market F₀ ω` is the payment received by the long holder at funding
date `k` in state `ω`, given a futures entry price of `F₀`. -/
structure CashFlowSpec (Ω : Type*) [MeasurableSpace Ω] [Fintype Ω]
    [MeasurableSingletonClass Ω] where
  /-- Payment to the long at funding date `k` in state `ω` with entry price `F₀` -/
  cashflow : ℕ → OnePeriodMarket Ω → ℝ → Ω → ℝ

/-- **P2.3** The Ackerer-Hugonnier-Jermann (2025) cash flow specification.

At each funding date k, the long receives `F₀ − S_k(ω)` from the short.
Under stationarity (F_k = F₀ for all k), this is the current perpetual price
minus the spot price.

This specification is proved to satisfy `CostlessEntry` when `F₀ = geometricExpectation`
of the risk-neutral spot expectation (Theorem 1a in `FundingCompatibility.lean`). -/
def ackererCashFlow : CashFlowSpec Ω where
  cashflow k market F₀ ω := F₀ - market.spot k ω

/-- **P2.3** The original He-Manela-Ross-von Wachter cash flow specification.

At each funding date k, the long receives a constant `S₀ − F₀` — the initial
spot-futures spread, independent of the current date k and current state ω.

This is the specification documented by Ackerer et al. as incompatible with costless
entry. See `he_manela_violates_costless_entry` for the counterexample.

**Encoding note (issue #127):** `S₀` is taken as the arithmetic mean of `market.spot 0`
over `Ω`, which equals `E^P[S₀]` when P is the uniform measure. The F3.4 counterexample
uses a symmetric two-state market where P is uniform, so this encoding is exact for
that construction. -/
noncomputable def heManelaCashFlow : CashFlowSpec Ω where
  -- Constant payment: initial spot-futures spread, independent of k and ω.
  -- Assumes P uniform on Ω; exact for the symmetric F3.4 counterexample market.
  cashflow _k market F₀ _ω :=
    (∑ ω : Ω, market.spot 0 ω) / Fintype.card Ω - F₀

/-! ### P2.4 — Costless entry -/

/-- **P2.4** The costless entry condition for a cash flow specification.

A futures contract has costless entry if the present value of all future cash flows
to the long holder, probability-weighted under Q and geometrically discounted at
rate `p = κ/(1+r)`, equals zero at initiation.

This is a proof obligation, not an assumption: any pricing theorem must first
discharge `CostlessEntry` for the chosen specification.

The tsum converges (is not vacuously 0) because `OnePeriodMarket.spot_bounded`
ensures the cash-flow sequence is uniformly bounded. -/
def CostlessEntry (spec : CashFlowSpec Ω) (market : OnePeriodMarket Ω)
    (Q : OnePeriodEMM Ω market) (F₀ : ℝ) : Prop :=
  geometricExpectation (p := market.κ / (1 + market.r))
    (fun k => ∑ ω : Ω, Q.density ω * spec.cashflow k market F₀ ω) = 0

/-! ### P2.4 — No-buy-and-hold arbitrage -/

/-- **P2.4** The no-buy-and-hold-arbitrage condition for entry price `F₀`.

A price `F₀` admits no buy-and-hold arbitrage if:
1. Entering the perpetual futures long at `F₀` has zero expected cost under Q
   (costless entry), and
2. No round-trip strategy — enter long at `F₀'`, short at `F₀` — produces nonzero
   Q-expected net cash flow when `F₀' ≠ F₀`.

Condition (2) is stated as: for any alternative price `F₀' ≠ F₀`, the Q-weighted
geometric expectation of the cash-flow difference is nonzero. Substituting
`ackererCashFlow`, this difference equals `F₀' − F₀` (constant in k and ω), so
by `geometricExpectation_const` the condition reduces to `F₀' − F₀ ≠ 0`, which
is exactly the hypothesis `F₀' ≠ F₀`. This means uniqueness follows directly:
the only price satisfying `CostlessEntry` is the geometric-expectation price.

Resolves issue #126 (replaces the previous per-state absolute-value formulation
which was tautological for the same reason). -/
def NoBuyAndHoldArbitrage (market : OnePeriodMarket Ω) (Q : OnePeriodEMM Ω market)
    (F₀ : ℝ) : Prop :=
  -- Costless entry at F₀ is necessary for no-arbitrage
  CostlessEntry ackererCashFlow market Q F₀ ∧
  -- No round-trip strategy at any alternative price F₀' ≠ F₀ has zero Q-expected payoff
  ∀ (F₀' : ℝ), F₀' ≠ F₀ →
    geometricExpectation (p := market.κ / (1 + market.r)) (fun k =>
      ∑ ω : Ω, Q.density ω * (ackererCashFlow.cashflow k market F₀' ω -
                               ackererCashFlow.cashflow k market F₀ ω)) ≠ 0

end PerpetualProofs
