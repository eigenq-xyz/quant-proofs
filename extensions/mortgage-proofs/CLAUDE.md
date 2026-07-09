# CLAUDE.md: mortgage-proofs

LangGraph multi-agent mortgage pipeline where an independent Lean 4 layer, proved
correct rather than only tested, checks every agent decision against codified
underwriting rules. Each routing decision is recorded as a `DecisionRecord` JSON (a
structured log of what was decided and why) and checked by `lake exe verify-trace`.

## Build

```bash
# Python (from extensions/mortgage-proofs/)
uv sync --all-extras

# Lean verifier (from extensions/mortgage-proofs/lean/)
lake exe cache get
lake build
```

## Test

```bash
# Unit tests (no LLM key or Lean binary required)
uv run pytest -m "not integration" -q

# Integration tests (require Lean binary + LLM API key)
uv run pytest -m integration -q

# Type check
uv run mypy src/ --strict

# Lint
uv run ruff check src/ tests/

# Zero-sorry check (sorry is Lean's "not proved yet" placeholder; none should remain)
grep -rn 'sorry' --include="*.lean" lean/

# Run verifier on sample trace
cd lean && lake exe verify-trace ../tests/fixtures/sample_record_valid.json
```

## Architecture

Data flow:

```text
MortgageApplication (JSON)
    |
    v
LangGraph Orchestrator
    |-- IntakeAgent           document completeness
    |-- RiskAssessmentAgent   DTI, LTV, credit score   (parallel)
    |-- ComplianceAgent       underwriting rule checks  (parallel)
    +-- UnderwriterAgent      final decision
    |
    v
DecisionRecord (JSON)  -->  lake exe verify-trace
                                  |
                                  v
                       VerificationResult { passed, violations }
```

Module layout:

```
extensions/mortgage-proofs/
  src/mortgage_proofs/
    app/              FastAPI entry point (POST /process, POST /verify, GET /health)
    domain/           Domain models: Applicant, Property, LoanRequest, etc.
    lean_bridge/      Trace serialization + verify-trace runner
    orchestrator/     LangGraph graph: intake -> risk+compliance (parallel) -> underwriter
    record/           DecisionRecord dataclass
  lean/
    MortgageProofs/
      Types.lean      Lean types mirroring Python domain models
      Invariants.lean Formal invariant definitions (DTI/LTV/credit-score underwriting caps)
      Theorems.lean   13 proof obligations, zero sorry
      Checker.lean    Validates a DecisionRecord sequence against invariants
      Parser.lean     JSON-to-Lean type parser
    Main.lean         lake exe verify-trace entry point
  schemas/
    decision_record.json  JSON schema: canonical Python/Lean interface
  tests/
    domain/           Unit tests for domain models and validators
    lean_bridge/      Unit tests for trace serialization and runner
    orchestrator/     Unit tests for agent routing logic
    integration/      End-to-end tests (require live Lean binary + LLM key)
```

## LLM provider

The provider is intentionally abstracted. Set `LLM_MODEL` in `.env` (see
`.env.example`). Do not hardcode any provider or model string in `src/`.

## Invariant contract

`schemas/decision_record.json` is the single source of truth for the
Python/Lean interface. When adding a new invariant:

1. Add the invariant to `MortgageProofs/Invariants.lean`.
2. Add the corresponding proof to `MortgageProofs/Theorems.lean`.
3. Update `MortgageProofs/Checker.lean` to apply the invariant.
4. Update the `DecisionRecord` schema and domain models if new fields are needed.
5. Add Python tests in `tests/lean_bridge/` for the new invariant path.

## Local notes

- Integration tests are marked `@pytest.mark.integration` and excluded from CI
  (`-m "not integration"`); they need a live LLM API key and the Lean binary.
- `schemas/decision_record.json` is canonical. Never let the Python dataclass diverge from it.
- No real applicant data in fixtures, tests, or docs.
