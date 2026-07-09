---
name: onboard-to-eigenq
description: >
  Complete briefing for the quant-proofs monorepo. Use when starting work in this
  repo, when uncertain where a project fits, or when routing a question to the right
  subdir. Covers project map, dependency graph, verification thesis, and key rules.
---

# Onboarding to quant-proofs

## Verification thesis

Backtesting, factor screening, and portfolio construction are increasingly automatable.
The durable skill: **directing and auditing AI-generated quant work** — which needs two
things AI can't self-supply:

1. **Mathematical depth** — knowing whether a proof obligation is trivial or subtle.
2. **Formal verification** — checking that the AI's output is actually correct, not just
   plausible-looking.

Every subdir here demonstrates that thesis concretely. `research-pipeline/` (the
flagship) machine-checks that a signal-research pipeline can't silently look ahead or
leak out-of-sample data. `foundations/ftap-proofs/` shows no-arbitrage pricing follows
from a constructively verified argument. `foundations/options-proofs/` closes the loop
from abstract theorem to concrete option pricing formula. `extensions/mortgage-proofs/`
shows even LLM-driven pipelines can have their routing decisions formally audited.

## Project map (verify against `DEPENDENCY_GRAPH.md` if this ever looks stale — that file is
generated directly from Lean source and is the ground truth for module structure)

```
quant-proofs/
├── research-pipeline/                 # FLAGSHIP: data->signals->stats->portfolio->backtest->eval->cross-asset
│   ├── lean/ResearchPipeline/         # NoLookahead, NoLeakage, Measurability (momentum + VRP signals)
│   └── src/, tests/, studies/         # Python engine (CLI: `rp`), reproducible studies incl. leakage-tax map
├── foundations/
│   ├── quant-core/                    # Shared pricing primitives (QuantCore namespace): Lean + Python
│   ├── ftap-proofs/                   # Discrete FTAP (FtapProofs namespace) — the theoretical spine
│   ├── options-proofs/                # Put-call parity via CRR (OptionsProofs namespace); cites ftap-proofs
│   ├── optimization-proofs/           # Abstract PGD + simplex/L1 projection core
│   └── portfolio-proofs/              # PGD simplex portfolio solver (Lean + Python/Cython), stress scenarios
├── extensions/
│   ├── vrp-proofs/                    # Discrete CRR variance-risk-premium identities; cites options-proofs
│   ├── hedge-proofs/                  # Delta-hedge accounting engine invariants; cites quant-core
│   ├── perpetual-proofs/              # No-arbitrage perpetual futures; cites stopped-time-proofs (heavy)
│   ├── stopped-time-proofs/           # Geometric PMF + expectation operator; mathlib-PR candidate, complete
│   └── mortgage-proofs/               # LangGraph multi-agent mortgage pipeline + Lean invariant checking
│       ├── agents/                    # intake, risk, compliance, underwriter LangGraph agents
│       ├── lean/                      # Lean 4 invariant definitions (MortgageProofs namespace)
│       └── traces/                    # DecisionRecord JSON output (gitignored if containing PII)
└── archive/                           # Superseded work (e.g. position-ledger/backtest-proofs). Read-only
                                        # history — never build, extend, or reference as active code.
```

**`backtest-proofs/` no longer exists as a live top-level project.** Archived, superseded
by `research-pipeline`, which generalizes and completes the "verified backtester" thesis
`backtest-proofs` only partially delivered (see the archived postmortem in
`archive/position-ledger/` if the history matters). A reference to `backtest-proofs/`
outside `archive/` is stale — flag it, don't trust it.

## Dependency graph (summary — `DEPENDENCY_GRAPH.md` has the full, generated, load-bearing-vs-
import-only detail per edge; read that for anything precise)

```
ftap-proofs           (the spine: discrete FTAP; standalone)
  ├── options-proofs  (load-bearing: crrMarket instantiates FtapProofs.FinancialMarket)
  └── research-pipeline (load-bearing, single point: Measurability.lean cites FtapProofs)

quant-core            (shared primitives; standalone)
  └── hedge-proofs    (load-bearing: imports QuantCore.Option, calls optionPayoff)

options-proofs
  └── vrp-proofs       (load-bearing: imports OptionsProofs.PutCallParity, uses CRR machinery)

stopped-time-proofs
  └── perpetual-proofs (load-bearing, heavy: geometricExpectation drives nearly every perp theorem)

optimization-proofs -> portfolio-proofs (Python/Cython solver routes through the verified PGD core)

mortgage-proofs: fully self-contained (no sibling imports)
```

Key implications:
- Build `foundations/ftap-proofs/` before `foundations/options-proofs/` or `research-pipeline`.
- Build `foundations/quant-core/lean` before `extensions/hedge-proofs/`.
- Build `extensions/stopped-time-proofs/` before `extensions/perpetual-proofs/`.
- `mortgage-proofs` is independent of everything else and can be worked on in isolation.

## What each subdir does (one-liners; full detail in each subdir's own `CLAUDE.md`)

### `research-pipeline/` (flagship)
A full quant-research-desk workflow, alpha-agnostic (cross-sectional and time-series
signals through one interface), driven by a CLI (`rp`). Machine-checks backtest
non-anticipation and out-of-sample no-leakage; the statistical layer (IC, Newey-West HAC,
PSR/DSR) is rigorous but not formally verified — its own README states that boundary
explicitly. Ships reproducible studies including a cross-asset momentum study and a
leakage-tax map (CFTC, EIA, payrolls data revisions).
**Before working here:** read `research-pipeline/CLAUDE.md`.

### `foundations/ftap-proofs/`
A Lean 4 proof of the discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska
1981): a finite market admits no arbitrage if and only if there exists a risk-neutral
probability measure. Namespace: `FtapProofs`. Complete, zero `sorry`; a mathlib-PR
candidate, not under active extension.
**Before working here:** read `foundations/ftap-proofs/CLAUDE.md`.

### `foundations/options-proofs/`
A Lean 4 proof of put-call parity using the Cox-Ross-Rubinstein binomial model. Imports
`FtapProofs` to ground the no-arbitrage argument. Namespace: `OptionsProofs`. Complete.
**Before working here:** read `foundations/options-proofs/CLAUDE.md`. Ensure
`foundations/ftap-proofs/` builds first.

### `foundations/optimization-proofs/` and `foundations/portfolio-proofs/`
Abstract projected-gradient-descent (PGD) convergence core, applied to a
simplex-constrained mean-variance portfolio solver (Lean + Python/Cython), benchmarked
against SciPy/Gurobi on stress scenarios designed to expose each competitor's known
failure mode.
**Before working here:** read `foundations/portfolio-proofs/CLAUDE.md`.

### `extensions/vrp-proofs/`
Discrete CRR variance-risk-premium identities: exact path-by-path replication, and the
premium as the sharp expectation gap between risk-neutral and physical measures. Cites
`options-proofs`.
**Before working here:** read `extensions/vrp-proofs/CLAUDE.md`.

### `extensions/hedge-proofs/`
Delta-hedge accounting engine invariants (self-financing, settlement-value,
value-update). Cites `quant-core`. Resurrected from the archived position-ledger work
once a real financial claim (the VRP decomposition) gave it a load-bearing purpose.
**Before working here:** read `extensions/hedge-proofs/CLAUDE.md`.

### `extensions/perpetual-proofs/`
No-arbitrage perpetual-futures pricing and the inverse-perp convexity correction.
Depends heavily on `stopped-time-proofs`.
**Before working here:** read `extensions/perpetual-proofs/CLAUDE.md`.

### `extensions/stopped-time-proofs/`
Geometric stopping-time expectations and a strict-monotonicity (Jensen) lemma. Pure
math, no finance content, complete. Best destiny is a merged mathlib PR.
**Before working here:** read `extensions/stopped-time-proofs/CLAUDE.md`.

### `extensions/mortgage-proofs/`
A LangGraph multi-agent pipeline for mortgage application processing. Four agents:
- **intake** — parses application, extracts structured fields
- **risk** — computes DTI, LTV, credit-score band
- **compliance** — checks RESPA/TILA/ECOA constraints
- **underwriter** — issues approve/deny/refer decision

Every routing decision is emitted as a `DecisionRecord` JSON object. The Lean 4 side
(`MortgageProofs` namespace) defines invariants (e.g., `compliance_before_underwriter`,
`risk_score_nonneg`) and validates traces via `lake exe verify-trace <trace.json>`. Fully
self-contained, no sibling imports.
**Before working here:** read `extensions/mortgage-proofs/CLAUDE.md`.

## Session start checklist

Run these at the start of every session before doing any substantive work:

```bash
# 1. Live skill/agent roster (changes frequently)
ls .claude/skills/
ls .claude/agents/ 2>/dev/null || echo "(no agents directory)"

# 2. Open PRs + any pending claude-review comments
gh pr list
gh pr view <open-PR> --comments

# 3. Open issues and milestone progress (canonical planning system)
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,due_on,open_issues}'
```

Don't trust `work_queue_status.md` for current status — it's retired (see the file
itself). Trust `DEPENDENCY_GRAPH.md` for module/proof structure and
`gh issue`/`gh api milestones` for task status.

New action items surface (from agents, code review, or conversation)? Open a GH issue
immediately rather than tracking in conversation. Close issues in the same PR cycle
using `closes #N` in the PR body.

## Navigating the repo: which skill to run

| Task | Skill to invoke first |
|------|-----------------------|
| Starting any session | `/onboard-to-eigenq` (this skill) |
| Writing Lean 4 proofs | `/write-lean4-proofs` |
| Writing Python or Cython | `/write-python-code` |
| Opening a PR or commit | `/contribute-to-eigenq` |
| Contributing to mathlib upstream | `/contribute-to-eigenq` |
| Working on mortgage agents | `/write-python-code`, then read `extensions/mortgage-proofs/CLAUDE.md` |
| Sourcing or citing financial data | `/source-financial-data` |
| Checking whether a doc or skill is stale | `ls .claude/skills/`, cross-check paths against `DEPENDENCY_GRAPH.md` and this file's project map |

## Build and test commands

| Subdir | Build | Verify no sorry | Python tests |
|--------|-------|-----------------|--------------|
| `research-pipeline/` | `cd research-pipeline/lean && lake build` | `grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake research-pipeline/lean` | `cd research-pipeline && pytest` |
| `foundations/quant-core/` | `cd foundations/quant-core/lean && lake build` | `grep -rn sorry foundations/quant-core/lean --include="*.lean"` | `cd foundations/quant-core/python && pytest` |
| `foundations/ftap-proofs/` | `cd foundations/ftap-proofs && lake build` | `grep -rn sorry foundations/ftap-proofs --include="*.lean"` | — |
| `foundations/options-proofs/` | `cd foundations/options-proofs && lake build` | `grep -rn sorry foundations/options-proofs --include="*.lean"` | — |
| `foundations/portfolio-proofs/` | `cd foundations/portfolio-proofs/lean && lake build` | `grep -rn sorry foundations/portfolio-proofs/lean --include="*.lean"` | `python3 foundations/portfolio-proofs/scenarios/cholesky_crash/scipy_slsqp.py` |
| `extensions/vrp-proofs/` | `cd extensions/vrp-proofs && lake build` | `grep -rn sorry extensions/vrp-proofs --include="*.lean"` | — |
| `extensions/hedge-proofs/` | `cd extensions/hedge-proofs && lake build` | `grep -rn sorry extensions/hedge-proofs --include="*.lean"` | — |
| `extensions/perpetual-proofs/` | `cd extensions/perpetual-proofs && lake build` | `grep -rn sorry extensions/perpetual-proofs --include="*.lean"` | — |
| `extensions/stopped-time-proofs/` | `cd extensions/stopped-time-proofs && lake build` | `grep -rn sorry extensions/stopped-time-proofs --include="*.lean"` | — |
| `extensions/mortgage-proofs/` | `cd extensions/mortgage-proofs && lake build` | `grep -rn sorry extensions/mortgage-proofs/lean --include="*.lean"` | `cd extensions/mortgage-proofs && pytest` |

Before any Lean build in a fresh checkout or worktree, run `lake exe cache get` first
(building mathlib from source otherwise takes about an hour). Run mypy on Python:
`mypy --strict <subdir>/src/` or `<subdir>/python/src/` depending on the subdir's layout.

## Key invariants and rules

- **Zero `sorry` on `main`.** A `sorry` in a committed proof means the theorem is
  unproven. A PR introducing `sorry` will not be merged. Use `sorry` freely on feature
  branches as scaffolding; remove before opening a PR.
- **`mypy --strict` clean.** All Python in `src/` directories must pass with no errors.
- **No licensed data in commits.** OptionMetrics, WRDS, Polygon paid-tier data must never
  be committed. See `/source-financial-data` for how to reference these datasets in code
  without committing them.
- **No private content.** No GPA, personal timelines, target firm names in strategy
  framing, resume paths, or application-cycle notes anywhere in this repo.
- **Each subdir has its own CLAUDE.md.** Read it before working in that subdir. The
  top-level CLAUDE.md (this file's parent) is a routing document only.
- **Never extend or reference `archive/` as active code.** It is read-only history.
- **If this skill's project map or dependency summary ever disagrees with
  `DEPENDENCY_GRAPH.md` or the actual directory listing, trust those over this file and
  flag this file as stale** — this exact skill went stale once already (missed
  `research-pipeline` and several `foundations/`/`extensions/` moves for multiple
  release cycles) before being rewritten 2026-07-02.

## Where to look for what

| Question | Where to look |
|----------|----------------|
| Lean 4 namespace and module structure | `<subdir>/lean/` and `<subdir>/CLAUDE.md` |
| Python package layout | `<subdir>/src/` or `<subdir>/python/` |
| Proof strategy for a theorem | `<subdir>/CLAUDE.md` and existing `.lean` files |
| Granular load-bearing-vs-vestigial dependency detail | `DEPENDENCY_GRAPH.md` |
| Agent routing logic | `extensions/mortgage-proofs/agents/` |
| Lean invariant definitions | `extensions/mortgage-proofs/lean/` |
| Trace validation | `lake exe verify-trace` in `extensions/mortgage-proofs/` |
| Mathlib PR process | `/contribute-to-eigenq` skill |
| Commit/PR standards | `/contribute-to-eigenq` skill |
