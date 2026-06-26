# Dependency graph: quant-proofs Lean 4 layer

Granular map of how axioms, definitions, lemmas, and theorems connect across the
eight Lean projects, generated from a full read of every `.lean` file in the import
closure (excluding `.lake/` and `archive/`). Ground truth is the Lean source and the
module import graph, not the prose docs.

Status as of this audit: **zero `sorry`** anywhere in the live tree, and **zero custom
`axiom` declarations**. Every proof closes against Lean core plus mathlib, so every
headline theorem's axiom set is the standard `[propext, Classical.choice, Quot.sound]`
(confirmed for the deliverables in `INCONSISTENCIES.md`).

## 1. Project topology (inter-project edges)

Eight Lean projects. An arrow `A -> B` means a file in A has `import B.…`. Edges are
tagged **(load-bearing)** when a proof or type signature in A actually references a named
declaration from B, or **(import-only)** when the `import` line exists but no B declaration
is used (a vestigial edge that fakes a dependency).

```text
                         ftap-proofs  (the spine: discrete FTAP)
                         /     |        \
        (load-bearing)  /      |         \  (import-only, vestigial)
                       v       v          v
            options-proofs  research-      perpetual-proofs
                  |         pipeline             |
   (import-only)  |                              | (load-bearing)
                  v                              v
            quant-core                    stopped-time-proofs

   mortgage-proofs : fully self-contained (Lean core JSON only, no sibling imports)
```

| Edge | Kind | Evidence |
|------|------|----------|
| options-proofs -> ftap-proofs | **load-bearing** | `crrMarket` instantiates `FtapProofs.FinancialMarket`; `crr_no_arbitrage` cites `FtapProofs.emm_implies_no_arbitrage`; martingale proof cites `discountedPrice_adapted`, `IsMartingaleMeasure`, `EquivalentMartingaleMeasure`. |
| research-pipeline -> ftap-proofs | **load-bearing (single point)** | `market_price_natural_le_filtration` (`Measurability.lean:104`) feeds `m.S_adapted` from `FtapProofs.FinancialMarket` into `naturalFiltration_le_of_adapted`. This is the only cross-project citation in the flagship. |
| perpetual-proofs -> stopped-time-proofs | **load-bearing (heavy)** | `geometricExpectation` and its lemma suite appear in nearly every perp definition and theorem; `geometricExpectation_strict_mono` (from `Jensen.lean`) is the sole engine behind Theorem 3 (`inverse_perp_convexity_discount`). |
| perpetual-proofs -> ftap-proofs | **import-only (vestigial)** | `PerpetualProofs/Market.lean:1` has `import FtapProofs.Market`, but no `FtapProofs.*` name is referenced in any signature or proof. `OnePeriodEMM`/`OnePeriodMarket` are deliberately self-contained. Removing the import breaks nothing. |
| options-proofs -> quant-core | **import-only (vestigial)** | `OptionsProofs.lean` and `PutCallParity.lean` import `QuantCore.Option`/`OptionInvariants`, but options-proofs defines its own real-valued `callPayoffReal`/`putPayoffReal` and never references a `QuantCore.*` declaration. |
| mortgage-proofs | self-contained | No sibling imports; only `Lean.Data.Json` and core `List` lemmas. |

Intra-project import trees are linear-ish spines; see each section for the module order.

## 2. ftap-proofs (the theoretical spine)

Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981): no arbitrage iff
an equivalent martingale measure exists. 16 theorems/lemmas, zero `sorry`.

Module spine: `Market -> Strategy -> {Arbitrage, MartingaleMeasure} -> Theorem`; `Density`
branches off `MartingaleMeasure`.

Granular edges (`KIND name (file:line) <- dependencies`):

```text
STRUCT FinancialMarket (Market.lean:55) <- (none)
DEF    discountedPrice (Market.lean:87) <- FinancialMarket
LEMMA  numeraire_pos (Market.lean:97) <- FinancialMarket            [terminal, unused internally]
LEMMA  discountedPrice_adapted (Market.lean:106) <- FinancialMarket, discountedPrice

DEF    prevTime (Strategy.lean:44) <- (none)
LEMMA  prevTime_zero/succ (Strategy.lean:48/52) <- prevTime          [@[simp]]
STRUCT TradingStrategy (Strategy.lean:64) <- FinancialMarket, prevTime
DEF    valueProcess (Strategy.lean:86) <- FinancialMarket, TradingStrategy   [terminal, unused]
DEF    discountedValueProcess (Strategy.lean:97) <- discountedPrice, ...
DEF    selfFinancing (Strategy.lean:121) <- discountedPrice, ...
DEF    gainsProcess (Strategy.lean:139) <- discountedPrice, ...
THM    selfFinancing_iff_value_eq_init_plus_gains (Strategy.lean:191) <- gainsProcess_succ_eq, ... [terminal subtree]

STRUCT ArbitrageOpportunity (Arbitrage.lean:41) <- selfFinancing, discountedValueProcess
DEF    NoArbitrage (Arbitrage.lean:59) <- ArbitrageOpportunity
DEF    attainablePayoffs (Arbitrage.lean:71) <- selfFinancing, discountedValueProcess
THM    attainablePayoffs_isLinearSubspace (Arbitrage.lean:160) <- {zero,sum,smul}Strategy + their sf_/dvp_ lemmas
THM    noArbitrage_iff_attainable_nonneg_eq_zero (Arbitrage.lean:201) <- NoArbitrage, attainablePayoffs, ArbitrageOpportunity

DEF    EquivalentMeasure (MartingaleMeasure.lean:44) <- FinancialMarket
DEF    IsMartingaleMeasure (MartingaleMeasure.lean:51) <- discountedPrice
DEF    EquivalentMartingaleMeasure (MartingaleMeasure.lean:59) <- EquivalentMeasure, IsMartingaleMeasure
THM    discountedValue_martingale_of_emm (MartingaleMeasure.lean:76) <- selfFinancing, EMM, discountedPrice_adapted, prevTime_succ  (mathlib: condExp_mul_of_stronglyMeasurable_left, condExp_finsetSum, Filtration.condExp_condExp)
THM    risk_neutral_pricing (MartingaleMeasure.lean:227) <- discountedValue_martingale_of_emm  (mathlib: integral_condExp)

DEF/LEMMA emmDensity + 6 density lemmas (Density.lean) <- EMM, discountedPrice   [terminal exports]

THM    emm_implies_no_arbitrage (Theorem.lean:99) <- EMM, NoArbitrage, risk_neutral_pricing
THM    state_price_functional (Theorem.lean:161, private) <- attainablePayoffs_isLinearSubspace, noArbitrage_iff_attainable_nonneg_eq_zero  (mathlib: geometric_hahn_banach_compact_closed, isCompact_stdSimplex, InnerProductSpace.toDual)
THM    state_prices_to_emm (Theorem.lean:285, private) <- attainablePayoffs, selfFinancing, discountedPrice_adapted  (mathlib: PMF.ofFintype, ae_eq_condExp_of_forall_setIntegral_eq)
THM    no_arbitrage_implies_emm (Theorem.lean:558) <- state_price_functional, state_prices_to_emm
THM    ftap (Theorem.lean:582) <- no_arbitrage_implies_emm, emm_implies_no_arbitrage     ★ DELIVERABLE
```

Hard direction (no arbitrage => EMM) is the separating-hyperplane argument:
`ftap` <- `no_arbitrage_implies_emm` <- {`state_price_functional` (Hahn-Banach on the
attainable subspace vs the simplex), `state_prices_to_emm` (turn the functional into a PMF)}.
Easy direction (EMM => no arbitrage) is `emm_implies_no_arbitrage` <- `risk_neutral_pricing`
<- `discountedValue_martingale_of_emm`.

**Terminal exports (no in-project dependents, correctly):** `ftap`, the `emmDensity` suite
(reused by perpetual-proofs conceptually), `selfFinancing_iff_value_eq_init_plus_gains`,
`numeraire_pos`, `valueProcess`. The last two and the entire `gainsProcess` cluster are an
isolated subtree: reachable only from a terminal lemma that nothing else uses.

## 3. options-proofs (put-call parity via CRR)

31 theorems/lemmas, zero `sorry`. Builds the Cox-Ross-Rubinstein binomial market, proves it
is an EMM and arbitrage-free by instantiating ftap-proofs, then derives parity.

Two terminal chains:

```text
put_call_parity (PutCallParity.lean:138)                              ★ DELIVERABLE (C - P = S0 - K/(1+r)^T)
   <- discounted_terminal_expectation (PutCallParity.lean:99)
        <- crrRNMeasure_martingale (RiskNeutral.lean:523)
             <- crrRNMeasure_one_step_sum <- riskNeutralProb_drift, crrRNDensity_eq_prod
   <- payoff_parity (PutCallParity.lean:51) <- callPayoffReal, putPayoffReal

crr_no_arbitrage (RiskNeutral.lean:638)                               ★ DELIVERABLE
   <- FtapProofs.emm_implies_no_arbitrage   (the FTAP easy direction, cited)
   <- crrRNMeasure_emm (RiskNeutral.lean:627)
        <- crrRNMeasure_equiv  (uses FtapProofs.EquivalentMeasure)
        <- crrRNMeasure_martingale  (uses FtapProofs.IsMartingaleMeasure, discountedPrice_adapted)
```

The CRR market object `crrMarket` (`Tree.lean:216`) is the instantiation point: it fills every
field of `FtapProofs.FinancialMarket` (`crrPrice`, `crrNumeraire`, `crrFiltration`,
`crrPrice_adapted`, `crrMeasure`). All real cross-project weight is on ftap-proofs.

**Note (vestigial edge):** quant-core is imported but never used; options-proofs rolls its own
real-valued payoffs rather than reusing `QuantCore.callPayoff`/`putPayoff` (which are
`Int`-valued).

## 4. quant-core (shared primitives)

8 theorems, zero `sorry`. Self-contained option-type layer.

```text
AssetId, OptionKind, EuropeanOption (Option.lean) <- (none)
callPayoff/putPayoff (Option.lean:63/67) <- (none)
optionPayoff (Option.lean:70) <- callPayoff, putPayoff
8 invariant theorems (OptionInvariants.lean) <- callPayoff/putPayoff/optionPayoff   [terminal API]
8 anonymous native_decide examples (Tests/UnitTests.lean)
```

This is the most under-connected project: nothing downstream in the live tree consumes it.
`optionPayoff_nonneg` and `EuropeanOption.mk'` are referenced only by the archived
`backtest-proofs` tests. See section 9 for showcase options.

## 5. optimization-proofs (PGD portfolio solver)

10 theorems, zero `sorry`, plus two compiled binaries. Split into a computational half
(`Float` arithmetic, no mathlib) and a proof half (mathlib).

Proof DAG (apex is `pgd_convergence`):

```text
ProblemDefs: IsInConstraintSet, quadObj, gradObj, ledoitWolfShrinkage   (the shared specs)

symmetric_bilin_form (QuadraticLemmas.lean:40)
   -> grad_sum_eq_dotProduct, quad_term_eq -> quadratic_identity -> quadratic_convexity
polarization_identity (QuadraticLemmas.lean:131)

pgd_descent_lemma (Convergence.lean:87) <- quadratic_identity, quadratic_convexity, polarization_identity
pgd_convergence (Convergence.lean:189) <- pgd_descent_lemma                       ★ DELIVERABLE (O(1/k))

projection_feasibility (Projection.lean:133) <- primalFromDual, budget_continuous, ... (mathlib: IVT)
projection_correctness (Projection.lean:319) <- IsInConstraintSet, primalFromDual  ★ DELIVERABLE (KKT)

shrinkage_isSymmetric, shrinkage_psd (Shrinkage.lean) <- ledoitWolfShrinkage      ★ DELIVERABLE (anti-Cholesky-crash)
```

Computational half: `pgdFlat` (`PGDFlat.lean`, unboxed `FloatArray`) is the production solver,
consumed by `CLI.lean` (`pgd_solve`, the default Python path), `Main.lean` (`pgd_bench`), and
`FFI.lean` (`pgdSolveFlat`). `pgd` (`PGD.lean`, boxed `Array Float`) is reachable only through
the FFI export `lean_pgd_solve`, whose Python consumer (`lean_pgd_ffi.py`) is imported by nothing
in the live tree.

**Two vestigial imports:** `PGDFlat.lean` imports `PGD` but uses no symbol from it;
`Convergence.lean` imports `Shrinkage` but cites `shrinkage_psd` only in a doc comment.

**Decoupling worth noting:** `shrinkage_psd` proves exactly the positive-definiteness hypothesis
that `pgd_convergence` assumes, but the two are never composed. They sit in the same library and
the same prose narrative, not in the same proof. See section 9.

## 6. research-pipeline (flagship)

13 theorems/lemmas, zero `sorry`. Three deliverable families plus the cross-project link.

```text
NoLookahead.lean (pure Lean, no deps):
  decision_uses_no_future (line 39) <- NonAnticipating, AgreeUpTo                 ★ no-look-ahead (pointwise)

NoLeakage.lean (pure Lean, no deps):
  embargo_blocks_label_leakage (line 44) <- WalkForwardSplit, labelEnd            ★ OOS no-leakage
  leakage_possible_without_embargo (line 53)                                       ★ tightness companion

Measurability.lean (mathlib + FtapProofs.Market):
  naturalFiltration (line 65)
  price_measurable_natural (line 76) <- naturalFiltration
  naturalFiltration_le_of_adapted (line 91) <- naturalFiltration
  market_price_natural_le_filtration (line 104) <- naturalFiltration_le_of_adapted, FtapProofs.FinancialMarket.S_adapted   ★ the ftap link
  momentumSignal_adapted (line 141) <- price_measurable_natural                    ★ Ft-measurability
  momentumSignal_adapted_of_le (line 164) <- momentumSignal_adapted

Bridge.lean (imports NoLookahead + Measurability):
  indistinguishableSpace, coordSpace (reducible sigma-algebras)
  adapted_pointwise_nonAnticipating (line 80) <- agreeUpTo_indistinguishable
  momentumSignal_pointwise_nonAnticipating (line 98) <- momentumSignal_adapted     ★ collapses the two formulations
  nonAnticipating_of_coordMeasurable (line 144) <- agree_coordSpace_indistinguishable
```

`Bridge.lean` is the top leaf: it depends on both `NoLookahead` (the pointwise predicate) and
`Measurability` (the measure-theoretic statement) and proves the forward direction
(measure-theoretic adaptedness => the literal `NonAnticipating` predicate). Nothing imports
Bridge; its theorems are end-product deliverables surfaced via the `ResearchPipeline` aggregator.
The reverse direction (pointwise => measurable) is explicitly out of scope (needs Doob-Dynkin).

The single ftap citation is real and exercised: `market_price_natural_le_filtration` feeds
`m.S_adapted` (the `FinancialMarket` adaptedness field) into the generic engine.

## 7. perpetual-proofs (no-arbitrage perpetual futures)

10 theorems, zero `sorry`. Ackerer-Hugonnier-Jermann 2025.

```text
OnePeriodMarket, OnePeriodEMM (Market.lean)                  [self-contained; ftap import is vestigial]
CashFlowSpec, ackererCashFlow, heManelaCashFlow, CostlessEntry, NoBuyAndHoldArbitrage (CashFlow.lean)
   <- geometricExpectation  (from stopped-time-proofs)

ackerer_cashflow_satisfies_costless_entry (FundingCompatibility.lean:95) <- ackerer_pv_eq    ★ Theorem 1a
he_manela_violates_costless_entry (line 141) <- he_manela_pv_eq                              ★ Theorem 1b (counterexample)
perp_futures_no_arb_price (PerpFuturesNoArb.lean:134) <- no_arb_existence, no_arb_uniqueness  ★ Theorem 2
inverse_perp_convexity_discount (InversePerpCorrection.lean:182) <- geom_exp_inv_gt           ★ Theorem 3
   geom_exp_inv_gt <- geometricExpectation_strict_mono  (the sole Jensen.lean consumer)
```

Heavy load-bearing dependence on stopped-time-proofs (`geometricExpectation`,
`geometricExpectation_const`, `geometricExpectation_summable`, `geometricExpectation_strict_mono`,
`geomPMF`, `geomPMF_tsum_eq_one`). The ftap-proofs import is vestigial (aspirational: a TODO to
swap in `MartingaleMeasure` once available, not yet done).

## 8. stopped-time-proofs and mortgage-proofs

**stopped-time-proofs** (8 lemmas, zero `sorry`, no finance content, mathlib-PR candidate):

```text
geomPMF (GeomPMF.lean:34) -> geomPMF_nonneg, geomPMF_tsum_eq_one                  ★ PMF sums to 1
geometricExpectation (GeomExpectation.lean:49) <- geomPMF
   -> geometricExpectation_summable, _const, _mono, _unroll
geomPMF_pos, geometricExpectation_strict_mono (Jensen.lean) <- geometricExpectation_summable
```

`geometricExpectation_strict_mono` is load-bearing (perpetual Theorem 3). `geometricExpectation_mono`
and `geometricExpectation_unroll` are orphan library lemmas (kept for the mathlib PR surface).

**mortgage-proofs** (13 theorems, zero `sorry`, fully self-contained): a parse -> check -> theorems
pipeline. `Types -> {Parser, Invariants} -> {Checker, Theorems}`; `Main` is the `verify-trace`
executable. The two headline theorems are `checkRecord_empty_implies_clean_decisions` and
`checkRecord_empty_implies_consistent_outcome`. The proofs are compile-time evidence and are not on
the executable path. `ReasoningStep` content fields are parsed but never verified (round-trip data).

## 9. Pruned / orphaned code and how to put it to work

No `.lean` file is fully orphaned: every file is in its project root's transitive import closure
or is a registered executable. What follows is code that compiles but does no proof or runtime work
on any live path, with a showcase proposal for each.

| Item | Where | Current status | Proposal |
|------|-------|----------------|----------|
| `quant-core` (whole project) | `foundations/quant-core/` | imported by options-proofs but never referenced; 8 invariant theorems are terminal API with no live consumer | Make the dependency real: have options-proofs derive `callPayoffReal`/`putPayoffReal` from `QuantCore.callPayoff`/`putPayoff` via a `Int -> Real` cast, so put-call parity actually rests on the shared primitives. Alternatively, promote quant-core to a documented standalone "verified option-payoff invariants" exhibit. |
| `PGD.lean` boxed chain + `pgdSolve`/`faEmpty` + `lean_pgd_ffi.py` | `optimization-proofs`, `portfolio-proofs` | off every live execution path (production is CLI -> `PGDFlat`); FFI consumer imported by nothing | Either retire the boxed FFI path entirely (one clean deletion), or showcase it as a differential-test oracle: a property test asserting `pgd` and `pgdFlat` agree to tolerance on random inputs, turning the dead variant into a cross-check of the production solver. |
| `shrinkage_psd` / `shrinkage_isSymmetric` | `optimization-proofs/Shrinkage.lean` | terminal; proves the PD hypothesis `pgd_convergence` assumes, but never composed with it | Compose them: state a corollary `shrunk_problem_pgd_converges` that feeds `shrinkage_psd` as the positive-definiteness witness into `pgd_convergence`, giving an end-to-end "Ledoit-Wolf input => PGD converges" guarantee. This is the single highest-value wiring in the repo. |
| `geometricExpectation_mono`, `geometricExpectation_unroll` | `stopped-time-proofs` | orphan library lemmas | Keep, but bundle explicitly into the mathlib-PR surface (the project's stated goal). Document them as part of the proposed `GeometricExpectation` API rather than leaving them looking accidental. |
| `EuropeanOption.mk'` | `quant-core/Option.lean:57` | referenced only by archived tests | Remove (live code uses the auto-generated `EuropeanOption.mk`), or fold into the quant-core showcase above. |
| ftap import in `perpetual/Market.lean` | `perpetual-proofs` | vestigial `import` | Either delete the import, or complete the aspirational link by replacing `OnePeriodEMM` with `FtapProofs.EquivalentMartingaleMeasure` so the claimed ftap dependency becomes real. |
| `market_price_natural_le_filtration` | `research-pipeline/Measurability.lean:104` | terminal; the sole ftap citation, but nothing downstream consumes it | Feature it: it is the formal seam between the flagship and the FTAP spine. Surface it in the docs as the unification theorem and, ideally, derive a corollary that the momentum signal is adapted to the FTAP market filtration specifically. |

## 10. English summary

The repository is a shallow, mostly-tree-shaped dependency graph with one true spine and one
true flagship. **ftap-proofs is the spine**: its discrete FTAP (`ftap`) is built bottom-up from a
`FinancialMarket` structure, through trading strategies and self-financing, to two opposing
arguments (a martingale/conditional-expectation argument for the easy direction, a
separating-hyperplane argument for the hard direction). Two projects genuinely rest on it.
options-proofs instantiates the FTAP market as the Cox-Ross-Rubinstein binomial tree and reuses
the FTAP no-arbitrage result to prove put-call parity. research-pipeline, the flagship, touches
ftap-proofs at exactly one point, feeding the FTAP market's adaptedness field into its proof that
the momentum signal is measurable with respect to the natural price filtration.

A second, independent spine sits in the extensions tier: **stopped-time-proofs** provides a
`geometricExpectation` operator and its lemma suite, on which **perpetual-proofs** leans heavily to
prove four no-arbitrage results for perpetual futures, including a strict-convexity correction that
depends entirely on the geometric-Jensen lemma. **mortgage-proofs** is an island: a self-contained
parse-check-prove pipeline with no sibling dependencies. **optimization-proofs** is two halves
bolted together, a `Float` solver compiled to two binaries and a mathlib proof of PGD convergence,
projection correctness, and shrinkage positive-definiteness, with the proof half and the runtime
half communicating only through shared problem-definition types.

The most important structural observation is that **several declared dependencies are not real**.
Three `import` lines create the appearance of edges that the proofs never use: perpetual-proofs
imports ftap-proofs but cites nothing from it, options-proofs imports quant-core but rolls its own
payoffs, and inside optimization-proofs both `PGDFlat -> PGD` and `Convergence -> Shrinkage` are
unused. quant-core is the least-connected project in the live tree. The single highest-value piece
of latent wiring is the uncomposed pair in optimization-proofs: `shrinkage_psd` proves precisely the
hypothesis `pgd_convergence` requires, and joining them would yield an end-to-end portfolio-solver
guarantee that the repository currently states only in prose.
