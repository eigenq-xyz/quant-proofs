# reports/

Canonical home for publishable research papers in the `quant-proofs` monorepo.
One Quarto document per project, rendered to PDF for archival and HTML for the
web.

Authoring guidance — section structure, formatting conventions, hard rules —
lives in the [`writing-research-reports`](../.claude/skills/writing-research-reports/SKILL.md)
skill. Run `/writing-research-reports` before drafting or reviewing.

## Files

| File                | Purpose                                                          |
|---------------------|------------------------------------------------------------------|
| `_template.qmd`     | Canonical template — copy to start a new paper                   |
| `_quarto.yml`       | Quarto project config (PDF + HTML output, biblatex author-year)  |
| `_eigenq.tex`       | Shared LaTeX preamble (math packages, finance macros, styling)   |
| `_references.bib`   | Shared bibliography                                              |
| `_output/`          | Render artifacts — not committed                                 |
| `<project>-proofs.qmd` | One per project; build with `quarto render <file>.qmd`        |

## Build

```bash
quarto render <project>-proofs.qmd      # one paper
quarto render                           # all papers in this directory
quarto preview <project>-proofs.qmd     # live HTML preview while drafting
```

PDF builds require a LaTeX distribution with the packages listed at the top
of `_eigenq.tex`. Install missing packages with `tlmgr install <name>`.

## How `reports/` composes with the rest of the monorepo

- `<project>-proofs/results/` — committed empirical artifacts (figures, JSON
  metrics). Papers cite these by relative path; they do not regenerate them.
- `docs/` — Jupyter Book reference site. A finished paper here can be indexed
  from the docs site via the `docs-research` skill.
- `<project>-proofs/CLAUDE.md` — project architecture; a paper's Setup section
  should be consistent with that document.
