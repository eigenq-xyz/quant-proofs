# No-Arbitrage Pricing

The EigenQ Research Series builds pricing proofs from first principles: a market cannot
sustainably produce riskless profit, and that single constraint determines prices. The
projects in this pillar trace the arc from the foundational theorem of asset pricing through
derivative pricing in a binomial tree and on to a modern crypto derivative whose payoff
depends on a geometric stopping time.

Every proof in this pillar is zero sorry and builds clean.

---

## `ftap-proofs`: The Theoretical Spine

The discrete Fundamental Theorem of Asset Pricing (Harrison and Pliska, 1981) is the result
everything else here cites. In a finite-state, discrete-time market, the theorem is a
biconditional: the market is free of arbitrage if and only if there exists an equivalent
martingale measure (EMM). The Lean 4 formalization proves both directions of this
biconditional, stated formally as `NoArbitrage ↔ ∃ EMM`, over an arbitrary finite
probability space.

Why it matters: once you have an EMM, risk-neutral pricing follows as a theorem, not an
assumption. Every pricing formula in the projects below inherits its no-arbitrage guarantee
from this result. The proof is a candidate for a mathlib contribution.

Reference: Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in the
Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11, no. 3
(1981): 215-260.

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/foundations/ftap-proofs)

---

## `options-proofs`: Put-Call Parity in the CRR Model

The first concrete pricing result in the series. This project builds a Cox-Ross-Rubinstein
(CRR) binomial market as an instance of the FTAP's market structure, then derives the
risk-neutral probability

$$q = \frac{1 + r - d}{u - d}$$

and proves, by invoking `ftap-proofs`, that the CRR market is arbitrage-free. From there,
put-call parity follows by risk-neutral pricing:

$$C - P = S_0 - \frac{K}{(1 + r)^T}$$

This is the first result in the series to price a derivative purely from no-arbitrage
reasoning. The proof is zero sorry and cites the FTAP theorem directly, making the logical
chain from foundational theorem to derivative price machine-verifiable.

Reference: Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified
Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229-263.

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/foundations/options-proofs)

---

## `perpetual-proofs`: No-Arbitrage Pricing for Perpetual Futures

Perpetual futures are the dominant derivative in cryptocurrency markets: contracts with no
expiry date, where the long pays the short a continuous funding rate. Pricing them correctly
requires summing cash flows over a geometric stopping time, which is what `stopped-time-proofs`
supplies (see below). This project then applies `ftap-proofs` to prove eight theorems about
perpetual futures pricing, all zero sorry:

- The Ackerer-Hugonnier-Jermann cash-flow specification satisfies costless entry (the
  no-arbitrage entry condition). The earlier He-Manela specification does not: an explicit
  counterexample is constructed and proved.
- The no-arbitrage price exists and is unique.
- The inverse perpetual price is strictly discounted relative to the forward price by a
  convexity correction, proved via Jensen's inequality.

The project follows Ackerer, Hugonnier, and Jermann (2025) and depends on both `ftap-proofs`
and `stopped-time-proofs`.

Reference: Ackerer, D., J. Hugonnier, and R. Jermann. "Perpetual Futures Pricing."
*Mathematical Finance* (2025).

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/extensions/perpetual-proofs)

---

## `stopped-time-proofs`: Infrastructure for Geometric Stopping Times

This is a self-contained mathlib contribution candidate with no finance content of its own.
It formalizes the geometric probability mass function and a `GeometricExpectation` operator,
the infrastructure `perpetual-proofs` needs to sum cash flows over the geometric stopping
time that models contract termination. Zero sorry. The separation keeps the mathematical
infrastructure reusable and the mathlib contribution clean.

[Read the proof](https://github.com/eigenq-xyz/quant-proofs/tree/main/extensions/stopped-time-proofs)

---

## `quant-core`: Shared Pricing Primitives

The reusable foundation that the pricing proofs import. On the Lean side: option types (call
and put, European options with positive strike) and eight payoff theorems proved zero sorry,
including nonnegativity of option payoffs and the call-minus-put payoff identity. On the
Python side: a Black-Scholes pricer and a seeded geometric Brownian motion simulator.

[Read the source](https://github.com/eigenq-xyz/quant-proofs/tree/main/foundations/quant-core)

---

## How the projects connect

`quant-core` supplies types. `ftap-proofs` supplies the no-arbitrage theorem. `options-proofs`
and `perpetual-proofs` each import `ftap-proofs` and use it to establish that their specific
market is arbitrage-free, then derive prices. `stopped-time-proofs` supplies the summation
infrastructure `perpetual-proofs` needs. The dependency graph is a directed acyclic chain:
no pricing result is proved in isolation.
