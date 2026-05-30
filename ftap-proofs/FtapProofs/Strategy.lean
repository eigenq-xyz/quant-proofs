import FtapProofs.Market
import Mathlib.Algebra.BigOperators.Group.Finset.Basic
import Mathlib.Algebra.BigOperators.Fin

/-!
# Trading Strategies

A trading strategy is a predictable process specifying portfolio holdings over time.

Formally, `θ = (θ₁, …, θₙ)` where `θ i t ω` gives the number of units of risky asset `i`
held over the period `[t-1, t)`. Predictability means `θ i t` is `ℱ_{t-1}`-measurable:
the decision of how much to hold in period `[t-1, t)` is made using only information
available strictly before time `t`.

A strategy is **self-financing** if no external cash is injected or withdrawn between
rebalancing times: the portfolio value at old prices does not change when rebalancing.

## Contents

- **S2.1** `TradingStrategy` — predictable holdings process
- **S2.2** `valueProcess` — undiscounted portfolio value `V t θ ω`
- **S2.3** `discountedValueProcess` — discounted portfolio value `Ṽ t θ ω`
- **S2.4** `selfFinancing` — no-cash-injection condition
- **S2.5** `gainsProcess` — cumulative discounted gains `G t θ ω`
- **S2.6** `selfFinancing_iff_value_eq_init_plus_gains` — the equivalence
           `selfFinancing θ ↔ ∀ t ω, Ṽ t θ ω = Ṽ 0 θ ω + G t θ ω`
-/

namespace FtapProofs

open BigOperators

variable {Ω : Type*} [MeasurableSpace Ω] [Fintype Ω] [MeasurableSingletonClass Ω]

/-! ### S2.1 — Trading strategy structure -/

/-- The previous time in the filtration: `prevTime t = t - 1` for `t > 0`, and `0` for `t = 0`.

Used to state the predictability condition: `holdings i t` is `ℱ_{prevTime t}`-measurable,
meaning the rebalancing decision for period `[t-1, t)` is made before observing `S t`.

`protected` (not `private`) so that downstream modules can refer to `FtapProofs.prevTime`
by name when writing proofs about `TradingStrategy.predictable`. -/
protected def prevTime {T : ℕ} (t : Fin (T + 1)) : Fin (T + 1) :=
  ⟨t.val.pred, Nat.lt_of_le_of_lt (Nat.pred_le t.val) t.isLt⟩

@[simp]
protected lemma prevTime_zero {T : ℕ} : FtapProofs.prevTime (⟨0, Nat.zero_lt_succ T⟩ : Fin (T + 1)) =
    ⟨0, Nat.zero_lt_succ T⟩ := Fin.ext rfl

@[simp]
protected lemma prevTime_succ {T : ℕ} (t : Fin T) : FtapProofs.prevTime t.succ = t.castSucc :=
  Fin.ext (by simp [FtapProofs.prevTime, Fin.val_succ])

/-- **S2.1** A trading strategy in the market `m`.

Holdings `θ.holdings i t ω` give the number of units of risky asset `i` held over
period `[t-1, t)`. The strategy is **predictable**: `θ i t` is `ℱ_{t-1}`-measurable,
so no information from time `t` onwards is used when deciding the holdings for period
`[t-1, t)`.

At time `t = 0`, the strategy is `ℱ_0`-measurable (the initial holding is determined
by the prior sigma-algebra). -/
structure TradingStrategy (m : FinancialMarket Ω) where
  /-- Holdings process: `holdings i t ω` is the number of units of asset `i` held over `[t-1, t)` -/
  holdings : Fin m.n → Fin (m.T + 1) → Ω → ℝ
  /-- **Predictability**: `holdings i t` is `ℱ_{t-1}`-measurable — decided before seeing `S t` -/
  predictable : ∀ i t, @Measurable Ω ℝ (m.𝒻 (FtapProofs.prevTime t)) _ (holdings i t)
  /-- Bond holdings process: `bondHolding t ω` is the number of units of the risk-free bond held
      over period `[t-1, t)`. The bond has constant discounted price 1 at all times, so bond
      holdings do not contribute to the gains process but do appear in the value process and the
      self-financing condition. -/
  bondHolding : Fin (m.T + 1) → Ω → ℝ
  /-- **Bond predictability**: `bondHolding t` is `ℱ_{t-1}`-measurable -/
  bondPredictable : ∀ t, @Measurable Ω ℝ (m.𝒻 (FtapProofs.prevTime t)) _ (bondHolding t)

/-! ### S2.2 — Value process -/

/-- **S2.2** Portfolio value process (undiscounted):
`V t θ ω = ∑ᵢ θᵢ t ω · Sᵢ t ω + bondHolding t ω · B t`.

The total market value of the portfolio at time `t` in state `ω`, including the bond
position valued at the (undiscounted) numeraire price `B t`. This stays parallel to
`discountedValueProcess` via `V t θ ω = B t · Ṽ t θ ω` (the bond's discounted price is
`B t / B t = 1`). See `discountedValueProcess` for the version used in the FTAP proof. -/
noncomputable def valueProcess (m : FinancialMarket Ω) (θ : TradingStrategy m)
    (t : Fin (m.T + 1)) (ω : Ω) : ℝ :=
  ∑ i : Fin m.n, θ.holdings i t ω * m.S i t ω + θ.bondHolding t ω * m.B t

/-! ### S2.3 — Discounted value process -/

/-- **S2.3** Discounted portfolio value process: `Ṽ t θ ω = ∑ᵢ θᵢ t ω · S̃ᵢ t ω`.

Portfolio value denominated in units of the numeraire (risk-free bond). Equivalently,
`Ṽ t θ ω = V t θ ω / B t`. This is the key process for the FTAP proof: a strategy
is arbitrage-free iff its discounted value is a martingale under an EMM. -/
noncomputable def discountedValueProcess (m : FinancialMarket Ω) (θ : TradingStrategy m)
    (t : Fin (m.T + 1)) (ω : Ω) : ℝ :=
  ∑ i : Fin m.n, θ.holdings i t ω * discountedPrice m i t ω + θ.bondHolding t ω

/-! ### S2.4 — Self-financing condition -/

/-- **S2.4** Self-financing condition (stated in discounted units).

A strategy is self-financing if no external cash is injected or withdrawn between
rebalancing times. At each rebalancing time `t`, the portfolio is rebalanced from
holdings `θ t` to `θ (t+1)`. The self-financing condition says this rebalancing
has zero cost at the prevailing (discounted) prices `S̃ t`:

    ∑ᵢ θᵢ (t+1) ω · S̃ᵢ t ω = ∑ᵢ θᵢ t ω · S̃ᵢ t ω   (for all `t`, `ω`)

**Index convention.** Following Harrison-Pliska (1981) §3, `holdings i t ω` is the number
of units of asset `i` held over period `[t-1, t)`. Thus `valueProcess m θ t ω` is the
portfolio value *at the end of period t*, using end-of-period prices `S i t`. Rebalancing
from `holdings t` to `holdings (t+1)` happens at time `t`, using prices `S t`, before
the next period's price `S (t+1)` is observed.

In discounted units (equivalent to the undiscounted condition since `B t > 0`).
See `selfFinancing_iff_value_eq_init_plus_gains` for an equivalent characterization
in terms of the value and gains processes. -/
def selfFinancing (m : FinancialMarket Ω) (θ : TradingStrategy m) : Prop :=
  ∀ (t : Fin m.T) (ω : Ω),
    ∑ i : Fin m.n, θ.holdings i t.succ ω * discountedPrice m i t.castSucc ω +
    θ.bondHolding t.succ ω =
    ∑ i : Fin m.n, θ.holdings i t.castSucc ω * discountedPrice m i t.castSucc ω +
    θ.bondHolding t.castSucc ω

/-! ### S2.5 — Discounted gains process -/

/-- **S2.5** Discounted gains process:
`G t θ ω = ∑_{s=1}^t ∑ᵢ θᵢ s ω · (S̃ᵢ s ω - S̃ᵢ (s-1) ω)`.

Cumulative trading gains in discounted units up to time `t`. This is the integral
of the holdings process against the discounted price changes: gains accumulate
by holding `θᵢ s` units of asset `i` over period `[s-1, s)` and gaining from
the price change `S̃ᵢ s - S̃ᵢ (s-1)`.

For `t = 0`, the gains process is zero (no periods have elapsed). -/
noncomputable def gainsProcess (m : FinancialMarket Ω) (θ : TradingStrategy m)
    (t : Fin (m.T + 1)) (ω : Ω) : ℝ :=
  -- The `dite` guards the `Fin` indices to stay in bounds. The `else 0` branch is
  -- unreachable: for `s ∈ range t.val`, we have `s < t.val ≤ m.T`, so `s < m.T` always holds.
  ∑ s ∈ Finset.range t.val,
    if h : s < m.T then
      ∑ i : Fin m.n, θ.holdings i ⟨s + 1, Nat.succ_lt_succ h⟩ ω *
        (discountedPrice m i ⟨s + 1, Nat.succ_lt_succ h⟩ ω -
         discountedPrice m i ⟨s, Nat.lt_of_succ_lt (Nat.succ_lt_succ h)⟩ ω)
    else 0

@[simp]
private lemma gainsProcess_zero (m : FinancialMarket Ω) (θ : TradingStrategy m) (ω : Ω) :
    gainsProcess m θ ⟨0, Nat.zero_lt_succ _⟩ ω = 0 := by
  simp [gainsProcess]

-- Helper: the gains process at `t.succ` decomposes into gains at `t.castSucc` plus one step.
private lemma gainsProcess_succ_eq (m : FinancialMarket Ω) (θ : TradingStrategy m)
    (t : Fin m.T) (ω : Ω) :
    gainsProcess m θ t.succ ω = gainsProcess m θ t.castSucc ω +
    ∑ i : Fin m.n, θ.holdings i t.succ ω *
      (discountedPrice m i t.succ ω - discountedPrice m i t.castSucc ω) := by
  simp only [gainsProcess, Fin.val_succ, Fin.val_castSucc, Finset.sum_range_succ]
  congr 1
  rw [dif_pos t.isLt]
  have h1 : (⟨t.val + 1, Nat.succ_lt_succ t.isLt⟩ : Fin (m.T + 1)) = t.succ := Fin.ext rfl
  have h2 : (⟨t.val, Nat.lt_of_succ_lt (Nat.succ_lt_succ t.isLt)⟩ : Fin (m.T + 1)) = t.castSucc :=
    Fin.ext rfl
  rw [h1, h2]

/-! ### S2.6 — Self-financing characterization -/

/-- **S2.6** A strategy is self-financing if and only if its discounted value process
equals the initial discounted value plus accumulated discounted gains:

    `selfFinancing θ ↔ ∀ t ω, Ṽ t θ ω = Ṽ 0 θ ω + G t θ ω`

**Significance.** This identity is the fundamental bookkeeping equation for
self-financing strategies. It says that all changes in portfolio value are
explained by price movements alone — no cash enters or leaves. In particular,
it shows that the discounted value process of any self-financing strategy
is entirely determined by its initial value and the accumulated gains.

This characterization is used in the FTAP proof (Phase 3) to show that
the discounted value process of a self-financing strategy is a martingale
under any equivalent martingale measure.

**Proof sketch.**
The forward direction (→) follows by induction on `t`: at each step, the self-financing
condition equates the rebalancing cost to zero, which translates to the gains increment
matching the change in discounted value. The backward direction (←) extracts the
self-financing condition by comparing consecutive values of the equation. -/
theorem selfFinancing_iff_value_eq_init_plus_gains (m : FinancialMarket Ω)
    (θ : TradingStrategy m) :
    selfFinancing m θ ↔
    ∀ (t : Fin (m.T + 1)) (ω : Ω),
      discountedValueProcess m θ t ω =
      discountedValueProcess m θ ⟨0, Nat.zero_lt_succ _⟩ ω + gainsProcess m θ t ω := by
  constructor
  · -- (→) Self-financing implies Ṽ t = Ṽ 0 + G t, by induction on t
    intro hsf t
    induction t using Fin.inductionOn with
    | zero =>
      intro ω
      simp [gainsProcess]
    | succ t ih =>
      intro ω
      -- IH: Ṽ t.castSucc ω = Ṽ 0 ω + G t.castSucc ω
      have hih := ih ω
      -- Self-financing at t: ∑ i, θ t.succ * S̃ t.castSucc = ∑ i, θ t.castSucc * S̃ t.castSucc
      have hself := hsf t ω
      -- Expand the gains process at t.succ
      rw [gainsProcess_succ_eq]
      -- Expand sum of differences:
      -- ∑ i, θ t.succ * (S̃ t.succ - S̃ t.castSucc) = ∑ i, θ t.succ * S̃ t.succ - ∑ i, θ t.succ * S̃ t.castSucc
      have expand : ∑ i : Fin m.n, θ.holdings i t.succ ω *
          (discountedPrice m i t.succ ω - discountedPrice m i t.castSucc ω) =
          (∑ i : Fin m.n, θ.holdings i t.succ ω * discountedPrice m i t.succ ω) -
          (∑ i : Fin m.n, θ.holdings i t.succ ω * discountedPrice m i t.castSucc ω) := by
        simp [mul_sub, ← Finset.sum_sub_distrib]
      simp only [discountedValueProcess] at hih ⊢
      -- hih: ∑ θ_t * D_t + bondHolding_t = Ṽ 0 + G_t
      -- hself: ∑ θ_{t+1} * D_t + bondHolding_{t+1} = ∑ θ_t * D_t + bondHolding_t
      -- expand: ∑ θ_{t+1} * (D_{t+1} - D_t) = ∑ θ_{t+1} * D_{t+1} - ∑ θ_{t+1} * D_t
      -- Goal: ∑ θ_{t+1} * D_{t+1} + bondHolding_{t+1} = Ṽ 0 + G_t + ∑ θ_{t+1} * (D_{t+1} - D_t)
      linarith
  · -- (←) Ṽ t = Ṽ 0 + G t for all t implies self-financing
    intro hval t ω
    -- Apply the equation at t.succ and t.castSucc
    have hsucc := hval t.succ ω
    have hcast := hval t.castSucc ω
    -- Expand the gains process at t.succ
    rw [gainsProcess_succ_eq] at hsucc
    -- Expand sum of differences at t.succ
    have expand : ∑ i : Fin m.n, θ.holdings i t.succ ω *
        (discountedPrice m i t.succ ω - discountedPrice m i t.castSucc ω) =
        (∑ i : Fin m.n, θ.holdings i t.succ ω * discountedPrice m i t.succ ω) -
        (∑ i : Fin m.n, θ.holdings i t.succ ω * discountedPrice m i t.castSucc ω) := by
      simp [mul_sub, ← Finset.sum_sub_distrib]
    simp only [discountedValueProcess] at hsucc hcast
    -- hsucc: ∑ θ_{t+1} * D_{t+1} + bondHolding_{t+1} = Ṽ 0 + G_t + ∑ θ_{t+1} * (D_{t+1} - D_t)
    -- hcast: ∑ θ_t * D_t + bondHolding_t = Ṽ 0 + G_t
    -- Goal (SF): ∑ θ_{t+1} * D_t + bondHolding_{t+1} = ∑ θ_t * D_t + bondHolding_t
    linarith

end FtapProofs
