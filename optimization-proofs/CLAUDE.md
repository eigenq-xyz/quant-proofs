# CLAUDE.md — optimization-proofs

Lean 4 implementation of the PGD portfolio solver core: computational
execution modules plus formally verified proof modules for convergence,
projection correctness, and covariance shrinkage.

## What this project is

A high-performance Lean 4 quadratic program solver using Projected Gradient
Descent with an analytical O(N log N) dual-bisection projection onto
`{sum(w)=1, sum|w|≤L}`.  Exposes two compiled binaries:

- **`pgd_solve`** — stdin/stdout server; Python's primary integration point.
- **`pgd_bench`** — benchmark binary with embedded test data (N=10, 1000 runs).

Also contains a Cython FFI layer (`ffi/`) that was the previous integration
path; it is preserved as a latency hedge but the subprocess path is the
default.

## Architecture

```
optimization-proofs/
  lakefile.lean               — package config; two lean_exe targets
  lean-toolchain              — Lean version lock
  OptimizationProofs/
    PGD.lean                  — boxed Array Float variant (reference impl)
    PGDFlat.lean              — unboxed FloatArray variant (production; used by CLI)
    FFI.lean                  — @[export] bindings for Cython path (unused by default)
    ProblemDefs.lean          — abstract types: IsInConstraintSet, quadObj, gradObj
    QuadraticLemmas.lean      — supporting lemmas (0 sorry): symmetric_bilin_form,
                                quadratic_identity, quadratic_convexity, polarization_identity
    Shrinkage.lean            — Ledoit-Wolf shrinkage theorems (0 sorry):
                                shrinkage_isSymmetric, shrinkage_psd
    Projection.lean           — dual-bisection projection proofs:
                                projection_feasibility (Cases 1+2a complete; Case 2b open),
                                projection_correctness (complete, 0 sorry)
    Convergence.lean          — PGD convergence proofs:
                                pgd_descent_lemma (proof body complete),
                                pgd_convergence (proof body complete)
  CLI.lean                    — stdin/stdout server loop (pgd_solve entry point)
  Main.lean                   — benchmark (pgd_bench entry point)
  ffi/
    pgd_ffi.pyx               — Cython bindings (not the default path)
    setup_ffi.py              — setuptools build for the Cython extension
```

## Theorem status

| Theorem | File | Status |
|---------|------|--------|
| `shrinkage_isSymmetric` | `Shrinkage.lean` | Complete, 0 sorry |
| `shrinkage_psd` | `Shrinkage.lean` | Complete, 0 sorry |
| `symmetric_bilin_form` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `quadratic_identity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `quadratic_convexity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `polarization_identity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `projection_feasibility` | `Projection.lean` | Cases 1+2a complete; Case 2b open (requires IVT) |
| `projection_correctness` | `Projection.lean` | **Complete, 0 sorry** |
| `pgd_descent_lemma` | `Convergence.lean` | Proof body complete |
| `pgd_convergence` | `Convergence.lean` | Proof body complete |

## Build & test commands

```bash
# Build both binaries (from optimization-proofs/)
lake build

# Build only the CLI server
lake build pgd_solve

# Run the benchmark (prints timing for 1000 solves at N=10)
lake exe pgd_bench

# Check zero sorry (tactic uses only; doc-comment strings are not flagged)
grep -rn '^\s*sorry\b' --include="*.lean" --exclude-dir=.lake .

# Build the Cython FFI extension (only if needed for the FFI path)
uv run python ffi/setup_ffi.py build_ext --inplace
```

## Wire protocol (CLI.lean)

`serveLoop` in `CLI.lean` reads one line per problem until an empty line:

```
N  sigma_00 sigma_01 … sigma_{N-1,N-1}  mu_0 … mu_{N-1}  lambda_max  leverage_cap
```

Writes one line of N space-separated float64 weights.  Terminates on an
empty line or EOF.  Float tokens are Python `repr()` strings; the custom
`parseFloat` function in `CLI.lean` handles both decimal and scientific
notation.

## Lean module map

| File | What it does | Key names |
|------|-------------|-----------|
| `PGDFlat.lean` | PGD loop + projection (FloatArray, production) | `pgdFlat`, `projectL1F`, `pgdStepF`, `matVecFlat` |
| `PGD.lean` | PGD loop + projection (Array Float, reference) | `pgd`, `projectL1`, `pgdStep`, `matVecMul` |
| `ProblemDefs.lean` | Abstract problem spec types | `IsInConstraintSet`, `quadObj`, `gradObj` |
| `QuadraticLemmas.lean` | Supporting lemmas for convergence proof | `quadratic_identity`, `quadratic_convexity`, `polarization_identity` |
| `Shrinkage.lean` | Ledoit-Wolf shrinkage correctness | `shrinkage_isSymmetric`, `shrinkage_psd` |
| `Projection.lean` | Projection feasibility + optimality | `projection_feasibility`, `projection_correctness` |
| `Convergence.lean` | PGD descent + convergence | `pgd_descent_lemma`, `pgd_convergence` |
| `FFI.lean` | `@[export]` wrappers for Cython | `pgdSolve`, `pgdSolveFlat`, `faEmpty` |
| `CLI.lean` | stdin/stdout server | `serveLoop`, `solveTokens`, `parseFloat` |
| `Main.lean` | Benchmark | `main` |

## Hard rules

- **Zero `sorry` as a tactic** on main.  Doc-comment strings containing the
  word "sorry" (describing proof status) are not proof-level sorry uses and
  are not flagged by the CI check.
- **Do not change the `CLI.lean` wire protocol** without updating
  `portfolio-proofs/lean_pgd.py` and its test suite simultaneously.
- Theorem names cited in Python docstrings as guarantees must appear in
  Lean sources.  Use the theorem cross-reference check:
  `python3 .github/scripts/check_theorem_refs.py portfolio-proofs/lean_pgd.py`
- `lake build pgd_solve` must always succeed on main.
