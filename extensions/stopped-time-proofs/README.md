# stopped-time-proofs

A self-contained Lean 4 library for geometric stopping-time expectations: the probability mass function, the expectation operator, and its core algebraic and order properties including strict monotonicity. No finance content; written to mathlib conventions as an upstream-PR candidate. Complete, zero `sorry`, axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

`geometricExpectation p f` is the expectation of `f : ℕ → ℝ` under a geometric random variable with success probability `p`:

$$\mathrm{geometricExpectation}(p, f) = \sum_{k=0}^{\infty} (1-p)^k\, p\, f(k).$$

The weights `geomPMF p k = (1-p)^k * p` form a genuine probability mass function on `ℕ` (`geomPMF_tsum_eq_one`), so `geometricExpectation` is a true probability-weighted average. The library proves the properties downstream results need: summability for bounded `f`, a one-step unrolling recurrence, the constant case, monotonicity, and strict monotonicity.

## Build and verify

```bash
cd extensions/stopped-time-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile and machine-check every proof
grep -rn '^[[:space:]]*sorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

`#print axioms` on the lemmas reports only `[propext, Classical.choice, Quot.sound]`.

## Project structure

| File | Contents |
| ---- | -------- |
| `StoppedTimeProofs/GeomPMF.lean` | `geomPMF` definition; non-negativity (`geomPMF_nonneg`) and sum-to-one (`geomPMF_tsum_eq_one`) |
| `StoppedTimeProofs/GeomExpectation.lean` | `geometricExpectation` definition; summability, one-step unrolling, constant, and monotonicity lemmas |
| `StoppedTimeProofs/Jensen.lean` | Strict positivity of `geomPMF` (`geomPMF_pos`) and strict monotonicity of the expectation operator (`geometricExpectation_strict_mono`) |
| `StoppedTimeProofs.lean` | Top-level import |
| `lakefile.lean` | Package definition; pins mathlib commit |

Eight lemmas are proved with zero `sorry`: `geomPMF_nonneg`, `geomPMF_tsum_eq_one`, `geometricExpectation_summable`, `geometricExpectation_unroll`, `geometricExpectation_const`, `geometricExpectation_mono`, `geomPMF_pos`, `geometricExpectation_strict_mono`.

## Mathlib PR candidacy

This library has no imports from any finance library. If `geomPMF` and `geometricExpectation` are accepted into mathlib, this module can be deleted and downstream importers switch to `Mathlib` directly.

## Used by

[`extensions/perpetual-proofs/`](../perpetual-proofs/): the strict-monotonicity lemma (`geometricExpectation_strict_mono`) is load-bearing for the inverse-perpetual convexity correction (Theorem 3).

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
