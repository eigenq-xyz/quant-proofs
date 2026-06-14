# options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein (CRR) binomial model.

The CRR model (Cox, Ross, Rubinstein 1979) is a finite-state, discrete-time market. The FTAP from [`ftap-proofs`](../ftap-proofs/) applies, exhibiting an explicit risk-neutral measure. Put-call parity is a corollary: for a European call and put with the same strike K and expiry T,

```
C - P = S - K \cdot B(0, T)
```

where S is the current spot price and B(0, T) is the present value of 1 unit at T.

This is a complete implementation of the CRR binomial model and its relationship to put-call parity. The `OptionsProofs` namespace is defined and all theorems are verified with zero `sorry`.

## Build & Test Commands

- `lake exe cache get` — fetch mathlib build cache (run after `lake update`)
- `lake build` — build the library
- `lake update` — refresh dependencies (mathlib; later `ftap-proofs`)
- `lake build --watch` — rebuild on file changes

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

Submodules: `OptionsProofs.Tree`, `OptionsProofs.RiskNeutral`, `OptionsProofs.PutCallParity`.

## Dependencies

- [`quant-core`](../quant-core/) — shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems from `QuantCore.OptionInvariants`).
- [`ftap-proofs`](../ftap-proofs/) — provides the no-arbitrage and equivalent martingale measures interface used for pricing.
- `mathlib` — measure theory, expectation, finite probability.

## References

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229–263.

## License

Apache License 2.0.
