# stopped-time-proofs

> A small, self-contained Lean 4 library for expectations under a geometric stopping time: the probability mass function, the expectation operator, and its core properties including strict monotonicity. **No finance content**, written to mathlib conventions as an upstream-PR candidate. Zero `sorry`, axioms verified.

[![Lean CI](https://github.com/eigenq-xyz/quant-proofs/actions/workflows/lean-ci.yml/badge.svg)](https://github.com/eigenq-xyz/quant-proofs/actions)

## What it provides

`geometricExpectation p f` is the expectation of `f : ℕ → ℝ` under a geometric random variable with success probability `p`:

$$\mathrm{geometricExpectation}(p, f) = \sum_{k=0}^{\infty} (1-p)^k\, p\, f(k).$$

The weights `geomPMF p k = (1-p)^k · p` are proved to form a genuine probability mass function on `ℕ` (`geomPMF_tsum_eq_one`), so this is a true expectation operator, and the library proves the algebraic properties downstream results need: summability, an unrolling recurrence, the constant case, and monotonicity.

## Why it exists separately

The geometric-stopping-time expectation is general probability infrastructure with no finance in it, which makes it a clean candidate for mathlib. It is factored out here so [`perpetual-proofs`](../perpetual-proofs/) can import it for the perpetual-futures pricing theorems, where the price is an expectation of the underlying sampled at a geometric stopping time. If `geomPMF` and `geometricExpectation` are accepted upstream, this module is deleted and the dependent import switches to `mathlib` directly.

## Verify it yourself

```bash
cd extensions/stopped-time-proofs
lake exe cache get     # fetch prebuilt mathlib (first run only)
lake build             # compile and machine-check every proof
grep -rn '^[[:space:]]*sorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

`#print axioms` on the lemmas reports only `[propext, Classical.choice, Quot.sound]`.

## What's inside

| File | Contents |
| ---- | -------- |
| `GeomPMF.lean` | `geomPMF`; nonnegativity, positivity, and that it sums to one |
| `GeomExpectation.lean` | `geometricExpectation`; summability, unrolling, constant, monotonicity |
| `Jensen.lean` | strict monotonicity of the expectation operator |

All eight lemmas are proved with zero `sorry`: `geomPMF_nonneg`, `geomPMF_pos`, `geomPMF_tsum_eq_one`, `geometricExpectation_summable`, `geometricExpectation_unroll`, `geometricExpectation_const`, `geometricExpectation_mono`, `geometricExpectation_strict_mono`.

## Used by

- [`perpetual-proofs`](../perpetual-proofs/): the geometric-stopping-time expectation and its strict monotonicity (the latter gives the inverse-perpetual convexity correction).

## License

Apache License 2.0, matching mathlib so the work can flow upstream.
