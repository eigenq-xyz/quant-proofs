---
name: commit-push-pr
description: >
  End-to-end workflow for committing staged work, pushing to remote, and
  opening a pull request in one motion. Use when the user says "commit and
  PR", "open a PR for this branch", "ship this", or has finished a unit of
  work. Enforces pre-flight gates, scope discipline, message conventions
  (via writing-commits-and-prs), and one-shot PR creation.
allowed-tools: Bash(git *) Bash(gh *) Read
---

# Commit, Push, PR

End-to-end workflow assistant. Composes other skills rather than duplicating
them — message format and PR templates live in `/writing-commits-and-prs`;
branch sequencing in `/contributing-to-eigenq`; post-push CI checks in
`/checking-ci-status`.

## When to use

The user has finished a unit of work and wants to commit, push, and open a
PR. Use this skill rather than running git commands ad-hoc — it enforces
the pre-flight gate, scope check, and PR conventions in one place.

Not this skill:

- Amending or rewriting history — deliberate, separate action.
- Pushing directly to `main` — never.
- Landing failing code — run the repo's verification gate first.

## Pre-flight (run in parallel)

```bash
git status
git diff --stat
git log -5 --oneline
git branch --show-current
```

Decide before staging:

1. **Branch.** If on `main`, branch off first. eigenq-xyz convention:
   `proof/<subdir>/<leanIdent>`, `feat/<subdir>/<desc>`,
   `fix/<subdir>/<desc>`, etc. — see `/writing-commits-and-prs`.
2. **Verification gate.** In any eigenq-xyz repo, run `/verify` (or the
   relevant level — `/verify-lean` for Lean-only changes, `/verify-unit`
   for Python-only). Never land a broken proof or failing test, even WIP.
3. **Scope.** A branch should touch ONE subdir in any monorepo. If the
   diff spans subdirs, split into separate branches before continuing.

## Stage by name, not by pattern

```bash
git add <path1> <path2>
git status                # confirm what's staged
```

Never `git add -A` or `git add .` — they sweep in unrelated edits, IDE
artifacts, and licensed data. Explicit file lists also catch accidental
inclusion of private context.

Hard exclusions for eigenq-xyz repos:

- Build artifacts: `_output/`, `.lake/`, `__pycache__/`, `node_modules/`,
  `*.egg-info/`, `.quarto/`
- Raw data: `.csv`, `.parquet`, `.h5`, `.pkl`, `.feather` — see
  `/sourcing-financial-data` for the data hierarchy
- Anything with private context (GPA, firm names, internship timing,
  "developed to impress X") — same rule as `/writing-commits-and-prs`

## Commit

Message format, type tokens (`Prove` / `Scaffold` / `Fix` / `Add` /
`Refactor` / `Docs` / `Test` / `Chore`), and examples are in
`/writing-commits-and-prs`.

Use a HEREDOC to preserve formatting:

```bash
git commit -m "$(cat <<'EOF'
<Type>(<scope>): <imperative subject ≤72 chars>

<body explaining WHY, wrapped at 72>

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"
```

Never `--no-verify`, never `--no-gpg-sign`. If a pre-commit hook fails:
fix the underlying issue, re-stage, and create a **new** commit. Do not
`--amend` — the failed commit never landed, so `--amend` would target the
previous (already-pushed) commit.

## Push

```bash
git push -u origin <branch>     # first push of a new branch
git push                        # subsequent pushes
```

Force-pushing your own feature branch (for rebases or fixups) is fine —
disclose it in the PR description if a reviewer has already commented.
Never force-push to `main`.

## Open PR

One `gh` invocation. Title format mirrors the commit subject; body uses
the template in `/writing-commits-and-prs`:

```bash
gh pr create --title "<Type>(<scope>): <subject>" --body "$(cat <<'EOF'
## Summary

- <what changed and why — one or two bullets>

## Proof sketch (Lean PRs only)

- Main theorem: `<LeanIdentifier>` in `<Module.Path>`
- Key lemmas: `<lemma1>`, `<lemma2>`
- Non-obvious step: <tactic / mathlib import worth flagging>

## Test plan

- [ ] `lake build` passes in `<subdir>/`
- [ ] `grep -rn sorry --include="*.lean" <subdir>/` returns empty
- [ ] `pytest` passes (if Python changed)
- [ ] `mypy --strict` clean (if Python changed)
- [ ] Dependent subdirs still build

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

Return the PR URL to the user when done.

If this PR depends on another unmerged PR, declare it at the top of the
body and branch off the dependency's branch (not `main`) — see
`/contributing-to-eigenq` for the full sequencing workflow.

## After the push

- Run `/checking-ci-status` to confirm CI is green.
- Do **not** merge on the user's behalf without explicit instruction.

## Hard rules

- Never push directly to `main`.
- Never use `--no-verify`, `--no-gpg-sign`, or `commit.gpgsign=false` to
  bypass hooks.
- Never amend a pushed commit unless the user explicitly asks.
- Never `git add -A` or `git add .` without first inspecting what would
  be staged.
- Never commit raw data files or content with private context.
- Never open a PR when the repo's verification gate is failing.
- Never merge on the user's behalf without explicit instruction.

## Related skills

- `/writing-commits-and-prs` — message format, type tokens, branch
  naming, PR description template, review checklist.
- `/contributing-to-eigenq` — branch sequencing, mathlib upstream
  process for ftap-proofs and options-proofs.
- `/checking-ci-status` — runs after the push lands.
- `/verify` (or `/verify-lean`, `/verify-unit`) — pre-commit gate for
  eigenq-xyz repos.
