# vrp-proofs

Discrete variance-risk-premium identities on the Cox-Ross-Rubinstein binomial tree,
formally verified in Lean 4. Cites `options-proofs`.

## What it proves

**Three results, zero `sorry`:**

1. **Replication** (`VrpProofs.Replication.replicates`): in the CRR market with
   `0 < d < u`, initial stock price `S₀ > 0`, and rate `r > −1`, the self-financing
   delta-hedging portfolio that starts at the backward-induction value `V₀(S₀)` reproduces
   the terminal payoff `g(S_T)` exactly on every path of the `{u,d}^T` tree. The proof is
   finite induction plus ring arithmetic, with no continuous stochastic calculus.

2. **VRP decomposition** (`VrpProofs.VarianceRiskPremium.vrp_decomposition`): the
   variance risk premium equals the discounted gap between the risk-neutral and physical
   expectations of the payoff:

   ```
   vrp = (E^Q[G] − E^P[G]) / (1 + r)^T
   ```

   This is an algebraic identity, not a no-arbitrage argument.

3. **VRP sign** (`VrpProofs.VarianceRiskPremium.vrp_pos_iff`): the VRP is positive if
   and only if the risk-neutral measure prices the claim above the physical measure:

   ```
   vrp > 0  ↔  E^P[G] < E^Q[G]
   ```

   This holds for any `r > −1` and needs no conditions on whether `q` is a genuine
   risk-neutral probability. The expectation gap is the complete, sharp criterion.

## What this module does NOT claim (by design)

Two apparent extensions are explicitly not proved, and the source documents why:

- **Convex-payoff bridge.** The statement "`q ≤ p` and `G` convex implies `E^P ≤ E^Q`"
  is **false** on a fixed CRR tree. Holding `u, d` fixed, a lower up-probability shifts
  the law toward lower prices; for an increasing convex payoff such as a call, this
  lowers, not raises, the risk-neutral expectation. The genuine variance risk premium
  compares an implied tree against a realized tree (two distinct `(u, d)` pairs) and is
  deliberately out of scope here.

- **Gamma-variance-gap P&L identity.** The claim that delta-hedged P&L equals the
  gamma-times-variance-gap term is vacuous in a complete binomial market: perfect
  replication (Claim 1) implies the terminal P&L is zero on every path, so the identity
  holds trivially with zero on both sides and carries no information.

The two claims that are made are the honest, sharp content for a single CRR tree.

## Dependency

`vrp-proofs` imports `options-proofs`, which in turn cites `ftap-proofs`
(Harrison-Pliska 1981, discrete FTAP). The CRR market definition, risk-neutral
probability, and put-call parity live in `options-proofs`.

## Build

```bash
cd extensions/vrp-proofs
lake exe cache get   # fetch the mathlib precompile cache (~1 min on first run)
lake build
```

## Test

```bash
# Zero-sorry check (empty output means clean):
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .
```

## Project structure

```
extensions/vrp-proofs/
  VrpProofs/
    Replication.lean          -- path-by-path replication theorem (replicates)
    VarianceRiskPremium.lean  -- vrp_decomposition, vrp_pos_iff, and the non-claims note
  lakefile.lean               -- requires options-proofs; mathlib pinned to monorepo rev
```

## Reference

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach."
*Journal of Financial Economics* 7, no. 3 (1979): 229-263.
