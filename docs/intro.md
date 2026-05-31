# EigenQ Research Series

The central question in quantitative research is not "what does the model say?" It is "should we trust it?" Standard testing tells you the code ran. Formal verification tells you the code is correct, as a machine-checked mathematical theorem.

Every project in the EigenQ Research Series takes a named result from financial theory, or a deployed decision system, and makes it formally verifiable. The theorem statement is the specification. The Lean 4 proof is the test. Zero `sorry` on main means no gaps.

## What this means in practice

A proof in Lean 4 is checked by a small, independently audited kernel. When a theorem carries zero `sorry`, every inference step has been verified, not sampled and not spot-checked. The result either compiles or it does not.

This is different from unit tests, which check behavior on selected inputs. It is different from type checking, which rules out a class of runtime errors. Formal verification rules out all counterexamples to the stated theorem, within the model as defined.

The honest caveat: a proof guarantees the theorem as stated, not that the model faithfully represents reality. Whether the model captures the right phenomenon is a separate question, answered by economic reasoning and empirical evidence, not by Lean. The proofs here are explicit about what they assume and what they conclude. See [How we verify](how-we-verify.md) for the method and its limits.

## Three pillars

**[No-Arbitrage Pricing](pillar-pricing.md).** The arc from the Fundamental Theorem of Asset Pricing through derivative pricing to perpetual futures. The discrete Harrison-Pliska theorem (complete, zero sorry) underlies put-call parity via the Cox-Ross-Rubinstein model (complete, zero sorry) and perpetual futures no-arbitrage pricing (complete, zero sorry).

**[Verified Optimization](pillar-optimization.md).** Formally verified projected gradient descent: convergence, projection correctness, and covariance shrinkage proofs (all complete, zero sorry), paired with seven stress scenarios where standard solvers fail and the verified solver holds.

**[Verified AI Decision Systems](pillar-ai-systems.md).** A multi-agent mortgage pipeline whose routing decisions are recorded and checked against Lean 4 invariants. Formal auditability for deployed systems built on large language models.

## Start here

Choose the entry point that matches your background:

- [For formal methods researchers and the Lean/mathlib community](audience/formal-methods.md)
- [For quantitative researchers and practitioners](audience/quant-researchers.md)
- [For finance academics in asset pricing and derivatives](audience/finance-academics.md)
- [For asset managers, risk managers, and compliance](audience/asset-managers.md)
- [For engineers building verified quantitative infrastructure](audience/engineering-leaders.md)
