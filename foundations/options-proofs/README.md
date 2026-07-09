# options-proofs

Put-call parity `C - P = S₀ - K/(1+r)^T` proved correct in Lean 4 from first principles via the Cox-Ross-Rubinstein binomial model. Zero `sorry` (Lean's placeholder tactic for "trust me, no proof yet"; none remain, so no unproven steps), axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb)

## What it proves

For a European call and put on the same underlying with the same strike `K` and expiry `T`:

```text
C - P = S₀ - K / (1 + r)^T
```

The call price minus the put price equals today's spot minus the discounted strike, with no reference to volatility, drift, or any model of how the underlying moves.

This project constructs a Cox-Ross-Rubinstein binomial tree (Cox, Ross, and Rubinstein, 1979), builds the risk-neutral measure on that tree, proves the discounted price process is a martingale under it, confirms the market is arbitrage-free, and derives parity from there. No-arbitrage is proved, not assumed.

| Guarantee | Theorem |
| --------- | ------- |
| `C - P = S₀ - K/(1+r)^T` for CRR European call and put | `put_call_parity` |
| The risk-neutral measure is equivalent to the physical measure | `crrRNMeasure_equiv` |
| Discounted prices are a martingale under the risk-neutral measure | `crrRNMeasure_martingale` |

31 theorems/lemmas total (see `DEPENDENCY_GRAPH.md` at the repo root), zero `sorry`. `#print axioms OptionsProofs.put_call_parity` reports only `propext`, `Classical.choice`, and `Quot.sound`.

## What it doesn't claim

The Colab notebook (below) checks the identity numerically for the inputs you pick. It is a sanity check, not a proof. The Lean theorem in this directory is what guarantees the identity for all admissible inputs at once; the two are not the same kind of evidence.

## Try it (no install)

Open the [binomial pricing notebook](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb) in Google Colab. It builds a CRR tree in pure Python, prices a call and a put by backward induction under the risk-neutral measure, and checks `C - P` against `S₀ - K/(1+r)^T` across randomized parameters.

## Build and verify

```bash
cd foundations/options-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile every proof; the Lean kernel checks each step
grep -rn '\bsorry\b' --include="*.lean" OptionsProofs/    # empty output = clean
```

Full build/test matrix: see `CLAUDE.md`.

## Dependencies

- [`ftap-proofs`](../ftap-proofs/): the no-arbitrage and equivalent-martingale-measure results the parity argument cites (zero `sorry`).
- [`quant-core`](../quant-core/): shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems).
- `mathlib`: finite probability, expectation, big operators.

## Reference

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229-263.

## License

Apache License 2.0.
