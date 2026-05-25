# FTAP Proof Roadmap

## Goal

Prove the Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981) in Lean 4,
zero `sorry`, targeting a mathlib PR.

**The theorem in one line:**

> A finite-state discrete-time market is arbitrage-free if and only if there exists
> an equivalent martingale measure.

In Lean:
```lean
theorem ftap : NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q
```

This is the foundational result underlying all of derivative pricing theory.
The `options-proofs` module (put-call parity via CRR) will import and cite it.

---

## Why this proof structure

The proof has two halves with very different characters:

- **Easy direction (⇐)**: EMM → NA. A martingale with non-negative terminal value
  and zero initial value must be identically zero. Straightforward from the definition
  of conditional expectation and martingales. ~20 lines of Lean.

- **Hard direction (⇒)**: NA → EMM exists. Requires a separating hyperplane argument
  (Farkas' lemma in finite dimensions). We show the attainable zero-cost payoff set
  is a linear subspace that misses the positive orthant, then construct the state-price
  vector from the separating functional and normalize it to a probability measure.
  This is the non-trivial part and the main mathematical contribution.

---

## Phase 1 — Market Model (`FtapProofs/Market.lean`)

The objects the theorem talks about.

- [ ] **M1.1** Define `FinancialMarket`: finite `Ω`, time horizon `T`, filtration
      `(ℱ_t)_{t=0..T}`, risky asset prices `S : Fin n → Fin (T+1) → Ω → ℝ`,
      numeraire `B : Fin (T+1) → ℝ`
- [ ] **M1.2** Measurability typeclass: `S i t` is `ℱ_t`-measurable for all `i, t`
- [ ] **M1.3** Define discounted prices `S̃ i t ω := S i t ω / B t`
- [ ] **M1.4** Lemma: `B t > 0` for all `t` (positivity of numeraire)
- [ ] **M1.5** Lemma: `S̃ i t` is `ℱ_t`-measurable (inherited from `S`)

**Mathlib touchpoints:** `MeasureTheory.Filtration`, `MeasureTheory.Measure.MeasureSpace`,
`MeasurableSpace`, `Finset`

---

## Phase 2 — Trading Strategies (`FtapProofs/Strategy.lean`)

The actions an investor can take.

- [ ] **S2.1** Define `TradingStrategy`: `θ : Fin n → Fin (T+1) → Ω → ℝ`
      where `θ i t` is `ℱ_{t-1}`-measurable (predictable)
- [ ] **S2.2** Define value process `V t θ ω := ∑ i, θ i t ω * S i t ω`
- [ ] **S2.3** Define discounted value process `Ṽ t θ := V t θ / B t`
- [ ] **S2.4** Define `selfFinancing θ`: no cash injections between rebalances
      (`V t θ = V (t-1) θ + ∑ i, θ i t * (S i t - S i (t-1))`)
- [ ] **S2.5** Define discounted gains process
      `G t θ := ∑_{s=1}^{t} ∑ i, θ i s * (S̃ i s - S̃ i (s-1))`
- [ ] **S2.6** Lemma: `selfFinancing θ ↔ Ṽ t θ = Ṽ 0 θ + G t θ` for all `t`
      (value equals initial investment plus accumulated gains, in discounted units)

**Mathlib touchpoints:** `Finset.sum`, `MeasureTheory.Filtration.predictable`

---

## Phase 3 — No-Arbitrage (`FtapProofs/Arbitrage.lean`)

The key condition on the market.

- [ ] **A3.1** Define `ArbitrageOpportunity θ`:
      `selfFinancing θ ∧ V 0 θ = 0 ∧ V T θ ≥ 0 a.s. ∧ P {ω | V T θ ω > 0} > 0`
- [ ] **A3.2** Define `NoArbitrage m`: `¬ ∃ θ, ArbitrageOpportunity m θ`
- [ ] **A3.3** Define attainable payoff set
      `K m := {G T θ | θ self-financing, V 0 θ = 0}`
- [ ] **A3.4** Lemma: `K m` is a linear subspace of `Ω → ℝ`
- [ ] **A3.5** Lemma: `NoArbitrage m ↔ K m ∩ {f | f ≥ 0 a.s., f ≠ 0 a.s.} = ∅`
      (NA reformulated in terms of attainable payoffs — the form Farkas uses)

---

## Phase 4 — Equivalent Martingale Measure (`FtapProofs/MartingaleMeasure.lean`)

The dual object that characterizes arbitrage-free markets.

- [ ] **Q4.1** Define `EquivalentMeasure P Q`: `∀ A, P A = 0 ↔ Q A = 0`
- [ ] **Q4.2** Define `IsMartingaleMeasure m Q`:
      `∀ i t, E^Q [S̃ i (t+1) | ℱ_t] = S̃ i t`
- [ ] **Q4.3** Define `EquivalentMartingaleMeasure m Q`:
      `EquivalentMeasure P Q ∧ IsMartingaleMeasure m Q`
- [ ] **Q4.4** Lemma: under any EMM `Q`, `Ṽ t θ` is a `Q`-martingale for
      any self-financing `θ` — the key property linking the two halves
- [ ] **Q4.5** Lemma (risk-neutral pricing): `V 0 θ = E^Q [V T θ / B T]`
      for self-financing `θ` under any EMM `Q`

**Mathlib touchpoints:** `MeasureTheory.Martingale`, `MeasureTheory.ConditionalExpectation`

---

## Phase 5 — The FTAP (`FtapProofs/Theorem.lean`)

Assemble the proof.

- [ ] **T5.1** Theorem `emm_implies_no_arbitrage`:
      `EquivalentMartingaleMeasure m Q → NoArbitrage m`
      (Easy direction: use Q4.4 + Q4.5; martingale with zero start and non-negative
      terminal value must be zero)
- [ ] **T5.2** Key lemma `separating_functional`:
      `NoArbitrage m → ∃ φ : (Ω → ℝ) →ₗ[ℝ] ℝ, StrictlyPositive φ ∧ ∀ f ∈ K m, φ f = 0`
      (Farkas' lemma / separating hyperplane in `ℝ^|Ω|`)
- [ ] **T5.3** Lemma `state_prices_to_emm`: construct `Q` from `φ` and verify
      `EquivalentMartingaleMeasure m Q`
- [ ] **T5.4** Theorem `no_arbitrage_implies_emm`:
      `NoArbitrage m → ∃ Q, EquivalentMartingaleMeasure m Q`
      (Combine T5.2 + T5.3)
- [ ] **T5.5** Theorem `ftap`:
      `NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q`
      (Combine T5.1 + T5.4)

**Mathlib touchpoints:** `Analysis.Convex.Cone`, `LinearAlgebra.Dual`,
`Analysis.InnerProductSpace.Basic` (for Farkas), or a direct finite-dimensional
argument via `Matrix.Finset`

---

## Dependencies for `options-proofs`

Once `ftap` is proved, `options-proofs` (put-call parity via CRR) imports:
- The `EquivalentMartingaleMeasure` definition (Q4.3)
- Risk-neutral pricing lemma (Q4.5)
- The FTAP itself as justification that the CRR model is arbitrage-free

---

## Notes on mathlib compatibility

- Use `MeasureTheory.Filtration` for the filtration (already in mathlib)
- `MeasureTheory.Martingale` defines discrete martingales — use directly
- For Farkas' lemma, check `Mathlib.LinearAlgebra.Farkas` — if present, import it;
  otherwise prove the finite-dimensional case from `Finset` linear algebra
- Follow mathlib naming: `camelCase` for definitions, `snake_case` for lemmas,
  `where` blocks for structure fields
