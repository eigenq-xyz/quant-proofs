import Lake
open Lake DSL

package «stopped-time-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "geometric distribution", "stopping time", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

@[default_target]
lean_lib StoppedTimeProofs
