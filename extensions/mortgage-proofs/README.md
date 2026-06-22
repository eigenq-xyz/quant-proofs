# mortgage-proofs

> An LLM multi-agent pipeline for mortgage application processing where **every routing decision is checked against formal invariants in Lean 4**. The agents propose; the verifier disposes. Decisions that violate the debt-to-income bound or predatory-lending rules are caught by a machine-checked checker, not by hoping the prompt held. Zero `sorry` on the Lean side, provider-agnostic on the LLM side.

[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it is and why

A LangGraph multi-agent system routes a mortgage application through four specialized roles (intake, risk, compliance, underwriter). Each agent records its routing decision as a structured `DecisionRecord`, and the resulting trace is validated against formal invariants written in Lean 4 via `lake exe verify-trace`.

The point is auditability. When an LLM makes a consequential, regulated decision, "the model usually gets it right" is not a control. Here the agents' reasoning is reduced to a decision trace, and a verifier with a machine-checked specification confirms the trace satisfies the rules (DTI bound, predatory-lending constraints) or reports exactly which obligation failed. The LLM is the proposer; the Lean checker is the gate.

## How it works

```text
MortgageApplication (JSON)
    |
    v
LangGraph Orchestrator
    |-- IntakeAgent          document completeness
    |-- RiskAssessmentAgent  DTI, LTV, credit score   (parallel)
    |-- ComplianceAgent      regulatory rules          (parallel)
    +-- UnderwriterAgent     final decision
    |
    v
DecisionRecord (JSON)  --->  Lean 4 checker (lake exe verify-trace)
                                  |
                                  v
                       VerificationResult { passed, violations }
```

The `DecisionRecord` JSON schema (`schemas/decision_record.json`) is the single source of truth for the Python/Lean interface. The LLM provider is abstracted: set `LLM_MODEL=anthropic/claude-sonnet-4-6`, `openai/gpt-4o`, or a per-agent override via environment variables.

## Setup

1. Install [elan](https://github.com/leanprover/elan) (Lean toolchain manager) and [uv](https://docs.astral.sh/uv/).
2. Copy `.env.example` to `.env` and fill in your API key(s).

```bash
make install      # install Python dependencies
make lean-build   # build the Lean verifier
```

## Usage

```bash
# Process an application end to end
vma process path/to/application.json

# Run only the Lean verifier on an existing decision record
vma verify path/to/record.json

# Print the DecisionRecord JSON schema
vma schema dump
```

Or run the HTTP API:

```bash
uvicorn mortgage_proofs.app.api:app --reload
# POST /process   full pipeline
# POST /verify    Lean verification only
# GET  /health    checks Lean binary availability
```

## Development

```bash
make lint       # ruff + mypy --strict
make test       # unit tests (mocked LLM + Lean)
make test-all   # includes integration tests (requires live credentials)
make schema     # regenerate schemas/decision_record.json
```

## License

Apache License 2.0.
