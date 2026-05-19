---
name: docs-report
description: >
  Builds the Quarto research papers in reports/ to PDF and HTML, then stages
  the output for GitHub Pages deployment under /reports/. Use after verify
  passes and when any reports/<project>-proofs.qmd or shared config
  (_quarto.yml, _eigenq.tex, _references.bib) changes.
paths:
  - "reports/**"
allowed-tools: Bash(quarto *) Bash(cp *) Bash(mkdir *) Bash(rm *)
---

# Docs Report

## Command

```bash
cd reports
quarto render                              # all papers → PDF + HTML in _output/
quarto render <project>-proofs.qmd         # one paper only
```

Output layout under `reports/_output/`:

```
<project>-proofs.pdf
<project>-proofs.html
<project>-proofs_files/                    # HTML assets (KaTeX, figures)
```

## Deployment

After `quarto render`, the orchestrator `docs-publish` stages the output for
GitHub Pages:

```bash
mkdir -p docs/reports
cp reports/_output/*.pdf reports/_output/*.html docs/reports/
cp -r reports/_output/*_files docs/reports/ 2>/dev/null || true
```

Target Pages layout: `/reports/<project>-proofs.{pdf,html}`. The PDF is the
canonical archival artifact (fixed pagination, citable). The HTML is the
web-discoverable version (linkable anchors, KaTeX math).

## Prerequisites

1. **Quarto CLI** installed (`quarto --version` ≥ 1.4).
2. **LaTeX distribution** with the packages listed at the top of
   `reports/_eigenq.tex`. Install missing packages with `tlmgr install <name>`.
3. **Authoring complete** — papers must be written via the
   `writing-research-reports` skill before this skill renders them.
4. **`/verify` Levels 1–5 passing** — never render docs from a broken proof
   or failing test. Enforced by `docs-publish`.

## Composition with other docs sub-builds

A paper's Formalization section cites Lean theorems by name. If `docs-lean`
is also rebuilt in the same publish cycle, the links to `/lean/` resolve.
Out-of-cycle builds may produce stale cross-links — `docs-publish` is the
orchestrator that keeps them in sync.

A paper's Results and Robustness sections cite figures from
`<project>-proofs/results/figures/*.pdf` by relative path. Those artifacts
are produced by the `verify-empirical` and `verify-regime` levels and
indexed by `docs-research` for the aggregation site. `docs-report` renders
them into the standalone paper PDF — it does not regenerate them.

## Current status

The `reports/` project exists with shared config (`_quarto.yml`,
`_eigenq.tex`, `_references.bib`, `_template.qmd`). No `<project>-proofs.qmd`
files have been authored yet — start with the `writing-research-reports`
skill before invoking this skill.

The Pages workflow at `pages.yml` currently deploys `/` and `/lean/`; the
`/reports/` path needs a `cp` step added to the workflow once a paper is
published.
