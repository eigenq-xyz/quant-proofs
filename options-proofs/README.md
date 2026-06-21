# options-proofs

> Put-call parity, `C - P = S₀ - K/(1+r)^T`, derived from first principles in Lean 4: build the Cox-Ross-Rubinstein binomial market, prove it carries a risk-neutral measure and admits no arbitrage, then obtain parity as a theorem rather than an assumption. Zero `sorry`, axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb)

## The result

For a European call and put on the same underlying with the same strike `K` and expiry `T`:

```text
C - P = S₀ - K / (1 + r)^T
```

The call price minus the put price equals today's spot minus the discounted strike. It holds with no reference to volatility, drift, or any model of how the underlying moves, which is exactly what makes it the first sanity check any options desk runs.

This project does not assume parity. It assumes only the structure of a Cox-Ross-Rubinstein binomial tree (Cox, Ross, and Rubinstein, 1979), constructs the risk-neutral measure on that tree, proves the discounted price process is a martingale under it, confirms the market is arbitrage-free, and derives parity from there. The economic content (no arbitrage) is proved, not asserted.

## Why prove it formally

Parity is "obvious" in the way that a lot of finance folklore is obvious: it is true under assumptions that are rarely stated, and the usual one-line proof quietly assumes a no-arbitrage pricing measure already exists. The interesting work is showing the binomial market actually supplies one. This project does that explicitly: the risk-neutral up-probability is shown to lie strictly in `(0, 1)`, the resulting measure is shown to be equivalent to the physical measure and to make discounted prices a martingale, and only then does parity follow. The argument reuses the no-arbitrage and martingale-measure machinery from [`ftap-proofs`](../ftap-proofs/), so the dependency is a real proof dependency, not a citation.

`#print axioms OptionsProofs.put_call_parity` reports only `propext`, `Classical.choice`, and `Quot.sound`. No `sorry`, no numerical shortcuts.

## Try it (no install)

Open the [binomial pricing notebook](https://colab.research.google.com/github/eigenq-xyz/quant-proofs/blob/main/notebooks/binomial_put_call_parity.ipynb) in Google Colab. It builds a CRR tree in pure Python, prices a call and a put by backward induction under the risk-neutral measure, and checks `C - P` against `S₀ - K/(1+r)^T` across randomized parameters. The notebook confirms the identity numerically for the inputs you pick; the Lean theorem in this directory is what guarantees it for *all* admissible inputs at once.

## Verify the proof yourself

```bash
cd options-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile and machine-check every proof
grep -rn "sorry" --include="*.lean" OptionsProofs    # empty output = clean
```

## What's inside

| Module | Role |
| ------ | ---- |
| `Tree.lean` | The CRR state space, up-move count, price process, and its adaptedness |
| `RiskNeutral.lean` | The risk-neutral measure: density positive, sums to one, equivalent, martingale |
| `PutCallParity.lean` | Payoff identity, discounted terminal expectation, and the parity theorem |

Headline theorems:

| Theorem | What it states |
| ------- | -------------- |
| `put_call_parity` | `C - P = S₀ - K/(1+r)^T` for the CRR European call and put |
| `crrRNMeasure_equiv` | The risk-neutral measure is equivalent to the physical measure |
| `crrRNMeasure_martingale` | Discounted prices are a martingale under the risk-neutral measure |

31 theorems total, zero `sorry`.

## Dependencies

- [`quant-core`](../quant-core/): shared option primitives (`OptionKind`, `EuropeanOption`, payoff theorems).
- [`ftap-proofs`](../ftap-proofs/): the no-arbitrage and equivalent-martingale-measure results the parity argument cites.
- `mathlib`: finite probability, expectation, big operators.

## Reference

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229-263.

## License

Apache License 2.0.
