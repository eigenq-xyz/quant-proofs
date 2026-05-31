# stopped-time-proofs

Lean 4 library for probability-weighted expectations under a geometric stopping time.

**No finance-specific content.** This module is a Mathlib PR candidate.

## Primary definition

`geometricExpectation p f` is the expectation of `f : ℕ → ℝ` under a geometric
random variable with success probability `p`:

$$\mathrm{geometricExpectation}(p, f) = \sum_{k=0}^\infty (1-p)^k \cdot p \cdot f(k)$$

The weights `geomPMF p k := (1-p)^k * p` form a valid probability mass function on `ℕ`
(`geomPMF_tsum_eq_one`), so `geometricExpectation` is a genuine expectation operator.

## Theorem status

All theorems are proved, zero `sorry`.

| Theorem | File | Status |
|---|---|---|
| `geomPMF_nonneg` | `GeomPMF.lean` | Proved (G1.2) |
| `geomPMF_tsum_eq_one` | `GeomPMF.lean` | Proved (G1.3) |
| `geometricExpectation_summable` | `GeomExpectation.lean` | Proved (G1.5) |
| `geometricExpectation_unroll` | `GeomExpectation.lean` | Proved (G1.6) |
| `geometricExpectation_const` | `GeomExpectation.lean` | Proved (G1.7) |
| `geometricExpectation_mono` | `GeomExpectation.lean` | Proved (G1.8) |
| `geomPMF_pos` | `Jensen.lean` | Proved (G2.1) |
| `geometricExpectation_strict_mono` | `Jensen.lean` | Proved (G2.2) |

## Project structure

```
stopped-time-proofs/
  StoppedTimeProofs.lean: root module; re-exports all submodules
  StoppedTimeProofs/
    GeomPMF.lean: geometric PMF definition and normalization theorems
    GeomExpectation.lean: GeometricExpectation operator and key properties
    Jensen.lean: strict monotonicity of the geometric expectation (the Jensen-type step)
  lakefile.lean: lake project config (mathlib dependency)
  lean-toolchain: pinned Lean 4 toolchain version
```

## Build

```bash
cd stopped-time-proofs
lake exe cache get   # fetch mathlib cache (first run)
lake build
```

## Used by

- [`perpetual-proofs`](../perpetual-proofs/): imports `geometricExpectation` and
  Jensen's inequality for the perpetual futures pricing theorems.

## Mathlib candidacy

If `geomPMF` and `geometricExpectation` are accepted into Mathlib upstream, this
module is deleted and `perpetual-proofs/lakefile.lean` switches the import to
`mathlib` directly.

## License

Apache License 2.0: matches mathlib's licensing.
