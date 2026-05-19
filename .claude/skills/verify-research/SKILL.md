---
name: verify-research
description: >
  Level 6 verification (LOCAL ONLY): full research pipeline using OptionMetrics
  via WRDS. Generates publication-quality results committed to results/. Requires
  WRDS account with active MFA session. Never runs in GitHub Actions.
paths:
  - "notebooks/**"
  - "results/**"
allowed-tools: Bash(jupyter *) Bash(uv run *)
---

# Verify Research — Level 6 (Local Only)

This level never runs in CI. WRDS MFA blocks automation. The output files
(`results/charts/*.png`, `results/tables/*.csv`) are what get committed.

## Prerequisites

```bash
# WRDS session must be active — re-authenticate if IP changed or session >30 days
python3 -c "import wrds; db = wrds.Connection()"

# OptionMetrics parquet files must be in local_data/ (gitignored)
ls local_data/optionmetrics_*.parquet
```

## Running the research pipeline

```bash
cd backtest-proofs/python
uv sync --extra docs

# Execute all notebooks (outputs are committed, not notebooks)
uv run jupyter nbconvert --to notebook --execute notebooks/*.ipynb --output-dir notebooks/executed/
```

## What this produces

| Output | Description |
|--------|-------------|
| `results/charts/parity_deviation_2015_2024.png` | Put-call parity deviation over time |
| `results/charts/regime_breakdown.png` | Deviation by VIX regime |
| `results/charts/backtest_pnl.png` | Delta-hedging strategy PnL |
| `results/tables/regression_results.csv` | VRP vs parity deviation regression |

## Data quality rules

- **OptionMetrics timestamp**: prices at 15:59 Eastern, not 16:00 — align by date only
- **In-sample / out-of-sample**: declare the split before running, never retroactively
- **No raw WRDS data committed** — outputs only, raw stays in `local_data/` (gitignored)

## Committing results

```bash
git add results/
git commit -m "docs(results): update empirical results YYYY-MM-DD"
```
