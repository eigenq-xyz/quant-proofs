# CLAUDE.md

Monorepo for formally verified quantitative finance. Lean 4 proofs + Python/Cython execution.

## Projects

| Dir | What | Build | Test |
|-----|------|-------|------|
| `foundations/ftap-proofs/` | Discrete FTAP (Harrison-Pliska 1981): no arbitrage iff EMM exists | `cd foundations/ftap-proofs && lake build` | `grep -rn sorry --include="*.lean" foundations/ftap-proofs/` |
| `foundations/options-proofs/` | Put-call parity via Cox-Ross-Rubinstein; depends on ftap-proofs | `cd foundations/options-proofs && lake build` | same |
| `foundations/quant-core/` | Shared pricing primitives (OptionKind, payoffs, Black-Scholes, GBM) | `cd foundations/quant-core/lean && lake build` | `cd foundations/quant-core/python && pytest` |
| `foundations/optimization-proofs/` | Formally verified abstract PGD & simplex/L1 projection core | `cd foundations/optimization-proofs && lake build` (planned) | `grep -rn sorry --include="*.lean" foundations/optimization-proofs/` |
| `foundations/portfolio-proofs/` | Formally verified PGD simplex portfolio solver core | `cd foundations/portfolio-proofs/lean && lake build` (planned) | `python3 foundations/portfolio-proofs/scenarios/cholesky_crash/scipy_slsqp.py` |
| `extensions/mortgage-proofs/` | LangGraph multi-agent mortgage pipeline + Lean 4 invariant checking | `cd extensions/mortgage-proofs && lake build` | `cd extensions/mortgage-proofs && pytest` |
| `extensions/stopped-time-proofs/` | Geometric PMF + `GeometricExpectation` operator, Mathlib PR candidate, no finance content | `cd extensions/stopped-time-proofs && lake build` | `grep -rn '^\s*sorry\b' --include="*.lean" extensions/stopped-time-proofs/` |
| `extensions/perpetual-proofs/` | No-arbitrage pricing for perpetual futures (Ackerer-Hugonnier-Jermann 2025); depends on stopped-time-proofs + ftap-proofs | `cd extensions/perpetual-proofs && lake build` | same |
| `research-pipeline/` | **Flagship**: full quant-research-desk workflow (data→signals→stats→portfolio→backtest→eval→cross-asset); proves no look-ahead (non-anticipation) AND signal $\mathcal{F}_t$-measurability vs the natural filtration; unifies the verified modules | `cd research-pipeline/lean && lake build` | `cd research-pipeline && pytest` |
| `archive/` | Superseded work, do not build or extend | — | — |

**Tiers** (the README groups by these): **flagship** = `research-pipeline`; **verified foundations** = `ftap-proofs`, `options-proofs`, `quant-core`, `optimization-proofs`, `portfolio-proofs`; **extensions** = `perpetual-proofs`, `stopped-time-proofs`, `mortgage-proofs`; **archive**.

`research-pipeline/` runs the full desk workflow end to end. Proved `sorry`-free: backtest non-anticipation, OOS no-leakage, and signal $\mathcal{F}_t$-measurability (`Measurability.lean`, cites `ftap-proofs`). The real Ken French momentum study is run and reported in `studies/REPORT.md`; cross-asset breadth uses free AQR data. The statistical layer is rigorous but unverified. Remaining: route portfolio construction through `pgd_solve` by default and extend the verified projection to the dollar-neutral simplex, tracked in the open GitHub issues under the **research-pipeline completion sprint** milestone.

Each active subdir has its own CLAUDE.md with architecture details. Read that before working in a subdir.

## Hard rules

- Zero `sorry` on main. No exceptions.
- `mypy --strict` clean on all Python in `src/`.
- Licensed data (OptionMetrics/WRDS, Polygon paid) never committed.
- No private content: no GPA, grades, target firm names in strategy context, resume paths, or application timelines.
- Never extend or reference `archive/` as active code. It is read-only history.

## Summer 2026 sequence

1. **FTAP proof** (`foundations/ftap-proofs/`): Harrison-Pliska 1981. Complete the Lean 4 proof. This is the theoretical spine everything else cites.
2. **Put-call parity** (`foundations/options-proofs/`): CRR binomial model; proof cites FTAP.
3. **Real backtester** (new `backtest-proofs/`): event-driven engine with $\mathcal{F}_t$-measurability proofs. Cites ftap-proofs results.

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

The durable skill in quant work is directing and auditing AI-generated output, which requires being able to verify it formally. Every project here demonstrates that capability.
