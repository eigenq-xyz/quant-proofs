# mortgage-proofs

A multi-agent mortgage pipeline (LangGraph) where LLM agents make the actual routing
decision at each stage of a rule-governed workflow. An independent Lean 4 layer,
proved correct in Lean 4 rather than only tested, checks every agent decision against
the workflow's codified rules: `lake exe verify-trace` runs that checker against the
recorded trace and feeds any violation back for revision.

[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

A LangGraph orchestrator routes a mortgage application through four agents (intake,
risk assessment, compliance, underwriter). Each agent records its routing decision as
a `DecisionRecord` JSON object (a structured log entry: what the agent decided, and why).
`lake exe verify-trace` feeds the full trace to a Lean 4 checker that confirms every
decision satisfies the formal invariants (the codified rules, proved to hold rather than
merely tested), or reports exactly which obligation failed and escalates for human
review.

| Guarantee | Theorem |
|-----------|---------|
| A clean (empty-violations) check implies every decision in the trace is clean | `checkRecord_empty_implies_clean_decisions` |
| A clean check implies the outcome is consistent with the decision record | `checkRecord_empty_implies_consistent_outcome` |

13 theorems total, proved with no unproven steps: `sorry` is Lean's placeholder tactic for
"assume this holds, prove it later," and a repo-wide check confirms none remain
(`grep -rn 'sorry' --include="*.lean" lean/`).

## What it doesn't claim

A trace that fails the check is rejected with a precise violation report; a trace that
passes only proves the two theorems above, not that the underlying LLM reasoning was
sound. `ReasoningStep` content fields are parsed but never verified; they round-trip
as data. The LLM-generated routing and risk-assessment logic in `src/` is not proved
correct; only the invariant check on the resulting trace is.

The invariants (`dtiCapConventional`, `creditFloorFHA`, `ltvCapJumbo`, and others in
`Invariants.lean`) are underwriting business rules with plausible numeric thresholds
(DTI, LTV, credit-score caps by loan type), not statutes. Nothing here cites TILA,
RESPA, ECOA, or any state mortgage code; there is no claim of regulatory compliance.

## Build and verify

Requires [elan](https://github.com/leanprover/elan) and [uv](https://docs.astral.sh/uv/).

```bash
cd extensions/mortgage-proofs
uv sync --all-extras
cd lean && lake exe cache get && lake build
grep -rn 'sorry' --include="*.lean" lean/         # empty = clean
cd lean && lake exe verify-trace ../tests/fixtures/sample_record_valid.json
```

Full build/test matrix (mypy, ruff, integration tests): see `CLAUDE.md`.

## LLM provider

Fully abstracted. Set `LLM_MODEL` in `.env` (see `.env.example`) to
`anthropic/claude-sonnet-4-6`, `openai/gpt-4o`, or any per-agent override. No provider
is hardcoded in `src/`.

## License

Apache 2.0.
