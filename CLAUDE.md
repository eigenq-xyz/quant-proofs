# CLAUDE.md

Monorepo for formally verified quantitative finance. Lean 4 proofs + Python/Cython execution.

## Projects

| Dir | What | Build | Test |
|-----|------|-------|------|
| `backtest-proofs/` | Options delta-hedging backtester with Lean 4 accounting kernel | `cd backtest-proofs/lean && lake build` | `cd backtest-proofs/python && pytest` |
| `ftap-proofs/` | Discrete Fundamental Theorem of Asset Pricing (Harrison-Pliska 1981) | `cd ftap-proofs && lake build` | `grep -rn sorry --include="*.lean" ftap-proofs/` |
| `binomial-proofs/` | Put-call parity via Cox-Ross-Rubinstein binomial model | `cd binomial-proofs && lake build` | same |
| `mortgage-proofs/` | LangGraph multi-agent mortgage pipeline + Lean 4 invariant checking | `cd mortgage-proofs && lake build` | `cd mortgage-proofs && pytest` |

Each subdir has its own CLAUDE.md with architecture details. Read that before working in a subdir.

## Hard rules

- Zero `sorry` on main. No exceptions.
- `mypy --strict` clean on all Python in `src/`.
- Licensed data (OptionMetrics/WRDS, Polygon paid) never committed. See `/sourcing-financial-data`.
- No private content: no GPA, grades, target firm names in strategy context, resume paths, or application timelines.

## Skills and agents

This repo has 12 skills and 6 agents in `.claude/skills/` and `.claude/agents/`.
Run `/onboarding-to-eigenq` for the full org briefing.
Run `/writing-lean4-proofs` or `/writing-python-code` before writing code.

## Thesis

Routine quant work will be largely automated. The durable skill is directing and auditing AI-generated quant work — which requires mathematical depth and the ability to verify outputs formally. Every project here demonstrates that capability.
