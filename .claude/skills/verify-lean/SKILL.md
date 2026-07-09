---
name: verify-lean
description: >
  Level 1 verification: machine-checks all Lean 4 proofs across research-pipeline,
  the foundations/ tier (quant-core, ftap-proofs, options-proofs, optimization-proofs,
  portfolio-proofs), and the extensions/ tier (vrp-proofs, hedge-proofs, perpetual-proofs,
  stopped-time-proofs, mortgage-proofs). Runs lake build and zero-sorry check. Use when
  any .lean file changes, or as the first step of /verify.
paths:
  - "**/*.lean"
  - "**/lakefile.*"
  - "**/lean-toolchain"
allowed-tools: Bash(lake *) Bash(grep *) Bash(git *)
---

# Verify Lean — Level 1

## Commands

```bash
# Build every Lean subdir — quant-core and ftap-proofs and stopped-time-proofs first
# (others in the same tier depend on them; see "Dependency chain" below)
for dir in research-pipeline/lean foundations/quant-core/lean foundations/ftap-proofs \
           foundations/options-proofs foundations/optimization-proofs foundations/portfolio-proofs/lean \
           extensions/vrp-proofs extensions/hedge-proofs extensions/stopped-time-proofs \
           extensions/perpetual-proofs extensions/mortgage-proofs/lean; do
  echo "=== $dir ===" && (cd "$dir" && lake exe cache get || true && lake build) || exit 1
done

# Zero-sorry check across all subdirs
for dir in research-pipeline/lean foundations/quant-core/lean foundations/ftap-proofs \
           foundations/options-proofs foundations/optimization-proofs foundations/portfolio-proofs/lean \
           extensions/vrp-proofs extensions/hedge-proofs extensions/stopped-time-proofs \
           extensions/perpetual-proofs extensions/mortgage-proofs/lean; do
  count=$(grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake "$dir/" | grep -v '^\s*--' | wc -l | tr -d ' ')
  [ "$count" -gt 0 ] && echo "FAIL: $count sorry in $dir" && exit 1 || echo "PASS: zero sorry in $dir"
done
```

If this loop and `onboard-to-eigenq/SKILL.md`'s "Build and test commands" table ever disagree,
that table wins — it's the authoritative current list.

## Dependency chain

- `quant-core`: no Lean deps beyond mathlib — build first.
- `ftap-proofs`: standalone (the spine); build before `options-proofs` and `research-pipeline`.
- `options-proofs`: depends on `ftap-proofs`. `vrp-proofs` depends on `options-proofs`.
- `hedge-proofs`: depends on `quant-core`.
- `stopped-time-proofs`: standalone; build before `perpetual-proofs` (heavy dependency).
- `optimization-proofs`: no sibling Lean deps. `portfolio-proofs`'s Python layer routes
  through its compiled binary, but no Lean-to-Lean import exists between them.
- `mortgage-proofs`: fully self-contained, no sibling imports.

If a dependent subdir fails, build its dependency first and confirm it passes alone.

## Mathlib cache

Run `lake exe cache get` before `lake build` in CI and after `lake update`.
A cache miss turns a 5-minute build into a 60-minute build.

## Common failures

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| `unknown identifier 'Mathlib.X'` | Mathlib lemma renamed upstream | `lake update`, search mathlib4 CHANGELOG or `exact?` |
| `type mismatch` | Proof logic error or API change | Read the InfoView goal state carefully |
| `unknown tactic 'omega'` | Missing `import Mathlib.Tactic.Omega` | Add specific import |
| Sorry found | Someone added sorry on main | Fix the proof; sorry on main is a hard block |

## Passes when

All eleven subdirs: `lake build` exits 0. Zero sorry terms found.
