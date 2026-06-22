# CLAUDE.md — perpetual-proofs

Lean 4 formalization of the no-arbitrage pricing theorem for perpetual futures,
building on `stopped-time-proofs` (geometric expectation infrastructure) and
`ftap-proofs` (Harrison-Pliska market model).

## What this project is

Three sorry-free Lean 4 theorems:

1. **`ackerer_cashflow_satisfies_costless_entry`** — the Ackerer-Hugonnier-Jermann cash
   flow specification satisfies costless entry.
2. **`he_manela_violates_costless_entry`** — explicit counterexample showing the original
   He-Manela-Ross-von Wachter specification does not.
3. **`perp_futures_no_arb_price`** — the unique no-arbitrage price is
   `geometricExpectation (κ/(1+r)) (E^Q[S_·])`.
4. **`inverse_perp_convexity_discount`** — the inverse perpetual price satisfies
   `G₀ < F₀` by Jensen's inequality.

Primary reference: Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures
Pricing." *Mathematical Finance*, 2025. DOI: 10.1111/mafi.70018.

## Architecture

```
extensions/perpetual-proofs/
  PerpetualProofs.lean             -- root module
  PerpetualProofs/
    Market.lean                    -- OnePeriodMarket, OnePeriodEMM (P2.1–P2.2)
    CashFlow.lean                  -- CashFlowSpec, ackererCashFlow, heManelaCashFlow,
                                   -- CostlessEntry, NoBuyAndHoldArbitrage (P2.3–P2.4)
    FundingCompatibility.lean      -- Theorems 1a + 1b (F3.1–F3.4)
    PerpFuturesNoArb.lean          -- Theorem 2 (PR4.1–PR4.3)
    InversePerpCorrection.lean     -- Theorem 3 (I4.1–I4.3)
  lakefile.lean                    -- requires mathlib + stopped-time-proofs + ftap-proofs
  lean-toolchain                   -- pinned toolchain (same as ftap-proofs)
  SPEC.md                          -- full project spec with roadmap and citations
```

## Theorem status

| Theorem | File | Status |
|---|---|---|
| `ackerer_cashflow_satisfies_costless_entry` | `FundingCompatibility.lean` | **Proved** (F3.2, PR #130) |
| `he_manela_violates_costless_entry` | `FundingCompatibility.lean` | **Proved** (F3.4, PR #130) |
| `no_arb_uniqueness` | `PerpFuturesNoArb.lean` | **Proved** (PR4.1) |
| `no_arb_existence` | `PerpFuturesNoArb.lean` | **Proved** (PR4.2) |
| `perp_futures_no_arb_price` | `PerpFuturesNoArb.lean` | **Proved** (PR4.3) |
| `inversePerp_noArb_price` | `InversePerpCorrection.lean` | **Proved** (I4.1) |
| `geom_exp_inv_gt` | `InversePerpCorrection.lean` | **Proved** (I4.2) |
| `inverse_perp_convexity_discount` | `InversePerpCorrection.lean` | **Proved** (I4.3) |

## Build & test commands

```bash
# Fetch mathlib cache (first run)
lake exe cache get

# Build all modules
lake build

# Zero sorry check (tactic form only)
grep -rn '^\s*sorry\b' --include="*.lean" --exclude-dir=.lake .
```

## Hard rules

- **Zero `sorry` as a tactic on main.** Commented-out `sorry` in TODO blocks is not
  a proof-level use and is not flagged by the CI check.
- **Do not import `FtapProofs.MartingaleMeasure`** until ftap-proofs Phase 4 (issue
  #110) is proved. Use `OnePeriodEMM` in `Market.lean` instead.
- **Resolve open questions in SPEC.md** (Q1: stationarity of F_k; Q2: Jensen in
  Mathlib; Q3: OnePeriodEMM martingale condition) before Week 3 proof writing.
- This is a **public repo**. Do not import private context from `~/ode/eigenq/`.
- Apache 2.0 license matches mathlib's so this work can flow upstream.
