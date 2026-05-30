import Lake
open Lake DSL

package «options-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "binomial model", "options", "put-call parity", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require «quant-core» from "../quant-core/lean"

require «ftap-proofs» from "../ftap-proofs"

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "d49d6649f50b54b813042b80d5837fd62561b48f"


@[default_target]
lean_lib OptionsProofs
