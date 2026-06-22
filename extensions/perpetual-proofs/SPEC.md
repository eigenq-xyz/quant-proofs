# Perpetual Futures Pricing: Formally Verified
## `stopped-time-proofs` + `perpetual-proofs`

**EigenQ Research Series | Draft spec, 2026-05-26**

---

## Overview

This is a two-module project. The seam between modules follows the same principle as
the `optimization-proofs` / `portfolio-proofs` split: one module is a general
mathematical library with no domain-specific content; the other is the financial
application that imports it.

| Module | Content | Mathlib relationship |
|---|---|---|
| `stopped-time-proofs` | `GeomPMF`, `GeometricExpectation`, convergence, Jensen | Mathlib PR candidate — no finance content |
| `perpetual-proofs` | Market model, cash flow specs, three pricing theorems | Imports `stopped-time-proofs` + `ftap-proofs` |

Both modules target zero `sorry` on `main`.

---

## 1. Problem Statement

A perpetual future is a derivative contract with no fixed expiration date. Unlike a
standard futures contract, there is no terminal date at which the futures price is
forced to converge to the spot price. The standard cost-of-carry pricing
argument — which derives futures prices from that forced convergence — does not apply.

The anchoring mechanism is a periodic **funding rate** κ. At each funding interval, the
long position pays the short an amount proportional to the spread between the futures
price and the spot price. This incentivizes the futures price to track spot, replacing
the role played by expiration in standard futures.

Perpetual futures are a significant instrument in cryptocurrency derivatives markets.
Ackerer, Hugonnier, and Jermann[^ahj2025] report that during the first half of 2023,
75% of the $27 billion USD daily average volume in Bitcoin futures and 94% of the $8
billion USD daily average open interest were attributable to perpetual futures. They are
the dominant format for Bitcoin futures by volume, with standard fixed-expiry contracts
representing a small minority.

For most of their history, perpetual futures have traded exclusively on unregulated
offshore venues (Binance, BitMEX, Bybit), where pricing model errors are not subject
to regulatory audit. This changed in July 2025: Coinbase Derivatives received CFTC
approval for the first U.S.-regulated Bitcoin and Ether perpetual futures contracts
(BTC-PERP and ETH-PERP), which became effective July 21, 2025.[^cftc2025] In April 2025,
the CFTC opened a 30-day public comment window on perpetual derivatives contract
design.[^cftc_rfi2025] Basel Committee standard SCO60, revised July 2024 and effective
January 1, 2026, establishes how banks must treat crypto derivatives exposures under
Pillar 1 capital requirements — including restricting banks to the standardized approach
(no internal models) for Group 2 cryptoassets such as Bitcoin.[^bis2024]

These two regulatory developments create a structural tension that is specific to
perpetual futures.

Basel SCO60 prohibits banks from using the Internal Models Approach (IMA) for
regulatory capital calculation on Group 2 crypto derivatives. This restriction applies
to the capital number submitted to prudential regulators — not to the internal pricing
models banks use for client quoting, delta hedging, P&L attribution, and stress
testing. A bank trading CFTC-regulated perpetual futures must still maintain an internal
pricing model for those purposes; SCO60 does not govern that model.

What does govern it is the Federal Reserve's SR 26-2 / OCC Bulletin 2026-13, the
revised interagency model risk management guidance issued April 2026,[^sr262026] which
supersedes SR 11-7. SR 26-2 defines "model" broadly as "a complex quantitative method,
system, or approach that applies statistical, economic, or financial theories to process
input data into quantitative estimates" — a definition that encompasses a perpetual
futures pricing model used for internal valuation. The guidance requires development
documentation, validation, and ongoing governance for models within scope. It is
asset-class agnostic: there is no crypto-specific guidance on what constitutes adequate
conceptual soundness review for a perpetual futures pricing formula.

This is the gap. SCO60 bars internal models for capital while SR 26-2 requires
governance of whatever internal models exist — but no regulatory body has specified
what adequate validation looks like for the Ackerer-Hugonnier-Jermann formula or any
other perpetual futures pricing model. As of the date of writing, no major regulated
bank has publicly announced plans to make markets in perpetual futures
specifically.[^nobank] But the CFTC approval in July 2025 means the regulatory
infrastructure for institutional participation now exists. When institutional adoption
occurs, the SR 26-2 gap will need to be filled.

Formal verification is one answer. A machine-checked proof that the pricing formula
$F_0 = E^Q[S_\tau]$ follows from the stated model assumptions satisfies the
"conceptual soundness" prong of SR 26-2 validation — not by backtesting fit, but by
logical necessity. The He et al. error demonstrates why this standard is worth meeting:
an incorrect formula can survive peer review. A type-checker would have caught it
before the paper was submitted.

The theoretical foundation for pricing was developed by Ackerer, Hugonnier, and
Jermann.[^ahj2025] Their main result, in the discrete finite-state setting, is:

$$F_0 = E^Q[S_\tau], \quad \tau \sim \mathrm{Geometric}\!\left(\tfrac{\kappa}{1+r}\right)$$

where $Q$ is the risk-neutral measure, $S_\tau$ is the spot price sampled at the
geometrically distributed stopping time $\tau$, and $r$ is the risk-free rate per
funding interval.

This formula is not a reformulation of any existing result. Classical commodity futures
pricing (Black 1976[^black1976]) constructs a replicating portfolio that matures at a
known date. There is no replication date here. The geometric distribution on $\tau$ is
the exact discrete analogue of the exponential holding time in the continuous model of
Ackerer et al., and it is an object that does not currently exist in Lean's Mathlib
library in this form. Constructing it is the project's primary infrastructure
contribution.

The result also comes with a documented pricing error in the prior literature. He,
Manela, Ross, and von Wachter[^hmrv2022] produced an earlier working paper, "Fundamentals
of Perpetual Futures." An initial version contained a cash flow specification that
Ackerer et al. document explicitly as "incompatible with the assumption that entering
the contract is costless."[^ahj2025] He et al. amended their specification and the
current version (He et al. 2024) contains a correct formula that is a special case of
the Ackerer et al. result. The original error is not in the current version of the
paper, but it persisted through the peer review process long enough to be documented
by a separate paper. This project formalizes that incompatibility: in Lean, costless
entry is a `Prop` that must be proved, and the original He et al. specification
produces a false proof obligation.

### Scope of the discrete model

All theorems are in the finite-state discrete-time framework of Harrison-Pliska
1981.[^hp1981] No stochastic calculus is required. The spot price process
$S : \mathbb{N} \to \Omega \to \mathbb{R}$ is an infinite-horizon but purely algebraic
object on a finite state space. Convergence of the geometric series is the only
analytical argument, and it reduces to a single Mathlib lemma (`tsum_geometric_of_lt_one`).

---

## 2. Related Work

### Perpetual futures pricing

**He, Manela, Ross, and von Wachter.[^hmrv2022]** "Fundamentals of Perpetual Futures."
arXiv:2212.06888. First posted December 2022; latest revision (version 6) August 2024.
Working paper, not yet journal-published. An initial version contained a cash flow
specification documented by Ackerer et al. as incompatible with costless entry. The
current version (He et al. 2024) corrects this and derives a formula that Ackerer et al.
show is a special case of their result. The `FundingCompatibility` theorem in this
project formalizes the incompatibility of the original specification via an explicit
counterexample.

**Ackerer, Hugonnier, and Jermann.[^ahj2025]** "Perpetual Futures Pricing." DOI:
10.1111/mafi.70018. *Mathematical Finance*, online first, 2025. Also NBER Working Paper
No. 32936 and arXiv:2310.11771. Primary reference for all three theorem statements in
this project. Proves $F_0 = E^Q[S_\tau]$, documents the He et al. error, and derives the
inverse perpetual convexity adjustment.

### Classical futures pricing

**Black (1976).[^black1976]** "The Pricing of Commodity Contracts." The pricing mechanism
depends on a known expiration date at which convergence to spot is forced. This argument
does not apply to perpetual futures, which is why the Ackerer et al. result requires an
entirely different argument.

### The FTAP foundation

**Harrison and Pliska (1981).[^hp1981]** The discrete-time finite-state FTAP. `ftap-proofs`
in this monorepo formalizes the Harrison-Pliska market model (Phase 1, complete) and
trading strategies (Phase 2, complete), with no-arbitrage (Phase 3), EMM (Phase 4), and
the full theorem (Phase 5) in progress (issues #109–#111).

`perpetual-proofs` imports `FtapProofs.Market` and `FtapProofs.Strategy` directly. It
defines its own `OnePeriodEMM` — a minimal EMM sufficient for the one-period pricing
theorem — rather than blocking on `FtapProofs.MartingaleMeasure`. Once Phase 4 of
`ftap-proofs` is proved, `OnePeriodEMM` can be replaced by the upstream definition
without changing any theorem statements.

### Additional perpetual futures theory

**Angeris, Chitra, Evans, and Lorig (2022).[^acl2022]** "A Primer on Perpetuals."
arXiv:2209.03307. Derives model-free expressions for funding rates and replication
strategies for perpetual contracts in continuous-time, arbitrage-free, frictionless
markets; extends to jump models. Establishes semi-robust pricing expressions that do
not depend on a specific volatility model. Complements Ackerer et al. by taking a
replication-based rather than risk-neutral-expectation approach.

**Kim and Park (2025).[^kp2025]** "Designing Funding Rates for Perpetual Futures in
Cryptocurrency Markets." arXiv:2506.08573. Uses infinite-horizon backward stochastic
differential equations (BSDEs) to characterize funding rate designs that keep perpetual
futures prices aligned to a target process. Introduces path-dependent funding rates as
a practical alternative to the standard proportional mechanism. The most mathematically
advanced recent contribution in the continuous-time setting.

### Regulatory context

**Basel Committee on Banking Supervision, SCO60.[^bis2024]** "Prudential Treatment of
Cryptoasset Exposures." Revised July 17, 2024; effective January 1, 2026. Restricts
banks to the standardized approach for regulatory capital on Group 2 cryptoassets (which
includes Bitcoin and Ether). The IMA prohibition applies to capital calculation only —
it does not govern internal pricing models used for trading, hedging, or P&L. Those
models fall under SR 26-2.

**Federal Reserve SR 26-2 / OCC Bulletin 2026-13.[^sr262026]** "Model Risk Management."
April 17, 2026. Supersedes SR 11-7 (2011). Defines "model" broadly to include any
"complex quantitative method, system, or approach that applies statistical, economic, or
financial theories to process input data into quantitative estimates." A perpetual
futures pricing model used for internal valuation would fall within this definition. The
guidance is asset-class agnostic: no crypto-specific guidance on what constitutes
adequate conceptual soundness review for a novel derivative pricing formula. This
creates the gap described in Section 1.

**CFTC (2025).[^cftc2025][^cftc_rfi2025]** Coinbase Derivatives received CFTC approval
under 17 CFR § 40.2 for BTC-PERP and ETH-PERP — the first U.S.-regulated perpetual
futures contracts — effective July 21, 2025. The CFTC's April 2025 request for public
comment on perpetual derivatives contract design reflects ongoing regulatory attention
to how these contracts are structured, priced, and whether they are susceptible to
manipulation.

### Formal verification of financial models

A literature search of Mathlib4 (as of 2026-05-26) returns no results for "perpetual
future," "funding rate," or "geometric stopping time" in a finance context. To the
author's knowledge, no formalization of perpetual futures pricing exists in Lean 4,
Coq, Isabelle/HOL, or Agda. No peer-reviewed paper addresses model risk governance for
perpetual futures pricing models under the SR 26-2 / OCC 2026-13 framework; the
academic literature on this governance question is absent as of the date of writing.
Both gaps inform the scope of this project.

---

## 3. Motivating Examples

### Example A: Costless entry as a proof obligation

A futures contract has **costless entry** if the present value of all future cash flows
to the long holder, discounted at the risk-free rate under the risk-neutral measure,
equals zero at initiation. This is not a market convention but a defining property of
any well-posed futures contract: if initiating the position had nonzero present value,
an immediate arbitrage would exist. In Lean:

```lean
def CostlessEntry (spec : CashFlowSpec Ω) (market : OnePeriodMarket Ω)
    (Q : OnePeriodEMM market) : Prop :=
  geometricExpectation (p := market.κ / (1 + market.r))
    (fun k => ∑ ω : Ω, Q.density ω * spec.cashflow k market ω) = 0
```

`CostlessEntry` is a `Prop`. Before any pricing theorem can be stated, the cash flow
specification must satisfy it. This is a proof obligation, not an assumption.

The Ackerer et al. specification: at date $k$, the long receives $F_k - S_k$ from the
short. In the time-homogeneous model, $F_k = F_0$ at all dates (stationarity), so the
funding payment is $F_0 - S_k$. The present value of this stream under the geometric
weighting equals $F_0 - E^Q[S_\tau]$, which is zero when $F_0 = E^Q[S_\tau]$. Proof
discharged. This is Theorem 1a.

The original He et al. specification (as documented by Ackerer et al.[^ahj2025]): at
each date, the long receives $S_0 - F_0$, the initial spot-futures spread, fixed
regardless of $k$. The present value under geometric weighting is $S_0 - F_0$ (by
`geometricExpectation_const`, since the payment is constant). This is zero only when
$S_0 = F_0$, which is not a general property of the model — under the correct pricing
formula, $F_0 = E^Q[S_\tau]$, which equals $S_0$ only if $S$ is a $Q$-martingale under
the geometric weighting. Proof obligation fails. Theorem 1b constructs an explicit
counterexample: $S_0 = 1$, $F_0 = 2$, $\kappa = 1/10$, $r = 1/20$. The proof that
costless entry fails reduces to $1 - 2 = -1 \neq 0$, closed by `norm_num`.

### Example B: Geometric expectation as a new Lean object

The formula $F_0 = E^Q[S_\tau]$ requires an expectation where the integration index is
geometrically distributed. In the finite-state model:

$$F_0 = \sum_{k=0}^{\infty} (1-p)^k \cdot p \cdot \sum_{\omega \in \Omega} Q(\omega) \, S_k(\omega),
\quad p = \frac{\kappa}{1+r}$$

The series converges for $0 < p < 1$: it is bounded by $\|S\|_\infty \cdot \sum_k (1-p)^k p = \|S\|_\infty$.
The object $\mathrm{GeometricExpectation}(p, f) := \sum_{k=0}^\infty (1-p)^k p \cdot f(k)$
is a probability-weighted average of $f$ with PMF weights summing to 1 (proved as
`geomPMF_tsum_eq_one`, using `tsum_geometric_of_lt_one` from Mathlib). This definition
and its supporting lemmas do not currently exist in Mathlib. The `stopped-time-proofs`
module provides them, with no finance-specific content.

### Example C: The inverse perpetual convexity adjustment

A coin-settled (inverse) perpetual future has margin denominated in the base asset
rather than the quote currency. Its no-arbitrage price satisfies:

$$G_0 = \bigl( E^Q[1/S_\tau] \bigr)^{-1}$$

Since $\varphi(x) = 1/x$ is strictly convex on $x > 0$, Jensen's inequality applied
to the probability measure defined by `geomPMF` gives:

$$E^Q[1/S_\tau] \geq 1/E^Q[S_\tau] = 1/F_0 \implies G_0 \leq F_0$$

Strict inequality holds when spot is not $Q$-almost-surely constant, which is a
non-degeneracy hypothesis on the market. This derivation uses only the definition of
strict convexity and the algebraic properties of `GeometricExpectation`. No
market-specific content is required beyond the definitions.

---

## 4. End State: What Success Looks Like

### `stopped-time-proofs`: five definitions, ten sorry-free lemmas

`geomPMF`, `geometricExpectation`, and their convergence, linearity, monotonicity,
unrolling, constant, and Jensen lemmas. No finance content. Extractable to a Mathlib PR.

### `perpetual-proofs`: three sorry-free theorems

**Theorem 1a: `ackerer_cashflow_satisfies_costless_entry`**
```lean
theorem ackerer_cashflow_satisfies_costless_entry
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
    (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r) :
    CostlessEntry ackererCashFlow market Q
```

**Theorem 1b: `he_manela_violates_costless_entry`**
```lean
theorem he_manela_violates_costless_entry :
    ∃ (Ω : Type) [Fintype Ω] [MeasurableSpace Ω] [MeasurableSingletonClass Ω]
      (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market),
      ¬ CostlessEntry heManelaCashFlow market Q
```

Proved by constructing a two-state market with $S_0 = 1$, $F_0 = 2$, $\kappa = 1/10$,
$r = 1/20$. The proof obligation reduces to $-1 \neq 0$, closed by `norm_num`.

Together, Theorems 1a and 1b constitute the `FundingCompatibility` result.

**Theorem 2: `perp_futures_no_arb_price`**
```lean
theorem perp_futures_no_arb_price
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
    (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r) :
    let p  := market.κ / (1 + market.r)
    let F₀ := geometricExpectation p
                (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
    NoBuyAndHoldArbitrage market Q F₀ ∧
    ∀ F₀' : ℝ, NoBuyAndHoldArbitrage market Q F₀' → F₀' = F₀
```

First conjunct: existence. Second conjunct: uniqueness — any other entry price admits
a round-trip arbitrage.

**Theorem 3: `inverse_perp_convexity_discount`**
```lean
theorem inverse_perp_convexity_discount
    (market : OnePeriodMarket Ω) (Q : OnePeriodEMM market)
    (hκ : 0 < market.κ) (hr : 0 < market.r) (hκr : market.κ < 1 + market.r)
    (hS_pos : ∀ k ω, 0 < market.spot k ω)
    (hS_nondegen : ∃ k ω₁ ω₂, market.spot k ω₁ ≠ market.spot k ω₂) :
    let p  := market.κ / (1 + market.r)
    let G₀ := (geometricExpectation p
                  (fun k => ∑ ω : Ω, Q.density ω / market.spot k ω))⁻¹
    let F₀ := geometricExpectation p
                  (fun k => ∑ ω : Ω, Q.density ω * market.spot k ω)
    G₀ < F₀
```

### Additional success criteria

- `lake build` passes with zero `sorry` in both modules.
- `stopped-time-proofs` has no imports from `ftap-proofs` or any finance module —
  only `mathlib`. This is enforced structurally by its separate `lakefile.lean`.
- `OnePeriodEMM` in `PerpetualProofs/Market.lean` carries the docstring note:
  `-- TODO: unify with FtapProofs.MartingaleMeasure.EMM once ftap-proofs Phase 4 is proved`.

---

## 5. Module Structure

### `extensions/stopped-time-proofs/`

```
extensions/stopped-time-proofs/
  StoppedTimeProofs.lean           -- root: re-exports GeomPMF, GeomExpectation, Jensen
  StoppedTimeProofs/
    GeomPMF.lean                   -- geomPMF, geomPMF_nonneg, geomPMF_tsum_eq_one
    GeomExpectation.lean           -- geometricExpectation, _summable, _unroll, _const, _mono
    Jensen.lean                    -- jensen_geom_convex, jensen_geom_strict_convex
  lakefile.lean                    -- requires mathlib only
  lean-toolchain                   -- same pinned toolchain as ftap-proofs
  README.md
```

No finance content. If `GeomPMF` and `GeometricExpectation` are accepted into Mathlib,
this module is deleted and `extensions/perpetual-proofs/lakefile.lean` switches to `mathlib`
directly.

### `extensions/perpetual-proofs/`

```
extensions/perpetual-proofs/
  PerpetualProofs.lean             -- root: re-exports all submodules
  PerpetualProofs/
    Market.lean                    -- OnePeriodMarket, OnePeriodEMM
    CashFlow.lean                  -- CashFlowSpec, ackererCashFlow, heManelaCashFlow,
                                   -- CostlessEntry, NoBuyAndHoldArbitrage
    FundingCompatibility.lean      -- Theorems 1a and 1b
    PerpFuturesNoArb.lean          -- Theorem 2
    InversePerpCorrection.lean     -- Theorem 3
  lakefile.lean                    -- requires mathlib + ftap-proofs + stopped-time-proofs
  lean-toolchain
  README.md
  SPEC.md                          -- this document
```

### Dependency graph

```
perpetual-proofs
  ├── stopped-time-proofs          (GeomPMF, GeometricExpectation, Jensen)
  ├── FtapProofs.Market            (FinancialMarket — complete)
  ├── FtapProofs.Strategy          (TradingStrategy, selfFinancing — complete)
  └── mathlib

stopped-time-proofs
  └── mathlib                      (tsum_geometric_of_lt_one, Summable, ConvexOn)

FtapProofs.MartingaleMeasure       NOT imported — OnePeriodEMM defined locally.
                                   Replace once ftap-proofs Phase 4 is proved.
```

---

## 6. Roadmap

### `stopped-time-proofs` — Weeks 1–2

**Week 1: `GeomPMF.lean` and `GeomExpectation.lean`**

**G1.1** Define `geomPMF (p : ℝ) (k : ℕ) : ℝ := (1 - p) ^ k * p`.

**G1.2** Lemma `geomPMF_nonneg`: For `0 < p < 1`, `0 ≤ geomPMF p k` for all `k`.

**G1.3** Lemma `geomPMF_tsum_eq_one`: $\sum_{k=0}^\infty \mathtt{geomPMF}\ p\ k = 1$
  for `0 < p < 1`. Uses `tsum_geometric_of_lt_one` on $(1-p)$, then multiplies through
  by $p$.

**G1.4** Define `geometricExpectation (p : ℝ) (f : ℕ → ℝ) : ℝ := ∑' k, geomPMF p k * f k`.

**G1.5** Lemma `geometricExpectation_summable`: For `0 < p < 1` and bounded `f`,
  `Summable (fun k => geomPMF p k * f k)`. Proof by comparison to the geometric series
  `(1-p)^k * p * C`, using `Summable.of_norm_bounded`.

**G1.6** Lemma `geometricExpectation_unroll`:
  `geometricExpectation p f = p * f 0 + (1-p) * geometricExpectation p (fun k => f (k+1))`.
  Uses `tsum_eq_zero_add` and a shift of the summation index.

**G1.7** Lemma `geometricExpectation_const`: `geometricExpectation p (fun _ => c) = c`.
  From G1.3 and linearity of `tsum`.

**G1.8** Lemma `geometricExpectation_mono`: `(∀ k, f k ≤ g k) →
  geometricExpectation p f ≤ geometricExpectation p g`.

**Week 2: `Jensen.lean`**

**G2.1** Lemma `jensen_geom_convex`: For `φ : ℝ → ℝ` convex, `f : ℕ → ℝ` bounded,
  `0 < p < 1`:
  `φ (geometricExpectation p f) ≤ geometricExpectation p (φ ∘ f)`.

  Proof strategy: G1.3 establishes that `geomPMF p` defines a probability measure on
  `ℕ`. Apply the definition of convexity to finite partial sums, then take the limit
  using `geometricExpectation_summable` and monotone convergence. If a suitable Mathlib
  Jensen lemma exists for `tsum` with a summable PMF, use it; otherwise the direct
  argument is estimated at ~25 lines.

**G2.2** Lemma `jensen_geom_strict_convex`: For `φ : ℝ → ℝ` strictly convex,
  `f : ℕ → ℝ` bounded, `0 < p < 1`, and `∃ k₁ k₂, f k₁ ≠ f k₂`:
  `φ (geometricExpectation p f) < geometricExpectation p (φ ∘ f)`.

**Milestone:** `stopped-time-proofs` builds with zero `sorry`.

---

### `perpetual-proofs` — Weeks 2–4

**Week 2: Definitions — `Market.lean`, `CashFlow.lean`**

**P2.1** Define `OnePeriodMarket Ω`. Fields: `spot : ℕ → Ω → ℝ`, `κ : ℝ`, `r : ℝ`,
  `κ_pos`, `r_pos`, `spot_pos : ∀ k ω, 0 < spot k ω`.

  Open question (resolve in Week 2): the Ackerer et al. cash flow at date $k$ involves
  $F_k$. In the time-homogeneous model, $F_k = F_0$ for all $k$. Confirm this reading
  against Ackerer et al.[^ahj2025] §2 before committing the definition of
  `ackererCashFlow`. If the model is not time-homogeneous, `ackererCashFlow` requires
  a recursive definition that needs careful treatment.

**P2.2** Define `OnePeriodEMM market`. Fields: `density : Ω → ℝ`, `density_pos`,
  `density_sum_eq_one`. Docstring note: replace with `FtapProofs.EMM` once Phase 4
  of `ftap-proofs` is proved.

**P2.3** Define `CashFlowSpec Ω`, `ackererCashFlow`, `heManelaCashFlow`.

**P2.4** Define `CostlessEntry` and `NoBuyAndHoldArbitrage` as stated in Section 4.

**Milestone:** `perpetual-proofs` definitions type-check. Zero `sorry`.

**Week 3: `FundingCompatibility.lean`**

**F3.1** Lemma `ackerer_pv_eq`: Under stationarity ($F_k = F_0$), the Ackerer cash flow
  present value equals $F_0 - E^Q[S_\tau]$. Proof by `geometricExpectation_unroll`
  applied to the constant $F_0$ term and the spot expectation term.

**F3.2** Prove `ackerer_cashflow_satisfies_costless_entry` (Theorem 1a): F3.1 is zero
  when $F_0 = E^Q[S_\tau]$.

**F3.3** Lemma `he_manela_pv_eq`: The He et al. original cash flow present value equals
  $S_0 - F_0$, by `geometricExpectation_const`.

**F3.4** Prove `he_manela_violates_costless_entry` (Theorem 1b): Two-state $\Omega$,
  $S_0 = 1$, $F_0 = 2$, $\kappa = 1/10$, $r = 1/20$. Reduces to $-1 \neq 0$, closed
  by `norm_num`.

**Milestone:** `FundingCompatibility.lean` sorry-free. Theorems 1a + 1b done.

**Week 4a: `PerpFuturesNoArb.lean`**

**PR4.1** Lemma `no_arb_uniqueness`: Two prices satisfying `NoBuyAndHoldArbitrage` are
  equal. If $F_0 \neq F_0'$, a round-trip strategy produces a nonzero expected payoff
  under $Q$, contradicting one of the two hypotheses.

**PR4.2** Lemma `no_arb_existence`: The geometric-expectation price satisfies
  `NoBuyAndHoldArbitrage`. Uses Theorem 1a and the risk-neutral pricing identity.

**PR4.3** Combine into `perp_futures_no_arb_price` (Theorem 2).

**Milestone:** `PerpFuturesNoArb.lean` sorry-free. Theorem 2 done.

**Week 4b: `InversePerpCorrection.lean`**

**I4.1** Define `inversePerp_noArb_price market Q` as the reciprocal of the geometric
  expectation of $1/S_k$ under $Q$.

**I4.2** Apply `jensen_geom_strict_convex` (G2.2) with $\varphi(x) = 1/x$ (strictly
  convex on $\mathbb{R}_{>0}$, established from `StrictConvexOn` for the reciprocal
  function, available in Mathlib under `Real.strictConvexOn_inv` or similar).

**I4.3** Rearrange using `inv_lt_inv_of_lt` to obtain $G_0 < F_0$ (Theorem 3).

**Milestone:** All three theorems done. Zero `sorry` across both modules.

---

## 7. Key Mathlib Touchpoints

| Symbol | Module | Phase |
|---|---|---|
| `tsum_geometric_of_lt_one` | `Topology.Algebra.InfiniteSum.Basic` | G1.3 |
| `tsum_eq_zero_add` | `Topology.Algebra.InfiniteSum.Basic` | G1.6 |
| `Summable.of_norm_bounded` | `Topology.Algebra.InfiniteSum.Basic` | G1.5 |
| `ConvexOn` / `StrictConvexOn` | `Analysis.Convex.Function` | G2.1–G2.2 |
| `Real.strictConvexOn_inv` (or nearest equivalent) | `Analysis.SpecialFunctions` | I4.2 |
| `inv_lt_inv_of_lt` | `Mathlib.Order.Bounds` | I4.3 |
| `MeasureTheory.IsProbabilityMeasure` | `MeasureTheory.Measure.MeasureSpace` | P2.2 |

---

## 8. Open Questions

Resolve before proof writing begins in Week 3.

**Q1: Stationarity of $F_k$.** `ackererCashFlow` uses $F_k$ for $k > 0$. In the
time-homogeneous discrete model, is $F_k = F_0$ for all $k$? If yes, `ackererCashFlow`
has no self-reference and F3.1 is straightforward. If no, the definition requires a
recursive treatment and the proof structure in F3.1 changes. Resolve against Ackerer
et al.[^ahj2025] §2 before Week 2 ends.

**Q2: Jensen in Mathlib for `tsum`.** Does Mathlib have Jensen's inequality in the form
needed for G2.1 (convex function, `tsum` with a summable PMF)? If not, the fallback is
a direct proof via finite partial sums and monotone convergence (~25 lines). Check
`MeasureTheory.integral_comp_le` and related discrete probability lemmas.

**Q3: `OnePeriodEMM` martingale condition.** The pricing theorem needs
$E^Q[S_{k+1}] = (1+r) \cdot E^Q[S_k]$ (or the appropriate stationarity condition)
to link consecutive geometric expectation terms. State this as a field in `OnePeriodEMM`
or as a separate hypothesis in Theorems 2 and 3. Decide in Week 2.

---

## 9. Timeline

| Week | Deliverable | Sorry target |
|---|---|---|
| 1 | `stopped-time-proofs`: G1.1–G1.8 complete | 0 sorry in stopped-time-proofs |
| 2 | `stopped-time-proofs`: G2.1–G2.2. `perpetual-proofs`: all definitions type-check | 0 sorry in stopped-time-proofs |
| 3 | `FundingCompatibility.lean` complete | 0 sorry through Theorems 1a + 1b |
| 4a | `PerpFuturesNoArb.lean` complete | 0 sorry through Theorem 2 |
| 4b | `InversePerpCorrection.lean` complete | 0 sorry across both modules |

---

## 10. Relation to the Summer 2026 Sequence

The summer sequence is `ftap-proofs` → `options-proofs` → `backtest-proofs`. This
project is parallel to `options-proofs` in the dependency graph: both import
`FtapProofs.Market` and `FtapProofs.Strategy`; neither blocks the other.

`stopped-time-proofs` has no dependency on `ftap-proofs`. It is a pure mathematics
module that could be submitted to Mathlib independently.

The SSRN preprint milestone (due 2026-07-31) can draw on this project for two
contributions: the `GeometricExpectation` infrastructure and the `FundingCompatibility`
counterexample for the original He et al. specification.

---

[^ahj2025]: Ackerer, D., J. Hugonnier, and U. Jermann. "Perpetual Futures Pricing."
*Mathematical Finance*, 2025. DOI: 10.1111/mafi.70018. Also NBER Working Paper No. 32936
and arXiv:2310.11771.

[^hmrv2022]: He, S., B. Manela, O. Ross, and H. von Wachter. "Fundamentals of Perpetual
Futures." arXiv:2212.06888. Latest revision: version 6, August 2024. Working paper, not
yet journal-published. The error in the original version is documented in Ackerer et al.
(2025), p. 1 of the Introduction.

[^hp1981]: Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in
the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11,
no. 3 (1981): 215–260.

[^black1976]: Black, F. "The Pricing of Commodity Contracts." *Journal of Financial
Economics* 3, no. 1–2 (1976): 167–179.

[^bis2024]: Basel Committee on Banking Supervision. "Prudential Treatment of Cryptoasset
Exposures." Basel Framework Chapter SCO60. Revised July 17, 2024; effective January 1,
2026. https://www.bis.org/bcbs/publ/d545.pdf

[^cftc2025]: Pillsbury Winthrop Shaw Pittman LLP. "CFTC Permits Exchange-Traded BTC and
ETH Perpetual Futures." July 22, 2025. https://www.pillsburylaw.com/en/news-and-insights/cftc-perpetual-futures-btc-eth-crypto-derivatives.html

[^cftc_rfi2025]: Sidley Austin LLP. "The U.S. CFTC Looks to the Future, Opens 30-Day
Window for Public Comment." April 2025.
https://www.sidley.com/en/insights/newsupdates/2025/04/the-us-cftc-looks-to-the-future-opens-30-day-window-for-public-comment

[^sr262026]: Board of Governors of the Federal Reserve System. "SR 26-2: Revised
Guidance on Model Risk Management." April 17, 2026.
https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm. Companion document:
OCC Bulletin 2026-13, same date. Supersedes SR 11-7 (April 4, 2011).

[^acl2022]: Angeris, G., T. Chitra, A. Evans, and M. Lorig. "A Primer on Perpetuals."
arXiv:2209.03307 [q-fin.MF], September 2022. DOI: 10.48550/arXiv.2209.03307.

[^kp2025]: Kim, J., and H. Park. "Designing Funding Rates for Perpetual Futures in
Cryptocurrency Markets." arXiv:2506.08573 [q-fin.MF], June 2025.
DOI: 10.48550/arXiv.2506.08573.

[^nobank]: Goldman Sachs trades CME-listed Bitcoin and Ether futures and OTC NDFs but
has not announced perpetual futures market making. JPMorgan, as of December 2025, was
reported to be exploring institutional crypto spot and derivatives trading (Fortune,
December 23, 2025), without specifying perpetual futures as a product line. No major
regulated bank had publicly announced a perpetual futures trading desk as of the date
of writing.
