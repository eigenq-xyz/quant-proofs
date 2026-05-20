---
name: write-research-reports
description: >
  Authoring assistant for full-length research papers in the eigenq-xyz Quarto
  format. Use when starting a new paper, drafting or reviewing a section, or
  auditing a draft for adherence to the AQR/JFE hybrid template with mandatory
  Formalization and Robustness sections. Distinct from write-readme-results
  (single exhibits) and docs-research (Jupyter Book aggregation site).
paths:
  - "reports/**"
allowed-tools: Bash(quarto *) Read Write Edit Glob
---

# Writing Research Reports

## When to use

- Starting a new `reports/<project>-proofs.qmd`
- Drafting or revising any section of an existing paper
- Reviewing a draft for adherence to the standard format

Not this skill:
- Single-exhibit results in a README → `write-readme-results`
- Cross-project aggregation site → `docs-research`
- Lean 4 proof docstrings → `write-technical-docs`
- Empirical methodology design → `conduct-quant-research`

## Format

Quarto (`.qmd`) only — never raw LaTeX, never plain Markdown.

| File | Purpose |
|------|---------|
| `reports/_template.qmd` | Canonical template — copy to start a new paper |
| `reports/_quarto.yml` | Project config (PDF + HTML output, biblatex author-year) |
| `reports/_eigenq.tex` | Shared LaTeX preamble (math packages, finance macros, styling) |
| `reports/_references.bib` | Shared bibliography |
| `reports/_output/` | Render artifacts — not committed |
| `reports/<project>-proofs.qmd` | One per project; build with `quarto render <file>.qmd` |

Build commands:

```bash
quarto render <project>-proofs.qmd      # one paper → PDF + HTML
quarto render                           # all papers in reports/
quarto preview <project>-proofs.qmd     # live HTML preview while drafting
```

PDF builds require a LaTeX distribution with the packages listed at the top of
`reports/_eigenq.tex`. Install missing packages with `tlmgr install <name>`.

## Composition with the rest of the monorepo

- `<project>-proofs/results/` — committed empirical artifacts (figures, JSON metrics).
  Papers cite these by relative path; they do not regenerate them.
- `docs/` — Jupyter Book reference site. A finished paper can be indexed from
  the docs site via the `docs-research` skill.
- `<project>-proofs/CLAUDE.md` — project architecture; a paper's Setup section
  should be consistent with that document.

## Mandatory sections

Every paper — including pure-proof papers — has these nine sections in this
order. Empirical content is required everywhere; "we proved it, no empirics" is
not acceptable in the eigenq-xyz series.

| # | Section          | Target      |
|---|------------------|-------------|
| 1 | Abstract         | 150–250 w   |
| 2 | Introduction     | 2–4 p       |
| 3 | Setup            | 2–4 p       |
| 4 | Main Results     | 3–6 p       |
| 5 | **Formalization**| 2–4 p       |
| 6 | Empirical Setup  | 1–2 p       |
| 7 | Results          | 4–8 p       |
| 8 | **Robustness**   | 3–5 p       |
| 9 | Discussion       | 1–2 p       |

Body length 20–30 pages, excluding appendix and references.

## Section conventions

The template's placeholder prose covers section content in detail. The points
below are the rules a reviewer should enforce in a draft.

**Abstract.** Question (1 sentence), answer (1 sentence), method,
formalization claim quoting the commit SHA and zero-`sorry` status, empirical
sample (window + universe + source), the single number that best conveys the
result, scope/limitation. No marketing language.

**Formalization** *(mandatory).* Table mapping every paper-level theorem to
its Lean name and source file. A `::: {.callout-note title="Formalization
claim"}` block stating "`lake build` succeeds and `grep -rn sorry` returns
no matches at commit `<short-sha>`." A scope statement listing what is NOT
formalized (floating-point execution, data ingestion, statistical claims).

**Empirical Setup.** A table with data source, sample window, universe,
frequency, filters, and final N. Licensed-data sources documented per
`source-financial-data`; raw data never committed.

**Results.** Lead with the headline figure. Plain-English result in the
figure caption. Every empirical claim traceable to
`<project>-proofs/results/<artifact>.json` or `.../figures/<artifact>.pdf`.

**Robustness** *(mandatory).* At minimum: (1) sample-period sensitivity
including 2008 and 2020 sub-periods, (2) regime conditioning (VIX quintiles
or NBER recessions), (3) data-source A/B where applicable, (4) at least one
specification alternative. Report worst-case bps/dollar magnitudes, not just
p-values. If the result reverses anywhere, report it here, not the appendix.

## Format conventions

- **Theorems**: Quarto native callouts `::: {#thm-name}`, not raw
  `\begin{theorem}`.
- **Lean code**: ` ```lean ` fences; caption states source file and theorem
  name; do not paste full proof bodies — link to the file.
- **Figures**: `<project>-proofs/results/figures/` by relative path; every
  caption states data source and sample window.
- **Tables**: from `<project>-proofs/results/*.json` rendered via a Quarto
  code cell (Python or R).
- **Citations**: BibTeX in `_references.bib`; add entries rather than inline
  URLs.
- **Numbers**: point estimate with SE in parentheses; range with brackets;
  unit (bps, %, $) stated on first use in each section.

## Authoring a new paper

```bash
cp reports/_template.qmd reports/<project>-proofs.qmd
```

Fill in this order, not document order:

1. Formalization theorem table — forces clarity on what is actually proved.
2. Empirical Setup table — forces clarity on data scope.
3. Results and Robustness — against committed `results/` artifacts.
4. Setup and Main Results — against the Lean source.
5. Introduction and Abstract last, once the result is settled.

Build and proofread the rendered PDF, not the source:

```bash
cd reports && quarto render <project>-proofs.qmd
```

Commit the `.qmd`; do not commit the rendered PDF or the `_output/` dir.

## Hard rules

- No paper without **both** Formalization and Robustness sections.
- No empirical claim without a sample window and a data source in the same
  paragraph.
- No theorem statement without a `verify-lean`–passing artifact in the
  corresponding `<project>-proofs/` source.
- No retroactive sample selection. In-sample / out-of-sample split declared
  in Empirical Setup.
- No private context: no GPA, firm names, internship timelines, or
  "developed to impress X." Write for a public research audience. Same rule
  as `write-readme-results`.
- No raw `.tex` reports. Quarto only.

## Related skills

- `write-readme-results` — short single-exhibit results writeup for a README. The
  Results section here can pull from a `write-readme-results` exhibit, but a paper
  is not a stitched series of exhibits.
- `docs-research` — Jupyter Book aggregation site; cites finished papers
  from `reports/`.
- `conduct-quant-research` — empirical methodology behind §6–§8.
- `write-technical-docs` — proof docstrings, narrative project docs.
- `verify-empirical`, `verify-regime` — produce the `results/` artifacts
  cited in §7 and §8.
- `write-commits-and-prs` — commit message conventions when landing a
  paper draft.
