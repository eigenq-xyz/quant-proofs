---
name: onboard-to-eigenq
description: >
  Complete briefing for the quant-proofs monorepo. Use when starting work in this
  repo, when uncertain where a project fits, or when routing a question to the right
  subdir. Covers project map, dependency graph, verification thesis, and key rules.
---

# Onboarding to quant-proofs

## Verification thesis

Routine quantitative finance work — backtesting, factor screening, portfolio construction —
is increasingly automatable. The durable skill is **directing and auditing AI-generated quant
work**, which requires two things that AI cannot self-supply:

1. **Mathematical depth** — knowing whether a proof obligation is trivial or subtle.
2. **Formal verification** — being able to check that the AI's output is actually correct,
   not just plausible-looking.

Every subdir in this repo is a concrete demonstration of that thesis. The Lean 4 kernel in
`backtest-proofs/` proves that the Python backtester cannot silently miscount P&L. The FTAP
proof in `ftap-proofs/` shows that no-arbitrage pricing follows from a constructively verified
argument. The binomial model in `options-proofs/` closes the loop from abstract theorem to
concrete option pricing formula. The mortgage agent in `mortgage-proofs/` shows that even
LLM-driven pipelines can have their routing decisions formally audited.

## Project map

```
quant-proofs/
├── quant-core/           # Shared pricing primitives (QuantCore namespace)
│   ├── lean/             # Lean 4: AssetId, OptionKind, EuropeanOption, payoff theorems
│   └── python/           # Python: Black-Scholes pricer, GBM simulator, PricePath
├── backtest-proofs/      # Options delta-hedging backtester
│   ├── lean/             # Lean 4 accounting kernel (BacktestProofs namespace)
│   └── python/           # Cython FFI + Python backtester (backtest_proofs package)
├── ftap-proofs/          # Discrete FTAP proof (FtapProofs namespace)
├── options-proofs/       # Put-call parity via CRR model (OptionsProofs namespace)
└── mortgage-proofs/      # LangGraph mortgage pipeline (MortgageProofs namespace)
    ├── agents/           # intake, risk, compliance, underwriter LangGraph agents
    ├── lean/             # Lean 4 invariant definitions
    └── traces/           # DecisionRecord JSON output (gitignored if containing PII)
```

## Dependency graph

```
quant-core                (shared; depends only on mathlib)
    ├── backtest-proofs   (accounting kernel imports QuantCore.Option)
    └── options-proofs    (pricing theorems import QuantCore.Option + QuantCore.OptionInvariants)
ftap-proofs               (standalone)
mortgage-proofs           (standalone)
```

Key implications:
- Always build `quant-core/lean` before `backtest-proofs/lean` or `options-proofs/`.
- Changes to `quant-core/lean` may require rebuilding both dependents.
- `ftap-proofs` and `mortgage-proofs` are independent of `quant-core`.

## What each subdir does

### `backtest-proofs/`
An options delta-hedging backtester whose accounting kernel is proven correct in Lean 4.
The 26 theorems (zero `sorry`, all on `main`) cover:
- Portfolio value equals sum of position values (`valueIdentity`)
- PnL attribution is additive across legs
- Option settlement is zero for OTM positions
- Cash flows balance across rebalancing events

The Python side (`backtest_proofs` package) calls the Lean-compiled kernel via Cython FFI.
**Before working here:** read `backtest-proofs/CLAUDE.md`.

### `ftap-proofs/`
A Lean 4 proof of the discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981):
a finite market admits no arbitrage if and only if there exists a risk-neutral probability
measure. Namespace: `FtapProofs`. Targeting a mathlib PR once complete.
**Before working here:** read `ftap-proofs/CLAUDE.md`. The mathlib PR process is described
in `/contribute-to-eigenq`.

### `options-proofs/`
A Lean 4 proof of put-call parity using the Cox-Ross-Rubinstein binomial model. Imports
`FtapProofs.NoArbitrage` to ground the no-arbitrage argument. Namespace: `OptionsProofs`.
**Before working here:** read `options-proofs/CLAUDE.md`. Ensure `ftap-proofs/` builds
cleanly first.

### `mortgage-proofs/`
A LangGraph multi-agent pipeline for mortgage application processing. Four agents:
- **intake** — parses application, extracts structured fields
- **risk** — computes DTI, LTV, credit-score band
- **compliance** — checks RESPA/TILA/ECOA constraints
- **underwriter** — issues approve/deny/refer decision

Every routing decision is emitted as a `DecisionRecord` JSON object. The Lean 4 side
(`MortgageProofs` namespace) defines invariants (e.g., `compliance_before_underwriter`,
`risk_score_nonneg`) and validates traces via `lake exe verify-trace <trace.json>`.
**Before working here:** read `mortgage-proofs/CLAUDE.md`.

## Session start checklist

Run these at the start of every session before doing any substantive work:

```bash
# 1. Live skill/agent roster (changes frequently)
ls .claude/skills/ && ls .claude/agents/

# 2. Open PRs + any pending claude-review comments
gh pr list
gh pr view <open-PR> --comments

# 3. Open issues and milestone progress (canonical planning system)
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,due_on,open_issues}'
```

Active milestones: #1 SSRN preprint (2026-08-01) · #2 JAR submission (2026-11-30).

When new action items surface (from agents, code review, or conversation), open a GH issue
immediately rather than tracking in conversation. Close issues in the same PR cycle using
`closes #N` in the PR body.

## Navigating the repo: which skill to run

| Task | Skill to invoke first |
|------|-----------------------|
| Starting any session | `/onboard-to-eigenq` (this skill) |
| Writing Lean 4 proofs | `/write-lean4-proofs` |
| Writing Python or Cython | `/write-python-code` |
| Opening a PR or commit | `/write-commits-and-prs` |
| Contributing to mathlib upstream | `/contribute-to-eigenq` |
| Working on mortgage agents | `/write-python-code`, then read `mortgage-proofs/CLAUDE.md` |
| Sourcing or citing financial data | `/source-financial-data` |

## Build and test commands

| Subdir | Build | Verify no sorry | Python tests |
|--------|-------|-----------------|--------------|
| `quant-core/` | `cd quant-core/lean && lake build` | `grep -rn sorry quant-core/lean --include="*.lean"` | `cd quant-core/python && pytest` |
| `backtest-proofs/` | `cd backtest-proofs/lean && lake build` | `grep -rn sorry backtest-proofs/lean --include="*.lean"` | `cd backtest-proofs/python && pytest` |
| `ftap-proofs/` | `cd ftap-proofs && lake build` | `grep -rn sorry ftap-proofs --include="*.lean"` | — |
| `options-proofs/` | `cd options-proofs && lake build` | `grep -rn sorry options-proofs --include="*.lean"` | — |
| `mortgage-proofs/` | `cd mortgage-proofs && lake build` | `grep -rn sorry mortgage-proofs/lean --include="*.lean"` | `cd mortgage-proofs && pytest` |

Build `quant-core/lean` before `backtest-proofs/lean` or `options-proofs/` on a fresh checkout.

Run mypy on Python: `mypy --strict <subdir>/python/src/` (or `mortgage-proofs/src/`).

## Key invariants and rules

- **Zero `sorry` on `main`.** A `sorry` in a committed proof means the theorem is unproven.
  A PR introducing `sorry` will not be merged. Use `sorry` freely on feature branches as
  scaffolding; remove before opening a PR.
- **`mypy --strict` clean.** All Python in `src/` directories must pass with no errors.
- **No licensed data in commits.** OptionMetrics, WRDS, Polygon paid-tier data must never
  be committed. See `/source-financial-data` for how to reference these datasets in code
  without committing them.
- **No private content.** No GPA, personal timelines, target firm names in strategy framing,
  resume paths, or application-cycle notes anywhere in this repo.
- **Each subdir has its own CLAUDE.md.** Read it before working in that subdir. The top-level
  CLAUDE.md (this file's parent) is a routing document only.
- **Dependency direction.** `backtest-proofs` and `options-proofs` both import `quant-core`.
  `options-proofs` may also import `ftap-proofs` (planned). `mortgage-proofs` does not
  import any other subdir's Lean library.

## Where to look for what

| Question | Where to look |
|----------|---------------|
| Lean 4 namespace and module structure | `<subdir>/lean/` and `<subdir>/CLAUDE.md` |
| Python package layout | `<subdir>/python/` or `<subdir>/src/` |
| Proof strategy for a theorem | `<subdir>/CLAUDE.md` and existing `.lean` files |
| Cython FFI bindings | `backtest-proofs/python/src/backtest_proofs/` |
| Agent routing logic | `mortgage-proofs/agents/` |
| Lean invariant definitions | `mortgage-proofs/lean/` |
| Trace validation | `lake exe verify-trace` in `mortgage-proofs/` |
| Mathlib PR process | `/contribute-to-eigenq` skill |
| Commit/PR standards | `/write-commits-and-prs` skill |
