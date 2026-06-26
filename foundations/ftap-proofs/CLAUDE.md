# CLAUDE.md: ftap-proofs

Lean 4 formalization of the discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no-arbitrage iff an equivalent martingale measure exists. Complete, zero `sorry`, targeting a mathlib PR.

## Build and test

```bash
# Run from foundations/ftap-proofs/
lake exe cache get          # fetch prebuilt mathlib (after clone or lake update)
lake build                  # compile and check all proofs
```

Zero-sorry check (empty output required):

```bash
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

Axiom check: add `#print axioms FtapProofs.ftap` to any file, rebuild, confirm the report is a subset of `[propext, Classical.choice, Quot.sound]`.

## Architecture

Single Lean library `FtapProofs`. All modules live under `FtapProofs/`:

| File | Contents |
|------|----------|
| `Market.lean` | `FinancialMarket Ω` structure: `T`, `n`, `S`, `B`, `𝒻`, `P`, adaptedness. `discountedPrice`, `numeraire_pos`, `discountedPrice_adapted`. |
| `Strategy.lean` | `TradingStrategy` (holdings + `bondHolding`), `selfFinancing`, `discountedValueProcess`. |
| `Arbitrage.lean` | `ArbitrageOpportunity`, `NoArbitrage`, `attainablePayoffs`, `attainablePayoffs_isLinearSubspace`, `noArbitrage_iff_attainable_nonneg_eq_zero`. |
| `Density.lean` | Measure-change densities and discounted-price expectations under a measure change. |
| `MartingaleMeasure.lean` | `EquivalentMartingaleMeasure`, `IsMartingaleMeasure`, `risk_neutral_pricing`. |
| `Theorem.lean` | `emm_implies_no_arbitrage` (T5.1), `state_price_functional` (T5.2, `private`), `state_prices_to_emm` (T5.3, `private`), `no_arbitrage_implies_emm` (T5.4), `ftap` (T5.5). |
| `FtapProofs.lean` | Top-level import; re-exports all submodules. |

The hard direction (NA implies EMM) proceeds via `geometric_hahn_banach_compact_closed` on `EuclideanSpace ℝ Ω`, with `InnerProductSpace.toDual` for the Riesz representation, and `PMF.ofFintype` to normalize state prices into a probability measure. The `TradingStrategy` structure carries an explicit `bondHolding` field so bond-funded buy-and-hold strategies lie in `attainablePayoffs m`.

## Conventions

- mathlib naming throughout: `camelCase` for definitions and structures, `snake_case` for lemmas and theorems, `where` blocks for structure fields.
- Module-level docstrings use `/-! ## Contents -/` listing with label codes matching the Harrison-Pliska proof sketch (M1.x, S2.x, A3.x, Q4.x, T5.x).
- Every exported theorem has a `/-- ... -/` docstring stating the result in plain English before restating the Lean signature.
- `private` for intermediate lemmas (`state_price_functional`, `state_prices_to_emm`) that are implementation detail rather than public API.

## Hard rules

- Zero `sorry` on main. No exceptions.
- Do not edit `.lean` files to change proof terms without running `lake build` to confirm zero sorry.
- No private content in commits or PRs: no personal timelines, no GPA, no target firm names.
- Apache 2.0 license matches mathlib; do not introduce incompatible dependencies.
- `lake update` bumps `lean-toolchain` and recompiles mathlib from scratch: run it intentionally, not as a reflex.
