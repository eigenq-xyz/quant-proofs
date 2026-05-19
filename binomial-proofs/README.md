# verified-binomial-model

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein (CRR) binomial model.

The CRR model is a finite-state market in which the FTAP from
[`verified-ftap`](https://github.com/eigenq-xyz/verified-ftap) applies, exhibiting an
explicit risk-neutral measure. Put-call parity follows.

This is a **work-in-progress skeleton.**

## Build

```bash
lake exe cache get   # fetch mathlib build cache (first run)
lake build           # build the library
```

## Dependencies

- `mathlib` — measure theory, expectation, finite probability.
- (Eventually) `verified-ftap` — once it exposes a stable interface for EMMs and
  no-arbitrage statements.

## License

Apache License 2.0.
