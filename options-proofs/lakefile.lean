import Lake
open Lake DSL

package «options-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "binomial model", "options", "put-call parity", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

require «quant-core» from "../quant-core/lean"


@[default_target]
lean_lib OptionsProofs
