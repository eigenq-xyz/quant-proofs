---
name: lean-style-check
description: >
  Reviews Lean 4 files against eigenq-xyz conventions and mathlib contribution
  guidelines. Use before opening a mathlib PR or to confirm a proof is ready
  for review. Read-only — reports issues, does not fix them.
paths:
  - "**/*.lean"
disallowedTools:
  - Edit
  - Write
  - NotebookEdit
---

# Lean Style Check

This skill reads and reports. The author fixes the issues.

## Checklist

### Required for all files

- [ ] Module has a `/-- ... -/` docstring at the top written for a non-Lean audience
- [ ] Namespace matches subdir convention (`BacktestProofs`, `FtapProofs`, `OptionsProofs`, `MortgageProofs`)
- [ ] All exported `theorem`, `def`, `structure` have docstrings
- [ ] Docstrings state the mathematical content in English first — not just Lean syntax
- [ ] No `import Mathlib` — all imports are specific (`import Mathlib.Data.Finset.Basic`)
- [ ] No bare `simp` — always `simp [specific_lemma]`
- [ ] No `sorry`
- [ ] Named `have` and `suffices` steps (not anonymous `_`)
- [ ] `-- Proof sketch:` comment at the top of non-trivial proofs

### Naming conventions

- Types and structures: `PascalCase` (`Portfolio`, `EuropeanOption`)
- Theorems and lemmas: `camelCase` (`valueIdentity`, `settlementFormula`) for eigenq-xyz; `snake_case` for mathlib candidates
- Local variables: single lowercase letters or short descriptive names

### For mathlib candidates (ftap-proofs, options-proofs)

- [ ] Namespace restructured: `FtapProofs.X` → `Mathlib.Finance.X` (or agreed parent)
- [ ] All local utility lemmas replaced by mathlib equivalents where possible
- [ ] Only imports from `Mathlib` and `Std` — no local dependencies
- [ ] Theorem names in `snake_case` per mathlib convention
- [ ] `lake build` passes on the `mathlib/<subdir>/` branch
- [ ] `lake exe cache get && lake build` clean on fresh clone

## Report format

```
[BLOCK] File: ftap-proofs/FtapProofs.lean, Line: 14
Issue: `import Mathlib` — wildcard import not accepted upstream
Fix: Replace with specific imports from the mathlib4 docs

[STYLE] File: ftap-proofs/FtapProofs.lean, Line: 22
Issue: theorem name `noArbitrageEMM` should be snake_case for mathlib
Fix: Rename to `no_arbitrage_emm`

[SUGGESTION] File: backtest-proofs/lean/BacktestProofs/Basic.lean, Line: 45
Issue: `simp` without lemma list — fragile on mathlib updates
Fix: `simp [Portfolio.value_def]`
```

Severity: **BLOCK** (must fix) / **STYLE** (should fix) / **SUGGESTION** (optional)
