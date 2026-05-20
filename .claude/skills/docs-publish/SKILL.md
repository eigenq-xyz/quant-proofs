---
name: docs-publish
description: >
  Orchestrates all documentation builds and deploys to GitHub Pages. docs-lean
  builds the Lean API reference from module docstrings; docs-research builds
  the aggregation site from results/; docs-report renders the Quarto research
  papers in reports/. Use after verify passes, or when .lean files, results/,
  or reports/ change.
allowed-tools: Bash(lake *) Bash(uv run *) Bash(quarto *) Bash(cp *) Bash(mkdir *) Bash(gh *)
---

# Docs Publish — Orchestrator

## Gate rule

`/verify` (Levels 1–5) must pass before docs-publish. Documentation built from
a broken proof or failing tests misleads readers.

## When each sub-build triggers

| Change                                                  | Sub-build       |
|---------------------------------------------------------|-----------------|
| Any `.lean` file                                        | `/docs-lean`    |
| Any file in `<project>-proofs/results/`                 | `/docs-research`|
| Any file in `reports/` (including shared config)        | `/docs-report`  |
| Multiple                                                | All affected — can run in parallel |

## Commands

```bash
# Lean API reference (per project, or loop over projects)
cd backtest-proofs/lean && lake doc

# Aggregation site (Jupyter Book) — narrative index across projects
cd backtest-proofs/python && uv run jupyter-book build ../../docs/

# Research papers (Quarto) — PDF + HTML per project
cd reports && quarto render
mkdir -p docs/reports
cp reports/_output/*.pdf reports/_output/*.html docs/reports/
cp -r reports/_output/*_files docs/reports/ 2>/dev/null || true

# Manual Pages deploy (usually done by CI)
gh workflow run pages.yml --repo eigenq-xyz/quant-proofs
```

## Deployment

GitHub Pages is enabled at `https://eigenq-xyz.github.io/quant-proofs/`

Enabled via:
```bash
gh api repos/eigenq-xyz/quant-proofs/pages --method POST -f build_type=workflow
```

Target layout (once fully implemented):
- `/` → root Jupyter Book (`docs/`) — landing page and narrative index
- `/lean/` → Lean API reference (doc-gen4 output)
- `/paper/` → Aggregation site (Jupyter Book pulled from `results/`)
- `/reports/` → Standalone research papers (Quarto PDF + HTML)

## Current status

The root Jupyter Book (`docs/`) and Pages workflow (`pages.yml`) are deployed.
- `/docs-lean` is blocked on doc-gen4 being added to lakefiles.
- `/docs-research` is blocked on `results/` directory existing.
- `/docs-report` is unblocked — `reports/` scaffold exists; needs the first
  `<project>-proofs.qmd` authored via `write-research-reports`, then a
  `cp` step added to `pages.yml`.
