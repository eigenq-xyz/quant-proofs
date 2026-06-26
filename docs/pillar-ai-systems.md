# Verified AI Decision Systems

Large language models are being deployed as decision-makers in consequential domains:
underwriting, compliance review, risk assessment. The standard accountability mechanism is
logging: record what the model decided and why it said so. Logging is necessary but not
sufficient. A log can record a decision that violates a rule, and no amount of prose policy
documentation prevents it. This pillar addresses that gap.

The thesis is that formal auditability is achievable for LLM-driven systems: not by
constraining what the model can say, but by checking what it decided against
machine-verified rules after every run, at every decision point.

---

## `mortgage-proofs`: Formally Auditable Multi-Agent Mortgage Processing

A mortgage application moves through four agents implemented in LangGraph: intake (document
parsing and structuring), risk (credit and collateral assessment), compliance (regulatory
rule checking), and underwriter (final approve/deny decision with conditions). The agents
are provider-agnostic; any language model backend can be substituted without changing the
pipeline structure or the verification layer.

### What the system does

Each agent produces a structured `DecisionRecord` at its decision point. The record captures
the agent's routing choice and the inputs it acted on. After all four agents have run, the
full trace of `DecisionRecord` objects is checked against Lean 4 invariants using
`lake exe verify-trace`. The invariants encode rules that any valid mortgage decision trace
must satisfy. A subset of the invariants proved in `MortgageProofs/Invariants.lean`:

- DTI caps by loan type: conventional loans require DTI below 0.43, FHA below 0.50, VA below
  0.41, jumbo below 0.38. An approval that violates the cap for its loan type is a violation.
- LTV caps by loan type: conventional loans at LTV above 0.97, FHA above 0.965, jumbo above
  0.80 are violations.
- Credit score floors by loan type: conventional below 620, FHA and VA below 580, jumbo below
  700 are violations.
- Escalation completeness: any escalation decision must carry a non-empty escalation reason.
- Record consistency: the record's declared final outcome must match the last decision in the
  trace.

Thirteen theorems are proved in Lean 4, zero sorry. The theorems cover structural properties
of each invariant (a rejection never triggers an approval-gated cap, an escalation with a
non-empty reason passes the escalation invariant) and completeness of the checker (a passing
record provably satisfies every rule). The `checkRecord` function is proved correct against
the full invariant list.

### Why formal checking matters here

An LLM agent can produce fluent, plausible-sounding reasoning while making a decision that
violates a hard rule. Prompt engineering and instruction tuning reduce this risk but do not
eliminate it. The `verify-trace` step is not probabilistic: it either confirms that the trace
satisfies all invariants or it rejects the trace with a specific failure message and decision
ID. The Lean 4 invariants are machine-verified theorems, not prose descriptions that a reader
might interpret differently.

The result is a system where the decision audit trail is not just logged but formally
checked. The trace either passes the invariants or the run is flagged for human review. This
is a stronger accountability property than logging alone, and it does not require replacing
the LLM agents with rule-based systems.

### The honest boundary

What is formally verified: the invariant definitions themselves, the structural properties of
each invariant, and the completeness of the checker. These are proved as Lean 4 theorems,
zero sorry.

What is not formally verified: the LLM agents' reasoning, the language model's compliance
with instructions, or the content of any individual routing decision. The LLM proposes; the
Lean-checked invariants gate.

### Connection to the EigenQ verification layer

The verification infrastructure uses the same Lean 4 toolchain as the pricing and
optimization proofs. `lake exe verify-trace` is an executable built from the same
`lakefile.toml` that builds the proof libraries. This is deliberate: a single formal
verification layer spans mathematical proofs and runtime system auditing.

[Read the pipeline and invariants](https://github.com/eigenq-xyz/quant-proofs/tree/main/extensions/mortgage-proofs)

---

## The broader pattern

`mortgage-proofs` demonstrates a design pattern that generalizes beyond mortgage processing:

1. Build the LLM pipeline to emit structured decision records at each routing point.
2. Express the rules the system must satisfy as Lean 4 invariants (proved theorems, not
   runtime assertions).
3. Run `verify-trace` on every trace before treating the decision as final.

The invariants are the only part that requires formal methods expertise. The agent pipeline
itself is standard LangGraph. The separation means the verification layer can be added to
an existing LLM pipeline without rewriting the agents.

This pattern is directly relevant to any domain where LLM decisions are subject to external
rules: regulatory compliance, credit decisions, automated trading controls, or clinical
triage. The mortgage pipeline is the proof of concept.
