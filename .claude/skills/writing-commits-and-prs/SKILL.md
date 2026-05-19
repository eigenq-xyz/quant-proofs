---
name: writing-commits-and-prs
description: >
  Commit message and PR standards for the quant-proofs monorepo. Use before writing
  a commit message, opening a PR, or reviewing a draft commit. Covers format rules,
  examples by change type, branch naming, and the PR review checklist.
---

# Writing commits and PRs

## Commit message format

```
<type>(<scope>): <imperative subject, ≤72 chars>

<body: explain WHY, not WHAT — reference theorem names, paper sections, or
issue numbers; wrap at 72 chars; may be omitted for trivial one-liners>
```

### Rules

- **Subject line:** imperative mood ("Add", "Fix", "Prove", "Refactor"), ≤72 characters,
  no trailing period.
- **Scope:** the subdir abbreviation — `backtest`, `ftap`, `binomial`, `mortgage` — or
  `meta` for top-level files (CLAUDE.md, `.claude/`).
- **Blank line** between subject and body. Always, even for short bodies.
- **Body:** explains the motivation. For proof commits, state the theorem name (Lean 4
  identifier), the key lemma used, and any non-obvious step. Do not restate what the diff
  already shows.
- **Theorem names** in proof commits: use the exact Lean 4 identifier in backticks so they
  are greppable.

### Type tokens

| Token | When to use |
|-------|-------------|
| `Prove` | A Lean 4 theorem is fully discharged (no sorry) |
| `Scaffold` | A Lean 4 theorem stub is added with sorry as placeholder |
| `Fix` | Bug fix — proof repair, Python logic error, type error |
| `Add` | New module, new agent, new FFI export |
| `Refactor` | Internal restructure with no behavior or spec change |
| `Docs` | CLAUDE.md, inline comments, docstrings — no code change |
| `Test` | Tests added or updated |
| `Chore` | Dependency bumps, CI config, tooling |

## Examples by change type

### Lean 4 proof completed
```
Prove(ftap): noArbitrageMartingale — FTAP no-arbitrage direction

Key lemma: `FtapProofs.existsRNM` (risk-neutral measure existence).
Discharges the forward direction of Harrison-Pliska 1981 Theorem 1.
The backward direction (RNM implies no-arbitrage) follows by linearity
and is handled in `noArbitrageConverse`.
```

### Lean 4 proof scaffolded
```
Scaffold(binomial): putCallParity with sorry placeholder

Skeleton compiles; proof obligation is the CRR replication argument.
Depends on `FtapProofs.NoArbitrage.noArbitrageMartingale` (must land
in ftap-proofs first). Tracking in issue #12.
```

### Python bug fix
```
Fix(backtest): settle_option now handles zero-quantity positions

Previously a ZeroDivisionError was raised when a position had qty=0
at expiry. Guard added before payoff computation. Regression test added
in test_settle_option.py.
```

### New FFI export
```
Add(backtest): BacktestProofs.Options.callPayoff Cython FFI export

Exposes the Lean-proven `callPayoff` function to the Python backtester.
The Cython wrapper validates that the Lean return type matches the
Python float64 contract at the FFI boundary.
```

### Mortgage agent change
```
Fix(mortgage): compliance agent emits DecisionRecord on ECOA rejection

Previously the compliance agent raised an exception on ECOA-triggering
inputs instead of emitting a DecisionRecord with status=DENIED. The Lean
invariant `compliance_emits_record` now validates this path in CI.
```

### Refactor
```
Refactor(ftap): split NoArbitrage module into Existence and Uniqueness

No proof content changed. Splitting improves build times (Uniqueness
does not depend on Existence's auxiliary lemmas) and aligns with
the expected mathlib module structure for the upstream PR.
```

### Top-level / meta
```
Docs(meta): update CLAUDE.md with mortgage-proofs verify-trace command
```

## Branch naming (summary)

Full conventions are in `/contributing-to-eigenq`. Quick reference:

```
proof/<subdir>/<leanIdentifier>    # completing or adding a theorem
feat/<subdir>/<description>        # new capability
fix/<subdir>/<description>         # bug fix
refactor/<subdir>/<description>    # restructure
docs/<subdir>/<description>        # documentation only
mathlib/<subdir>/<module-name>     # mathlib upstream preparation
```

Use lowercase kebab-case for `<description>`, camelCase for `<leanIdentifier>`.

## PR title and description

### Title
- Same format as a commit subject: `<Type>(<scope>): <description>`, ≤70 characters.
- Examples:
  ```
  Prove(ftap): noArbitrageMartingale — FTAP forward direction
  Fix(mortgage): compliance agent DecisionRecord on ECOA rejection
  Add(backtest): callPayoff Cython FFI export
  ```

### Description template

```markdown
## Summary

- <What changed and why — one or two bullets.>
- <Any cross-subdir implications, e.g., "binomial-proofs updated to match new FtapProofs API".>

## Proof sketch (Lean PRs only)

- Main theorem: `<LeanIdentifier>` in `<Module.Path>`
- Key lemmas used: `<lemma1>`, `<lemma2>`
- Non-obvious step: <explain any tricky tactic or mathlib import>
- How any prior `sorry` placeholders were discharged

## Test plan

- [ ] `lake build` passes in `<subdir>/`
- [ ] `grep -rn sorry <subdir>/lean --include="*.lean"` returns empty
- [ ] `pytest` passes (if Python changed)
- [ ] `mypy --strict <subdir>/src/` clean (if Python changed)
- [ ] `lake exe verify-trace` passes on sample trace (mortgage-proofs only)
- [ ] Dependent subdir still builds (if ftap-proofs changed, also build binomial-proofs)
```

## Review checklist

When reviewing a PR (or self-reviewing before merge):

### Lean 4
- [ ] No `sorry` terms anywhere in the subdir (use `grep -rn sorry`)
- [ ] `lake build` passes from a clean checkout
- [ ] New theorems have `-- Proof sketch:` doc comments
- [ ] Theorem names match the Lean 4 identifier referenced in the commit message
- [ ] Imports are minimal — no unused `import Mathlib.X` lines

### Python
- [ ] `pytest` passes with no skipped tests that weren't skipped before
- [ ] `mypy --strict` is clean
- [ ] No data files (`.csv`, `.parquet`, `.h5`, raw tick data) in the diff
- [ ] FFI wrapper (if Cython) validates types at the boundary

### All PRs
- [ ] Branch is scoped to one subdir
- [ ] No private content (no GPA, personal timelines, target firm names in strategy framing)
- [ ] CLAUDE.md updated if new commands or modules were added
- [ ] Commit history is linear (rebase on `main`, do not merge-commit)
