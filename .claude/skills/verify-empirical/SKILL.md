---
name: verify-empirical
description: >
  Level 4 verification: data quality gate then empirical tests on committed
  datasets (FRED, AQR, Fama-French, CBOE, synthetic). Verifies put-call parity
  deviations, VRP sign convention, and result reproducibility. Runs after
  verify-property passes.
paths:
  - "data/**"
  - "results/**"
  - "tests/empirical/**"
allowed-tools: Bash(uv run pytest *) Bash(python3 *)
---

# Verify Empirical — Level 4

## Data quality gate (must pass first)

```bash
uv run pytest tests/data_quality/ -v
```

Checks across all `data/` files:
- No missing values in critical columns (price, date, return)
- Dates monotonically increasing
- All prices > 0
- VIX > 0 at all dates
- Factor returns within historical range (no 50%+ daily moves)
- VRP mean positive over full sample (implied > realized on average)

## Empirical tests

```bash
uv run pytest tests/empirical/ -v
uv run pytest tests/reproducibility/ -v
```

What gets tested:
- **Put-call parity deviation** (synthetic + yfinance): deviation within bid-ask spread for liquid strikes
- **VRP sign convention**: FRED VIX² minus VOLARE realized vol² has positive mean
- **Factor return range**: Fama-French factors within historical distribution
- **Reproducibility**: committed `results/` files match what the notebooks produce on re-run

## Hard rule: data source tiers

| Source | Goes to | Publishable |
|--------|---------|-------------|
| FRED, AQR, French, CBOE, VOLARE | `data/` | ✅ (with citation) |
| yfinance snapshots | `tests/fixtures/` only | ❌ never in README results |
| OptionMetrics/WRDS | `results/` (outputs only, not raw) | ✅ outputs only |

## On failure

1. Run data quality gate first — bad data is upstream of most empirical failures
2. Check the specific deviation magnitude in the failure output
3. If parity deviation > bid-ask: check yfinance vs OptionMetrics discrepancy
4. If VRP sign flips: check VOLARE download date and realized vol computation lag

## Current status

`tests/empirical/`, `tests/data_quality/`, and `data/` pipeline not yet built.
Implement `data-fred` and `data-synthetic` source skills first, then this gate.
