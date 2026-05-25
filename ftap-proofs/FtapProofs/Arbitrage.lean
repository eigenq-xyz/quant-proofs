/-!
# No-Arbitrage

An **arbitrage opportunity** is a self-financing strategy that:
1. Costs nothing to initiate: `V 0 θ = 0`
2. Cannot lose money: `V T θ ≥ 0` almost surely under `P`
3. Has a positive probability of profit: `P {ω | V T θ ω > 0} > 0`

Informally: a free lottery ticket. A market is **arbitrage-free** (satisfies NA)
if no such strategy exists.

In the finite-state setting, NA is equivalent to saying that the set of reachable
discounted terminal payoffs from zero-cost strategies has trivial intersection with
the positive orthant — a statement amenable to Farkas' lemma.
-/

namespace FtapProofs

-- TODO: define ArbitrageOpportunity
-- TODO: define NoArbitrage (NA condition)
-- TODO: lemma: NA is equivalent to: the only zero-cost strategy
--       with V_T ≥ 0 a.s. is V_T = 0 a.s.
-- TODO: lemma: the set of attainable zero-cost discounted payoffs
--       is a linear subspace of ℝ^Ω

end FtapProofs
