---
name: eigenq-orchestrator
description: "The central coordination skill for managing multi-agent workflows in the eigenq repo."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# EigenQ Orchestrator

This skill is used by the primary Hermes session to coordinate complex, multi-step tasks by delegating to `eigenq-engineer` and `eigenq-verifier`.

## Orchestration Logic
1.  **Plan**: Decompose the user's request into a series of `delegate_task` calls.
2.  **Delegate (Engineer)**: Spawn `eigenq-engineer` as a `leaf` agent to implement the core logic or proofs.
3.  **Verify (Verifier)**: After the engineer completes, spawn `token-verifier` to audit the changes against the `CLAUDE.md` hard rules.
4.  **Report**: Summarize the findings and final state to the user.

## Task Delegation Patterns
- **For Code Implementation**:
  - Goal: "Implement [feature] in [path]"
  - Toolset: `['terminal', 'file', 'search', 'web']`
  - Context: Project structure and `CLAUDE.md` rules.
- **For Verification**:
  - Goal: "Verify [path] complies with zero-sorry and mypy-strict rules"
  - Toolset: `['terminal', 'file', 'search']`
  - Context: The diff or the recently modified files.

## Error Handling
- If `eigenq-verifier` finds a `sorry` or `mypy` error, re-delegate to `eigenq-engineer` with the error log as context.
- If the engineer fails to complete a task, evaluate if the task was too large and needs further decomposition.
