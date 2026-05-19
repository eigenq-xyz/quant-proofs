---
name: contributing-to-eigenq
description: >
  PR workflow, branch conventions, testing requirements, and mathlib upstream process
  for the quant-proofs monorepo. Use before opening a PR, when setting up a branch,
  or when preparing ftap-proofs or options-proofs for a mathlib contribution.
paths:
  - "**/*"
---

# Contributing to quant-proofs

## Branch naming conventions

Every branch is scoped to a single subdir. Pick the prefix that describes the intent:

| Prefix | Use when |
|--------|----------|
| `feat/<subdir>/<description>` | New capability, new module, new agent |
| `fix/<subdir>/<description>` | Bug fix, proof repair, type error |
| `proof/<subdir>/<theorem-name>` | Adding or completing a Lean 4 proof |
| `refactor/<subdir>/<description>` | Internal restructure, no behavior change |
| `docs/<subdir>/<description>` | CLAUDE.md, inline comments, docstrings |
| `mathlib/<subdir>/<module-name>` | Branch tracking a mathlib upstream PR |

Examples:
```
feat/backtest-proofs/cython-ffi-export
fix/mortgage-proofs/compliance-agent-nil-trace
proof/ftap-proofs/noArbitrageMartingale
proof/options-proofs/putCallParity
mathlib/ftap-proofs/Mathlib.Finance.NoArbitrage
```

Use lowercase kebab-case for `<description>` and camelCase for `<theorem-name>` (matching
the Lean 4 identifier).

## Pre-merge checklist

Before opening a PR — and before requesting review — verify every item:

### Lean 4
- [ ] `lake build` passes with no errors in the affected subdir
- [ ] Zero `sorry` in all `.lean` files under the affected subdir:
  ```
  grep -rn sorry <subdir>/lean --include="*.lean"
  ```
  (An empty result is required. `-- sorry` comments in docs are fine; actual `sorry` terms
  are not.)
- [ ] If `options-proofs/` is changed, also build `ftap-proofs/` — the dependency goes
  `options-proofs → ftap-proofs`, so `ftap-proofs` must still build cleanly.
- [ ] New theorems have `-- Proof sketch:` comments explaining the high-level argument.

### Python / Cython
- [ ] `pytest` passes in the affected subdir's Python tree
- [ ] `mypy --strict <subdir>/python/src/` (or `<subdir>/src/`) is clean
- [ ] No licensed data files are staged (`git diff --cached --name-only` must not include
  `.csv`, `.parquet`, `.h5`, or raw data files)

### All PRs
- [ ] Branch is scoped to one subdir (one `lake build` root, one Python package)
- [ ] Commit history is clean (no merge commits from `main`; rebase if needed)
- [ ] PR description follows the template below

## PR template

Use this structure for every PR. Omit sections that don't apply (e.g., no Proof sketch for
a pure Python change), but keep the headers so reviewers can scan quickly.

```markdown
## Summary

- One-sentence description of what changed and why.
- Any subdir-level dependency implications (e.g., "bumps FtapProofs API; options-proofs
  updated in tandem").

## Proof sketch (Lean PRs only)

High-level argument for the main theorem(s) introduced or modified:
- State the key lemmas used.
- Note any non-obvious steps (e.g., "the martingale characterization requires Doob's
  optional stopping, invoked via `Mathlib.Probability.Martingale.Stopping`").
- If a `sorry` was present on the feature branch, state explicitly how it was discharged.

## Test plan

- [ ] `lake build` passes in `<subdir>/`
- [ ] `grep -rn sorry <subdir>/lean --include="*.lean"` returns empty
- [ ] `pytest` passes (if Python changed)
- [ ] `mypy --strict` clean (if Python changed)
- [ ] `lake exe verify-trace` passes on sample trace (mortgage-proofs only)
```

## Mathlib upstream process

When a proof in `ftap-proofs/` or `options-proofs/` is ready for mathlib:

### Namespace requirements

Lean 4 identifiers must conform to mathlib style:
- Top-level namespace must be `Mathlib.` (e.g., `Mathlib.Finance.NoArbitrage`)
- The module name should fit under an existing mathlib parent:
  - `Mathlib.Analysis.` for analytical results
  - `Mathlib.Probability.` for measure-theoretic probability
  - `Mathlib.Finance.` (proposed; check current mathlib tree before assuming this exists)
- Use `theorem` not `lemma` for results intended as the main export.
- All `def`, `theorem`, and `lemma` names must be in `UpperCamelCase` (types/structures)
  or `lowerCamelCase` (theorems/lemmas) per mathlib convention.

### Preparation steps

1. **Create a `mathlib/<subdir>/<module-name>` branch** from the current `main`.
2. **Restructure the namespace.** Move from `FtapProofs.X` to `Mathlib.Finance.X` (or
   agreed parent). Update all imports in `options-proofs/` accordingly.
3. **Strip non-mathlib dependencies.** The submitted file must import only from `Mathlib`
   and `Std`. Remove any local utility lemmas that duplicate existing mathlib lemmas —
   search `Mathlib` first.
4. **Add `#check` and `#eval` sanity lines** in a separate `Examples.lean` file (not
   submitted, but useful for review prep).
5. **Run mathlib4 CI locally** using the `leanprover-community/mathlib4` Docker image or
   `lake exe cache get && lake build`.
6. **Open a draft PR on mathlib4.** Title format: `feat(Finance): <short description>`.
   The PR description must include the mathematical statement in plain English, the
   formalization approach, and a pointer to the paper (Harrison-Pliska 1981 for FTAP).
7. **Track review comments on the `mathlib/` branch** and sync back to `main` once merged.

### Timing

Do not open the mathlib PR until:
- `lake build` is clean on the `mathlib/` branch with zero `sorry`.
- The proof has been stable on `main` for at least one week (no further edits anticipated).
- The `options-proofs/` dependency on the FTAP result has been tested post-namespace-change.

## PR sequencing and dependency management

**PRs must be sequential, not parallel, when they share files or build on each other.**
Opening two PRs that both touch the same file creates a race: whichever merges second
will have conflicts or silently overwrite the other's changes. Sequence instead.

### Express the dependency through branch structure

Branch the dependent PR off the dependency's branch — not off main:

```bash
# PR A: foundational change
git checkout main && git checkout -b feat/backtest-proofs/new-invariant

# PR B: builds on A — branch off A, not off main
git checkout feat/backtest-proofs/new-invariant
git checkout -b feat/backtest-proofs/ffi-export-for-invariant
```

When PR A merges to main, rebase B onto main and force-push:
```bash
git fetch origin && git rebase origin/main
git push --force-with-lease
```
B's diff on GitHub is now clean against main, showing only B's actual changes.

### Document the dependency in the PR description

In PR B's description, add explicitly:

```
> **Depends on #A — merge that first.** This branch was cut from
> `feat/backtest-proofs/new-invariant`. After #A merges, rebase this
> branch onto main before merging.
```

Use "blocked by" or "depends on" — not "related to". It signals merge order.

### Merge strategy: squash and merge, one at a time

Use **squash and merge** for every PR. Each PR becomes one commit on main; the
history stays linear. Never merge two dependent PRs simultaneously — merge A,
pull main locally, rebase B, then merge B.

### Recovering from parallel PRs that conflict

If two parallel PRs already exist and conflict:
1. Merge the more foundational one first (squash and merge)
2. `git fetch origin && git rebase origin/main` on the other branch
3. Resolve conflicts during the rebase
4. `git push --force-with-lease` to update the PR
5. Merge the rebased PR

## PR sequencing and dependency management

**PRs must be sequential, not parallel, when they share files or build on each other.**
Opening two PRs that both touch the same file creates a race: whichever merges second
will have conflicts or silently overwrite the other's changes. Sequence instead.

### Express the dependency through branch structure

Branch the dependent PR off the dependency's branch — not off main:

```bash
# PR A: foundational change
git checkout main && git checkout -b feat/backtest-proofs/new-invariant

# PR B: builds on A — branch off A, not off main
git checkout feat/backtest-proofs/new-invariant
git checkout -b feat/backtest-proofs/ffi-export-for-invariant
```

When PR A merges to main, rebase B onto main and force-push:
```bash
git fetch origin && git rebase origin/main
git push --force-with-lease
```
B's diff on GitHub is now clean against main, showing only B's actual changes.

### Document the dependency in the PR description

```markdown
> **Depends on #N — merge that first.** This branch was cut from
> `feat/backtest-proofs/new-invariant`. After #N merges, rebase this
> branch onto main before merging.
```

Use "depends on" or "blocked by" — not "related to". It signals merge order.

### Merge strategy: squash and merge, one at a time

Use **squash and merge** for every PR. Each PR becomes one commit on main; the
history stays linear. Never merge two dependent PRs simultaneously — merge A,
pull main locally, rebase B, then merge B.

### Recovering from parallel PRs that conflict

If two parallel PRs already exist and conflict:
1. Merge the more foundational one first (squash and merge)
2. `git fetch origin && git rebase origin/main` on the other branch
3. Resolve conflicts during the rebase
4. `git push --force-with-lease` to update the PR
5. Merge the rebased PR

## GitHub workflow rules

**Never push directly to a protected branch.** All changes go through a PR, regardless
of how small. The repo's `PreToolUse` hook enforces this automatically by querying the
GitHub API for protected branches before any push; the same rule applies when working
manually.

**Use draft PRs for work in progress.** If a branch isn't ready for review — sorry
still present, tests failing, proof incomplete — open it as a draft:
```bash
gh pr create --draft --title "proof/ftap-proofs/noArbitrageEMM" --body "..."
```
This signals intent without triggering review requests. Convert to ready when the
pre-merge checklist is fully green.

**Reviewer etiquette:**
- Respond to every review comment, even with just "done" or "won't fix, because...".
- Use GitHub's "Resolve conversation" only after the fix is pushed — not to dismiss.
- For blocking concerns, push a fix and re-request review; don't merge over a BLOCKING
  comment.
- Prefer GitHub's suggestion feature for one-line reviewer edits; it makes the
  diff reviewable.

## Commit standards

See `/writing-commits-and-prs` for the full commit message format. Summary:
- Imperative mood, subject ≤72 characters.
- Reference theorem names by their Lean 4 identifier for proof commits.
- Body explains why the change was made, not what the diff shows.
- One logical change per commit (a proof and its FFI export may be one commit if inseparable;
  otherwise split).
