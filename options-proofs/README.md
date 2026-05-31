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

The proof is **complete**: zero `sorry`. The CRR market (`Tree`), the explicit
risk-neutral measure `q = (1 + r - d) / (u - d)` with no-arbitrage established via
the FTAP (`RiskNeutral`), and put-call parity `C - P = S - K / (1 + r)^T`
(`PutCallParity`) are all proved.

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
  OptionsProofs.lean: root module; re-exports all submodules
  OptionsProofs/
    Tree.lean: CRR binomial market model (up/down/risk-free factors)
    RiskNeutral.lean: explicit risk-neutral measure q = (1+r-d)/(u-d);
                               no-arbitrage via FTAP
    PutCallParity.lean: put-call parity: C - P = S - K/(1+r)^T
  lakefile.lean: lake project config (mathlib + quant-core + ftap-proofs)
  lean-toolchain: pinned Lean 4 toolchain version
```

## Dependencies

- [`quant-core`](../quant-core/): shared option primitives (`OptionKind`,
  `EuropeanOption`, payoff theorems from `QuantCore.OptionInvariants`).
- [`ftap-proofs`](../ftap-proofs/): FTAP biconditional (arbitrage-free iff EMM exists);
  provides the no-arbitrage infrastructure used in `RiskNeutral`.
- `mathlib`: measure theory, expectation, finite probability.

## References

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach."
*Journal of Financial Economics* 7, no. 3 (1979): 229–263.

## License

Apache License 2.0.
