import Lake
open Lake DSL

package «backtest-proofs» where
  version := v!"0.1.0"
  keywords := #["formal verification", "options", "finance"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "5719ef278ac6921b1a68b558d9282377f93d0b80"

require «quant-core» from "../../foundations/quant-core/lean"

@[default_target]
lean_lib BacktestProofs where
  globs := #[.submodules `BacktestProofs]
  -- Lean generates C files automatically in .lake/build/ir/
  -- These will be compiled to .o files by Lake
