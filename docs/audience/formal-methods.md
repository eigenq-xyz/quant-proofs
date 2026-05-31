# For the Lean and Formal Methods Community

If you work in interactive theorem proving, type theory, or the formalization of
mathematics, this is the starting point for understanding what the EigenQ Research
Series contributes and where it sits relative to mathlib.

## What this project is

The quant-proofs monorepo formalizes results from quantitative finance in Lean 4,
following mathlib conventions throughout. The goal is not merely to translate
textbook theorems into code: every proof is machine-checked under a zero-sorry CI
gate on the main branch. No theorem is marked admitted, and no build passes with
an outstanding sorry.

The verification methodology is described in full at [how-we-verify.md](../how-we-verify.md).

## Mathlib-track work

Two subprojects are being prepared for upstream contribution to mathlib:

**`ftap-proofs/`** formalizes the discrete Fundamental Theorem of Asset Pricing
(Harrison-Pliska 1981). The central result is that a finite financial market
admits no arbitrage if and only if there exists an equivalent martingale measure.
The proof constructs both directions: the forward direction using a separating
hyperplane argument over the space of attainable payoffs, and the reverse direction
by direct construction of an arbitrage portfolio when no such measure exists. The
formalization makes all measure-theoretic hypotheses explicit and uses the mathlib
probability and measure theory library throughout. See the [No-Arbitrage Pricing
pillar](../pillar-pricing.md) for the full theorem list.

**`stopped-time-proofs/`** formalizes the geometric probability mass function and a
`GeometricExpectation` operator over a stopping time on a discrete filtered
probability space. This module contains no financial content and is designed as a
standalone mathlib contribution.

## Proof architecture worth examining

The pricing pillar ([pillar-pricing.md](../pillar-pricing.md)) has the most
structurally interesting proof work:

- `ftap-proofs/` uses a compact convex separation argument. The attainable payoff
  set is shown to be a linear subspace of the finite-dimensional real vector space
  of payoffs; the no-arbitrage condition rules out any nonnegative nonzero element
  of that subspace; a Hahn-Banach-type separation then produces the martingale
  measure.
- `options-proofs/` proves put-call parity and arbitrage-freeness for the
  Cox-Ross-Rubinstein binomial model, citing the FTAP result from `ftap-proofs/`
  as a dependency.
- `perpetual-proofs/` includes a formal counterexample: a published specification
  of perpetual futures pricing (He-Manela) is shown to admit arbitrage under the
  stated hypotheses. The corrected specification follows Ackerer-Hugonnier-Jermann
  (2025). Formal counterexamples of this kind are uncommon in the finance
  formalization literature.

The optimization pillar ([pillar-optimization.md](../pillar-optimization.md))
proves convergence properties of projected gradient descent: a descent lemma, a
projection correctness theorem, and a shrinkage positive-semidefiniteness result.
These are standard results in convex optimization, formalized here to support the
portfolio solver.

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
- Pricing theorems (FTAP, put-call parity, perpetual futures): [pillar-pricing.md](../pillar-pricing.md)
- Optimization theorems (PGD, projection, descent): [pillar-optimization.md](../pillar-optimization.md)
- AI decision invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
