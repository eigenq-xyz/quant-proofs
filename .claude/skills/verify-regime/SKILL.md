---
name: verify-regime
description: >
  Level 5 verification: regime conditioning tests across VIX regimes, stress event
  validations (March 2020, February 2018), and A-B data source comparisons.
  Runs after verify-empirical passes.
paths:
  - "data/computed/**"
  - "tests/regime/**"
allowed-tools: Bash(uv run pytest *)
---

# Verify Regime — Level 5

## Command

```bash
uv run pytest tests/regime/ -v
```

## Regime definitions

VIX-based thresholds applied to `data/computed/regime_labels.csv`:

| Regime | VIX range | Expected behavior |
|--------|-----------|------------------|
| Low | < 12 | Small parity deviations, positive VRP |
| Normal | 12–20 | Baseline results hold |
| Elevated | 20–30 | Wider deviations, VRP signal noisy |
| Crisis | > 30 | Large parity deviations, VRP may flip |

## What regime tests check

- **Parity deviation by regime**: crisis deviation > normal deviation (statistically)
- **Backtest performance by regime**: strategy Sharpe higher in normal than crisis
- **VRP signal**: positive mean in low/normal, check sign in elevated/crisis
- **Regime transition**: no artificial jumps at threshold boundaries

## Stress event validations

Specific dates that must show expected behavior:

| Event | Date | Expected |
|-------|------|---------|
| COVID crash | 2020-03-16 | VIX > 80, parity deviation > 2% |
| VIX spike | 2018-02-05 | VIX > 37, large call/put spread widening |
| GFC | 2008-10-10 | If in sample: VIX > 70 |

## A-B data source comparison

FRED VIXCLS vs CBOE VIX historical should match within 0.01 vol points.
Run: `pytest tests/regime/test_source_comparison.py -v`

## Current status

`tests/regime/` and `data/computed/regime_labels.csv` not yet built.
Depends on `data-computed` skill producing regime labels from VIX thresholds.
