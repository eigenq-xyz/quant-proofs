# perpetual-proofs

Lean 4 proof of no-arbitrage pricing for perpetual futures, following Ackerer, Hugonnier,
and Jermann (2025), plus a counterexample to a cash-flow specification from an earlier
draft by He, Manela, Ross, and von Wachter, proved (not just tested) to fail in Lean 4.

## What it proves

In a finite-state, discrete-time market with funding rate `k` and risk-free rate `r`,
the unique no-arbitrage perpetual-futures price is the risk-neutral expectation of spot
weighted by a geometric distribution set by the funding mechanism:

```
F₀ = geometricExpectation (k/(1+r)) (E^Q[S_·])
```

| Theorem | Statement |
|---------|-----------|
| `ackerer_cashflow_satisfies_costless_entry` | The Ackerer-Hugonnier-Jermann cash-flow specification satisfies costless entry |
| `he_manela_violates_costless_entry` | An earlier specification fails costless entry: a two-state counterexample reduces the obligation to `-1 != 0`, closed by `norm_num` |
| `perp_futures_no_arb_price` | The geometric-expectation price is the unique no-arbitrage price (existence and uniqueness) |
| `inverse_perp_convexity_discount` | The inverse perpetual price `G₀` satisfies `G₀ < F₀`, by Jensen's inequality (for a strictly convex function, the average of the function exceeds the function of the average) applied to `1/x` on `R_{>0}` |

10 theorems total, zero `sorry` (Lean's placeholder tactic for an unproven step; none remain
here). `#print axioms` (Lean's command listing the axioms a proof ultimately rests on) on the
headline theorems reports only `[propext, Classical.choice, Quot.sound]`, the three axioms
mathlib itself relies on, not any unproven assumption specific to this project; check this
yourself, see below.

## What it doesn't claim

The `ftap-proofs` import in `Market.lean` is currently vestigial (present in the code but
not load-bearing): `OnePeriodMarket` and `OnePeriodEMM` are self-contained structs, and no
proof in this project cites a `FtapProofs.*` declaration (`ftap-proofs`' formalization of
the Fundamental Theorem of Asset Pricing, Harrison-Pliska 1981: no arbitrage iff an
equivalent martingale measure, EMM, exists). The dependency listed below is real for
`stopped-time-proofs` and not yet real for `ftap-proofs`; see `DEPENDENCY_GRAPH.md` at the
repo root for the exact edge classification.

## Build and verify

```bash
cd extensions/perpetual-proofs
lake exe cache get          # fetch prebuilt mathlib (first run only)
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

## Dependencies

- [`extensions/stopped-time-proofs/`](../stopped-time-proofs/): `GeometricExpectation`,
  its convergence lemmas, and the strict Jensen inequality
  (`geom_exp_inv_gt` uses `geometricExpectation_strict_mono`). Load-bearing.
- [`foundations/ftap-proofs/`](../../foundations/ftap-proofs/): imported but not
  load-bearing; see "What it doesn't claim" above.

## Reference

Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing." *Mathematical
Finance*, 2025. DOI: 10.1111/mafi.70018.

## License

Apache 2.0.
