# For Quant Developers and Engineering Leaders

If you lead teams that build or maintain quantitative production systems, this
page describes the engineering architecture of the EigenQ Research Series:
the Lean-to-Cython pipeline, the integer arithmetic contract that closes the
gap between proofs and execution, and the reproducibility infrastructure.

## The core engineering problem this project addresses

Formally proved properties are only useful if the proved code runs in production.
The standard gap between a verified specification and a deployed system is the
FFI boundary: the proof is about a mathematical model, and the deployed code is
a different program written in a different language.

This project closes that gap by design. The [verification methodology](../how-we-verify.md)
describes the full pipeline. The short version: proofs are written in Lean 4 over
integers; the Python and Cython execution layer uses the same integer representation;
and the FFI contract is auditable because the representation is the same on both
sides.

## Basis-point integer arithmetic: why it matters

All prices and payoffs in the quant-core library are represented as integers
scaled by 10,000 (one unit equals one basis point, or 0.01%). This is not a
style convention: it is the mechanism that makes the proof-arithmetic and the
machine-arithmetic identical.

Floating-point arithmetic is non-associative. On any modern processor, the result
of summing a large array of floating-point numbers depends on the order of the
additions. In a portfolio weight calculation or a constraint check, this means
that the "correct" result is not well-defined without specifying the exact
computation sequence. Proofs about floating-point programs are therefore proofs
about a specific execution path, not about the algorithm in general.

Integer arithmetic does not have this problem. The sum of a sequence of integers
is the same regardless of the order of additions, and the result is exact. The
Lean proofs in this monorepo are proved over integers; the Cython extension
modules use the same integer representation; and the Python layer converts to
floating-point only at the output boundary, where the precision requirements are
specified and bounded.

The practical consequence: when the Lean proof says the projection step satisfies
the budget constraint, that guarantee applies to the number that the Cython code
actually computes, not to an approximation of it. Details are at
[how-we-verify.md](../how-we-verify.md).

## The Lean-to-Cython pipeline

The optimization pillar ([pillar-optimization.md](../pillar-optimization.md)) is
the best illustration of the pipeline architecture:

1. `foundations/optimization-proofs/` proves abstract properties of projected gradient descent
   in Lean 4: projection correctness, the descent lemma, convergence under the
   step-size condition, and shrinkage PSD preservation. (The dual-bisection
   projection is O(N log N), an implementation property rather than a theorem.)
2. `foundations/portfolio-proofs/` instantiates the abstract solver for the portfolio problem
   (simplex constraint, long-only constraint) and connects the Lean proofs to a
   Cython implementation via the integer FFI contract.
3. Seven empirical stress scenarios run the Cython solver against SciPy SLSQP,
   SciPy trust-constr, and Gurobi on inputs designed to expose constraint violations
   and numerical drift.

For an engineering leader evaluating this architecture, the key question is: where
is the trust boundary? The answer is explicit: the Lean proofs establish properties
of the abstract algorithm; the Cython code implements that algorithm with the same
integer arithmetic; the scenarios verify that the implementation behaves as the
proof predicts on realistic inputs. The trust boundary is the FFI contract, and it
is documented precisely.

## The AI decision pipeline: verifiable audit trails

The AI systems pillar ([pillar-ai-systems.md](../pillar-ai-systems.md)) covers
`extensions/mortgage-proofs/`, a LangGraph multi-agent pipeline where every routing decision
is recorded as a `DecisionRecord` JSON object and checked against Lean 4 invariants
via a command-line verifier (`lake exe verify-trace`).

From an engineering perspective, this is a general pattern for building AI systems
with auditable decision logic:

- The agents themselves may be LLM-driven and not fully interpretable.
- Every decision the agents make is serialized in a standard format before it
  takes effect.
- A separate, formally verified checker reads the decision log and flags any
  decision that violates the stated invariants.

This separates the concerns of AI capability (handled by the agents) and rule
compliance (handled by the verified checker). The checker is small, auditable,
and provably correct. The agents can be updated, retrained, or replaced without
touching the checker.

## CI infrastructure: zero-sorry gate

The main branch is protected by a CI gate that rejects any commit containing a
sorry in any Lean source file. The grep pattern used:

```bash
grep -rn '^\s*sorry\b' --include="*.lean" <subdir>/
```

This catches indented sorrys, sorry inside docstrings, and sorry introduced by
automated refactoring. An empty result from this command is the production-ready
criterion for a Lean proof.

Python quality gates run `mypy --strict` on all source in `src/`. Type errors
block merge.

## Entry points

- Verification methodology and FFI contract: [how-we-verify.md](../how-we-verify.md)
- Optimization pipeline and stress scenarios: [pillar-optimization.md](../pillar-optimization.md)
- AI decision pipeline and audit trail pattern: [pillar-ai-systems.md](../pillar-ai-systems.md)
- Pricing proofs (for the derivatives pricing layer): [pillar-pricing.md](../pillar-pricing.md)
