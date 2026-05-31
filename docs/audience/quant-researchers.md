# For Quant Researchers and Practitioners

If you build or audit quantitative systems, this page describes the parts of the
EigenQ Research Series that address the guarantees practitioners care about most:
no look-ahead bias, no constraint drift, and reproducibility across environments.

## The core concern formal verification addresses

A backtest or optimization routine can appear to pass every manual test and still
contain a subtle error: a solver that silently drops a budget constraint under
numerical stress, a pricing formula that mixes up calendar conventions, a pipeline
that leaks future information through a lagged variable constructed incorrectly.
These failures are hard to catch with unit tests because they appear only in
specific market regimes or numerical edge cases.

Lean 4 proof provides a different kind of assurance. When a property is proved, it
holds for every input that satisfies the stated hypotheses, not just the inputs in
the test suite. The [verification methodology](../how-we-verify.md) explains how
that assurance is connected to the Python and Cython execution layer.

## The FFI contract: why basis-point arithmetic matters

The quant-core library represents all prices and payoffs as integers scaled by
10,000 (basis points). This is not a convention choice: it is a correctness
requirement. The Lean theorems are proved over integers; the Python and Cython
execution layer uses the same integer representation. As a result, the arithmetic
in the proof and the arithmetic in production are identical. There is no rounding
gap between the proved result and the computed result.

This matters for practitioners because floating-point summation is
non-associative: the order of operations can change the result by small amounts,
and those small amounts can accumulate in a portfolio rebalancing loop or a
constraint check. The basis-point contract eliminates that class of discrepancy.
Details are in [how-we-verify.md](../how-we-verify.md).

## Optimization guarantees the solver actually satisfies

The optimization pillar ([pillar-optimization.md](../pillar-optimization.md))
covers two subprojects:

**`optimization-proofs/`** proves nine theorems about the projected gradient
descent (PGD) algorithm at the abstract level:

- The projection onto the probability simplex is correct (the result is always
  feasible and is the nearest feasible point).
- The descent lemma holds: each step reduces the objective by a provable amount
  relative to the gradient step size.
- The dual-bisection projection runs in O(N log N) time and produces a result
  that satisfies the KKT conditions exactly.
- The shrinkage operator preserves positive semidefiniteness of a covariance
  matrix.

**`portfolio-proofs/`** connects those abstract guarantees to a PGD portfolio
solver and runs seven empirical stress scenarios, comparing results against
SciPy SLSQP, SciPy trust-constr, and Gurobi. The Lean proofs cover the solver's
structural properties; the scenarios demonstrate behavior on realistic market
data.

The constraint that the Lean proof covers is the budget constraint (weights sum
to one) and the no-leverage constraint (each weight is nonnegative). A solver
that is formally proved to respect these constraints cannot silently violate
them, even under numerical stress inputs that would cause a floating-point solver
to produce infeasible results.

## Pricing results with explicit hypotheses

The pricing pillar ([pillar-pricing.md](../pillar-pricing.md)) formalizes results
that underpin routine derivatives pricing:

- The discrete FTAP (`ftap-proofs/`) gives a machine-checked proof that no
  arbitrage is equivalent to the existence of an equivalent martingale measure.
  Every hypothesis is stated explicitly in the Lean type signature, so there is
  no ambiguity about what market conditions the result requires.
- Put-call parity (`options-proofs/`) is proved for the CRR binomial model via
  the FTAP: C - P = S0 - K/(1+r)^T. The proof is constructive: it exhibits the
  replicating portfolio.
- The perpetual-proofs subproject includes a formal counterexample showing that
  a published perpetual futures specification (He-Manela) admits arbitrage under
  its own stated conditions.

For practitioners who write pricing models, the explicit-hypothesis discipline is
the key contribution: it forces every assumption about market structure, trading
constraints, and the probability space to be stated in a form that a machine can
check.

## Entry points

- Verification methodology and the FFI contract: [how-we-verify.md](../how-we-verify.md)
- Optimization proofs and stress scenarios: [pillar-optimization.md](../pillar-optimization.md)
- Pricing results and explicit hypotheses: [pillar-pricing.md](../pillar-pricing.md)
- AI decision pipeline invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
