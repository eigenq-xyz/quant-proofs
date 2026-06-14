# options-proofs

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model.

## What it proves

**Put-call parity:** For a European call and put with the same strike and expiry in a no-arbitrage market, `C − P = S − K·B(0,T)` where `B(0,T)` is the discount factor.

The proof route: the CRR binomial model is a finite-state, discrete-time market. The FTAP from `ftap-proofs` applies, giving an explicit risk-neutral measure. Under that measure, put-call parity follows from the definition of option payoffs and linearity of expectation.

## Status

**Complete** — 31 theorems, zero `sorry`. The main result `OptionsProofs.put_call_parity` depends only on the standard axioms `[propext, Classical.choice, Quot.sound]` (verified via `#print axioms`).

The module builds the CRR binomial market, proves its risk-neutral measure is an equivalent martingale measure (`crrRNMeasure_emm`) and that the market is arbitrage-free (`crr_no_arbitrage`), then derives `put_call_parity` (`C − P = S₀ − K/(1+r)^T`) under the standard CRR no-arbitrage condition `0 < d < 1 + r < u`.

## Dependencies

- `quant-core` — `EuropeanOption` types, payoff functions, and 8 payoff theorems (active path dependency; Lake builds it automatically).
- `ftap-proofs` — risk-neutral measure and no-arbitrage condition (wired in).

## Building

```bash
# quant-core is a path dependency — Lake builds it automatically
cd options-proofs && lake exe cache get && lake build
```

## References

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229–263.
