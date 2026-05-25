/-!
# Market Model

A finite-state, discrete-time financial market for the discrete FTAP.

We work with:
- A finite probability space `(Ω, ℱ, P)` over a finite set `Ω`
- A finite time horizon `T : ℕ`
- A filtration `(ℱ_t)_{t=0}^T` encoding the information structure
- `n` risky assets with `ℱ_t`-measurable price processes `S i t`
- A risk-free numeraire `B t > 0` with `B 0 = 1`
- Discounted price processes `S̃ i t = S i t / B t`

This module defines the `MarketModel` structure and proves basic measurability
and positivity lemmas needed downstream.
-/

namespace FtapProofs

-- TODO: define MarketModel structure
-- TODO: define discounted price process S̃
-- TODO: lemma: S̃ i t is ℱ_t-measurable
-- TODO: lemma: B t > 0 for all t

end FtapProofs
