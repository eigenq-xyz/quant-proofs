# Verified AI Decision Systems

Large language models are being deployed as decision-makers in consequential domains:
underwriting, compliance review, risk assessment. The standard accountability mechanism is
logging: record what the model decided and why it said so. Logging is necessary but not
sufficient. A log can record a decision that violates a rule, and no amount of prose policy
documentation prevents it. This pillar addresses that gap.

The thesis is that formal auditability is achievable for LLM-driven systems: not by
constraining what the model can say, but by checking what it decided against
machine-verified rules after the fact, at every decision point.

---

## `mortgage-proofs`: Formally Auditable Multi-Agent Mortgage Processing

A mortgage application moves through four agents, implemented in LangGraph: intake
(document parsing and structuring), risk (credit and collateral assessment), compliance
(regulatory rule checking), and underwriter (final approve/deny decision with conditions).
The agents are provider-agnostic: any language model backend can be substituted without
changing the pipeline structure or the verification layer.

### What the system does

Each agent produces a structured `DecisionRecord` at its decision point. The record captures
the agent's routing choice and the inputs it acted on. After all four agents have run, the
full trace of `DecisionRecord` objects is checked against Lean 4 invariants using
`lake exe verify-trace`. The invariants encode rules that any valid mortgage decision trace
must satisfy, for example that a compliance agent cannot forward an application that has
failed a regulatory check, or that an underwriter approval must be preceded by a passing
risk assessment.

### Why formal checking matters here

An LLM agent can produce fluent, plausible-sounding reasoning while making a decision that
violates a hard rule. Prompt engineering and instruction tuning reduce this risk but do not
eliminate it. The `verify-trace` step is not probabilistic: it either confirms that the trace
satisfies all invariants or it rejects the trace with a specific failure. The Lean 4
invariants are machine-verified theorems, not prose descriptions that a reader might
interpret differently.

The result is a system where the decision audit trail is not just logged but formally
checked: the trace either passes the invariants or the run is flagged for human review.
This is a stronger accountability property than logging alone, and it does not require
replacing the LLM agents with rule-based systems.

### Connection to the pricing pillar

The verification infrastructure here uses the same Lean 4 toolchain as the pricing proofs.
`lake exe verify-trace` is an executable built from the same `lakefile` that builds the
proof libraries. This is deliberate: the EigenQ Research Series uses a single formal
verification layer across both mathematical proofs and runtime system auditing.

[Read the pipeline and invariants](https://github.com/eigenq-xyz/quant-proofs/tree/main/mortgage-proofs)

---

## The broader pattern

`mortgage-proofs` demonstrates a design pattern that generalizes beyond mortgage processing:

1. Build the LLM pipeline to emit structured decision records at each routing point.
2. Express the rules the system must satisfy as Lean 4 invariants (proved theorems, not
   runtime assertions).
3. Run `verify-trace` on every trace before treating the decision as final.

The invariants are the only part that requires formal methods expertise. The agent pipeline
itself is standard LangGraph. The separation means the verification layer can be added to
an existing LLM system without rewriting the agents.

This pattern is directly relevant to any domain where LLM decisions are subject to external
rules: regulatory compliance, credit decisions, automated trading controls, or clinical
triage. The mortgage pipeline is the proof of concept.
