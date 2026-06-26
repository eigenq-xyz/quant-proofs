# For Finance Academics

If you work in asset pricing, derivatives theory, or financial economics, the most
relevant starting points are the [Research Integrity flagship](../pillar-research-integrity.md)
and the [No-Arbitrage Pricing pillar](../pillar-pricing.md). The flagship shows what
formal verification looks like when applied to a running empirical study, including
honest reporting of the leakage-tax map and the variance-risk-premium results. The
pricing pillar covers machine-checked formalizations of Harrison-Pliska, put-call
parity via Cox-Ross-Rubinstein, and the discrete variance-risk-premium identities,
along with a formal counterexample to a published perpetual futures specification.

Formal verification provides something that pen-and-paper proofs cannot: a guarantee
that every inference step is logically valid as stated, with all hypotheses explicit
and no implicit appeal to convention or context. The
[verification methodology](../how-we-verify.md) describes how Lean 4 and the mathlib
library achieve this and where the method's limits lie.

## Machine-checked theorems in asset pricing

### The discrete FTAP

`foundations/ftap-proofs/` is a Lean 4 formalization of the discrete Fundamental Theorem
of Asset Pricing (Harrison and Pliska, 1981): a finite securities market admits no
arbitrage if and only if there exists a probability measure equivalent to the physical
measure under which all discounted asset prices are martingales. 16 theorems, zero sorry.

The formalization states all hypotheses explicitly in the Lean type signature: finite
state space, finite trading horizon, a fixed filtration on the probability space, and
completeness of the trading strategy space. A reader who wants to know exactly what
conditions the theorem requires can read the type signature directly, without parsing
prose. The proof is a candidate for a mathlib contribution.

Reference: Harrison, J.M., and S.R. Pliska. "Martingales and Stochastic Integrals in
the Theory of Continuous Trading." *Stochastic Processes and Their Applications* 11,
no. 3 (1981): 215-260.

### Put-call parity via the binomial model

`foundations/options-proofs/` proves European put-call parity in the Cox-Ross-Rubinstein
binomial model:

$$C - P = S_0 - K \cdot (1+r)^{-T}$$

The proof constructs an explicit replicating portfolio for the call-minus-put position
and invokes the FTAP from `foundations/ftap-proofs/` to conclude that two portfolios with
identical payoffs must have identical prices in any arbitrage-free market. The formal
statement specifies precisely which version of the binomial model is assumed (one risky
asset, one bond, no dividends, frictionless trading) and how the risk-neutral measure
is constructed. 31 theorems, zero sorry.

Reference: Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified
Approach." *Journal of Financial Economics* 7, no. 3 (1979): 229-263.

### Discrete variance-risk-premium identities

`extensions/vrp-proofs/` proves the discrete pricing identities behind the variance risk
premium on the CRR tree, citing `options-proofs/`. The replicating portfolio is proved
to reproduce any terminal-price payoff at maturity on every path. The premium decomposes
exactly as the discounted gap between the risk-neutral and physical expectations, positive
precisely when the risk-neutral measure values the payoff above the physical one.

Two tempting claims are deliberately not made, with the reasons recorded in the proof.
A convexity shortcut that would sign the premium from the payoff's shape alone is false
on a fixed tree, shown by a numerical counterexample constructed and proved in Lean.
The gamma-weighted variance-gap profit identity is vacuous in a complete binomial market,
where the hedge is perfect and the hedging-error profit is zero. 12 theorems, zero sorry.

The empirical companion is the [variance-risk-premium study](../pillar-research-integrity.md)
in the research pipeline.

### A formal counterexample in perpetual futures pricing

`extensions/perpetual-proofs/` contains ten theorems including a formal counterexample.
The He-Manela specification of the no-arbitrage funding rate for perpetual futures is
shown to admit arbitrage under the hypotheses stated in that paper. The corrected
specification follows Ackerer, Hugonnier, and Jermann (2025). The counterexample is
machine-checked: Lean verifies that the He-Manela formula, under the stated conditions,
produces a price that allows a riskless profit.

Formal counterexamples to published specifications are uncommon in the finance
formalization literature. This result illustrates what machine-checked proofs add
beyond peer review: a proof assistant will reject a subtly flawed argument that a
careful human reader might accept.

Reference: Ackerer, D., J. Hugonnier, and R. Jermann. "Perpetual Futures Pricing."
*Mathematical Finance* (2025).

## Signal measurability and the point-in-time discipline

The [Research Integrity flagship](../pillar-research-integrity.md) adds a
measure-theoretic contribution directly relevant to empirical asset pricing. The
`research-pipeline` module proves that the 12-1 momentum signal is adapted to the
natural filtration of the price process (`momentumSignal_adapted`) and that the
variance-risk-premium signal is adapted to the joint filtration of prices and implied
volatility (`vrpSignal_adapted`). These are machine-checked proofs that the signals
use only what was knowable at decision time.

Paired with these proofs is the leakage-tax map, an empirical study measuring how
much apparent backtest alpha is a data look-ahead artifact across several macroeconomic
series. The result is honest: the binding axis is signal functional form, not revision
magnitude. A standardized, clipped signal is structurally immune; a hard threshold on
the same data is exposed, though modestly and regime-dependently.

## Explicit hypotheses as a research discipline

One contribution that runs across all subprojects is the discipline of making hypotheses
explicit. In the Lean formalization, every assumption that a textbook might state
informally ("assume frictionless markets," "assume the probability space is finite") must
be written as a formal type-class constraint or function argument. This forces a precision
that paper proofs often lack.

For researchers interested in the scope and limitations of classical asset-pricing results,
the type signatures of the theorems in this monorepo provide a precise account of what
each result requires.

## Entry points

- Research integrity, leakage-tax map, and VRP study: [pillar-research-integrity.md](../pillar-research-integrity.md)
- Pricing theorems (FTAP, put-call parity, VRP, perpetual futures): [pillar-pricing.md](../pillar-pricing.md)
- Verification methodology: [how-we-verify.md](../how-we-verify.md)
- Optimization theorems (PGD, projection, shrinkage): [pillar-optimization.md](../pillar-optimization.md)
- AI decision invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
