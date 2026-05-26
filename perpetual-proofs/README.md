# perpetual-proofs

Lean 4 formalization of the no-arbitrage pricing theorem for perpetual futures.

> **Theorem (Ackerer, Hugonnier, and Jermann 2025).** In a finite-state
> discrete-time market with funding rate κ and risk-free rate r, the unique
> no-arbitrage price of a perpetual future is
>
> $$F_0 = E^Q[S_\tau], \quad \tau \sim \mathrm{Geometric}\!\left(\tfrac{\kappa}{1+r}\right)$$
>
> Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing."
> *Mathematical Finance*, 2025. DOI: 10.1111/mafi.70018.

## Theorem status

| Theorem | File | Status |
|---|---|---|
| `ackerer_cashflow_satisfies_costless_entry` | `FundingCompatibility.lean` | Planned (F3.2) |
| `he_manela_violates_costless_entry` | `FundingCompatibility.lean` | Planned (F3.4) |
| `perp_futures_no_arb_price` | `PerpFuturesNoArb.lean` | Planned (PR4.3) |
| `inverse_perp_convexity_discount` | `InversePerpCorrection.lean` | Planned (I4.3) |

## Build

```bash
cd perpetual-proofs
lake exe cache get   # fetch mathlib cache (first run, takes several minutes)
lake build
```

Zero sorry check:

```bash
grep -rn '^\s*sorry\b' --include="*.lean" --exclude-dir=.lake .
```

## Project structure

```
perpetual-proofs/
  PerpetualProofs.lean             -- root module
  PerpetualProofs/
    Market.lean                    -- OnePeriodMarket, OnePeriodEMM
    CashFlow.lean                  -- CashFlowSpec, ackererCashFlow, heManelaCashFlow,
                                   -- CostlessEntry, NoBuyAndHoldArbitrage
    FundingCompatibility.lean      -- Theorems 1a and 1b
    PerpFuturesNoArb.lean          -- Theorem 2
    InversePerpCorrection.lean     -- Theorem 3
```

## Dependencies

- [`stopped-time-proofs`](../stopped-time-proofs/) — `geometricExpectation`,
  Jensen's inequality (Mathlib PR candidate, no finance content)
- [`ftap-proofs`](../ftap-proofs/) — `FtapProofs.Market` (complete),
  `FtapProofs.Strategy` (complete)
- `mathlib` — measure theory, probability, analysis

## The He et al. error

The initial version of He, Manela, Ross, and von Wachter (arXiv:2212.06888, 2022)
contained a cash flow specification documented by Ackerer et al. as incompatible
with the costless-entry assumption. The theorem `he_manela_violates_costless_entry`
provides a machine-checked counterexample: a two-state market with specific numerical
parameters for which the original specification fails the costless-entry proof
obligation. The proof reduces to `−1 ≠ 0`, closed by `norm_num`.

## License

Apache License 2.0.
