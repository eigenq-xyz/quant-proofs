# CLAUDE.md: optimization-proofs

Lean 4 PGD solver for convex QPs on the budget-leverage constraint set. Exposes two compiled binaries (`pgd_solve`, `pgd_bench`) and an optional Cython FFI layer. 10 theorems, zero `sorry`.

## Build and test

```bash
# From foundations/optimization-proofs/

# Fetch prebuilt mathlib cache (first run per worktree)
lake exe cache get

# Build both binaries and machine-check all proofs
lake build

# Build only the CLI server
lake build pgd_solve

# Run the embedded benchmark (1000 solves at N=10)
lake exe pgd_bench

# Zero-sorry check (empty output = clean)
grep -rn '^\s*sorry\b' --include="*.lean" --exclude-dir=.lake .

# Build the Cython FFI extension (only needed for the FFI path, not the default)
uv run python ffi/setup_ffi.py build_ext --inplace
```

## Architecture

```
foundations/optimization-proofs/
  OptimizationProofs/
    ProblemDefs.lean       abstract problem types: IsInConstraintSet, quadObj, gradObj
    QuadraticLemmas.lean   supporting algebra for the convergence proof (4 thms)
    Shrinkage.lean         Ledoit-Wolf shrinkage: symmetry and PD (2 thms)
    Projection.lean        dual-bisection projection: feasibility and correctness (2 thms)
    Convergence.lean       descent lemma and O(1/k) convergence (2 thms)
    PGD.lean               reference PGD implementation (Array Float)
    PGDFlat.lean           production PGD implementation (FloatArray); used by CLI
    FFI.lean               @[export] bindings for the Cython path
  CLI.lean                 pgd_solve: stdin/stdout server loop
  Main.lean                pgd_bench: benchmark entry point
  ffi/
    pgd_ffi.pyx            Cython bindings (latency hedge; subprocess is default)
    setup_ffi.py           setuptools build
```

## Theorem status

| Theorem | File | Status |
|---------|------|--------|
| `symmetric_bilin_form` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `quadratic_identity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `quadratic_convexity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `polarization_identity` | `QuadraticLemmas.lean` | Complete, 0 sorry |
| `shrinkage_isSymmetric` | `Shrinkage.lean` | Complete, 0 sorry |
| `shrinkage_psd` | `Shrinkage.lean` | Complete, 0 sorry |
| `projection_feasibility` | `Projection.lean` | Complete, 0 sorry |
| `projection_correctness` | `Projection.lean` | Complete, 0 sorry |
| `pgd_descent_lemma` | `Convergence.lean` | Complete, 0 sorry |
| `pgd_convergence` | `Convergence.lean` | Complete, 0 sorry |

## Key module details

**`ProblemDefs.lean`** defines `IsInConstraintSet B L w` (budget sum = B, L1 norm <= L), `quadObj Cov ret w` (mean-variance objective), and `gradObj Cov ret w` (its gradient).

**`Projection.lean`** implements `primalFromDual y θ μ` (soft-thresholding shifted by θ), then proves `projection_feasibility` (existence of valid dual variables for any feasible (B, L) with |B| <= L, via IVT on the budget-maintaining leverage curve) and `projection_correctness` (KKT conditions imply optimality, proved by budget-cancellation, pointwise KKT subgradient bound, and complementary slackness).

**`Convergence.lean`** proves `pgd_descent_lemma` (one PGD step reduces objective by at least (1/2η)(D_k - D_{k+1}), closed by `nlinarith` combining `quadratic_identity`, `quadratic_convexity`, Lipschitz bound, projection inequality, and `polarization_identity`) and `pgd_convergence` (telescopes the descent lemma to the O(1/k) bound; witness K_0 = ceil(D_0 / (2η ε)) + 1).

**`PGDFlat.lean`** is the production implementation used by `CLI.lean`. It uses `FloatArray` (unboxed) rather than `Array Float` (boxed). Both variants implement the same dual-bisection projection algorithm.

## Wire protocol (CLI.lean / pgd_solve)

`serveLoop` reads one line per problem until an empty line or EOF:

```
N  sigma_00 sigma_01 ... sigma_{N-1,N-1}  mu_0 ... mu_{N-1}  lambda_max  leverage_cap
```

Writes one line of N space-separated float64 weights. Float tokens are Python `repr()` strings; `parseFloat` handles decimal and scientific notation.

## Hard rules

- Zero `sorry` as a tactic on main. Doc-comment strings containing "sorry" (describing proof status) are not proof-level sorry and are not flagged by CI.
- Do not change the `CLI.lean` wire protocol without updating `foundations/portfolio-proofs/lean_pgd.py` and its test suite simultaneously.
- Theorem names cited in Python docstrings as guarantees must appear in Lean sources. Verify with: `python3 .github/scripts/check_theorem_refs.py foundations/portfolio-proofs/lean_pgd.py`
- `lake build pgd_solve` must always succeed on main.
- Do not edit `.lean` files to fix doc issues without running `lake build` to confirm the proof still compiles.
