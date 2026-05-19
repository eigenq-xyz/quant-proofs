# ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing.

## What it proves

**Harrison and Pliska (1981):** A finite-state, discrete-time securities market is free of arbitrage if and only if there exists an equivalent martingale measure (EMM).

This is the foundational result of modern mathematical finance. The discrete version is the right starting point for a machine-checked proof: finite state spaces avoid measure-theoretic technicalities while preserving the core no-arbitrage ↔ EMM equivalence.

## Status

**In progress** — skeleton scaffolded May 2026, implementation planned Summer 2026.

The `FtapProofs` namespace is open; the proof structure (`FtapProofs.Market`, `FtapProofs.Arbitrage`, `FtapProofs.MartingaleMeasure`, `FtapProofs.Theorem`) will be filled in during development.

Target: mathlib PR once proof is complete and stable.

## Building

```bash
cd ftap-proofs && lake exe cache get && lake build
```

## References

Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215–260.
