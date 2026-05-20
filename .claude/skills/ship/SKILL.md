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

## Step 5 — solicit Claude Code Review

Immediately after the PR is created, post a comment on the PR thread that tags
`@claude` and asks for focused feedback. Tailor the asks to what actually changed
in this PR. Template:

```bash
gh pr comment <PR-number> --body "$(cat <<'EOF'
@claude Please review this PR with focus on:

- <specific concern 1 — e.g., "correctness of the Lean accounting invariants">
- <specific concern 2 — e.g., "mypy strict compliance in the new stress.py module">
- <specific concern 3 — e.g., "Quarto chunk labels and freeze cache correctness">

Any issues that would block merge or require a follow-up commit are most useful.

---
*Review request authored by Claude Code (claude-sonnet-4-6) on behalf of @akhilkarra*
EOF
)"
```

Adapt the bullet points to the PR's actual content. This offloads review work to
the Claude Code Review bot and generates feedback that informs future commits.

**Hard rule: never merge before `claude-review` completes.** Even when all other
CI checks are green, wait for the Claude review — it surfaces issues the automated
checks miss (logic errors, convention violations, paper-section inconsistencies).

After posting the @claude comment, schedule **two wakeups** in the same message:

```python
# Wakeup 1 — check if claude-review CI check completed (fast turnaround)
ScheduleWakeup(delaySeconds=270, reason="Check claude-review CI completion on PR #N",
  prompt="Check if claude-review check on PR #N has completed: gh pr view N --json statusCheckRollup ...")

# Wakeup 2 — read the full review comment once the bot posts it
ScheduleWakeup(delaySeconds=600, reason="Read claude-review comment body on PR #N",
  prompt="Read claude-review comment on PR #N: gh pr view N --comments --json comments | python3 -c \"import json,sys; [print(c['body']) for c in json.load(sys.stdin)['comments'] if c['author']['login']=='claude']\". Summarize blocking findings to user. If no comment yet, reschedule at 270s.")
```

If the review is still IN_PROGRESS when a wakeup fires, reschedule at 270s.

## Do all five steps in a single message

Call all necessary tools in one response — do not pause between steps.
