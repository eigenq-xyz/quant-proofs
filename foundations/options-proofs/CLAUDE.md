# CLAUDE.md

Lean 4 proof of put-call parity via the Cox-Ross-Rubinstein binomial model, proved correct rather than only tested. Builds the CRR market, establishes the equivalent martingale measure, and derives parity as a theorem. Complete, 31 theorems, zero `sorry` (Lean's placeholder tactic for "trust me, no proof yet"; none remain, so no unproven steps).

## Build and test

```bash
cd foundations/options-proofs
lake exe cache get          # fetch prebuilt mathlib (first run only, or after lake update)
lake build                  # compile and verify all proofs
grep -rn '\bsorry\b' --include="*.lean" OptionsProofs/    # must be empty
```

## Architecture

Single library `OptionsProofs`. Three modules in dependency order:

| File | Contents |
| ---- | -------- |
| `OptionsProofs/Tree.lean` | CRR state space `Ω := Fin T → Bool`, up-count `ups`, risky-asset price `crrPrice`, numeraire `crrNumeraire`, natural filtration `crrFiltration`, adaptedness `crrPrice_adapted`. Imports `FtapProofs.Market`. |
| `OptionsProofs/RiskNeutral.lean` | Risk-neutral probability `riskNeutralProb q`, density `crrRNDensity`, sum-to-one (binomial theorem), measure equivalence `crrRNMeasure_equiv`. Imports `OptionsProofs.Tree`, `FtapProofs.MartingaleMeasure`, `FtapProofs.Theorem`. |
| `OptionsProofs/PutCallParity.lean` | Real-valued payoffs `callPayoffReal`/`putPayoffReal`, payoff identity `payoff_parity`, risk-neutral pricing operator `rnPrice`, discounted martingale identity `discounted_terminal_expectation`, headline theorem `put_call_parity`. Imports `OptionsProofs.RiskNeutral`, `QuantCore.Option`. |

## Dependencies

- `ftap-proofs` (complete, zero `sorry`): no-arbitrage and EMM machinery. Imported as `FtapProofs.Market`, `FtapProofs.MartingaleMeasure`, `FtapProofs.Theorem`.
- `quant-core`: shared option primitives (`QuantCore.Option`).
- `mathlib`: finite probability, conditional expectation, big operators.

## Local notes

- Never suppress linter warnings with `set_option linter.X false` — fix the root cause.
- Apache 2.0 license: compatible with mathlib for upstream contribution.
