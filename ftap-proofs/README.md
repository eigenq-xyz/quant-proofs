# ftap-proofs

> A machine-checked proof that a finite market admits no arbitrage **if and only if** a consistent risk-neutral pricing measure exists. Both directions, in Lean 4, with zero `sorry` and axioms confined to Lean's standard logical core.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## The result

The discrete Fundamental Theorem of Asset Pricing (Harrison and Pliska, 1981) is the load-bearing theorem of modern derivative pricing. Stated plainly:

> In a finite-state, discrete-time market, there is no arbitrage (no strategy that turns nothing into a guaranteed something) **if and only if** there exists an equivalent martingale measure: a reassignment of probabilities, agreeing with the real world on which outcomes are possible, under which every discounted asset price is a fair game.

Once that measure exists, every attainable payoff has one and only one arbitrage-free price, equal to its discounted expectation under the measure. That single fact is what licenses the rest of the field to price options at all. This repository states the theorem in Lean 4 and proves it, both directions, with no gaps.

## Why prove it formally

The forward direction (a martingale measure rules out arbitrage) is a short calculation. The reverse direction is the hard half, and it is where informal proofs lean on a confident "clearly such a measure exists." It does not just exist by assertion: the proof has to construct it. Here it is built explicitly from a strict separating hyperplane between the cone of arbitrage payoffs and the nonnegative orthant, then verified to be both equivalent to the original measure and a genuine martingale measure.

A textbook proof is trusted because a careful human read it. This proof is trusted because the Lean kernel checked every step, and `#print axioms` confirms it rests only on `propext`, `Classical.choice`, and `Quot.sound`, the standard logical core shared with all of mathlib. No `sorry`, no `native_decide`, no unproven shortcuts.

## Verify it yourself

```bash
cd ftap-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only; a few minutes)
lake build             # compile and machine-check every proof
```

Confirm there are no gaps (empty output means clean):

```bash
grep -rn "sorry" --include="*.lean" FtapProofs
```

Confirm the main theorem rests only on the standard axioms. Add the line `#print axioms FtapProofs.ftap` to any module under `FtapProofs/`, rebuild, and check the report is a subset of `[propext, Classical.choice, Quot.sound]` (no `sorryAx`, no `Lean.ofReduceBool`).

## What's inside

The proof is a pipeline of modules under `FtapProofs/`:

| Module | Role |
| ------ | ---- |
| `Market.lean` | Finite probability space, numeraire, asset-price processes, discounting |
| `Strategy.lean` | Trading strategies, self-financing condition, value and gains processes |
| `Arbitrage.lean` | Attainable payoffs as a linear subspace; the no-arbitrage characterization |
| `Density.lean` | Measure-change densities and discounted-price expectations |
| `MartingaleMeasure.lean` | Equivalent martingale measures and risk-neutral pricing |
| `Theorem.lean` | The two implications and the final `ftap` equivalence |

Headline theorems:

| Theorem | What it states |
| ------- | -------------- |
| `ftap` | No arbitrage ⟺ an equivalent martingale measure exists (full-support market) |
| `emm_implies_no_arbitrage` | A martingale measure rules out arbitrage |
| `no_arbitrage_implies_emm` | No arbitrage forces a martingale measure to exist (separating hyperplane) |
| `risk_neutral_pricing` | Attainable payoffs price as discounted expectations under the measure |

16 theorems total, zero `sorry`.

## See it applied

[`options-proofs`](../options-proofs/) builds a Cox-Ross-Rubinstein binomial market, invokes this theorem to obtain its risk-neutral measure, and derives put-call parity as a corollary. For a runnable feel of what "discounted expectation under the risk-neutral measure" means numerically, open the binomial-pricing notebook linked from that project.

## Dependencies

- `mathlib` (measure theory, finite probability, linear algebra, geometric Hahn-Banach separation)

## Used by

- [`options-proofs`](../options-proofs/): consumes the risk-neutral measure and no-arbitrage characterization.
- [`perpetual-proofs`](../perpetual-proofs/): cites the no-arbitrage pricing results.

## Status

Complete. The intended endpoint is a mathlib pull request, so the code follows mathlib naming and style conventions throughout.

## Reference

Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215-260.

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
