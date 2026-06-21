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
-- The measure-theoretic upgrade (Measurability.lean) states signal
-- 𝓕ₜ-measurability against the natural filtration of the price process and
-- cites `ftap-proofs`. The mathlib rev below is pinned to ftap's resolved rev
-- (d49d66…) so the shared mathlib build stays consistent; do NOT run
-- `lake update` (it would bump mathlib to master and break the pin).
require «ftap-proofs» from "../../ftap-proofs"
require mathlib from git
  "https://github.com/leanprover-community/mathlib4.git" @ "d49d6649f50b54b813042b80d5837fd62561b48f"

@[default_target]
lean_lib ResearchPipeline
