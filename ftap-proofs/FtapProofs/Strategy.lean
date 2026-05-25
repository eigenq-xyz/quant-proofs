/-!
# Trading Strategies

A trading strategy is a predictable process specifying portfolio holdings at each time step.

Formally, `θ = (θ⁰, θ¹, ..., θⁿ)` where:
- `θ i t` gives the number of units of asset `i` held over period `[t-1, t)`
- Each `θ i t` is `ℱ_{t-1}`-measurable (predictable — decided *before* observing `S t`)

A strategy is **self-financing** if no cash is injected or withdrawn between trades:
all rebalancing is funded internally by selling some assets to buy others.

The **value process** `V t θ` and **gains process** `G t θ` are derived quantities
used throughout the FTAP proof.
-/

namespace FtapProofs

-- TODO: define TradingStrategy (predictable process)
-- TODO: define selfFinancing predicate
-- TODO: define value process V
-- TODO: define gains process G (in discounted units)
-- TODO: lemma: selfFinancing ↔ ΔV_t = θ_t · ΔS_t for all t
-- TODO: lemma: V is ℱ_t-measurable when θ is predictable

end FtapProofs
