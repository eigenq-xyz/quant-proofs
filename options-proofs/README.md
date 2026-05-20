# options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein (CRR) binomial model.

The CRR model (Cox, Ross, Rubinstein 1979) is a finite-state, discrete-time market.
The FTAP from [`ftap-proofs`](../ftap-proofs/) applies, exhibiting an explicit
risk-neutral measure. Put-call parity is a corollary: for a European call and put
with the same strike K and expiry T,

```
C - P = S - K · B(0, T)
```

where S is the current spot price and B(0, T) is the present value of 1 unit at T.

This is a **skeleton** — the `OptionsProofs` namespace is defined; proof content
depends on `ftap-proofs` reaching a stable interface for no-arbitrage and equivalent
martingale measures.

## Build

```bash
cd options-proofs && lake exe cache get   # fetch mathlib build cache (first run)
cd options-proofs && lake build           # build the library
```

## Test

```bash
# Zero sorry check (empty output means clean)
grep -rn sorry --include="*.lean" options-proofs/
```

## Project structure

```
options-proofs/
  OptionsProofs.lean    — root module; re-exports submodules as they are added
  lakefile.lean         — lake project config (mathlib + quant-core dependencies)
  lean-toolchain        — pinned Lean 4 toolchain version
```

Planned submodules: `OptionsProofs.Tree`, `OptionsProofs.RiskNeutral`,
`OptionsProofs.PutCallParity`.

## Dependencies

- [`quant-core`](../quant-core/) — shared option primitives (`OptionKind`,
  `EuropeanOption`, payoff theorems from `QuantCore.OptionInvariants`).
- [`ftap-proofs`](../ftap-proofs/) — FTAP direction (arbitrage-free → EMM exists);
  added as a dependency once `ftap-proofs` exposes a stable interface.
- `mathlib` — measure theory, expectation, finite probability.

## References

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach."
*Journal of Financial Economics* 7, no. 3 (1979): 229–263.

## License

Apache License 2.0.
