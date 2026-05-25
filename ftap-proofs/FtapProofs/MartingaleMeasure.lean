/-!
# Equivalent Martingale Measure

A probability measure `Q` on `(Ω, ℱ)` is an **equivalent martingale measure** (EMM) if:

1. **Equivalence**: `Q ~ P`, meaning `Q A > 0 ↔ P A > 0` for all `A ∈ ℱ`.
   In the finite-state case this means `Q {ω} > 0` for all `ω ∈ Ω`.

2. **Martingale property**: the discounted asset price processes `S̃ i` are
   `Q`-martingales:
   `E^Q [S̃ i (t+1) | ℱ_t] = S̃ i t`  for all `i`, `t`.

The existence of an EMM is the other side of the FTAP biconditional.
In the finite-state case, an EMM is equivalent to a strictly positive
state-price vector `(q ω)_{ω ∈ Ω}` summing to 1 such that
`S̃ i t = ∑_ω q ω · S̃ i T ω` (risk-neutral pricing).
-/

namespace FtapProofs

-- TODO: define EquivalentMeasure Q P (Q ~ P)
-- TODO: define MartingaleMeasure Q (discounted prices are Q-martingales)
-- TODO: define EquivalentMartingaleMeasure (EMM)
-- TODO: lemma: under an EMM, the discounted value process of any
--       self-financing strategy is a Q-martingale
-- TODO: lemma (risk-neutral pricing): V_0 θ = E^Q [V_T θ / B_T]
--       for any self-financing θ under any EMM Q

end FtapProofs
