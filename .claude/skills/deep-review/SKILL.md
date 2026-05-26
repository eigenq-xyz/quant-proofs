---
name: deep-review
description: >
  Multi-agent deep review for quant-proofs: static analysis, bug finding, security
  vulnerabilities, stale/unused dependencies, quant-specific logic audit, and dead-code
  detection — all run in parallel before a serial QA gate. Returns a synthesized
  MERGE / REWORK / BLOCKED verdict. Use before any significant PR or before cutting
  a release. Mutation testing runs separately in CI (mutation-test.yml).
---

# `/deep-review` — quant-proofs

Full-depth multi-agent review. Distinct from `/verify` (which runs the build/test
pyramid) and `qa-checker` (which is a serial gate). This skill fans out six review
agents in parallel, waits for all to complete, then runs `qa-checker` as the final
serial gate.

**Mutation testing** is intentionally excluded from this skill — it belongs in
the scheduled `mutation-test.yml` CI job (weekly + `workflow_dispatch`). Do not
inline it here.

---

## Phase structure

```
Phase 1 — parallel (~2–4 min)
  lean4-reviewer        existing agent  Lean: sorry, build, naming, mathlib style
  python-reviewer       existing agent  Python: mypy, ruff, pytest, FFI contract
  security-reviewer     new agent       bandit, pip-audit, secrets scan, shell injection
  deps-reviewer         new agent       stale packages, unused top-level deps, licenses
  quant-logic-reviewer  new agent       look-ahead bias, NaN propagation, magic constants
  dead-code-reviewer    new agent       vulture, orphaned Lean defs, commented-out blocks

Phase 2 — serial (~2 min, after Phase 1 completes)
  qa-checker            existing agent  Full PASS/FAIL gate (sorry, lake build, pytest, mypy, docs)
```

---

## How to run

Spawn all Phase 1 agents in a single message so they run concurrently:

```
Agent(lean4-reviewer, "Review Lean changes in this diff: <context>")
Agent(python-reviewer, "Review Python changes in this diff: <context>")
Agent(security-reviewer, "Review all Python subdirs for security issues")
Agent(deps-reviewer, "Audit dependencies across all Python subdirs")
Agent(quant-logic-reviewer, "Audit quant logic in changed Python files: <context>")
Agent(dead-code-reviewer, "Scan for dead code across all subdirs")
```

After all six return, spawn qa-checker:
```
Agent(qa-checker, "Run full QA gate and return PASS/FAIL table")
```

Then synthesize all seven verdicts into the report below.

---

## Scoping the diff

Before spawning agents, determine what changed:

```bash
# Files changed in this branch vs main
git diff --name-only origin/main...HEAD

# Summary by subdir
git diff --name-only origin/main...HEAD | cut -d/ -f1 | sort -u
```

Pass the relevant file list to each agent in its prompt. Agents that operate
repo-wide (security-reviewer, deps-reviewer, dead-code-reviewer) always scan
all subdirs regardless of diff scope.

---

## Checklist agents cover

| Check | Agent |
|---|---|
| `sorry` in Lean proofs | lean4-reviewer |
| `lake build` per subdir | lean4-reviewer, qa-checker |
| Lean naming / docstrings / mathlib compat | lean4-reviewer |
| `mypy --strict` | python-reviewer, qa-checker |
| `ruff check` + `ruff format --check` | python-reviewer |
| `pytest` pass | python-reviewer, qa-checker |
| FFI float/basis-point contract | python-reviewer |
| `bandit` security scan | security-reviewer |
| `pip-audit` CVE check | security-reviewer |
| Secrets / hardcoded credentials | security-reviewer |
| Shell injection patterns | security-reviewer |
| Stale packages (2+ versions behind) | deps-reviewer |
| Unused top-level dependencies | deps-reviewer |
| License compatibility | deps-reviewer |
| Look-ahead bias patterns | quant-logic-reviewer |
| NaN / overflow / precision issues | quant-logic-reviewer |
| Magic numeric literals in finance logic | quant-logic-reviewer |
| Mixed tz-aware/tz-naive datetimes | quant-logic-reviewer |
| Unused Python code (`vulture`) | dead-code-reviewer |
| Orphaned Lean `def`/`theorem` | dead-code-reviewer |
| Commented-out code blocks > 10 lines | dead-code-reviewer |
| Doc cross-references | qa-checker |
| Privacy check (GPA, firm names) | qa-checker, python-reviewer |

**Not covered here (see CI):**
- Mutation testing → `mutation-test.yml` (weekly, `workflow_dispatch`)

---

## Output format

After all agents return, synthesize into this report:

```
## Deep Review — <branch> — <date>

### Phase 1 Verdicts

| Agent | Verdict | Blocking issues |
|---|---|---|
| lean4-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |
| python-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |
| security-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |
| deps-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |
| quant-logic-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |
| dead-code-reviewer | APPROVED / NEEDS CHANGES / BLOCKED | <count> |

### Phase 2 QA Gate

<paste qa-checker PASS/FAIL table>

### Blocking Issues (must fix before merge)

1. [AGENT] file:line — description — required fix
2. ...

### Warnings (should fix; may merge with documented justification)

1. ...

### Notes (optional improvements)

1. ...

### Overall Verdict: MERGE | REWORK | BLOCKED

- MERGE: all Phase 1 APPROVED, qa-checker PASS, zero blocking issues
- REWORK: any NEEDS CHANGES or warnings without justification
- BLOCKED: any BLOCKED verdict, any qa-checker FAIL, or any blocking issue
```

---

## Escalation rules

Stop immediately and surface to the user if:
- Any `sorry` found in Lean proofs (unconditional merge block)
- `lake build` fails in any subdir (invalidates downstream checks)
- A CVE-rated vulnerability found by `pip-audit` (security-reviewer escalates)
- A hardcoded secret or credential found (security-reviewer escalates)

Do not wait for remaining agents to complete — escalate immediately when any of
the above is detected.

---

## Relationship to other skills

| Skill / Agent | Scope | When to use |
|---|---|---|
| `/verify` | Build + test pyramid only | Pre-merge health check |
| `/review-code-quality` | Lean + Python checklist | Lightweight PR self-check |
| `/check-lean-style` | Lean mathlib style | Before mathlib PR |
| `qa-checker` | Full QA gate (serial) | After reviewers approve |
| `/deep-review` | All of the above + security + deps + quant logic | Before significant PR or release cut |
