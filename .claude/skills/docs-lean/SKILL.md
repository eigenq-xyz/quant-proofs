---
name: docs-lean
description: >
  Builds the Lean 4 API documentation from module docstrings using doc-gen4.
  Every exported theorem and definition gets a page with its statement and
  cross-references. Deploys to /docs/lean/ on GitHub Pages.
paths:
  - "**/*.lean"
  - "**/lakefile.*"
allowed-tools: Bash(lake *)
---

# Docs Lean

## Command

```bash
cd backtest-proofs/lean && lake doc
```

Output: `backtest-proofs/lean/.lake/build/doc/`

## Adding doc-gen4 to a lakefile

```lean
require doc-gen4 from git
  "https://github.com/leanprover/doc-gen4" @ "main"
```

Then add a `lean_exe` target:
```lean
lean_exe «doc-gen4» where
  root := `DocGen4
```

Or simply run `lake doc` — Lake handles it if doc-gen4 is in the manifest.

## Docstring requirements

doc-gen4 renders `/-- ... -/` docstrings as HTML. For the output to be useful
to a non-Lean reader, every exported theorem must have:

1. **English statement** — what the theorem says in words
2. **Mathematical context** — why it matters, what it enables
3. **Citation** for non-trivial results (Harrison-Pliska 1981, CRR 1979)
4. **No Lean syntax in prose** — the proof is shown separately; the docstring is for humans

Bad docstring:
```lean
/-- `portfolio_value p = p.cash + hedge_sum_position_values p.positions` -/
```

Good docstring:
```lean
/-- Portfolio value equals cash plus the sum of all position values.
This is the fundamental accounting identity — no value is created or destroyed
by the accounting layer. Proved for arbitrary portfolios in BacktestProofs. -/
```

## Current status

doc-gen4 is not yet in any lakefile in this repo. Add it to `backtest-proofs/lean/lakefile.lean` first, then `ftap-proofs` and `options-proofs` for mathlib PR preparation.
