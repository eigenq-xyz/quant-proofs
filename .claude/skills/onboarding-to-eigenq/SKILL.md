---
name: onboarding-to-eigenq
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
argument. The binomial model in `binomial-proofs/` closes the loop from abstract theorem to
concrete option pricing formula. The mortgage agent in `mortgage-proofs/` shows that even
LLM-driven pipelines can have their routing decisions formally audited.

## Project map

```
quant-proofs/
├── backtest-proofs/      # Options delta-hedging backtester
│   ├── lean/             # Lean 4 accounting kernel (BacktestProofs namespace)
│   └── python/           # Cython FFI + Python backtester (backtest_proofs package)
├── ftap-proofs/          # Discrete FTAP proof (FtapProofs namespace)
├── binomial-proofs/      # Put-call parity via CRR model (BinomialProofs namespace)
└── mortgage-proofs/      # LangGraph mortgage pipeline (MortgageProofs namespace)
    ├── agents/           # intake, risk, compliance, underwriter LangGraph agents
    ├── lean/             # Lean 4 invariant definitions
    └── traces/           # DecisionRecord JSON output (gitignored if containing PII)
```

## Dependency graph

```
ftap-proofs
    └── binomial-proofs   (imports FtapProofs.NoArbitrage)
backtest-proofs           (standalone; accounting kernel is self-contained)
mortgage-proofs           (standalone; imports no other subdir's Lean library)
```

Key implication: changes to `ftap-proofs/` may require updating `binomial-proofs/`. Always
run `lake build` in `binomial-proofs/` after touching `ftap-proofs/` interfaces.

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
in `/contributing-to-eigenq`.

### `binomial-proofs/`
A Lean 4 proof of put-call parity using the Cox-Ross-Rubinstein binomial model. Imports
`FtapProofs.NoArbitrage` to ground the no-arbitrage argument. Namespace: `BinomialProofs`.
**Before working here:** read `binomial-proofs/CLAUDE.md`. Ensure `ftap-proofs/` builds
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

## Navigating the repo: which skill to run

| Task | Skill to invoke first |
|------|-----------------------|
| Starting any session | `/onboarding-to-eigenq` (this skill) |
| Writing Lean 4 proofs | `/writing-lean4-proofs` |
| Writing Python or Cython | `/writing-python-code` |
| Opening a PR or commit | `/writing-commits-and-prs` |
| Contributing to mathlib upstream | `/contributing-to-eigenq` |
| Working on mortgage agents | `/writing-python-code`, then read `mortgage-proofs/CLAUDE.md` |
| Sourcing or citing financial data | `/sourcing-financial-data` |

## Build and test commands

| Subdir | Build | Verify no sorry | Python tests |
|--------|-------|-----------------|--------------|
| `backtest-proofs/` | `cd backtest-proofs/lean && lake build` | `grep -rn sorry backtest-proofs/lean --include="*.lean"` | `cd backtest-proofs/python && pytest` |
| `ftap-proofs/` | `cd ftap-proofs && lake build` | `grep -rn sorry ftap-proofs --include="*.lean"` | — |
| `binomial-proofs/` | `cd binomial-proofs && lake build` | `grep -rn sorry binomial-proofs --include="*.lean"` | — |
| `mortgage-proofs/` | `cd mortgage-proofs && lake build` | `grep -rn sorry mortgage-proofs/lean --include="*.lean"` | `cd mortgage-proofs && pytest` |

Run mypy on Python: `mypy --strict <subdir>/python/src/` (or `mortgage-proofs/src/`).

## Key invariants and rules

- **Zero `sorry` on `main`.** A `sorry` in a committed proof means the theorem is unproven.
  A PR introducing `sorry` will not be merged. Use `sorry` freely on feature branches as
  scaffolding; remove before opening a PR.
- **`mypy --strict` clean.** All Python in `src/` directories must pass with no errors.
- **No licensed data in commits.** OptionMetrics, WRDS, Polygon paid-tier data must never
  be committed. See `/sourcing-financial-data` for how to reference these datasets in code
  without committing them.
- **No private content.** No GPA, personal timelines, target firm names in strategy framing,
  resume paths, or application-cycle notes anywhere in this repo.
- **Each subdir has its own CLAUDE.md.** Read it before working in that subdir. The top-level
  CLAUDE.md (this file's parent) is a routing document only.
- **Dependency direction.** `binomial-proofs` may import `ftap-proofs`. Nothing else imports
  across subdirs. `mortgage-proofs` does not import `backtest-proofs`.

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
| Mathlib PR process | `/contributing-to-eigenq` skill |
| Commit/PR standards | `/writing-commits-and-prs` skill |
