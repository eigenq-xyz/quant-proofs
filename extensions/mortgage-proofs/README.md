# mortgage-proofs

A LangGraph multi-agent mortgage pipeline whose routing decisions are recorded as
structured JSON and validated against machine-checked Lean 4 invariants via
`lake exe verify-trace`: auditable AI for high-stakes decisions.

[![Python CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/python-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it does

A LangGraph orchestrator routes a mortgage application through four specialized
agents (intake, risk assessment, compliance, underwriter). Each agent records its
routing decision as a `DecisionRecord` JSON object. After the pipeline completes,
`lake exe verify-trace` feeds the full trace to a Lean 4 checker that confirms
every decision satisfies the formal invariants or reports exactly which obligation
failed.

```text
MortgageApplication (JSON)
    |
    v
LangGraph Orchestrator
    |-- IntakeAgent           document completeness
    |-- RiskAssessmentAgent   DTI, LTV, credit score   (parallel)
    |-- ComplianceAgent       regulatory rules          (parallel)
    +-- UnderwriterAgent      final decision
    |
    v
DecisionRecord (JSON)  -->  lake exe verify-trace
                                  |
                                  v
                       VerificationResult { passed, violations }
```

The key claim: when an LLM makes a consequential, regulated decision, "the model
usually gets it right" is not a control. Here the Lean checker holds the
specification; a trace that violates the DTI bound or predatory-lending invariants
is rejected with a precise violation report, not a probabilistic hope.

The Lean invariants are proved complete, zero `sorry`. The statistical and
reasoning layers are LLM-generated and not formally verified.

## Build

Requires [elan](https://github.com/leanprover/elan) and [uv](https://docs.astral.sh/uv/).

```bash
# From extensions/mortgage-proofs/
uv sync --all-extras            # Python dependencies

cd lean && lake exe cache get   # fetch mathlib cache
cd lean && lake build           # compile the Lean verifier
```

## Test

```bash
# Unit tests (no LLM key or Lean binary required)
cd extensions/mortgage-proofs
uv run pytest -m "not integration" -q

# Type check and lint
uv run mypy src/ --strict
uv run ruff check src/ tests/

# Zero-sorry check on the Lean invariants
grep -rn 'sorry' --include="*.lean" lean/
# (empty output means zero sorry)

# Run the Lean verifier on a sample trace
cd lean && lake exe verify-trace ../tests/fixtures/sample_record_valid.json
```

## Project layout

| Path | What it is |
|------|------------|
| `lean/MortgageProofs/Invariants.lean` | Formal invariant definitions (DTI bound, predatory-lending rules) |
| `lean/MortgageProofs/Theorems.lean` | Proof obligations: 13 theorems, zero `sorry` |
| `lean/MortgageProofs/Checker.lean` | Trace checker: validates a `DecisionRecord` sequence |
| `lean/MortgageProofs/Types.lean` | Lean types mirroring the Python domain models |
| `lean/Main.lean` | `lake exe verify-trace` entry point |
| `src/mortgage_proofs/orchestrator/` | LangGraph agent graph (intake, risk, compliance, underwriter) |
| `src/mortgage_proofs/lean_bridge/` | Python-to-Lean trace serialization and runner |
| `src/mortgage_proofs/record/` | `DecisionRecord` dataclass |
| `schemas/decision_record.json` | JSON schema: the single source of truth for the Python/Lean interface |
| `tests/` | Unit tests (mocked LLM and Lean) plus integration tests |

## LLM provider

The LLM provider is fully abstracted. Set `LLM_MODEL` in `.env` (see
`.env.example`) to `anthropic/claude-sonnet-4-6`, `openai/gpt-4o`, or any
per-agent override. No provider is hardcoded in `src/`.

## License

Apache 2.0, compatible with mathlib for upstream contribution.
