import StoppedTimeProofs.GeomPMF
import StoppedTimeProofs.GeomExpectation
import StoppedTimeProofs.Jensen

/-!
# StoppedTimeProofs

General-purpose library for probability-weighted expectations under a geometric
stopping time. No finance-specific content.

**Primary definition** (`StoppedTimeProofs.GeomExpectation.geometricExpectation`):

```
geometricExpectation p f = ∑' k, (1-p)^k * p * f k
```

The weights `geomPMF p k := (1-p)^k * p` form a probability mass function on `ℕ`
(proved in `geomPMF_tsum_eq_one`), so `geometricExpectation` is a genuine
probability-weighted average of `f`.

## Module structure

- `StoppedTimeProofs.GeomPMF` — `geomPMF`, non-negativity, PMF sum-to-1
- `StoppedTimeProofs.GeomExpectation` — `geometricExpectation`, convergence,
  one-step unrolling, constant lemma, monotonicity
- `StoppedTimeProofs.Jensen` — strict monotonicity of `geometricExpectation` under
  pointwise strict domination (the targeted Jensen-style lemma consumed by
  `perpetual-proofs`)

## Mathlib PR candidacy

This module has no imports from any finance library. If `geomPMF` and
`geometricExpectation` are accepted into Mathlib, this library can be deleted
and downstream modules can import from Mathlib directly.

## Status

Complete, zero `sorry`. `geometricExpectation_strict_mono` (`Jensen.lean`) is
load-bearing for `perpetual-proofs` Theorem 3 (the inverse-perp convexity
correction). See `SPEC.md` in `perpetual-proofs/` for the proof roadmap.
-/
