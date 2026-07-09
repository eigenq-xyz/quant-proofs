# CLAUDE.md

Monorepo for formally verified quantitative finance: Lean 4 proofs paired with Python/Cython
execution. This file orients an agent at the repo root. Each subproject has its own `CLAUDE.md`
with local detail — read that before working in a subproject.

**The point:** every project takes a named result from asset-pricing theory, or a load-bearing
step of quant research, and proves it correct in Lean 4 rather than only testing it. The research
is the point; verification makes its correctness auditable, not just asserted from a backtest. The
flagship, `research-pipeline/`, runs a full research-desk workflow whose correctness-critical steps
are proved this way.

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
| `extensions/research-ideas/` | exploratory | Leakage-tax map (CFTC/EIA/payrolls) + AQR cross-asset breadth; no Lean, no verified claim | — | `cd extensions/research-ideas && pytest` |
| `archive/` | archive | Superseded work, do not build or extend | — | — |

Run `lake exe cache get` before any Lean build in a fresh checkout or worktree — it fetches the
mathlib cache (building mathlib from source otherwise takes about an hour). All projects pin
`leanprover/lean4:v4.30.0` and one mathlib rev; keep new projects consistent with that.

## Hard rules

- **Zero `sorry` on `main`.** No exceptions. Develop on a branch; discharge before merge.
- `mypy --strict` clean on all Python in `src/`; `ruff` clean.
- **Never commit licensed data** (OptionMetrics/WRDS, paid Polygon).
- **Public-neutral repo:** no GPA, no grades, no target-firm names in strategy context, no resume
  paths, no application timelines. Describe the work as a research and verification artifact.
- `archive/` is read-only history. Never extend it or treat it as active code.

## Verified vs unverified

State this boundary wherever a claim could be misread.

- **Proved** (zero `sorry`, clean axioms): the asset-pricing theorems, backtest non-anticipation
  (the Lean type is literally named `NonAnticipating`: no future data reaches a past decision), OOS
  no-leakage, signal 𝓕ₜ-measurability (the signal only reads information available by time `t`).
- **Rigorous but not formally verified:** the statistical layer (IC, Newey-West HAC, PSR/DSR) and
  all P&L and strategy economics.

**Current status (verified in-tree, state without hedging):** research-pipeline, options/FTAP
(put-call parity + no-arbitrage theorem), and PGD convergence/projection are all sorry/axiom-free.
Say "formally proved" or "verified in Lean 4" — not "targets" or "in progress."

- The 7-scenario PGD benchmark is **adversarial by design** (built around each competitor's known
  weakness). Lead with: production solvers (Gurobi, SciPy SLSQP — both run and observed failing on
  stress instances) fail *silently* on structural edge cases. Don't lead with "only solver to pass
  all 7" — that framing is circular given the benchmark's design.
- Architecture is Python-around-the-verified-core via subprocess (compiled binary, stdin/stdout).
  FFI is opt-in, not the default path — never call it an FFI wrapper.

## Origin and motivation

For anyone, human or AI, presenting or extending this work:

- Started from self-taught Lean 4 (Natural Numbers Game, online courses, no formal class), after
  seeing CMU peers and mathematicians use Lean/Mathlib as a standard proof tool.
- **The core conviction:** as AI generates more quant code, statistical testing cannot verify that
  an LLM-generated implementation satisfies the underlying math — formal proofs can. That gap,
  between "passes backtests" and "is mathematically correct," is what this library closes.
- The framing term is **verification-guided development** (see the AWS Cedar use case at
  lean-lang.org/use-cases/cedar — same idea applied to a production authorization stack, and the
  original inspiration here).
- **The Fed connection is thematic, not causal.** The look-ahead-bias work overlaps in kind (same
  class of silent bugs, caught late), but this project's motivation was independent AI-code-
  correctness concern, not a specific Fed finding. Never describe it as "coming from" the Fed work.

## Planning

GitHub issues and milestones are the planning system. Check at session start; open an issue per
task, close it in the same PR cycle.

```bash
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,open_issues}'
```

## Skills and agents

`.claude/` holds Claude Code skills and agents for this repo. Run `/onboard-to-eigenq` for the full
briefing.
