# CLAUDE.md

Monorepo for formally verified quantitative finance. Lean 4 proofs + Python/Cython execution.

## Projects

| Dir | What | Build | Test |
|-----|------|-------|------|
| `ftap-proofs/` | Discrete FTAP (Harrison-Pliska 1981): no arbitrage iff EMM exists | `cd ftap-proofs && lake build` | `grep -rn sorry --include="*.lean" ftap-proofs/` |
| `options-proofs/` | Put-call parity via Cox-Ross-Rubinstein; depends on ftap-proofs | `cd options-proofs && lake build` | same |
| `quant-core/` | Shared pricing primitives (OptionKind, payoffs, Black-Scholes, GBM) | `cd quant-core/lean && lake build` | `cd quant-core/python && pytest` |
| `portfolio-proofs/` | Formally verified PGD simplex portfolio solver core | `cd portfolio-proofs/lean && lake build` (planned) | `python3 portfolio-proofs/showcase/stressed_solver_master.py` |
| `mortgage-proofs/` | LangGraph multi-agent mortgage pipeline + Lean 4 invariant checking | `cd mortgage-proofs && lake build` | `cd mortgage-proofs && pytest` |
| `archive/` | Superseded work — do not build or extend | — | — |

Planned: `backtest-proofs/` (event-driven backtester, $\mathcal{F}_t$-measurability proofs, after FTAP).

Each active subdir has its own CLAUDE.md with architecture details. Read that before working in a subdir.

## Hard rules

- Zero `sorry` on main. No exceptions.
- `mypy --strict` clean on all Python in `src/`.
- Licensed data (OptionMetrics/WRDS, Polygon paid) never committed.
- No private content: no GPA, grades, target firm names in strategy context, resume paths, or application timelines.
- Never extend or reference `archive/` as active code. It is read-only history.

## Summer 2026 sequence

1. **FTAP proof** (`ftap-proofs/`) — Harrison-Pliska 1981. Complete the Lean 4 proof. This is the theoretical spine everything else cites.
2. **Put-call parity** (`options-proofs/`) — CRR binomial model; proof cites FTAP.
3. **Real backtester** (new `backtest-proofs/`) — event-driven engine with $\mathcal{F}_t$-measurability proofs. Cites ftap-proofs results.

Read López de Prado (AFML Ch 1–4, 8–11) and Grinold & Kahn (Ch 1–6) in parallel with FTAP work.

## Planning

Open GitHub issues for all action items; close them in the same PR cycle. Check issues and
milestones at session start:

```bash
gh issue list --state open
gh api repos/eigenq-xyz/quant-proofs/milestones --jq '.[] | {number,title,due_on,open_issues}'
```

## Skills and agents

Run `/onboard-to-eigenq` for the full codebase briefing.

## Why this repo exists

The durable skill in quant work is directing and auditing AI-generated output — which requires being able to verify it formally. Every project here demonstrates that capability.
