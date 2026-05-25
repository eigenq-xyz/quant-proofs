/-!
# The Fundamental Theorem of Asset Pricing

**Theorem (Harrison-Pliska 1981, discrete-time finite-state).**
A market is arbitrage-free if and only if there exists an equivalent martingale measure.

```
NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q
```

## Proof sketch

**(⇐) EMM implies NA** (the easy direction).
Suppose `Q` is an EMM and `θ` is a self-financing strategy with `V 0 θ = 0`.
Since `Q ~ P`, `V T θ ≥ 0` a.s. under `P` implies `V T θ ≥ 0` a.s. under `Q`.
The discounted value process `Ṽ t θ` is a `Q`-martingale, so:
  `E^Q [Ṽ T θ] = Ṽ 0 θ = 0`
Since `Ṽ T θ ≥ 0` and has expectation 0, we get `Ṽ T θ = 0` `Q`-a.s., hence `P`-a.s.
So no free lunch is possible.

**(⇒) NA implies EMM exists** (the hard direction, via Farkas' lemma).
In the finite-state setting, let `K` be the linear subspace of attainable
discounted terminal payoffs from zero-cost self-financing strategies.
NA says `K ∩ ℝ₊^Ω = {0}`.
By the separating hyperplane theorem (Farkas' lemma for finite dimensions),
there exists a strictly positive linear functional `φ : ℝ^Ω → ℝ` that
vanishes on `K`. Normalize `φ` to a probability measure: `Q ω := φ(1_ω) / φ(1)`.
Strict positivity of `φ` gives `Q ~ P`. The martingale property of `S̃ i` under `Q`
follows from `φ` vanishing on `K` (buy-and-hold strategies lie in `K`).
-/

namespace FtapProofs

-- TODO: theorem emm_implies_no_arbitrage :
--   EquivalentMartingaleMeasure m Q → NoArbitrage m

-- TODO: theorem no_arbitrage_implies_emm :
--   NoArbitrage m → ∃ Q, EquivalentMartingaleMeasure m Q
--   (requires: Farkas' lemma applied to the attainable payoff subspace)

-- TODO: theorem ftap :
--   NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q

end FtapProofs
