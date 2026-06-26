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

-- Pinned to the monorepo-wide canonical mathlib rev (5719ef2, toolchain v4.30.0);
-- this matches ftap-proofs, quant-core, and every other sibling project. Bump the whole
-- monorepo together, never run `lake update` (it would pull mathlib@master and drift).
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "5719ef278ac6921b1a68b558d9282377f93d0b80"


@[default_target]
lean_lib OptionsProofs
