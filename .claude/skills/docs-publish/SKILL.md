---
name: docs-publish
description: >
  Orchestrates both documentation builds and deploys to GitHub Pages. docs-lean
  builds the Lean API reference from module docstrings; docs-research builds the
  research paper site from results/. Use after verify passes, or when .lean files
  or results/ change.
allowed-tools: Bash(lake *) Bash(uv run *) Bash(gh *)
---

# Docs Publish — Orchestrator

## Gate rule

`/verify` (Levels 1–5) must pass before docs-publish. Documentation built from
a broken proof or failing tests misleads readers.

## When each sub-build triggers

| Change | Sub-build |
|--------|----------|
| Any `.lean` file | `/docs-lean` |
| Any file in `results/` | `/docs-research` |
| Both | Both, can run in parallel |

## Commands

```bash
# Lean API reference
cd backtest-proofs/lean && lake doc

# Research paper site
cd backtest-proofs/python && uv run jupyter-book build ../../docs/

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
- `/` → root JupyterBook (`docs/`)
- `/lean/` → Lean API reference (doc-gen4 output)
- `/paper/` → Research paper site

## Current status

The root JupyterBook (`docs/`) and Pages workflow (`pages.yml`) are deployed.
`/docs-lean` is blocked on doc-gen4 being added to lakefiles.
`/docs-research` is blocked on `results/` directory existing.
