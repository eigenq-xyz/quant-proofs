# CLAUDE.md

Monorepo for formally verified quantitative finance. Lean 4 proofs + Python/Cython execution.

## Projects

| Dir | What | Build | Test |
|-----|------|-------|------|
| `ftap-proofs/` | Discrete FTAP (Harrison-Pliska 1981): no arbitrage iff EMM exists | `cd ftap-proofs && lake build` | `grep -rn sorry --include="*.lean" ftap-proofs/` |
| `options-proofs/` | Put-call parity via Cox-Ross-Rubinstein; depends on ftap-proofs | `cd options-proofs && lake build` | same |
| `quant-core/` | Shared pricing primitives (OptionKind, payoffs, Black-Scholes, GBM) | `cd quant-core/lean && lake build` | `cd quant-core/python && pytest` |
| `optimization-proofs/` | Formally verified abstract PGD & simplex/L1 projection core | `cd optimization-proofs && lake build` (planned) | `grep -rn sorry --include="*.lean" optimization-proofs/` |
| `portfolio-proofs/` | Formally verified PGD simplex portfolio solver core | `cd portfolio-proofs/lean && lake build` (planned) | `python3 portfolio-proofs/scenarios/cholesky_crash/scipy_slsqp.py` |
| `mortgage-proofs/` | LangGraph multi-agent mortgage pipeline + Lean 4 invariant checking | `cd mortgage-proofs && lake build` | `cd mortgage-proofs && pytest` |
| `stopped-time-proofs/` | Geometric PMF + `GeometricExpectation` operator — Mathlib PR candidate, no finance content | `cd stopped-time-proofs && lake build` | `grep -rn '^\s*sorry\b' --include="*.lean" stopped-time-proofs/` |
| `perpetual-proofs/` | No-arbitrage pricing for perpetual futures (Ackerer-Hugonnier-Jermann 2025); depends on stopped-time-proofs + ftap-proofs | `cd perpetual-proofs && lake build` | same |
| `research-pipeline/` | **Flagship** — full quant-research-desk workflow (data→signals→stats→portfolio→backtest→eval→cross-asset); backtest stage proves no look-ahead (non-anticipation / $\mathcal{F}_t$-measurability); unifies the verified modules. In progress | `cd research-pipeline/lean && lake build` | `cd research-pipeline && pytest` |
| `archive/` | Superseded work — do not build or extend | — | — |

`research-pipeline/` is scaffolded (full desk workflow runs; backtest no-look-ahead core proved `sorry`-free; statistical layer rigorous but unverified). Next: measure-theoretic $\mathcal{F}_t$-measurability upgrade citing `ftap-proofs` + verified-solver wiring — see `research-pipeline/ROADMAP.md`.

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
