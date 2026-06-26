# For the Lean and Formal Methods Community

If you work in interactive theorem proving, type theory, or the formalization of
mathematics, this page orients you to what the EigenQ Research Series contributes
and where it sits relative to mathlib.

The primary entry point for the mathematics here is the
[No-Arbitrage Pricing pillar](../pillar-pricing.md), which contains the most
structurally interesting proof work: a Hahn-Banach separation argument for the
FTAP, a formal counterexample to a published finance specification, and a
standalone geometric-stopping-time library. The
[Research Integrity flagship](../pillar-research-integrity.md) adds the
measure-theoretic layer: machine-checked signal adaptedness and
filtration-measurability proofs over a natural price filtration.

## What this project is

The quant-proofs monorepo formalizes results from quantitative finance in Lean 4,
following mathlib conventions throughout. The goal is not to translate textbook
theorems into code for their own sake: every proof supports a claim made by a
running empirical system, and the CI gate on the main branch rejects any commit
that introduces a sorry. No theorem is marked admitted, and no build passes with
an outstanding sorry.

The verification methodology is described at [how-we-verify.md](../how-we-verify.md).

## Mathlib-candidate work

Two subprojects are designed as standalone mathlib contributions.

**`foundations/ftap-proofs/`** formalizes the discrete Fundamental Theorem of Asset Pricing
(Harrison and Pliska, 1981). The central result: a finite securities market is free
of arbitrage if and only if there exists an equivalent martingale measure. The proof
constructs both directions. The forward direction uses a compact convex separation
argument over the space of attainable payoffs: the no-arbitrage condition rules out
any nonnegative nonzero element of that subspace, and a Hahn-Banach-type
separation produces the martingale measure. The reverse direction constructs an
explicit arbitrage portfolio when no such measure exists. All measure-theoretic
hypotheses are explicit in the type signature. See the
[No-Arbitrage Pricing pillar](../pillar-pricing.md) for the full theorem list
(16 theorems, zero sorry).

**`extensions/stopped-time-proofs/`** formalizes the geometric probability mass function
and a `GeometricExpectation` operator over a discrete stopping time. This module
contains no financial content; it is designed as a self-contained mathlib
contribution. It is the load-bearing infrastructure for the perpetual futures
pricing theorems in `extensions/perpetual-proofs/`.

## Proof architecture worth examining

**Pricing pillar ([pillar-pricing.md](../pillar-pricing.md)):**

- `foundations/ftap-proofs/`: compact convex separation for the FTAP, 16 theorems.
- `foundations/options-proofs/`: put-call parity in the Cox-Ross-Rubinstein binomial model,
  citing the FTAP result from `foundations/ftap-proofs/`, 31 theorems.
- `extensions/vrp-proofs/`: discrete variance-risk-premium identities on the CRR tree.
  Includes two deliberately unmade claims, documented with machine-checked justifications:
  a convex-payoff shortcut is false on a fixed tree (numerical counterexample constructed
  and proved), and the gamma-variance-gap profit identity is vacuous in a complete market.
  12 theorems, zero sorry.
- `extensions/perpetual-proofs/`: a formal counterexample showing the He-Manela perpetual
  futures specification admits arbitrage under its stated hypotheses. The corrected
  specification follows Ackerer, Hugonnier, and Jermann (2025). Formal counterexamples
  of this kind are uncommon in the finance formalization literature. 10 theorems,
  zero sorry.

**Research Integrity flagship ([pillar-research-integrity.md](../pillar-research-integrity.md)):**

- `research-pipeline/`: signal adaptedness and filtration-measurability, proved for the
  12-1 momentum signal (`momentumSignal_adapted`) and the variance-risk-premium signal
  (`vrpSignal_adapted`), the latter over a joint price-and-implied-volatility filtration.
  Non-anticipation of the backtester and embargo-enforced OOS leakage prevention also
  proved here. 14 theorems, zero sorry.

**Optimization pillar ([pillar-optimization.md](../pillar-optimization.md)):**

- `foundations/optimization-proofs/`: projected gradient descent convergence, simplex
  projection correctness, and Ledoit-Wolf shrinkage PSD preservation. Standard convex
  optimization results, formalized to support the portfolio solver. 10 theorems, zero sorry.

## Zero-sorry discipline

The CI configuration rejects any push to main that introduces a sorry, including
sorrys inside docstrings (a subtlety that has caused false negatives in other
projects). Every theorem listed in the pillar pages is fully proved. The grep
command used in CI is:

```bash
grep -rn '^\s*sorry\b' --include="*.lean" <subdir>/
```

This catches indented sorrys that a simpler grep might miss.

## Entry points

- Proof methodology: [how-we-verify.md](../how-we-verify.md)
- Research integrity and signal measurability: [pillar-research-integrity.md](../pillar-research-integrity.md)
- Pricing theorems (FTAP, put-call parity, VRP, perpetual futures): [pillar-pricing.md](../pillar-pricing.md)
- Optimization theorems (PGD, projection, shrinkage): [pillar-optimization.md](../pillar-optimization.md)
- AI decision invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
