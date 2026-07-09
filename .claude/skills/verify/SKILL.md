---
name: verify
description: >
  Runs the full 7-level verification pyramid for quant-proofs in sequence.
  Stops at the first failing level and surfaces the level-specific skill to
  diagnose. Use before any merge to main or for a complete health check.
allowed-tools: Bash(lake *) Bash(uv run *) Bash(grep *) Bash(git *)
---

# Verify — quant-proofs

Each level must pass before the next runs.

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
# Level 1 — Lean (full current subdir list; see /verify-lean for the authoritative loop)
for dir in research-pipeline/lean foundations/quant-core/lean foundations/ftap-proofs \
           foundations/options-proofs foundations/optimization-proofs foundations/portfolio-proofs/lean \
           extensions/vrp-proofs extensions/hedge-proofs extensions/stopped-time-proofs \
           extensions/perpetual-proofs extensions/mortgage-proofs/lean; do
  (cd "$dir" && lake build) || exit 1
done
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake \
  {research-pipeline/lean,foundations/quant-core/lean,foundations/ftap-proofs,foundations/options-proofs,\
foundations/optimization-proofs,foundations/portfolio-proofs/lean,extensions/vrp-proofs,extensions/hedge-proofs,\
extensions/stopped-time-proofs,extensions/perpetual-proofs,extensions/mortgage-proofs/lean}/

# Level 2 — Python (see /verify-unit for the authoritative per-subdir commands)
(cd research-pipeline && pytest -q && mypy --strict src/ && ruff check .)
(cd foundations/quant-core/python && uv run pytest -q)
(cd foundations/portfolio-proofs && uv run pytest tests/test_lean_pgd.py -v -k "not integration")
(cd extensions/mortgage-proofs && uv run pytest -m "not integration" -q && uv run mypy src/ --strict)

# Levels 3–5 (when infrastructure exists)
uv run pytest tests/property/ tests/empirical/ tests/regime/ -v
```

## Gate rule

A failing level **stops the run**. Diagnose with the level-specific skill, fix,
re-run from that level. Never skip ahead.

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

## Pre-commit hooks

Hooks run automatically on `git commit`: `ruff`, `mypy --strict`, `lake build`, `pytest` for
each changed subdir. A failing hook **aborts the commit** — fix, re-stage, retry.
Never `--no-verify`. Run without committing: `pre-commit run --all-files`.
