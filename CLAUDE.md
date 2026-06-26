# CLAUDE.md

Monorepo for formally verified quantitative finance: Lean 4 proofs paired with Python/Cython
execution. This file orients an AI agent working at the repo root; each subproject has its own
`CLAUDE.md` with local detail. Read that before working in a subproject.

## What this repo is

Each project takes a named result from asset-pricing theory or a load-bearing step of quant research
and makes it machine-checkable. The flagship, `research-pipeline/`, runs a full research-desk
workflow whose correctness-critical steps are proved in Lean 4. The research is the point;
verification is what makes its correctness auditable.

## Projects

| Dir | Tier | What | Build | Zero-sorry check |
|-----|------|------|-------|------------------|
| `research-pipeline/` | flagship | data→signals→stats→portfolio→backtest→eval→cross-asset; proves backtest non-anticipation, OOS no-leakage, and signal 𝓕ₜ-measurability | `cd research-pipeline/lean && lake build` | `grep -rn '\bsorry\b' --include="*.lean" --exclude-dir=.lake research-pipeline/lean` |
| `foundations/ftap-proofs/` | foundation | Discrete FTAP (Harrison-Pliska): no arbitrage iff an EMM exists | `cd foundations/ftap-proofs && lake build` | same pattern |
| `foundations/options-proofs/` | foundation | Put-call parity via Cox-Ross-Rubinstein; cites ftap-proofs | `cd foundations/options-proofs && lake build` | same |
| `foundations/quant-core/` | foundation | Shared pricing primitives (OptionKind, payoffs, Black-Scholes, GBM); Lean + Python | `cd foundations/quant-core/lean && lake build` | `cd foundations/quant-core/python && pytest` |
| `foundations/optimization-proofs/` | foundation | Abstract PGD + simplex/L1 projection core | `cd foundations/optimization-proofs && lake build` | same |
| `foundations/portfolio-proofs/` | foundation | PGD simplex portfolio solver (Lean + Python/Cython); stressed-solver scenarios | `cd foundations/portfolio-proofs/lean && lake build` | `python3 foundations/portfolio-proofs/scenarios/cholesky_crash/scipy_slsqp.py` |
| `extensions/vrp-proofs/` | extension | Discrete CRR variance-risk-premium identities; cites options-proofs | `cd extensions/vrp-proofs && lake build` | same |
| `extensions/hedge-proofs/` | extension | Delta-hedge accounting engine invariants; cites quant-core | `cd extensions/hedge-proofs && lake build` | same |
| `extensions/perpetual-proofs/` | extension | No-arbitrage perpetual-futures pricing; depends on stopped-time-proofs + ftap-proofs | `cd extensions/perpetual-proofs && lake build` | same |
| `extensions/stopped-time-proofs/` | extension | Geometric PMF + expectation operator; mathlib-PR candidate, no finance content | `cd extensions/stopped-time-proofs && lake build` | same |
| `extensions/mortgage-proofs/` | extension | LangGraph multi-agent pipeline + Lean invariant checking | `cd extensions/mortgage-proofs && lake build` | `cd extensions/mortgage-proofs && pytest` |
| `archive/` | archive | Superseded work, do not build or extend | — | — |

Before any Lean build in a fresh checkout or worktree, run `lake exe cache get` in that project to
fetch the mathlib cache (building mathlib from source otherwise takes about an hour). All projects
pin `leanprover/lean4:v4.30.0` and one mathlib rev; keep that consistent when adding a project.

## Hard rules

- Zero `sorry` on `main`. No exceptions. Develop on a branch; discharge any `sorry` before merge.
- `mypy --strict` clean on all Python in `src/`; `ruff` clean.
- Licensed data (OptionMetrics/WRDS, paid Polygon) is never committed.
- Public repo, public-neutral: no GPA, no grades, no target-firm names in strategy context, no
  resume paths, no application timelines. Describe the work as a research and verification artifact.
- Never extend or reference `archive/` as active code. It is read-only history.

## Verified vs unverified

State the boundary wherever a claim could be misread. Proved (zero `sorry`, clean axioms): the
asset-pricing theorems, the backtest non-anticipation and OOS no-leakage guarantees, and signal
𝓕ₜ-measurability. Rigorous but not formally verified: the statistical layer (IC, Newey-West HAC,
PSR/DSR) and all P&L and strategy economics.

## Planning

GitHub issues and milestones are the planning system. Check them at session start; open an issue
per task and close it in the same PR cycle.

```bash
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,open_issues}'
```

## Skills and agents

`.claude/` holds Claude Code skills and agents for this repo. Run `/onboard-to-eigenq` for the full
briefing.
