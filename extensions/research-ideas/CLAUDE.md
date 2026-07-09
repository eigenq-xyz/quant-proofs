# CLAUDE.md: research-ideas

Exploratory studies moved out of `research-pipeline/` because they don't meet its bar for a
load-bearing result. No Lean here. Treat every finding as a lead, not a claim.

## Layout

| Path | What |
|------|------|
| `LEAKAGE_MAP.md` | Cross-study summary of the data-revision leakage question |
| `commodity-leakage-tax/` | CFTC COT positioning + EIA gas-storage leakage studies |
| `macro-leakage/` | Nonfarm-payrolls leakage studies (standardized and threshold signal forms) |
| `crossasset.py` | 4 exploratory functions: `analyze_return_streams`, `reproduction_table`, `combine_sleeves_walkforward`, `verification_status_line` |
| `run_cross_asset.py` | CLI entry point for the AQR cross-asset breadth study |
| `compare_combine.py` | Compares verified-MV vs. equal-weight sleeve combination |
| `test_crossasset.py` | Offline, deterministic tests for `crossasset.py` |

`research_pipeline.crossasset.run_cross_asset` (the raw-price, backtester-routed function) is
**not** here: it stayed in `research-pipeline/src/` because it inherits the verified no-look-ahead
guarantee, and the package's own `__init__.py` and `scripts/run_demo.py` depend on it directly.
Don't move it here without re-checking those call sites.

## Import pattern

This directory is not an installed package. Every script and test inserts
`research-pipeline/src/` onto `sys.path` before importing `research_pipeline`, and inserts its own
directory before a local `from crossasset import ...` (`crossasset.py` here is a different module
from `research_pipeline.crossasset`, deliberately (see README for the split rationale).

## `_meta` provenance block

Every result JSON in this directory carries the repo-wide standard block: `generated_by`,
`generated_at`, `reproduce`, `verified` (always `false` here), `notes`. Regenerate a result by
running the `reproduce` command in its own `_meta`, not by guessing the invocation.

## Build / test

```bash
cd extensions/research-ideas
python3.12 -m pytest commodity-leakage-tax/ macro-leakage/ test_crossasset.py -v
mypy --strict crossasset.py run_cross_asset.py compare_combine.py
ruff check .
```

## Fail-loud

Like every study script in this repo, these fail hard on a missing dependency or data-fetch
failure. No script here silently falls back to synthetic or cached data when a live fetch fails.

## License

Apache 2.0.
