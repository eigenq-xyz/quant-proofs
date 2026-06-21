# For Asset Managers, Risk, and Compliance

If you manage portfolios, oversee risk systems, or sit on a model governance
committee, this page describes the parts of the EigenQ Research Series that
address auditability, constraint enforcement, and the defensibility of
algorithmic decisions.

## The governance gap in quantitative systems

Most quantitative systems are validated through backtesting and unit testing.
These approaches have well-known limits: a backtest covers the scenarios that
were anticipated; a unit test covers the inputs that were written. Neither
provides a guarantee that a solver will remain within its stated constraints
under every possible input, or that an AI pipeline will always follow its
stated decision rules.

Formal verification provides a different kind of assurance. A machine-checked
proof that a solver satisfies a constraint is not a claim about behavior on
a sample of inputs: it is a mathematical guarantee that holds for every input
satisfying the stated hypotheses. The [verification methodology](../how-we-verify.md)
explains what this means in practice and where the limits of that assurance lie.

## Portfolio constraints that the solver cannot violate

The optimization pillar ([pillar-optimization.md](../pillar-optimization.md))
covers a portfolio solver whose constraint-satisfaction properties are formally
proved in Lean 4.

The constraints covered by the proofs are the budget constraint (portfolio
weights sum to one) and the no-leverage constraint (each weight is nonnegative).
The Lean proof of projection correctness establishes that the simplex projection
step always returns a weight vector that satisfies both constraints, regardless
of the gradient step that precedes it. A solver whose projection step is proved
correct cannot produce infeasible weights, even under numerical inputs that
would cause a floating-point solver to violate the constraints.

The `portfolio-proofs/` subproject runs seven empirical stress scenarios, comparing
the verified solver against SciPy SLSQP, SciPy trust-constr, and Gurobi. The
scenarios are designed to expose constraint violations under conditions (low
liquidity, correlated shocks, near-singular covariance matrices) where
unverified solvers have historically produced infeasible results.

For model governance purposes, the formal proof provides documentation of what
the solver guarantees and under what conditions. The proof can be audited by
any reader with access to the Lean source, without relying on proprietary
internal documentation.

## AI decision pipelines with formally checked routing rules

The AI systems pillar ([pillar-ai-systems.md](../pillar-ai-systems.md)) covers
`mortgage-proofs/`, a multi-agent pipeline for processing structured decisions
(in this case, mortgage applications) using a LangGraph orchestration layer.

The key governance feature is the `DecisionRecord` contract. Every routing
decision made by the AI agents is serialized as a `DecisionRecord` JSON object
before it is acted upon. The Lean invariant checker (`lake exe verify-trace`)
reads the sequence of decision records and verifies that each one satisfies
the formal invariants: the stated eligibility conditions are met, the routing
is consistent with the declared rules, and no decision violates the integrity
constraints.

This design means that compliance with routing rules is not enforced by
code review of the AI agent's internal logic (which may be opaque) but by
a machine-checkable audit trail. An auditor can re-run the invariant checker
on any logged decision sequence and obtain a machine-readable verdict.

The pattern is general: the same architecture (serialize decisions as records,
check records against formal invariants) can be applied to any decision pipeline
where auditability is required.

## Pricing results for derivatives risk

The pricing pillar ([pillar-pricing.md](../pillar-pricing.md)) provides
machine-checked proofs of results that underpin derivatives pricing:

- The discrete Fundamental Theorem of Asset Pricing (`ftap-proofs/`): no arbitrage
  is equivalent to the existence of a risk-neutral measure. This result, proved
  by Harrison and Pliska (1981), is the theoretical foundation for all derivatives
  pricing in a no-arbitrage framework.
- Put-call parity for European options in the CRR binomial model (`options-proofs/`):
  C - P = S0 - K/(1+r)^T, proved by constructing the replicating portfolio.
- Perpetual futures no-arbitrage conditions (`perpetual-proofs/`), including a
  formal demonstration that a previously published specification was incorrect.

For risk and compliance teams, the explicit-hypothesis discipline of the
formalizations is the relevant contribution: every assumption about market
structure and trading conditions is stated precisely in the proof, not buried
in prose.

## Entry points

- Verification methodology: [how-we-verify.md](../how-we-verify.md)
- Portfolio solver proofs and stress scenarios: [pillar-optimization.md](../pillar-optimization.md)
- AI decision pipeline invariants: [pillar-ai-systems.md](../pillar-ai-systems.md)
- Pricing results: [pillar-pricing.md](../pillar-pricing.md)
