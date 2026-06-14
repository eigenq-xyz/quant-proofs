# ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing.

## What it proves

**Harrison and Pliska (1981):** A finite-state, discrete-time securities market is free of arbitrage if and only if there exists an equivalent martingale measure (EMM).

This is the foundational result of modern mathematical finance. The discrete version is the right starting point for a machine-checked proof: finite state spaces avoid measure-theoretic technicalities while preserving the core no-arbitrage ↔ EMM equivalence.

## Status

**Complete** — 16 theorems, zero `sorry`. The main result `FtapProofs.ftap` depends only on the standard axioms `[propext, Classical.choice, Quot.sound]` (verified via `#print axioms`).

The proof spans `FtapProofs.Market`, `FtapProofs.Arbitrage`, `FtapProofs.MartingaleMeasure`, `FtapProofs.Strategy`, `FtapProofs.Density`, and `FtapProofs.Theorem`. The hard direction (no-arbitrage ⟹ EMM) is proved via the separating-hyperplane theorem on the cone of attainable payoffs; the easy direction uses risk-neutral pricing. The theorem assumes the standard finite-state full-support condition (`∀ ω, 0 < P {ω}`).

Target: mathlib PR.

## Building

```bash
cd ftap-proofs && lake exe cache get && lake build
```

## References

Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215–260.
