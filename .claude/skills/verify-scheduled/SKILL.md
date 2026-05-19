---
name: verify-scheduled
description: >
  Level 7 verification: weekly CI pipeline that refreshes FRED data, regenerates
  computed series, runs Levels 1-5, and commits updated data files with timestamp.
  CI-only — triggers Monday 8am UTC or via workflow_dispatch.
---

# Verify Scheduled — Level 7 (CI Only)

## Trigger

```yaml
# In .github/workflows/scheduled.yml (not yet created):
on:
  schedule:
    - cron: '0 8 * * 1'  # Monday 8am UTC
  workflow_dispatch:       # Manual trigger
```

Manual trigger:
```bash
gh workflow run scheduled.yml --repo eigenq-xyz/quant-proofs
```

## What the weekly job does

1. **Refresh FRED data** — download five series (VIX, T-bill, 10yr, SP500, HY spread)
2. **Regenerate computed series** — VRP, regime labels from fresh FRED + VOLARE data
3. **Run data-quality gate** — block commit if any quality check fails
4. **Run Levels 1–5** — full verification pyramid (no Level 6, WRDS blocked)
5. **Commit updated CSVs** — with `[skip ci]` to avoid infinite loop

## Rate limit awareness

FRED allows 120 requests/minute. Batch all five series in a single session:
```python
import fredapi
fred = fredapi.Fred(api_key=os.environ["FRED_API_KEY"])
# Fetch all series before closing session
```

## Commit format

```
chore(data): weekly refresh 2026-MM-DD [skip ci]

Auto-refresh: FRED (5 series), computed VRP + regime labels.
All quality checks passed. Levels 1-5 green.
```

## What it does NOT do

- Does NOT touch WRDS / OptionMetrics data (MFA blocks automation)
- Does NOT run `verify-research` (Level 6)
- Does NOT rebuild Cython FFI (Lean sources unchanged)

## Current status

`.github/workflows/scheduled.yml` does not yet exist. The existing `lean-ci.yml`
runs on push/PR only. Create the scheduled workflow when the data pipeline
(`data-fred`, `data-computed`, `data-quality` skills) is implemented.
