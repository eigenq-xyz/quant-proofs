# stopped-time-proofs

A self-contained Lean 4 library for geometric stopping-time expectations: the probability
mass function, the expectation operator, and its core algebraic and order properties
including strict monotonicity. No finance content; written to mathlib conventions as an
upstream-PR candidate.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

`geometricExpectation p f` is the expectation of `f : ℕ → ℝ` under a geometric random variable with success probability `p`:

$$\mathrm{geometricExpectation}(p, f) = \sum_{k=0}^{\infty} (1-p)^k\, p\, f(k).$$

| Guarantee | Theorem |
|---|---|
| `geomPMF p k = (1-p)^k * p` is non-negative | `geomPMF_nonneg` |
| `geomPMF` sums to one over `ℕ` (a genuine probability mass function) | `geomPMF_tsum_eq_one` |
| `geometricExpectation` is summable for bounded `f` | `geometricExpectation_summable` |
| One-step unrolling recurrence | `geometricExpectation_unroll` |
| Expectation of a constant function | `geometricExpectation_const` |
| Monotonicity in `f` | `geometricExpectation_mono` |
| `geomPMF` is strictly positive | `geomPMF_pos` |
| Strict monotonicity of the expectation operator | `geometricExpectation_strict_mono` |

Eight lemmas, zero `sorry` (Lean's placeholder tactic for an unproven step; none remain here).
`#print axioms` (Lean's command listing the axioms a proof ultimately rests on) on each
reports only `[propext, Classical.choice, Quot.sound]`, the three axioms mathlib itself
relies on, not any unproven assumption specific to this project.

## Build and verify

```bash
cd extensions/stopped-time-proofs
lake exe cache get
lake build
grep -rn '^[[:space:]]*sorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

Full build/test matrix: see CLAUDE.md.

## Dependencies

No imports from any finance library. Used by
[`extensions/perpetual-proofs/`](../perpetual-proofs/): `geometricExpectation_strict_mono`
(strict monotonicity: a strictly larger input function gives a strictly larger expectation)
is load-bearing for the inverse-perpetual convexity correction (Theorem 3).

If `geomPMF` and `geometricExpectation` are accepted into mathlib, this module can be
deleted and downstream importers switch to `Mathlib` directly.

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
