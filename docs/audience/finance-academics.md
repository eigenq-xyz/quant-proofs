# For Finance Academics

If you work in asset pricing, derivatives theory, or financial economics, this
page describes what the EigenQ Research Series contributes to the formal
treatment of results that appear in the academic literature.

## Machine-checked theorems in asset pricing

Formal verification provides something that pen-and-paper proofs cannot: a
guarantee that every step of an argument is logically valid as stated, with
all hypotheses explicit and no implicit appeal to convention or context. The
[verification methodology](../how-we-verify.md) describes how Lean 4 and the
mathlib library are used to achieve this.

The pricing pillar ([pillar-pricing.md](../pillar-pricing.md)) covers three
areas of direct interest to asset-pricing researchers.

## The discrete FTAP: a machine-checked proof

`ftap-proofs/` is a Lean 4 formalization of the discrete Fundamental Theorem
of Asset Pricing as stated by Harrison and Pliska (1981). The central theorem:
a finite securities market admits no arbitrage if and only if there exists a
probability measure equivalent to the physical measure under which all
discounted asset prices are martingales.

The formalization makes the following hypotheses explicit in the Lean type
signature: finite state space, finite trading horizon, a fixed filtration on
the probability space, and the completeness of the trading strategy space. A
reader who wants to know exactly what conditions the theorem requires can read
the type signature directly, without parsing prose.

The proof is being prepared for submission to mathlib, the community-maintained
library of formalized mathematics for Lean 4. It is the first formalization of
the Harrison-Pliska result in Lean 4 at the level of generality required for
a mathlib contribution.

## Put-call parity via the binomial model

`options-proofs/` proves European put-call parity in the Cox-Ross-Rubinstein
binomial model:

$$C - P = S_0 - K \cdot (1+r)^{-T}$$

The proof proceeds by constructing an explicit replicating portfolio for the
call-minus-put position and invoking the FTAP from `ftap-proofs/` to conclude
that two portfolios with identical payoffs must have identical prices in any
arbitrage-free market. The formal statement makes precise which version of the
binomial model is assumed (one risky asset, one bond, no dividends, frictionless
trading) and how the risk-neutral measure is constructed.

## A formal counterexample in perpetual futures pricing

`perpetual-proofs/` addresses a result in the literature on perpetual futures,
a class of derivatives that has no fixed expiry and charges a periodic funding
payment to keep the futures price close to the spot price.

The subproject contains eight theorems, including a formal counterexample. The
He-Manela specification of the no-arbitrage funding rate for perpetual futures
is shown to admit arbitrage under the hypotheses stated in that paper. The
corrected specification follows Ackerer, Hugonnier, and Jermann (2025). The
counterexample is machine-checked: Lean verifies that the He-Manela formula,
under the stated conditions, produces a price that allows a riskless profit.

Formal counterexamples to published specifications are uncommon in the finance
formalization literature. This result illustrates what machine-checked proofs
add beyond peer review: a proof assistant will reject a subtly flawed argument
that a careful human reader might accept.

## Explicit hypotheses as a research discipline

One contribution that runs across all three subprojects is the discipline of
making hypotheses explicit. In the Lean formalization, every assumption that a
textbook might state informally ("assume frictionless markets," "assume the
probability space is finite") must be written as a formal type-class constraint
or function argument. This forces a precision that paper proofs often lack.

For researchers interested in the scope and limitations of classical asset-pricing
results, the type signatures of the theorems in this monorepo provide a precise
account of what each result requires.

## Optimization results

The optimization pillar ([pillar-optimization.md](../pillar-optimization.md))
covers convex optimization results (projected gradient descent, projection onto
the probability simplex) that underpin mean-variance portfolio construction. These
are standard results, formalized here to support the portfolio solver in
`portfolio-proofs/`.

## Entry points

- Verification methodology: [how-we-verify.md](../how-we-verify.md)
- Pricing theorems: [pillar-pricing.md](../pillar-pricing.md)
- Optimization theorems: [pillar-optimization.md](../pillar-optimization.md)
- AI decision invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
