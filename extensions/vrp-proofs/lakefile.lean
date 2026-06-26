import Lake
open Lake DSL

package «vrp-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "binomial model", "delta hedging",
    "variance risk premium", "replication", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require «options-proofs» from "../../foundations/options-proofs"

-- Pinned to the monorepo-wide canonical mathlib rev (5719ef2, toolchain v4.30.0);
-- this matches options-proofs, ftap-proofs, quant-core, and every sibling. Bump the whole
-- monorepo together, never run `lake update` (it would pull mathlib@master and drift).
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "5719ef278ac6921b1a68b558d9282377f93d0b80"

@[default_target]
lean_lib VrpProofs
