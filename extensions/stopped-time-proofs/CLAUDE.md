# CLAUDE.md: stopped-time-proofs

Self-contained Lean 4 library for geometric stopping-time expectations. No finance content. Mathlib-PR candidate. Complete, zero `sorry`.

## Build and test

```bash
cd extensions/stopped-time-proofs
lake exe cache get          # fetch prebuilt mathlib (once per worktree)
lake build                  # compile; must exit 0
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # must be empty
```

## Architecture

| File | Role |
| ---- | ---- |
| `StoppedTimeProofs/GeomPMF.lean` | Core: `geomPMF` definition, non-negativity, sum-to-one |
| `StoppedTimeProofs/GeomExpectation.lean` | Core: `geometricExpectation` definition, summability, unrolling, constant, monotonicity |
| `StoppedTimeProofs/Jensen.lean` | Jensen: strict positivity of `geomPMF`; `geometricExpectation_strict_mono` (load-bearing for `perpetual-proofs` Theorem 3) |
| `StoppedTimeProofs.lean` | Top-level re-export |
| `lakefile.lean` | Pins mathlib to a specific commit |

**Exported definitions:** `geomPMF`, `geometricExpectation`.

**Exported lemmas (8, all zero `sorry`):** `geomPMF_nonneg`, `geomPMF_tsum_eq_one`, `geometricExpectation_summable`, `geometricExpectation_unroll`, `geometricExpectation_const`, `geometricExpectation_mono`, `geomPMF_pos`, `geometricExpectation_strict_mono`.

## Mathlib PR intent

No imports from any finance library. If `geomPMF` and `geometricExpectation` land in mathlib, delete this module and update the `perpetual-proofs` import.

## Hard rules

- Zero `sorry` on main. No exceptions.
- Do not add finance-domain content (no asset prices, rates, or payoff logic).
- Do not bump the mathlib pin without verifying that `perpetual-proofs` still builds against the new revision.
- Do not suppress linter warnings with `set_option linter.X false`; fix the root cause.
