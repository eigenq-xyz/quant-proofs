import OptionsProofs.PutCallParity

/-!
# Perfect path-by-path replication in the CRR binomial model (CLAIM 1)

This module proves the **discrete delta-hedging replication theorem** of the
Cox-Ross-Rubinstein model: the self-financing portfolio that, at every node, holds the
one-step replicating delta of shares plus a money-market account reproduces the option
payoff `g(S_N)` **exactly on every path** of the `{u, d}^N` tree. This is the financial
content behind variance-risk-premium harvesting: a delta-hedged short option position has
zero terminal P&L *in the model*, so any realized P&L is the gap between the realized and
priced variance.

The proof uses only finite induction and ring arithmetic, no continuous stochastic calculus.
It reuses the CRR tree and one-step price recursion (`crrPrice`, `crrPrice_succ`) and the
risk-neutral probability and its drift identity (`riskNeutralProb`, `riskNeutralProb_drift`)
from `OptionsProofs`.

## Model recap

Because the European payoff `g(S_N)` depends only on the terminal **price** and the CRR tree
is recombining, the backward-induction value at a node depends only on `(current price, steps
remaining)`. We therefore define everything price-first, then specialise to a path.

- `nodeVal g u d r k S` — the CRR value at a node with price `S` and `k` steps remaining:
  `nodeVal 0 S = g S` and `nodeVal (k+1) S = (q · nodeVal k (S·u) + (1-q) · nodeVal k (S·d)) / (1+r)`,
  with `q = riskNeutralProb u d r`.
- `nodeDelta g u d r k S = (nodeVal k (S·u) - nodeVal k (S·d)) / (S·(u-d))` — the one-step
  replicating share count at a node with `k+1` steps remaining.
- Along a path `ω`, `pathVal n ω = nodeVal (T-n) (crrPrice n ω)` and likewise `pathDelta`.
- The money-market holding `bondHold n ω = pathVal n ω - pathDelta n ω · crrPrice n ω`.
- The self-financing portfolio `replPortfolio` starts at `pathVal 0` and rolls forward by
  `Π_{n+1} = Δ_n · S_{n+1} + B_n · (1+r)`.

## Contents

- `nodeVal`, `nodeDelta`, `nodeBond` (price-level definitions).
- `nodeVal_succ` — the backward-induction recursion unfolded once.
- `node_one_step_replication` — the key algebraic identity: at a node, holding `Δ` shares and
  `B` bond reproduces the child value on **both** branches. Pure ring arithmetic + drift.
- `pathVal`, `pathDelta`, `bondHold`, `replPortfolio` (path-level definitions).
- `replPortfolio_succ_eq_pathVal` — the self-financing roll-forward lands on the next value.
- `replicates` — **CLAIM 1**: `replPortfolio T … T ω = g (terminalSpot ω)` on every path.
-/

namespace VrpProofs

open OptionsProofs

variable {T : ℕ}

/-! ### Price-level backward-induction value and replicating delta -/

/-- The CRR node value with `k` steps remaining and current price `S`, for payoff `g`.
Backward induction: at expiry (`k = 0`) the value is the payoff `g S`; with one more step it
is the discounted risk-neutral average of the two child values. -/
noncomputable def nodeVal (g : ℝ → ℝ) (u d r : ℝ) : ℕ → ℝ → ℝ
  | 0,     S => g S
  | k + 1, S =>
      (riskNeutralProb u d r * nodeVal g u d r k (S * u)
        + (1 - riskNeutralProb u d r) * nodeVal g u d r k (S * d)) / (1 + r)

/-- The one-step recursion for `nodeVal`, stated as an equation (the `k+1` defining clause). -/
@[simp] lemma nodeVal_succ (g : ℝ → ℝ) (u d r : ℝ) (k : ℕ) (S : ℝ) :
    nodeVal g u d r (k + 1) S =
      (riskNeutralProb u d r * nodeVal g u d r k (S * u)
        + (1 - riskNeutralProb u d r) * nodeVal g u d r k (S * d)) / (1 + r) := rfl

/-- The one-step replicating share count at a node with price `S` and `k+1` steps remaining:
`Δ = (V(S·u) - V(S·d)) / (S·(u - d))`, the discrete hedge ratio. -/
noncomputable def nodeDelta (g : ℝ → ℝ) (u d r : ℝ) (k : ℕ) (S : ℝ) : ℝ :=
  (nodeVal g u d r k (S * u) - nodeVal g u d r k (S * d)) / (S * (u - d))

/-- The money-market holding that makes the node value self-financing: `B = V - Δ·S`. -/
noncomputable def nodeBond (g : ℝ → ℝ) (u d r : ℝ) (k : ℕ) (S : ℝ) : ℝ :=
  nodeVal g u d r (k + 1) S - nodeDelta g u d r k S * S

/-! ### The key one-step replication identity -/

/-- **One-step replication (the algebraic crux).** At a node with price `S > 0` and `k+1`
steps remaining, holding `Δ = nodeDelta … k S` shares of stock and `B = nodeBond … k S` in the
money market reproduces the child value `nodeVal … k (S·f)` exactly, for **either** realized
move factor `f ∈ {u, d}`:

`Δ · (S·f) + B · (1 + r) = nodeVal … k (S·f)`.

This is pure ring arithmetic plus the drift identity `q·u + (1-q)·d = 1 + r`. It is the heart
of perfect replication: the portfolio chosen at the parent matches the value at whichever child
is realized. -/
lemma node_one_step_replication (g : ℝ → ℝ) {u d r : ℝ} (hdu : d < u) (hr : -1 < r)
    {S : ℝ} (hS : S ≠ 0) (k : ℕ) {f : ℝ} (hf : f = u ∨ f = d) :
    nodeDelta g u d r k S * (S * f) + nodeBond g u d r k S * (1 + r) =
      nodeVal g u d r k (S * f) := by
  have hud : u - d ≠ 0 := by intro h; apply absurd (sub_eq_zero.mp h); linarith
  have hr0 : (1 + r) ≠ 0 := by intro h; linarith
  -- Abbreviate the two child values.
  set Vu := nodeVal g u d r k (S * u) with hVu
  set Vd := nodeVal g u d r k (S * d) with hVd
  -- `S·(u-d) ≠ 0`.
  have hSud : S * (u - d) ≠ 0 := mul_ne_zero hS hud
  -- Unfold the definitions and expand `q = (1 + r - d)/(u - d)` so the goal becomes a pure
  -- rational identity in `u, d, r, S, Vu, Vd`. The drift `q·u + (1-q)·d = 1+r` then holds
  -- definitionally, so `field_simp; ring` closes each branch with no auxiliary lemma.
  simp only [nodeBond, nodeDelta, nodeVal_succ, ← hVu, ← hVd, riskNeutralProb]
  rcases hf with hfu | hfd
  · -- Up branch: `nodeVal k (S·f) = Vu`.
    rw [hfu, ← hVu]
    field_simp
    ring
  · -- Down branch: `nodeVal k (S·f) = Vd`.
    rw [hfd, ← hVd]
    field_simp
    ring

/-! ### Path-level portfolio along the tree -/

/-- The backward-induction value along a path: at time `n` the node has `T - n` steps
remaining and price `crrPrice T S₀ u d n ω`. -/
noncomputable def pathVal (g : ℝ → ℝ) (T : ℕ) (S₀ u d r : ℝ)
    (n : Fin (T + 1)) (ω : CRRState T) : ℝ :=
  nodeVal g u d r (T - (n : ℕ)) (crrPrice T S₀ u d n ω)

/-- The replicating delta held over the step from time `n` to `n+1`, along the path `ω`. -/
noncomputable def pathDelta (g : ℝ → ℝ) (T : ℕ) (S₀ u d r : ℝ)
    (n : Fin T) (ω : CRRState T) : ℝ :=
  nodeDelta g u d r (T - (n.val + 1)) (crrPrice T S₀ u d n.castSucc ω)

/-- The money-market holding over the step from time `n` to `n+1`, along the path `ω`. -/
noncomputable def bondHold (g : ℝ → ℝ) (T : ℕ) (S₀ u d r : ℝ)
    (n : Fin T) (ω : CRRState T) : ℝ :=
  nodeBond g u d r (T - (n.val + 1)) (crrPrice T S₀ u d n.castSucc ω)

/-- The self-financing replicating portfolio value at time `n` along path `ω`.
`Π₀ = pathVal 0` and `Π_{n+1} = Δ_n · S_{n+1} + B_n · (1 + r)`, where `Δ_n` shares and `B_n`
bond are chosen at time `n` and then carried (self-financingly) to time `n+1`. -/
noncomputable def replPortfolio (g : ℝ → ℝ) (T : ℕ) (S₀ u d r : ℝ) (ω : CRRState T) :
    ℕ → ℝ
  | 0 => pathVal g T S₀ u d r ⟨0, Nat.zero_lt_succ T⟩ ω
  | n + 1 =>
      if h : n < T then
        pathDelta g T S₀ u d r ⟨n, h⟩ ω * crrPrice T S₀ u d (⟨n, h⟩ : Fin T).succ ω
          + bondHold g T S₀ u d r ⟨n, h⟩ ω * (1 + r)
      else
        replPortfolio g T S₀ u d r ω n

/-! ### The replication theorem -/

/-- A node price is nonzero whenever `S₀, u, d` are all positive: it is a product of positive
factors. Needed to apply `node_one_step_replication`. -/
lemma crrPrice_ne_zero {S₀ u d : ℝ} (hS₀ : 0 < S₀) (hu : 0 < u) (hd : 0 < d)
    (n : Fin (T + 1)) (ω : CRRState T) : crrPrice T S₀ u d n ω ≠ 0 := by
  rw [crrPrice]
  positivity

/-- **One self-financing step lands on the next value.** With the node delta/bond chosen at
time `n`, the rolled-forward portfolio at time `n+1` equals the backward-induction value
`pathVal (n+1)`. This is `node_one_step_replication` specialised to the realized branch, using
the one-step price recursion `crrPrice_succ` and the bookkeeping `T - n = (T - (n+1)) + 1`. -/
lemma replStep_eq_pathVal (g : ℝ → ℝ) {S₀ u d r : ℝ}
    (hS₀ : 0 < S₀) (hd : 0 < d) (hdu : d < u) (hr : -1 < r)
    (n : Fin T) (ω : CRRState T) :
    pathDelta g T S₀ u d r n ω * crrPrice T S₀ u d n.succ ω
        + bondHold g T S₀ u d r n ω * (1 + r) =
      pathVal g T S₀ u d r n.succ ω := by
  have hu : 0 < u := lt_trans hd hdu
  set S := crrPrice T S₀ u d n.castSucc ω with hS
  have hSne : S ≠ 0 := crrPrice_ne_zero hS₀ hu hd n.castSucc ω
  set k := T - (n.val + 1) with hk
  -- The realized move factor.
  set f : ℝ := (if ω ⟨n.val, n.isLt⟩ = true then u else d) with hf
  have hfud : f = u ∨ f = d := by
    rw [hf]; by_cases hb : ω ⟨n.val, n.isLt⟩ = true
    · exact Or.inl (if_pos hb)
    · exact Or.inr (if_neg hb)
  -- Next price = S · f.
  have hnext : crrPrice T S₀ u d n.succ ω = S * f := by
    rw [hS, hf]; exact crrPrice_succ S₀ u d n ω
  -- Steps-remaining bookkeeping: `T - n.val = k + 1`.
  have hsteps : T - (n.succ : ℕ) = k := by simp only [Fin.val_succ, hk]
  -- Apply the one-step replication identity at the node `(k, S)`.
  rw [pathDelta, bondHold, pathVal, hnext, ← hS, ← hk, hsteps]
  exact node_one_step_replication g hdu hr hSne k hfud

/-- **The portfolio value equals the backward-induction value at every time** along every path
(by finite induction on `n`). The base case is the definition `Π₀ = pathVal 0`; the inductive
step is `replStep_eq_pathVal`. -/
lemma replPortfolio_eq_pathVal (g : ℝ → ℝ) {S₀ u d r : ℝ}
    (hS₀ : 0 < S₀) (hd : 0 < d) (hdu : d < u) (hr : -1 < r)
    (ω : CRRState T) :
    ∀ n : ℕ, (hn : n < T + 1) →
      replPortfolio g T S₀ u d r ω n = pathVal g T S₀ u d r ⟨n, hn⟩ ω := by
  intro n
  induction n with
  | zero =>
    intro hn
    rfl
  | succ m ih =>
    intro hn
    have hmT : m < T := by omega
    have hmsucc : m < T + 1 := by omega
    -- Unfold the portfolio recursion at `m + 1`.
    rw [replPortfolio, dif_pos hmT]
    -- The index `⟨m, hmT⟩.succ : Fin (T+1)` equals `⟨m+1, hn⟩`.
    have hidx : (⟨m, hmT⟩ : Fin T).succ = (⟨m + 1, hn⟩ : Fin (T + 1)) := Fin.ext rfl
    -- The step lemma at node `m`.
    have hstep := replStep_eq_pathVal g hS₀ hd hdu hr ⟨m, hmT⟩ ω
    rw [hidx] at hstep
    rw [hidx, hstep]

/-- **CLAIM 1 — perfect path-by-path replication.** In the CRR binomial market with
`0 < d < u`, `S₀ > 0`, `r > -1`, the self-financing portfolio that starts with capital
`pathVal 0 = V₀(S₀)` and, at each node, holds `pathDelta` shares of the stock plus `bondHold`
in the money market, reproduces the option payoff exactly on **every** path of the tree:

`replPortfolio T S₀ u d r ω T = g (terminalSpot T S₀ u d ω)`   for all `ω : CRRState T`.

This is the discrete Cox-Ross-Rubinstein delta-hedging result: the option is perfectly hedged
along every realization. The proof is the time-`T` instance of `replPortfolio_eq_pathVal`
(`Π_N = V_N`), where the terminal value `V_N = nodeVal 0 (S_T) = g(S_T)` by definition of
`nodeVal`. Source: Cox-Ross-Rubinstein 1979; Nielsen-Jonsson-Poulsen 2012. -/
theorem replicates (g : ℝ → ℝ) (T : ℕ) {S₀ u d r : ℝ}
    (hS₀ : 0 < S₀) (hd : 0 < d) (hdu : d < u) (hr : -1 < r)
    (ω : CRRState T) :
    replPortfolio g T S₀ u d r ω T = g (terminalSpot T S₀ u d ω) := by
  -- Π_T = pathVal T (by the equality-at-every-time lemma).
  rw [replPortfolio_eq_pathVal g hS₀ hd hdu hr ω T (Nat.lt_succ_self T)]
  -- pathVal T = nodeVal (T - T) (crrPrice (last)) = nodeVal 0 (S_T) = g(S_T).
  rw [pathVal]
  simp only [Nat.sub_self]
  -- `crrPrice` at the index `⟨T, _⟩` is `terminalSpot` (which is `crrPrice (Fin.last T)`).
  rfl

end VrpProofs
