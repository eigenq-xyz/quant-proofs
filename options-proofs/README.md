# options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein (CRR) binomial model.

The CRR model is a finite-state market in which the FTAP from
[`ftap-proofs`](https://github.com/eigenq-xyz/quant-proofs/tree/main/ftap-proofs) applies, exhibiting an
explicit risk-neutral measure. Put-call parity follows.

This is a **work-in-progress skeleton.**

## Build

```bash
lake exe cache get   # fetch mathlib build cache (first run)
lake build           # build the library
```

## Dependencies

- `quant-core` — shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems).
- `mathlib` — measure theory, expectation, finite probability.
- `ftap-proofs` (planned) — once it exposes a stable interface for EMMs and no-arbitrage.

## License

Apache License 2.0.
