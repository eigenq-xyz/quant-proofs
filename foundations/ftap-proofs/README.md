# ftap-proofs

A Lean 4 machine-checked proof of the discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981).

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it proves

In a finite-state, discrete-time market with full support, there is no arbitrage (no strategy that turns nothing into a guaranteed profit) if and only if there exists an equivalent martingale measure: a reassignment of probabilities, agreeing with the real world on which outcomes are possible, under which every discounted asset price is a fair game.

The formal Lean statement:

```lean
theorem ftap (m : FinancialMarket Ω) (hP_full : ∀ ω : Ω, 0 < m.P {ω}) :
    NoArbitrage m ↔ ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q
```

| Guarantee | Theorem |
|-----------|---------|
| Full biconditional: no arbitrage iff an EMM exists | `ftap` |
| An equivalent martingale measure rules out arbitrage | `emm_implies_no_arbitrage` |
| Absence of arbitrage forces an EMM to exist | `no_arbitrage_implies_emm` |
| Attainable payoffs price as discounted expectations under the measure | `risk_neutral_pricing` |

16 theorems/lemmas total (see `DEPENDENCY_GRAPH.md` at the repo root), zero `sorry`, axioms confined to `[propext, Classical.choice, Quot.sound]`.

The forward direction (no arbitrage implies an EMM exists) goes through a geometric Hahn-Banach separation of the attainable-payoff subspace from the standard simplex in `EuclideanSpace ℝ Ω`, constructing the state-price vector explicitly via `InnerProductSpace.toDual`. The reverse direction is a short contradiction from risk-neutral pricing: a zero-cost strategy with non-negative terminal value has zero expected value under any EMM, ruling out any strictly positive profit.

## What it doesn't claim

The proof is complete and machine-checked. It has not been submitted to mathlib — no PR exists yet. "Complete" here means the Lean proof compiles with zero `sorry` and standard axioms; it does not mean the result has cleared mathlib review or naming conventions.

## Build and verify

```bash
cd foundations/ftap-proofs
lake exe cache get    # fetch prebuilt mathlib (first run; a few minutes)
lake build            # compile and machine-check every proof
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty output = clean
```

Full build/test matrix: see `CLAUDE.md`.

## Used by

- [`foundations/options-proofs/`](../options-proofs/): invokes `ftap` to obtain the risk-neutral measure for the Cox-Ross-Rubinstein binomial market, then derives put-call parity.
- [`extensions/perpetual-proofs/`](../../extensions/perpetual-proofs/): cites the no-arbitrage pricing results.
- [`research-pipeline/`](../../research-pipeline/): cites this module for signal measurability proofs.

## Dependencies

- `mathlib` (measure theory, finite probability, linear algebra, geometric Hahn-Banach separation).

## Reference

Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215-260.

## License

Apache License 2.0.
