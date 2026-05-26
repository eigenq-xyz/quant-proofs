import Lake
open Lake DSL

package «perpetual-proofs» where
  version := v!"0.0.1"
  keywords := #["formal verification", "perpetual futures", "funding rate", "no-arbitrage", "mathlib"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "master"

require «stopped-time-proofs» from "../stopped-time-proofs"

require «ftap-proofs» from "../ftap-proofs"

@[default_target]
lean_lib PerpetualProofs
