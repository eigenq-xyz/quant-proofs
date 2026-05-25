import Lake
open Lake DSL

package «optimization-proofs» where
  version := v!"0.0.1"
  keywords := #["optimization", "portfolio", "PGD", "formal verification"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

-- No mathlib dependency yet — pure computational implementation.

@[default_target]
lean_lib OptimizationProofs

lean_exe pgd_bench where
  root := `Main

lean_exe pgd_solve where
  root := `CLI
