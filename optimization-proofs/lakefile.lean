import Lake
open Lake DSL

package «optimization-proofs» where
  version := v!"0.0.1"
  keywords := #["optimization", "portfolio", "PGD", "formal verification"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

-- Mathlib required for proof modules (Shrinkage, Projection, Convergence).
-- Computational modules (PGD, PGDFlat, FFI, CLI) compile without mathlib;
-- they are included in the same library target so lake only builds mathlib once.
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

@[default_target]
lean_lib OptimizationProofs

lean_exe pgd_bench where
  root := `Main

lean_exe pgd_solve where
  root := `CLI
