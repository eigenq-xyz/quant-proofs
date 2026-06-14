---
name: eigenq-verifier
description: "Specialized agent for auditing code quality, math correctness, and rule adherence."
version: 1.0.0
author: Hermes Agent
license: MIT
---

# EigenQ Verifier

This skill is used to audit work performed by other agents or the `eigenq-engineer`.

## Verification Checklist
1.  **Lean 4 Audit**:
    - Scan for `sorry` using `grep -rn sorry --include="*.lean"`.
    - Verify imports and Mathlib dependencies.
2.  **Python Audit**:
    - Run `mypy --strict <path>` on all new/modified Python files.
    - Check for compliance with `quant-core` primitives.
3.  **Policy Audit**:
    - Ensure no licensed data or private information is present.
    - Confirm no changes to `archive/` are being introduced as active.

## Audit Workflow
- Use `search_files` to perform scans.
- Use `terminal` to execute `lake build` and `pytest`.
- Report findings as a structured list of `[PASS/FAIL]` with evidence.
