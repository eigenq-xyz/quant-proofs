---
name: docs-report
description: >
  Builds the Quarto research papers in reports/ to PDF and HTML, then stages
  the output for GitHub Pages deployment under /paper/. Use after verify
  passes and when any reports/<project>-proofs.qmd or shared config
  (_quarto.yml, _eigenq.tex, _references.bib) changes.
  NOTE: the /paper/ Pages route and the pages.yml "copy PDF" step described
  below do not currently exist in .github/workflows/pages.yml — that workflow
  only builds docs/ (JupyterBook) and copies portfolio-proofs scenario reports.
  Treat the deployment section as the target design, not the current CI behavior,
  until pages.yml is updated to match.
paths:
  - "reports/**"
allowed-tools: Bash(quarto *) Bash(cp *) Bash(mkdir *) Bash(rm *)
---

# Docs Report

Builds the Quarto research papers in `reports/` to PDF and HTML.

## Quarto configuration (best practices)

**Engine:** `xelatex`. Unicode-aware, no encoding declarations needed.
Set via `pdf-engine: xelatex` in the `format.pdf` block of `_quarto.yml`.
Never `pdflatex` for eigenq papers — Unicode math symbols in prose fail.

**Citations:** `cite-method: citeproc` (Quarto-native, CSL-driven).
Set at the top level of `_quarto.yml`. Do NOT use `cite-method: biblatex` or
`biblio-style: authoryear` — biblatex 3.18+ needs `.dbx` files that TinyTeX
doesn't consistently have, which breaks CI.

**Cross-references:** Quarto native (`@fig-x`, `@tbl-x`, `@thm-x`).
Do NOT load `cleveref` in `_eigenq.tex`. Cleveref must load after hyperref,
but `include-in-header` runs before Pandoc adds hyperref, and `\usepackage`
inside `\AtBeginDocument` is illegal.

**Freeze:** `execute: freeze: auto` in `_quarto.yml`. Frozen outputs live in
`reports/_freeze/` (committed to git). `--no-execute` skips chunk re-execution
for CI fast-path and HTML-only renders.

**Post-render hook:** `reports/post-render.sh` copies `_output/*.pdf` to the
project root (`reports/<name>.pdf`). CI deploys this committed PDF to
Pages — no LaTeX install needed in GitHub Actions.

## Commands

```bash
cd reports

# Full render (PDF + HTML, re-executes stale frozen chunks):
quarto render ftap-proofs.qmd

# Fast render from frozen cache (PDF + HTML, no Python execution):
quarto render ftap-proofs.qmd --no-execute

# PDF only:
quarto render ftap-proofs.qmd --to pdf --no-execute

# HTML only (for draft previewing; no LaTeX needed):
quarto render ftap-proofs.qmd --to html --no-execute
```

No root-level or `reports/`-level `Makefile` exists in the current tree. The `make paper` /
`make paper-fast` / `make paper-clean` targets in older versions of this skill don't exist
today. Use the `quarto render` commands above directly; run `rm -rf _freeze/ _output/`
manually for a clean-cache re-render.

Output layout after rendering:

```
reports/_output/         ← gitignored; Quarto's working output
  ftap-proofs.pdf         ← xelatex-built PDF
  ftap-proofs.html        ← HTML with KaTeX math
  ftap-proofs_files/      ← HTML assets
reports/ftap-proofs.pdf  ← committed stable path (copied by post-render.sh)
reports/_freeze/          ← committed frozen chunk cache
```

Note: `reports/backtest-proofs_files/` also exists on disk today, as leftover asset debris from
before the `backtest-proofs` archival. No corresponding `backtest-proofs.qmd` source file exists
anymore. Don't treat that directory as evidence a `backtest-proofs` paper is live — it's stale
and safe to ignore (removing it is outside this skill's narrow scope).

## GitHub Pages deployment

CI (`pages.yml`) deploys paper under `/paper/`:
- **HTML** — rendered in CI from frozen cache via `quarto render --no-execute`.
- **PDF** — copied directly from committed `reports/<name>.pdf`. No LaTeX in CI.

Pages URLs (target design, not yet wired in `pages.yml` — see the note at the top of this
file): `/paper/ftap-proofs.html` and `/paper/ftap-proofs.pdf`.

Adding a new paper to Pages requires a corresponding `cp` step in `pages.yml`'s
"Copy paper to Pages artifact" step.

## LaTeX package management (local rendering only)

For packages not in TinyTeX by default, install via:

```bash
~/Library/TinyTeX/bin/universal-darwin/tlmgr install <package>
```

The `_eigenq.tex` preamble documents which packages are required.
The `keep-tex: true` option in `_quarto.yml` leaves `_output/<name>.tex` for
debugging compilation failures.

## Composition with other docs sub-builds

A paper's Formalization section cites Lean theorems by name. Results sections
cite figures from `<project>-proofs/results/figures/*.pdf`. The `verify-empirical`
and `verify-regime` skills produce both — `docs-report` renders them into the
paper, it does not regenerate them.

## Current status

`reports/ftap-proofs.qmd` is the first live paper: complete, with an empirical
companion (see `reports/ftap-proofs.pdf`/`.html`/`.tex` and `_output/` for
rendered artifacts). A `backtest-proofs.qmd` paper was never authored as a
live `reports/` file — only stale asset debris (`reports/backtest-proofs_files/`)
remains from before that project's archival. As of this writing, `reports/**`
changes do not trigger a Pages deploy of the rendered paper — see the note at
the top of this file. `pages.yml` currently only reacts to `docs/**` and
`foundations/portfolio-proofs/{reports,scenarios}/**`.
