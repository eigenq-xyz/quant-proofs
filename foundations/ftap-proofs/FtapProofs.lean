import FtapProofs.Market
import FtapProofs.Strategy
import FtapProofs.Arbitrage
import FtapProofs.MartingaleMeasure
import FtapProofs.Theorem
import FtapProofs.Density

/-!
# FtapProofs

Lean 4 formalization of the Discrete Fundamental Theorem of Asset Pricing
(Harrison-Pliska 1981).

**Main theorem** (`FtapProofs.Theorem.ftap`):
```
NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q
```

## Module structure

- `FtapProofs.Market` — market model: finite probability space, filtration,
  asset price processes, discounted prices
- `FtapProofs.Strategy` — trading strategies: predictability, self-financing,
  value and gains processes
- `FtapProofs.Arbitrage` — no-arbitrage condition and attainable payoff sets
- `FtapProofs.MartingaleMeasure` — equivalent martingale measures and
  risk-neutral pricing
- `FtapProofs.Theorem` — the FTAP biconditional and its proof
- `FtapProofs.Density` — the EMM → singleton-density bridge for finite-state models

## Status

Complete, zero `sorry`; `#print axioms FtapProofs.ftap` reports only
`[propext, Classical.choice, Quot.sound]`.
-/
