# CLAUDE.md

Monorepo for formally verified quantitative finance. Lean 4 proofs + Python/Cython execution.

## Projects

| Dir | What | Build | Test |
|-----|------|-------|------|
| `quant-core/` | Shared pricing primitives (OptionKind, payoffs, Black-Scholes, GBM) | `cd quant-core/lean && lake build` | `cd quant-core/python && pytest` |
| `backtest-proofs/` | Options delta-hedging backtester with Lean 4 accounting module | `cd backtest-proofs/lean && lake build` | `cd backtest-proofs/python && pytest` |
| `ftap-proofs/` | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981) | `cd ftap-proofs && lake build` | `grep -rn sorry --include="*.lean" ftap-proofs/` |
| `options-proofs/` | Put-call parity via Cox-Ross-Rubinstein binomial model | `cd options-proofs && lake build` | same |
| `mortgage-proofs/` | LangGraph multi-agent mortgage pipeline + Lean 4 invariant checking | `cd mortgage-proofs && lake build` | `cd mortgage-proofs && pytest` |

Each subdir has its own CLAUDE.md with architecture details. Read that before working in a subdir.

## Hard rules

- Zero `sorry` on main. No exceptions.
- `mypy --strict` clean on all Python in `src/`.
- Licensed data (OptionMetrics/WRDS, Polygon paid) never committed. See `/source-financial-data`.
- No private content: no GPA, grades, target firm names in strategy context, resume paths, or application timelines.

## Planning

Open GitHub issues for all action items; close them in the same PR cycle. Check issues and
milestones at session start:

```bash
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,due_on,open_issues}'
```

Active milestones: #1 SSRN preprint (2026-08-01) · #2 JAR submission (2026-11-30).

## Skills and agents

Run `/onboard-to-eigenq` for the full codebase briefing.
Run `/write-lean4-proofs` or `/write-python-code` before writing code.

## Why this repo exists

The durable skill in quant work is directing and auditing AI-generated output — which requires being able to verify it formally. Every project here demonstrates that capability.
