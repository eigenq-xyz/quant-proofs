# CLAUDE.md — optimization-proofs

Lean 4 implementation of the PGD portfolio solver core.  This module is
**pure computation** — no theorems yet, no FFI, no Python dependencies.
Formal proofs (`pgd_convergence`, `projection_correctness`) are on the
roadmap; see `README.md` for the planned proof strategy.

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
  CLI.lean                    — stdin/stdout server loop (pgd_solve entry point)
  Main.lean                   — benchmark (pgd_bench entry point)
  ffi/
    pgd_ffi.pyx               — Cython bindings (not the default path)
    setup_ffi.py              — setuptools build for the Cython extension
```

## Build & test commands

```bash
# Build both binaries (from optimization-proofs/)
lake build

# Build only the CLI server
lake build pgd_solve

# Run the benchmark (prints timing for 1000 solves at N=10)
lake exe pgd_bench

# Check zero sorry
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .

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
| `PGDFlat.lean` | PGD loop + projection (FloatArray) | `pgdFlat`, `projectL1F`, `pgdStepF`, `matVecFlat` |
| `PGD.lean` | PGD loop + projection (Array Float) | `pgd`, `projectL1`, `pgdStep`, `matVecMul` |
| `FFI.lean` | `@[export]` wrappers for Cython | `pgdSolve`, `pgdSolveFlat`, `faEmpty` |
| `CLI.lean` | stdin/stdout server | `serveLoop`, `solveTokens`, `parseFloat` |
| `Main.lean` | Benchmark | `main` |

## Hard rules

- **No `sorry`**.  This module contains only computational definitions, not
  proofs, so there should be nothing to sorry.
- **Do not change the `CLI.lean` wire protocol** without updating
  `portfolio-proofs/lean_pgd.py` and its test suite simultaneously.
- Theorem names cited in Python docstrings as guarantees must appear in
  Lean sources.  Currently no theorems exist — all proof obligations are
  planned.  Use the word "planned" when referring to future theorems.
- `lake build pgd_solve` must always succeed on main.
