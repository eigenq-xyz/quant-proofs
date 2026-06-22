import Lake
open Lake DSL

package «ftap-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "asset pricing", "finance", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

@[default_target]
lean_lib FtapProofs
