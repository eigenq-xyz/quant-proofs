# Results index

Every empirical number this repo cites traces to a committed JSON file. This page is the map:
what each file measures, where it lives, and the exact command that regenerates it. Read this
before citing a number in a paper, PR, or conversation with another assistant — confirm the
number is still current, or regenerate it first.

**Convention: regenerate before you cite, don't re-run by default.** These files are small,
committed, and carry provenance (date, seed, or platform) in a `_meta` block or docstring. Trust
the committed value for day-to-day reference. Re-run only when you're about to publish a number,
when you've changed the code the number depends on, or when the date below looks stale relative
to a change that should have moved it.

## Foundations

| Result | What it measures | File | Regenerate | Last updated |
|---|---|---|---|---|
| Solver benchmark (all 7 scenarios × SLSQP/trust-constr/Gurobi/OR-Tools/Lean PGD) | Wall-clock latency (median + IQR, 15 timed reps after 3 warmup) per solver per stress scenario, including Gurobi | `foundations/portfolio-proofs/results/benchmark_all_solvers.json` | `cd foundations/portfolio-proofs && uv run python reports/benchmark_all_solvers.py` | 2026-06-21 |
| Lean PGD solve latency | Warm-subprocess median solve time, 12 reps, for the verified solver alone | `foundations/portfolio-proofs/results/lean_pgd_benchmark.json` | `cd foundations/portfolio-proofs && python reports/regenerate_lean_pgd.py` | 2026-06-21 |
| Put-call parity deviation under quote noise | Parity gap in basis points of spot on a synthetic Black-Scholes cross-section perturbed by multiplicative quote noise, at several friction levels | `foundations/ftap-proofs/results/metrics/parity_consistency.json` | `cd foundations/ftap-proofs && python results/parity_consistency_study.py` | 2026-06-21 |

**Gurobi is in `benchmark_all_solvers.json`.** Every row records the solver name, scenario, N,
condition number, median/q1/q3/min/max latency, and a convergence flag — Gurobi's rows are not
different in kind from SLSQP's or Lean PGD's. If you can't find it: it's one JSON key away
(`"solver": "Gurobi"`), not a separate file.

## research-pipeline studies

| Result | What it measures | File | Regenerate | Last updated |
|---|---|---|---|---|
| Headline momentum study | 12-1 cross-sectional momentum, 49 Ken French industries, daily, 1926-2026 | `research-pipeline/studies/results_ken_french_49ind.json` | `cd research-pipeline && python -m scripts.run_study` | 2026-06-21 |
| Verified PGD vs. naive construction, single-name universe | Head-to-head: verified PGD mean-variance vs. naive portfolio construction on the same 12-1 momentum signal, Ken French 49 industries, monthly rebalance | `research-pipeline/studies/results_pgd_comparison_monthly.json` | `cd research-pipeline && uv run python -m scripts.compare_pgd` (default `--rebalance monthly`, ~2 min; `--rebalance daily` is ~40+ min, see the script's own docstring for why that mode is not the default comparison) | 2026-06-21 |
| Variance-risk-premium delta-hedged short-vol study | Short-vol S&P 500 delta-hedge P&L under realistic hedging frictions and option-spread sensitivity sweeps | `research-pipeline/studies/vrp/results_vrp.json` | `python3.12 research-pipeline/studies/vrp/run_study.py` | 2026-07-09 |

Exploratory work (the CFTC/EIA/payrolls leakage-tax map, AQR cross-asset breadth) moved to
[`extensions/research-ideas/`](extensions/research-ideas/README.md) and is intentionally left out
of this index: those results aren't load-bearing claims yet. See that directory's own README for
its result files and reproduce commands.

## Why these are safe to store instead of re-running

Every generator above runs in seconds to low minutes on free or already-committed data (Ken
French, Yahoo/FRED, synthetic). The one exception is `compare_pgd.py --rebalance daily` (~40+
minutes) — its default `monthly` mode is the one cited everywhere in this repo. Re-running any
of these on every read would cost nothing in most cases and tens of minutes in that one case, for
no benefit over trusting a committed, dated, provenance-carrying JSON. Re-run when the code
changes, not when you're just checking a number.
