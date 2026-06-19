import Lake
open Lake DSL

package «research-pipeline» where
  version := v!"0.0.1"
  keywords := #["formal verification", "quant research", "backtesting", "no look-ahead"]
  leanOptions := #[
    ⟨`pp.unicode.fun, true⟩,
    ⟨`pp.proofs.withType, false⟩
  ]

-- The no-look-ahead core (NoLookahead.lean) is pure-Lean and builds with no deps.
--
-- PLANNED (see ROADMAP.md): the measure-theoretic upgrade — stating signal
-- 𝓕ₜ-measurability against the natural filtration of the price process — will
-- cite `ftap-proofs`. Uncomment to wire the dependency (pulls ftap's pinned mathlib):
--
-- require «ftap-proofs» from "../../ftap-proofs"
-- require «quant-core» from "../../quant-core/lean"
-- require mathlib from git
--   "https://github.com/leanprover-community/mathlib4.git" @ "d49d6649f50b54b813042b80d5837fd62561b48f"

@[default_target]
lean_lib ResearchPipeline
