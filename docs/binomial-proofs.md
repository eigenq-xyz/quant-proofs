# binomial-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model.

## What it proves

**Put-call parity:** For a European call and put with the same strike and expiry in a no-arbitrage market, `C − P = S − K·B(0,T)` where `B(0,T)` is the discount factor.

The proof route: the CRR binomial model is a finite-state, discrete-time market. The FTAP from `ftap-proofs` applies, giving an explicit risk-neutral measure. Under that measure, put-call parity follows from the definition of option payoffs and linearity of expectation.

## Status

**In progress** — skeleton scaffolded May 2026, depends on `ftap-proofs`.

Implementation begins once the FTAP proof exposes a stable interface for the no-arbitrage condition and the EMM.

## Building

```bash
# ftap-proofs must be built first
cd ftap-proofs && lake exe cache get && lake build
cd ../binomial-proofs && lake build
```

## References

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229–263.
