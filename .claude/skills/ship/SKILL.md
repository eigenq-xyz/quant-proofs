---
name: ship
description: >
  Commit staged and unstaged changes, push the branch, and open a PR — all in one
  pass using quant-proofs conventions. Reads write-commits-and-prs for commit
  format and type tokens, and contribute-to-eigenq for branch naming and PR
  template. Use after finishing a unit of work that is ready for review.
allowed-tools: >
  Bash(git status)
  Bash(git diff *)
  Bash(git log *)
  Bash(git branch *)
  Bash(git checkout *)
  Bash(git add *)
  Bash(git commit *)
  Bash(git push *)
  Bash(gh pr create *)
  Bash(gh pr view *)
  Bash(grep *)
---

# Ship — commit, push, and open a PR

## Context (read before acting)

- Working tree status: !`git status`
- Staged and unstaged diff: !`git diff HEAD`
- Current branch: !`git branch --show-current`
- Recent commits: !`git log --oneline -10`

## Step 1 — branch

If on `main`, cut a branch first using the naming convention from `/contribute-to-eigenq`:

```
proof/<subdir>/<leanIdentifier>    # theorem fully discharged
feat/<subdir>/<description>        # new capability
fix/<subdir>/<description>         # bug fix
refactor/<subdir>/<description>    # restructure, no spec change
docs/<subdir>/<description>        # docs only
mathlib/<subdir>/<module-name>     # mathlib upstream prep
```

Use lowercase kebab-case for `<description>`, camelCase for `<leanIdentifier>`.

If already on a feature branch, stay on it.

## Step 2 — commit

Stage all relevant files and write a commit message following `/write-commits-and-prs`:

```
<type>(<scope>): <imperative subject, ≤72 chars>

<body: WHY — theorem name, paper section, or motivation; wrap at 72 chars>
```

**Type tokens:**

| Token | When |
|-------|------|
| `Prove` | Lean 4 theorem fully discharged (no sorry) |
| `Scaffold` | Lean 4 stub added with sorry placeholder |
| `Fix` | Bug fix — proof repair, Python logic error, type error |
| `Add` | New module, agent, or FFI export |
| `Refactor` | Internal restructure, no behavior change |
| `Docs` | CLAUDE.md, comments, docstrings — no code change |
| `Test` | Tests added or updated |
| `Chore` | Dependency bumps, CI config, tooling |

**Scope:** subdir abbreviation — `backtest`, `ftap`, `options`, `mortgage`, `quant-core` — or `meta` for top-level files.

**Body:** for proof commits, include the exact Lean 4 identifier in backticks. For Python commits, state what broke and what the fix is.

Before committing, verify:
- `grep -rn sorry --include="*.lean" .` returns nothing (on non-scaffold commits)
- No data files (`.csv`, `.parquet`, `.h5`) in the diff
- No private content in any file

## Step 3 — push

```bash
git push -u origin <branch>
```

## Step 4 — open the PR

Use `gh pr create` with this description structure (omit sections that don't apply):

```markdown
## Summary

- <What changed and why — one or two bullets>
- <Cross-subdir implications if any>

## Proof sketch (Lean PRs only)

- Main theorem: `<LeanIdentifier>` in `<Module.Path>`
- Key lemmas: `<lemma1>`, `<lemma2>`
- Non-obvious step: <tactic or import explanation>
- How any sorry placeholders were discharged

## Test plan

- [ ] `lake build` passes in `<subdir>/`
- [ ] `grep -rn sorry <subdir>/lean --include="*.lean"` returns empty
- [ ] `pytest` passes (if Python changed)
- [ ] `mypy --strict <subdir>/src/` clean (if Python changed)
- [ ] `lake exe verify-trace` passes on sample trace (mortgage-proofs only)
- [ ] Dependent subdir still builds (if ftap-proofs changed, also build options-proofs)
```

If this PR depends on another unmerged PR, add at the top:

```markdown
> **Depends on #N — merge that first.** This branch was cut from
> `<dependency-branch-name>`, not from main.
```

## Do all four steps in a single message

Call all necessary tools in one response — do not pause between steps.
