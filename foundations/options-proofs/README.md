# options-proofs

Put-call parity `C - P = S₀ - K/(1+r)^T` proved from first principles in Lean 4 via the Cox-Ross-Rubinstein binomial model. Zero `sorry`, axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb)

## The result

For a European call and put on the same underlying with the same strike `K` and expiry `T`:

```text
C - P = S₀ - K / (1 + r)^T
```

The call price minus the put price equals today's spot minus the discounted strike. It holds with no reference to volatility, drift, or any model of how the underlying moves, which is exactly what makes it the first sanity check any options desk runs.

This project does not assume parity. It constructs a Cox-Ross-Rubinstein binomial tree (Cox, Ross, and Rubinstein, 1979), builds the risk-neutral measure on that tree, proves the discounted price process is a martingale under it, confirms the market is arbitrage-free, and derives parity from there. The economic content (no arbitrage) is proved, not asserted.

`#print axioms OptionsProofs.put_call_parity` reports only `propext`, `Classical.choice`, and `Quot.sound`. No `sorry`, no numerical shortcuts.

## Try it (no install)

Open the [binomial pricing notebook](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb) in Google Colab. It builds a CRR tree in pure Python, prices a call and a put by backward induction under the risk-neutral measure, and checks `C - P` against `S₀ - K/(1+r)^T` across randomized parameters. The notebook confirms the identity numerically for the inputs you pick; the Lean theorem in this directory is what guarantees it for all admissible inputs at once.

## Verify the proof

```bash
cd foundations/options-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile and machine-check every proof
grep -rn '\bsorry\b' --include="*.lean" OptionsProofs/    # empty output = clean
```

## What's inside

| Module | Role |
| ------ | ---- |
| `OptionsProofs/Tree.lean` | CRR state space (`Ω = Fin T → Bool`), up-move count, price process, natural filtration, adaptedness |
| `OptionsProofs/RiskNeutral.lean` | Risk-neutral probability `q = (1+r-d)/(u-d)`, density positivity, sum-to-one (binomial theorem), equivalence to the uniform measure |
| `OptionsProofs/PutCallParity.lean` | Real-valued payoffs, payoff identity `(S-K)⁺ - (K-S)⁺ = S-K`, risk-neutral pricing operator, discounted martingale identity, and `put_call_parity` |

Headline theorems:

| Theorem | What it states |
| ------- | -------------- |
| `put_call_parity` | `C - P = S₀ - K/(1+r)^T` for CRR European call and put |
| `crrRNMeasure_equiv` | The risk-neutral measure is equivalent to the physical measure |
| `crrRNMeasure_martingale` | Discounted prices are a martingale under the risk-neutral measure |

31 theorems total, zero `sorry`.

## Dependencies

- [`ftap-proofs`](../ftap-proofs/): the no-arbitrage and equivalent-martingale-measure results the parity argument cites (complete, zero `sorry`).
- [`quant-core`](../quant-core/): shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems).
- `mathlib`: finite probability, expectation, big operators.

## Reference

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229-263.

## License

Apache License 2.0.
