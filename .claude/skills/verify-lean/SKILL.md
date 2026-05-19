---
name: verify-lean
description: >
  Level 1 verification: machine-checks all Lean 4 proofs across backtest-proofs,
  ftap-proofs, options-proofs, and mortgage-proofs. Runs lake build and zero-sorry
  check. Use when any .lean file changes, or as the first step of /verify.
paths:
  - "**/*.lean"
  - "**/lakefile.*"
  - "**/lean-toolchain"
allowed-tools: Bash(lake *) Bash(grep *) Bash(git *)
---

# Verify Lean — Level 1

## Commands

```bash
# Build all four Lean subdirs
for dir in backtest-proofs/lean ftap-proofs options-proofs mortgage-proofs/lean; do
  echo "=== $dir ===" && (cd "$dir" && lake exe cache get || true && lake build) || exit 1
done

# Zero-sorry check across all subdirs
for dir in backtest-proofs/lean ftap-proofs options-proofs mortgage-proofs/lean; do
  count=$(grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake "$dir/" | grep -v '^\s*--' | wc -l | tr -d ' ')
  [ "$count" -gt 0 ] && echo "FAIL: $count sorry in $dir" && exit 1 || echo "PASS: zero sorry in $dir"
done
```

## Dependency chain

`options-proofs` depends on `ftap-proofs`. If `options-proofs` fails, build `ftap-proofs` first and confirm it passes independently.

## Mathlib cache

Always run `lake exe cache get` before `lake build` in CI and after `lake update`.
A cache miss turns a 5-minute build into a 60-minute build.

## Common failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `unknown identifier 'Mathlib.X'` | Mathlib lemma renamed upstream | `lake update`, search mathlib4 CHANGELOG or `exact?` |
| `type mismatch` | Proof logic error or API change | Read the InfoView goal state carefully |
| `unknown tactic 'omega'` | Missing `import Mathlib.Tactic.Omega` | Add specific import |
| Sorry found | Someone added sorry on main | Fix the proof; sorry on main is a hard block |

## Passes when

All four subdirs: `lake build` exits 0, zero sorry terms found.
