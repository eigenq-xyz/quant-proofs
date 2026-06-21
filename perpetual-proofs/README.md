# perpetual-proofs

> A Lean 4 formalization of no-arbitrage pricing for **perpetual futures**, the dominant crypto derivative, following Ackerer, Hugonnier, and Jermann (2025). It proves the pricing formula, derives the inverse-perpetual convexity correction, and ships a machine-checked counterexample to a cash-flow specification from an earlier published draft. Zero `sorry`, axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## The result

A perpetual future never expires; instead a periodic funding payment ties its price to the underlying. Ackerer, Hugonnier, and Jermann (2025) show that this funding mechanism pins down a unique no-arbitrage price. In a finite-state, discrete-time market with funding rate `κ` and risk-free rate `r`:

$$F_0 = \mathbb{E}^{Q}[S_\tau], \qquad \tau \sim \mathrm{Geometric}\!\left(\tfrac{\kappa}{1+r}\right).$$

The price is the risk-neutral expectation of the underlying sampled at a geometric stopping time whose hazard rate is set by the funding mechanism. This repository states and proves that result, derives the convexity correction for inverse (coin-margined) perpetuals, and verifies where an earlier specification fails.

## Why prove it formally

Perpetual futures are young and the literature is still settling. The initial draft of He, Manela, Ross, and von Wachter (2022) used a cash-flow specification that Ackerer et al. document as incompatible with costless entry. This is exactly the situation where machine checking earns its place: the theorem `he_manela_violates_costless_entry` is a concrete two-state counterexample whose costless-entry obligation reduces to `−1 ≠ 0`, closed by `norm_num`. The proof does not argue that the specification is probably wrong; it exhibits a market in which it provably fails. The correct specification is then proved to satisfy costless entry, and the pricing and convexity theorems are built on top.

`#print axioms` on the headline theorems reports only `[propext, Classical.choice, Quot.sound]`. No `sorry`.

## Verify it yourself

```bash
cd perpetual-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile and machine-check every proof
grep -rn '^[[:space:]]*sorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

## What's inside

| Module | Role |
| ------ | ---- |
| `Market.lean` | One-period market and equivalent martingale measure |
| `CashFlow.lean` | Cash-flow specifications, costless entry, no buy-and-hold arbitrage |
| `FundingCompatibility.lean` | The Ackerer specification satisfies costless entry; the earlier one does not |
| `PerpFuturesNoArb.lean` | Existence, uniqueness, and the no-arbitrage price |
| `InversePerpCorrection.lean` | Inverse-perpetual convexity correction via Jensen |

Headline theorems (all proved, zero `sorry`):

| Theorem | What it states |
| ------- | -------------- |
| `perp_futures_no_arb_price` | The unique no-arbitrage price is the geometric-stopping-time expectation above |
| `ackerer_cashflow_satisfies_costless_entry` | The Ackerer cash-flow specification admits costless entry |
| `he_manela_violates_costless_entry` | An earlier specification provably fails costless entry (explicit counterexample) |
| `inverse_perp_convexity_discount` | The inverse-perpetual price satisfies `G₀ < F₀` by Jensen's inequality |

10 theorems total.

## Dependencies

- [`stopped-time-proofs`](../stopped-time-proofs/): the geometric stopping-time expectation operator and its strict monotonicity.
- [`ftap-proofs`](../ftap-proofs/): the finite-market model and self-financing strategy machinery.
- `mathlib`: measure theory, probability, analysis.

## Reference

Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing." *Mathematical Finance*, 2025. DOI: 10.1111/mafi.70018.

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
