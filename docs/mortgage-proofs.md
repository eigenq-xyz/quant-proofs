# mortgage-proofs

LangGraph multi-agent mortgage pipeline with formally verified routing invariants.

## What it proves

Lean 4 invariants on the agent routing logic: structural properties of the decision graph that must hold on every trace — for example, that a DTI-violating application cannot reach the underwriter without a compliance flag, or that every approved application has a non-null risk score.

Violations are caught at trace-validation time, not at runtime: the agent emits `DecisionRecord` JSON, and `lake exe verify-trace` checks the record against the Lean invariants.

## Architecture

```
mortgage-proofs/
├── lean/MortgageProofs/   # Lean 4 invariant checker
│   ├── Types.lean         # DecisionRecord, ApplicationState types
│   ├── Invariants.lean    # Formal invariant statements
│   ├── Checker.lean       # Checker logic
│   ├── Theorems.lean      # Soundness proofs
│   └── Parser.lean        # JSON → Lean type bridge
└── src/mortgage_proofs/   # LangGraph pipeline
    ├── orchestrator/      # Graph definition, agent nodes, router
    ├── domain/            # Pydantic models, validators
    ├── lean_bridge/       # verify-trace subprocess wrapper
    └── record/            # DecisionRecord emission and I/O
```

## Running

```bash
# Build the Lean verifier
cd mortgage-proofs/lean && lake build

# Validate a trace
lake exe verify-trace path/to/record.json

# Python pipeline
cd mortgage-proofs && uv sync --all-extras
uv run pytest -m "not integration"
```
