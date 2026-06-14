# ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (FTAP, Harrison-Pliska 1981).

> **Theorem (FTAP, discrete-time, $\mathcal{F}_t$-complete market).** A market is arbitrage-free if and only if there exists an equivalent martingale measure (EMM).
>
> Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215–260.

This is a complete formalization of the discrete FTAP (Harrison-Pliska 1981). The `FtapProofs` namespace is defined and all theorems are verified with zero `sorry`.

## Build & Test Commands

- `lake exe cache get` — fetch mathlib build cache (run after `lake update`)
- `lake build` — build the library
- `lake update` — refresh mathlib dependency to current master
- `lake build --watch` — rebuild on file changes

## Architecture

Single Lean library `FtapProofs`. Submodules include:
- `FtapProofs.Market`
- `FtapProofs.Arbitrage`
- `FtapProofs.MartingaleMeasure`
- `FtapProofs.Theorem`
- `FtapProofs.Strategy`
- `FtapProofs.Density`

## Dependencies

- `mathlib` — measure theory, probability, linear
- `quant-core` (as dependency for shared primitives)

## Used by

- [`options-proofs`](../options-proofs/) — uses the stable interface for equivalent martingale measures and no-arbitrage conditions provided by this library.

## License

Apache License 2.0 — matches mathlib's licensing so contributions can flow upstream.
