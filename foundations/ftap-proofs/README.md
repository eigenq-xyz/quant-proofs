# ftap-proofs

A Lean 4 machine-checked proof of the discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981), targeting a mathlib PR.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it proves

In a finite-state, discrete-time market with full support, there is no arbitrage (no strategy that turns nothing into a guaranteed profit) if and only if there exists an equivalent martingale measure: a reassignment of probabilities, agreeing with the real world on which outcomes are possible, under which every discounted asset price is a fair game.

The formal Lean statement:

```lean
theorem ftap (m : FinancialMarket Ω) (hP_full : ∀ ω : Ω, 0 < m.P {ω}) :
    NoArbitrage m ↔ ∃ Q : MeasureTheory.Measure Ω, EquivalentMartingaleMeasure m Q
```

Both directions are proved with no gaps. The forward direction (no arbitrage implies an EMM exists) goes through a geometric Hahn-Banach separation of the attainable-payoff subspace from the standard simplex in `EuclideanSpace ℝ Ω`, constructing the state-price vector explicitly via `InnerProductSpace.toDual`. The reverse direction is a short contradiction from risk-neutral pricing: a zero-cost strategy with non-negative terminal value has zero expected value under any EMM, ruling out any strictly positive profit.

## Build and test

```bash
cd foundations/ftap-proofs
lake exe cache get    # fetch prebuilt mathlib (first run; a few minutes)
lake build            # compile and machine-check every proof
```

Confirm zero gaps (empty output means clean):

```bash
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

Confirm the main theorem rests only on the standard axioms by adding `#print axioms FtapProofs.ftap` to any file under `FtapProofs/`, rebuilding, and verifying the report is a subset of `[propext, Classical.choice, Quot.sound]`.

## Structure

| File | Role |
|------|------|
| `FtapProofs/Market.lean` | `FinancialMarket` structure: finite state space, numeraire, adapted price processes, discounting |
| `FtapProofs/Strategy.lean` | Trading strategies, self-financing condition, discounted value and gains processes |
| `FtapProofs/Arbitrage.lean` | `ArbitrageOpportunity`, `NoArbitrage`, attainable payoffs as a linear subspace |
| `FtapProofs/Density.lean` | Measure-change densities and discounted-price expectations |
| `FtapProofs/MartingaleMeasure.lean` | `EquivalentMartingaleMeasure`, risk-neutral pricing |
| `FtapProofs/Theorem.lean` | Both implications and the final `ftap` biconditional (16 theorems, zero `sorry`) |

## Headline theorems

| Theorem | Statement |
|---------|-----------|
| `ftap` | `NoArbitrage m ↔ ∃ Q, EquivalentMartingaleMeasure m Q` (full biconditional) |
| `emm_implies_no_arbitrage` | An equivalent martingale measure rules out arbitrage |
| `no_arbitrage_implies_emm` | Absence of arbitrage forces an equivalent martingale measure to exist |
| `risk_neutral_pricing` | Attainable payoffs price as discounted expectations under the measure |

16 theorems total, zero `sorry`, axioms confined to `[propext, Classical.choice, Quot.sound]`.

## Used by

- [`foundations/options-proofs/`](../options-proofs/): invokes `ftap` to obtain the risk-neutral measure for the Cox-Ross-Rubinstein binomial market, then derives put-call parity.
- [`extensions/perpetual-proofs/`](../../extensions/perpetual-proofs/): cites the no-arbitrage pricing results.
- [`research-pipeline/`](../../research-pipeline/): the flagship pipeline cites this module for signal measurability proofs.

## Dependencies

- `mathlib` (measure theory, finite probability, linear algebra, geometric Hahn-Banach separation)

## Reference

Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215-260.

## License

Apache 2.0, compatible with mathlib for upstream contribution.
