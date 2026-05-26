# CLAUDE.md — mortgage-proofs

LangGraph multi-agent mortgage pipeline with Lean 4 invariant checking.
Every routing decision is recorded as a `DecisionRecord` JSON and validated
against Lean 4 invariants by `lake exe verify-trace`.

## What this project is

A multi-agent system that processes mortgage applications through four
specialized agents (intake, risk, compliance, underwriter).  The Python
orchestrator produces a trace of `DecisionRecord` objects; the Lean 4
verifier checks that the trace satisfies the DTI bound, predatory-lending
invariants, and other regulatory constraints — making the agent's reasoning
formally auditable.

## Architecture

```
mortgage-proofs/
  src/mortgage_proofs/
    app/              — FastAPI application entry point
    domain/           — domain models (Applicant, Property, LoanRequest, etc.)
    lean_bridge/      — Python ↔ Lean trace serialization and verification runner
    orchestrator/     — LangGraph agent graph (intake → risk → compliance → underwriter)
    record/           — DecisionRecord dataclass + JSON schema
  lean/
    MortgageProofs/
      Types.lean      — Lean types mirroring Python domain models
      Invariants.lean — Formal invariant definitions (DTI, predatory lending)
      Theorems.lean   — Proof obligations
      Checker.lean    — Trace checker: validates DecisionRecord sequences
      Parser.lean     — JSON → Lean type parser
    Main.lean         — `lake exe verify-trace` entry point
  schemas/
    decision_record.json  — JSON schema for DecisionRecord (source of truth)
  tests/
    domain/           — unit tests for domain models and validators
    lean_bridge/      — unit tests for trace serialization + runner
    orchestrator/     — unit tests for agent routing logic
    integration/      — end-to-end tests (require live Lean binary + LLM key)
```

## Build & test commands

```bash
# Install Python dependencies (from mortgage-proofs/)
uv sync --all-extras

# Unit tests only (no LLM key, no Lean binary required)
uv run pytest -m "not integration" -q

# Integration tests (require LEAN binary + OPENAI_API_KEY or equivalent)
uv run pytest -m integration -q

# Type check
uv run mypy src/ --strict

# Lint
uv run ruff check src/ tests/

# Build Lean verifier (from mortgage-proofs/lean/)
cd lean && lake build

# Run trace verifier on a sample trace
cd lean && lake exe verify-trace ../schemas/decision_record.json
```

## Lean–Python invariant contract

The `DecisionRecord` JSON schema (`schemas/decision_record.json`) is the
source of truth for the interface.  When adding a new invariant:

1. Add the invariant to `MortgageProofs/Invariants.lean`.
2. Add the corresponding proof to `MortgageProofs/Theorems.lean`.
3. Update `MortgageProofs/Checker.lean` to apply the invariant during trace verification.
4. Update the `DecisionRecord` schema and domain models if new fields are needed.
5. Add Python tests in `tests/lean_bridge/` for the new invariant path.

## Hard rules

- Zero `sorry` in `lean/`.
- `mypy --strict` must pass on `src/`.
- Integration tests are marked `@pytest.mark.integration` and excluded from
  CI (`-m "not integration"`); they require a live LLM API key and the Lean binary.
- `schemas/decision_record.json` is the canonical interface between Python
  and Lean — never diverge the Python dataclass from the schema.
- LLM provider is intentionally abstracted; do not hardcode any specific
  provider or model name in `src/`.
