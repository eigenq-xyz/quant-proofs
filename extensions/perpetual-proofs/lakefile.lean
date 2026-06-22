import Lake
open Lake DSL

package «perpetual-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "perpetual futures", "funding rate", "no-arbitrage", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require «stopped-time-proofs» from "../stopped-time-proofs"

require «ftap-proofs» from "../../foundations/ftap-proofs"

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

@[default_target]
lean_lib PerpetualProofs
