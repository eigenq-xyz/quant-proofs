import Lake
open Lake DSL

package «quant-core» where
  version := v!"0.1.0"
  keywords := #["formal verification", "options", "finance", "quantitative"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "5719ef278ac6921b1a68b558d9282377f93d0b80"

@[default_target]
lean_lib QuantCore where
  globs := #[.submodules `QuantCore]
