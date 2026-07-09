# vrp-proofs

Discrete variance-risk-premium identities on the Cox-Ross-Rubinstein (CRR) binomial tree,
proved correct in Lean 4. Cites `options-proofs`.

## What it proves

Three results, zero `sorry` (Lean's placeholder tactic for an unproven step; none remain here).
Confirm with `grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .`, which returns empty.

| Guarantee | Theorem |
|---|---|
| In the CRR market with `0 < d < u`, `S₀ > 0`, `r > −1`, the self-financing (no cash added or withdrawn after inception) delta-hedging portfolio starting at the backward-induction value `V₀(S₀)` replicates (exactly reproduces) the terminal payoff `g(S_T)` on every path of the `{u,d}^T` tree. Proof is finite induction plus ring arithmetic, no continuous stochastic calculus. | `VrpProofs.Replication.replicates` |
| The variance risk premium equals the discounted gap between risk-neutral and physical expectations: `vrp = (E^Q[G] − E^P[G]) / (1 + r)^T`. An algebraic identity, not a no-arbitrage argument. | `VrpProofs.VarianceRiskPremium.vrp_decomposition` |
| The VRP is positive iff the risk-neutral measure prices the claim above the physical measure: `vrp > 0 ↔ E^P[G] < E^Q[G]`. Holds for any `r > −1`, no conditions on whether `q` is a genuine risk-neutral probability. | `VrpProofs.VarianceRiskPremium.vrp_pos_iff` |

## What this module does NOT claim

Two apparent extensions are not proved, and the source documents why:

- **Convex-payoff bridge.** "`q ≤ p` and `G` convex implies `E^P ≤ E^Q`" is false on a fixed
  CRR tree. Holding `u, d` fixed, a lower up-probability shifts the law toward lower prices;
  for an increasing convex payoff such as a call, this lowers the risk-neutral expectation,
  not raises it. A genuine variance risk premium compares an implied tree against a realized
  tree (two distinct `(u, d)` pairs), out of scope here.

- **Gamma-variance-gap P&L identity.** The claim that delta-hedged P&L equals the
  gamma-times-variance-gap term is vacuous in a complete binomial market: perfect replication
  (`replicates`) means terminal P&L is zero on every path, so the identity holds trivially
  with zero on both sides and carries no information.

The two claims above are the sharp content available for a single CRR tree.

## Build and verify

```bash
cd extensions/vrp-proofs
lake exe cache get
lake build
grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake .   # empty = clean
```

Full build/test matrix: see CLAUDE.md.

## Dependencies

Imports `options-proofs`, which cites `ftap-proofs` (Harrison-Pliska 1981, discrete Fundamental
Theorem of Asset Pricing: no arbitrage iff an equivalent martingale measure, EMM, exists).
The CRR market definition, risk-neutral probability, and put-call parity live in
`options-proofs`.

## Reference

Cox, J.C., S.A. Ross, and M. Rubinstein. "Option Pricing: A Simplified Approach."
*Journal of Financial Economics* 7, no. 3 (1979): 229-263.

## License

Apache License 2.0.
