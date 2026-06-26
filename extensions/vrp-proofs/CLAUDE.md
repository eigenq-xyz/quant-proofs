# vrp-proofs

Lean 4 proofs of discrete variance-risk-premium identities on the CRR binomial tree.
Namespace: `VrpProofs`. Depends on `options-proofs` (which cites `ftap-proofs`).

## Build

```bash
cd extensions/vrp-proofs
lake exe cache get    # mathlib precompile cache; run before first build in a worktree
lake build
```

## Test

```bash
# Zero-sorry check (empty output = clean):
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

## Architecture

| File | Contents |
|------|----------|
| `VrpProofs/Replication.lean` | `nodeVal`, `nodeDelta`, `nodeBond`, `replPortfolio`; the main theorem `replicates` (perfect path-by-path replication) |
| `VrpProofs/VarianceRiskPremium.lean` | `binomDensity`, `binomExp`, `claimPrice`, `physicalPV`, `vrp`; theorems `vrp_decomposition`, `vrp_pos_iff`, and the documented non-claims (convex-payoff bridge is false; gamma-variance-gap is vacuous) |
| `lakefile.lean` | Declares `require «options-proofs»` from `../../foundations/options-proofs`; mathlib pinned to monorepo-wide rev |

## Key identifiers

- `replicates` (CLAIM 1): `replPortfolio T … T ω = g (terminalSpot T S₀ u d ω)` on every path.
- `vrp_decomposition` (CLAIM 2a): `vrp = (E^Q[G] − E^P[G]) / (1+r)^T`.
- `vrp_pos_iff` (CLAIM 2b): `0 < vrp ↔ binomExp p G < binomExp q G`.

## Hard rules

- Zero `sorry` on `main`. No exceptions.
- Do not remove or weaken the non-claims note at the end of `VarianceRiskPremium.lean`; it is
  the documented reason the convex-payoff bridge and the gamma-variance-gap identity are absent.
- Do not run `lake update`: it bumps mathlib to HEAD and drifts from sibling proofs. Bump the
  whole monorepo together by updating the pinned rev in every `lakefile.lean` simultaneously.
- No private content: no GPA, no grades, no target firm names, no application timelines.

## Dependency context

`options-proofs` provides: `CRRState T`, `crrPrice`, `terminalSpot`, `riskNeutralProb`,
`ups`, `crrRNDensity`, `crrRNMeasure`, `crrRNMeasure_integral_eq_sum`, `rnPrice`,
`crrPrice_succ`. All are in the `OptionsProofs` namespace, opened in both files.
