---
name: checking-ci-status
description: >
  Check CI health across the quant-proofs monorepo: workflow run results,
  PR check statuses, and failure logs. Use when a push fails, a PR is blocked,
  or you want to confirm main is green before branching.
allowed-tools: Bash(gh run *) Bash(gh pr *) Bash(gh api *) Bash(python3 *)
---

# Checking CI Status — quant-proofs

## Quick status: is main green?

```bash
gh run list --repo eigenq-xyz/quant-proofs --branch main --limit 5 \
  --json name,status,conclusion,createdAt \
  | python3 -c "
import sys, json
runs = json.load(sys.stdin)
for r in runs:
    conclusion = r.get('conclusion') or ''
    status = r.get('status') or ''
    icon = '✓' if conclusion == 'success' else ('…' if (not conclusion or status in ('in_progress','queued','waiting')) else '✗')
    result = conclusion or status
    print(f\"{icon} {r['name']:<35} {result:<12} {r['createdAt'][:16]}\")
"
```

## PR check status

```bash
# All checks on a specific PR
gh pr checks <PR-number> --repo eigenq-xyz/quant-proofs

# List open PRs with their overall check status
gh pr list --repo eigenq-xyz/quant-proofs --json number,title,statusCheckRollup \
  | python3 -c "
import sys, json
prs = json.load(sys.stdin)
for pr in prs:
    checks = pr.get('statusCheckRollup') or []
    states = [c.get('conclusion') or c.get('state','') for c in checks]
    overall = 'PASS' if all(s in ('SUCCESS','success','') for s in states) \
              else ('PENDING' if any(s in ('PENDING','IN_PROGRESS') for s in states) \
              else 'FAIL')
    print(f\"#{pr['number']:<4} {overall:<8} {pr['title']}\")
"
```

## What failed and why

```bash
# Get logs from the most recent failure on main
gh run list --repo eigenq-xyz/quant-proofs --branch main --status failure \
  --limit 1 --json databaseId --jq '.[0].databaseId' \
  | xargs gh run view --repo eigenq-xyz/quant-proofs --log-failed 2>&1 | head -80
```

## Re-run a failed workflow

```bash
gh run list --repo eigenq-xyz/quant-proofs --branch main --status failure \
  --limit 1 --json databaseId --jq '.[0].databaseId' \
  | xargs gh run rerun --repo eigenq-xyz/quant-proofs --failed-only
```

## Watch a running job live

```bash
gh run watch --repo eigenq-xyz/quant-proofs
```

## Common failures in this repo

| Failure | Likely cause | Fix |
|---------|-------------|-----|
| `Publish Docs` 404 on deploy | GitHub Pages not enabled | `gh api repos/eigenq-xyz/quant-proofs/pages --method POST -f build_type=workflow` |
| `Publish Docs` build error | File missing from `docs/_toc.yml` | Check every path in `_toc.yml` exists under `docs/` |
| Lean CI build fail | mathlib cache miss or toolchain mismatch | Check `lean-toolchain`; run `lake exe cache get` locally |
| Lean CI sorry check fails | A `sorry` on main | `grep -rn sorry --include="*.lean" --exclude-dir=.lake <subdir>/` |
| Python CI mypy failure | Missing type annotations | `uv run mypy src/ --strict` locally |
| Python CI Cython build failure | Lean IR files missing | Ensure Lean build step ran before Cython build |

## Background monitoring (automatic)

After every `git push` or `gh pr merge`, a background hook polls GitHub until
all CI runs on that branch complete, then wakes Claude with the result:

- `CI finished: PASS: all checks on <branch>` — everything green
- `CI finished: FAIL on <branch>: <workflow names>` — one or more failed

The hook polls every 15 seconds and times out after 11 minutes. If CI is still
running at that point, check manually with the commands above.

## Checklist before merging a PR

- [ ] Main is green: `gh run list --branch main --status failure --limit 1` returns empty
- [ ] PR checks pass: `gh pr checks <number>` shows all green
- [ ] No check is still pending — wait rather than merging speculatively
