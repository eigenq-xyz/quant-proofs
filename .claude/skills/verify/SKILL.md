---
name: verify
description: >
  Runs the full 7-level verification pyramid for quant-proofs in sequence.
  Stops at the first failing level and surfaces the level-specific skill to
  diagnose. Use before any merge to main or for a complete health check.
allowed-tools: Bash(lake *) Bash(uv run *) Bash(grep *) Bash(git *)
---

# Verify — quant-proofs

Verification pyramid: each level must pass before the next runs.

| Level | Skill | CI | Local | What it checks |
|-------|-------|----|-------|---------------|
| 1 | `/verify-lean` | ✅ | ✅ | Lean proofs compile, zero sorry |
| 2 | `/verify-unit` | ✅ | ✅ | Python tests, mypy, ruff |
| 3 | `/verify-property` | ✅ | ✅ | Hypothesis property tests |
| 4 | `/verify-empirical` | ✅ | ✅ | Data quality gate + empirical tests |
| 5 | `/verify-regime` | ✅ | ✅ | Regime conditioning + stress events |
| 6 | `/verify-research` | ❌ | ✅ | WRDS full research pipeline |
| 7 | `/verify-scheduled` | ✅ | ❌ | Weekly data refresh + CI |

## Quick commands per level

```bash
# Level 1 — Lean
for dir in backtest-proofs/lean ftap-proofs options-proofs extensions/mortgage-proofs/lean; do
  (cd "$dir" && lake build) || exit 1
done
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake {backtest-proofs/lean,ftap-proofs,options-proofs,extensions/mortgage-proofs/lean}/

# Level 2 — Python
(cd backtest-proofs/python && uv run pytest -q && uv run mypy src/ --strict && uv run ruff check src/ tests/)
(cd extensions/mortgage-proofs && uv run pytest -m "not integration" -q && uv run mypy src/ --strict)

# Levels 3–5 (when infrastructure exists)
uv run pytest tests/property/ tests/empirical/ tests/regime/ -v
```

## Gate rule

A level that fails stops the run. Diagnose with the level-specific skill, fix,
and re-run from that level — do not skip ahead.

## Pre-merge minimum

Before opening any PR: Levels 1 and 2 must pass. For PRs that touch data or
results: Levels 1–4. For PRs targeting mathlib: Levels 1–2 plus `/check-lean-style`.

## On failure

Run the level-specific skill for diagnosis commands and common causes:
- Level 1 fails → `/verify-lean`
- Level 2 fails → `/verify-unit`
- Level 3 fails → `/verify-property`
- Level 4 fails → `/verify-empirical`
- Level 5 fails → `/verify-regime`
