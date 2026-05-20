---
name: docs-report
description: >
  Builds the Quarto research papers in reports/ to PDF and HTML, then stages
  the output for GitHub Pages deployment under /paper/. Use after verify
  passes and when any reports/<project>-proofs.qmd or shared config
  (_quarto.yml, _eigenq.tex, _references.bib) changes.
paths:
  - "reports/**"
allowed-tools: Bash(quarto *) Bash(cp *) Bash(mkdir *) Bash(rm *)
---

# Docs Report

## Quarto configuration (best practices)

**Engine:** `xelatex` — Unicode-aware, no encoding declarations needed.
Set via `pdf-engine: xelatex` in the `format.pdf` block of `_quarto.yml`.
Never use `pdflatex` for eigenq papers (Unicode math symbols in prose fail).

**Citations:** `cite-method: citeproc` (Quarto-native, CSL-driven).
Set at the top level of `_quarto.yml`. Do NOT use `cite-method: biblatex` or
`biblio-style: authoryear` — biblatex 3.18+ requires `.dbx` files that are
not consistently available in TinyTeX, causing CI failures.

**Cross-references:** Quarto native (`@fig-x`, `@tbl-x`, `@thm-x`).
Do NOT load `cleveref` in `_eigenq.tex` — cleveref must load after hyperref,
but `include-in-header` is processed before Pandoc adds hyperref, and
`\usepackage` inside `\AtBeginDocument` is illegal.

**Freeze:** `execute: freeze: auto` in `_quarto.yml`. Frozen outputs live in
`reports/_freeze/` (committed to git). `--no-execute` skips chunk re-execution
for CI fast-path and HTML-only renders.

**Post-render hook:** `reports/post-render.sh` copies `_output/*.pdf` to the
project root (`reports/<name>.pdf`). The committed PDF is what CI deploys to
Pages — no LaTeX installation required in GitHub Actions.

## Commands

```bash
cd reports

# Full render (PDF + HTML, re-executes stale frozen chunks):
quarto render backtest-proofs.qmd

# Fast render from frozen cache (PDF + HTML, no Python execution):
quarto render backtest-proofs.qmd --no-execute

# PDF only:
quarto render backtest-proofs.qmd --to pdf --no-execute

# HTML only (for draft previewing; no LaTeX needed):
quarto render backtest-proofs.qmd --to html --no-execute

# Or use the Makefile from backtest-proofs/:
make paper        # full re-render (stale chunks only)
make paper-fast   # no-execute fast path
make paper-clean  # wipe _freeze/, _output/, results/figures/, metrics.json
```

Output layout after rendering:

```
reports/_output/           ← gitignored; Quarto's working output
  backtest-proofs.pdf      ← xelatex-built PDF
  backtest-proofs.html     ← HTML with KaTeX math
  backtest-proofs_files/   ← HTML assets
reports/backtest-proofs.pdf  ← committed stable path (copied by post-render.sh)
reports/_freeze/             ← committed frozen chunk cache
```

## GitHub Pages deployment

CI (`pages.yml`) deploys paper under `/paper/`:
- **HTML**: rendered in CI from frozen cache via `quarto render --no-execute`
- **PDF**: copied directly from committed `reports/<name>.pdf` — no LaTeX in CI

Pages URLs: `/paper/backtest-proofs.html` and `/paper/backtest-proofs.pdf`

Adding a new paper to Pages requires adding a corresponding `cp` step in
`pages.yml`'s "Copy paper to Pages artifact" step.

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
cite figures from `<project>-proofs/results/figures/*.pdf`. Both are produced
by the `verify-empirical` and `verify-regime` skills — `docs-report` renders
them into the paper but does not regenerate them.

## Current status

`reports/backtest-proofs.qmd` is the first live paper. It has all 9 sections
scaffolded with hidden plan callouts and 7 figure chunks backed by frozen
outputs. Prose sections are TODO stubs pending the fill-order pass
(§5 → §6 → §7 → §8 → §3 → §4 → §2 → §1). The paper deploys to Pages via
`pages.yml` whenever `reports/**` changes on main.
