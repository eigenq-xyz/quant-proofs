# ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing
(FTAP, Harrison-Pliska 1981).

> **Theorem (FTAP, discrete-time, finite-state).** A market is arbitrage-free
> if and only if there exists an equivalent martingale measure (EMM).
>
> Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the
> Theory of Continuous Trading." *Stochastic Processes and Their Applications*
> 11, no. 3 (1981): 215–260.

This is a **skeleton** — the `FtapProofs` namespace is defined; proof content is
planned. The intended endpoint is a mathlib PR.

## Build

```bash
cd ftap-proofs && lake exe cache get   # fetch mathlib build cache (first run)
cd ftap-proofs && lake build           # build the library
```

The first cache fetch + build takes several minutes.

## Test

```bash
# Zero sorry check (empty output means clean)
grep -rn sorry --include="*.lean" ftap-proofs/
```

## Project structure

```
ftap-proofs/
  FtapProofs.lean       — root module; re-exports submodules as they are added
  lakefile.lean         — lake project config (mathlib dependency)
  lean-toolchain        — pinned Lean 4 toolchain version
```

Planned submodules: `FtapProofs.Market`, `FtapProofs.Arbitrage`,
`FtapProofs.MartingaleMeasure`, `FtapProofs.Theorem`.

## Dependencies

- `mathlib` — measure theory, probability, linear algebra

## Used by

- [`options-proofs`](../options-proofs/) — imports this library once it exposes a
  stable interface for equivalent martingale measures and no-arbitrage conditions.

## License

Apache License 2.0 — matches mathlib's licensing so contributions can flow upstream.
