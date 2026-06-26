# For Asset Managers, Risk, and Compliance

If you manage portfolios, oversee risk systems, or sit on a model governance committee,
the most relevant starting points are the
[Research Integrity flagship](../pillar-research-integrity.md) and the
[Verified Optimization pillar](../pillar-optimization.md).

The flagship demonstrates what trustworthy quantitative research looks like in practice:
a pipeline whose non-anticipation and leakage-prevention properties are machine-checked,
paired with empirical studies that report their limitations honestly, including the
conditions under which apparent alpha is an artifact of data look-ahead.

The optimization pillar covers portfolio constraints that the solver is formally proved
to respect: budget feasibility and the no-leverage constraint, held under numerical stress
inputs that cause unverified solvers to produce infeasible results.

## The governance gap in quantitative systems

Most quantitative systems are validated through backtesting and unit testing. These
approaches have well-known limits: a backtest covers the scenarios that were anticipated;
a unit test covers the inputs that were written. Neither provides a guarantee that a
solver will remain within its stated constraints under every possible input, or that a
pipeline will not inadvertently use data that was not knowable at decision time.

Formal verification provides a different kind of assurance. A machine-checked proof that
a solver satisfies a constraint is not a claim about behavior on a sample of inputs: it
is a mathematical guarantee that holds for every input satisfying the stated hypotheses.
The [verification methodology](../how-we-verify.md) explains what this means in practice
and where the limits of that assurance lie.

## A pipeline proved non-anticipating

The `research-pipeline` module is a full research-desk workflow, and its trust-critical
properties are machine-checked:

- The backtester is proved non-anticipating: a position built from a non-anticipating
  signal cannot depend on the future.
- The out-of-sample split is proved unable to leak a training label into the test window
  when the embargo is at least the label horizon.
- The signal map is proved adapted to the natural filtration of the price process, the
  measure-theoretic form of "uses only what was knowable at this time."

What is rigorous but not formally verified: the statistical layer and all profit-and-loss
economics. The report states the verified and unverified boundary explicitly.

The [leakage-tax map](../pillar-research-integrity.md) addresses a related governance
concern: even a perfectly non-anticipating pipeline can be contaminated if the values it
reads were later revised. The study measures this on real data across CFTC positioning,
EIA gas storage, and nonfarm payrolls, and finds that the binding axis is signal
functional form. A standardized, clipped signal is structurally immune; a hard threshold
on the same data is exposed. For model governance, this means that data look-ahead risk
is not uniform across signal designs, and the risk can be bounded.

## Portfolio constraints the solver cannot violate

The [Verified Optimization pillar](../pillar-optimization.md) covers a portfolio solver
whose constraint-satisfaction properties are formally proved.

The constraints covered: the budget constraint (portfolio weights sum to one) and the
no-leverage constraint (each weight is nonnegative). The Lean proof of projection
correctness establishes that the simplex projection step always returns a weight vector
satisfying both constraints, regardless of the gradient step that precedes it. A solver
whose projection step is proved correct cannot produce infeasible weights, even under
numerical inputs that would cause a floating-point solver to violate the constraints.

The `foundations/portfolio-proofs/` subproject runs seven empirical stress scenarios comparing
the verified solver against SciPy SLSQP, SciPy trust-constr, and Gurobi. The scenarios
are designed to expose constraint violations under conditions where unverified solvers
have historically produced infeasible results, including near-singular covariance matrices
and correlated stress shocks.

For model governance purposes, the formal proof provides documentation of what the solver
guarantees and under what conditions. The proof can be audited by any reader with access
to the Lean source, without relying on proprietary internal documentation.

## AI decision pipelines with formally checked routing rules

The [Verified AI Decision Systems pillar](../pillar-ai-systems.md) covers
`extensions/mortgage-proofs/`, a multi-agent pipeline for processing structured decisions
using a LangGraph orchestration layer.

The key governance feature is the `DecisionRecord` contract. Every routing decision made
by the AI agents is serialized as a `DecisionRecord` JSON object before it is acted upon.
The Lean invariant checker (`lake exe verify-trace`) reads the sequence of decision
records and verifies that each one satisfies the formal invariants: the stated eligibility
conditions are met, the routing is consistent with the declared rules, and no decision
violates the integrity constraints.

Compliance with routing rules is not enforced by code review of the AI agent's internal
logic, which may be opaque, but by a machine-checkable audit trail. An auditor can
re-run the invariant checker on any logged decision sequence and obtain a machine-readable
verdict. The pattern generalizes to any decision pipeline where auditability is required.

## Pricing results for derivatives risk

The [No-Arbitrage Pricing pillar](../pillar-pricing.md) provides machine-checked proofs
of results that underpin derivatives pricing:

- The discrete Fundamental Theorem of Asset Pricing: no arbitrage is equivalent to the
  existence of a risk-neutral measure. Every hypothesis about market structure is stated
  precisely in the proof, not buried in prose.
- Put-call parity for European options in the CRR binomial model: C - P = S0 - K/(1+r)^T,
  proved by constructing the replicating portfolio.
- Perpetual futures no-arbitrage conditions, including a formal demonstration that a
  previously published specification was incorrect.

## Entry points

- Research integrity, non-anticipation, and leakage: [pillar-research-integrity.md](../pillar-research-integrity.md)
- Portfolio solver proofs and stress scenarios: [pillar-optimization.md](../pillar-optimization.md)
- AI decision pipeline invariants and audit trail: [pillar-ai-systems.md](../pillar-ai-systems.md)
- Pricing results with explicit hypotheses: [pillar-pricing.md](../pillar-pricing.md)
- Verification methodology: [how-we-verify.md](../how-we-verify.md)
