---
name: reviewing-documentation
description: >
  Documentation review checklist for quant-proofs. Use when reviewing READMEs,
  proof docstrings, notebook prose, or any public-facing documentation. This skill
  reads and reports — it does not edit files.
paths:
  - "**/README.md"
  - "**/*.md"
  - "**/*.lean"
  - "**/notebooks/**"
disallowedTools:
  - Edit
  - Write
---

# Reviewing Documentation — quant-proofs

This skill is read-only. Report issues found; do not fix them directly. The author
fixes the issues and re-requests review.

---

## How to use this checklist

Work through each section that applies. For each item, mark it:
- **Pass** — verified correct
- **Fail** — describe the specific file and location of the issue
- **N/A** — section does not apply

A documentation change is ready to merge only when all applicable items are **Pass**.

---

## Cross-reference accuracy

Every command or path mentioned in the documentation must actually work.

- [ ] Every shell command in the documentation runs as written from the directory
  stated. Test each command; do not assume it works because it looks plausible.
  Commands to check: install, build, test, and any example invocations.
- [ ] Every file path mentioned in the documentation exists in the repository
  (or is clearly marked as a path that will exist after a build step).
- [ ] Every internal link (relative Markdown link) resolves to an existing file.
  Check with: `find . -name "*.md" | xargs grep -l "\]\(\./"` and verify each target.
- [ ] Every external URL is reachable and points to the correct resource. Spot-check
  at least three external links per document.

---

## Notation consistency

Mathematical notation must be consistent within a file and across files in the same
subproject.

- [ ] The same symbol is used for the same quantity throughout. Flag any case where
  two symbols are used for the same concept (e.g., `S_t` and `P_t` both used for
  stock price in different sections).
- [ ] The same concept is not denoted by two different symbols in different files
  within the same subproject (e.g., `B(0,T)` in one file and `P(0,T)` for the
  bond price in another).
- [ ] Conventions are stated explicitly where they are introduced. For example: "All
  returns are log returns unless stated otherwise" or "Prices are in basis points
  throughout."
- [ ] LaTeX notation is rendered consistently: inline math uses `$...$`; display
  math uses `$$...$$` or a fenced code block. Do not mix styles within a document.
- [ ] Factor names match their published names: Mkt-RF (not MKT or market), SMB,
  HML, RMW, CMA (Fama-French 5-factor convention); MOM or UMD for momentum.

---

## Attribution

Mathematical results must be attributed to their sources.

- [ ] The FTAP is attributed to Harrison and Pliska: "Harrison, J.M., and S.R. Pliska.
  'Martingales and Stochastic Integrals in the Theory of Continuous Trading.'
  *Stochastic Processes and Their Applications* 11, no. 3 (1981): 215–260."
- [ ] The binomial model is attributed to Cox, Ross, and Rubinstein: "Cox, J.C.,
  S.A. Ross, and M. Rubinstein. 'Option Pricing: A Simplified Approach.'
  *Journal of Financial Economics* 7, no. 3 (1979): 229–263."
- [ ] The Black-Scholes formula (when referenced) is attributed to Black and Scholes:
  "Black, F., and M. Scholes. 'The Pricing of Options and Corporate Liabilities.'
  *Journal of Political Economy* 81, no. 3 (1973): 637–654."
- [ ] Fama-French factors cite the relevant Fama-French paper (1993 for 3-factor,
  2015 for 5-factor).
- [ ] Any claim about empirical performance or stylized facts cites a specific source.
  Do not write "it is well known that..." without a citation.

---

## Privacy check

Public documentation must not contain private context.

- [ ] No GPA, grades, or academic performance metrics anywhere in public files.
- [ ] No personal application timelines or recruiting context.
- [ ] No target firm names used in a strategy-framing context (e.g., "this project
  is designed to demonstrate skills for X firm"). AQR and Fama-French are fine as
  data source names — they publish public datasets.
- [ ] No paths to personal files outside the repository (e.g., no references to
  `~/ode/mfe-applications/`).
- [ ] Positioning language, if present, refers to "academic and industry research"
  or "production quant codebases" — not to specific firms or job applications.

---

## Proof docstrings

Proof docstrings must be written for a mathematician who does not know Lean — not
for a Lean expert.

- [ ] Every exported theorem has a `/-- ... -/` docstring.
- [ ] The docstring states the theorem in plain English first, before or instead of
  restating the Lean syntax.
- [ ] The docstring explains why the result matters: what it enables, what it
  prevents (e.g., "this rules out arbitrage in the binomial model"), or how it
  connects to the broader mathematical theory.
- [ ] The docstring cites the mathematical literature for non-trivial results.
- [ ] The docstring does not explain Lean syntax or tactics (that belongs in inline
  comments inside the proof body, not the docstring).
- [ ] A reader who knows Harrison-Pliska (1981) but not Lean 4 could understand the
  docstring. Test this by reading it yourself without looking at the proof.

---

## Example code

All example code must be clearly marked and must actually run.

- [ ] Every code block that is intended to be runnable is actually runnable. Test it.
  Copy the block into a fresh environment and run it.
- [ ] Code that is not runnable (pseudocode, schematic, illustrative) is clearly
  marked as such with a comment: `# Pseudocode — not runnable as-is` or a note in
  the surrounding prose.
- [ ] Example code uses the conventions from `/writing-python-code`: `from __future__
  import annotations`, typed function signatures, no bare `Any`.
- [ ] Example code does not import private modules or modules that are not in the
  project's `pyproject.toml` dependencies.
- [ ] Example Lean code does not use `sorry`. If a proof is incomplete, mark the
  gap explicitly in prose rather than including a `sorry` in an example.

---

## Reporting format

Use this format for each issue found:

```
[SECTION] [SEVERITY] File: path/to/file.md, Line: 42
Issue: <description of what is wrong>
Required fix: <what needs to change>
```

Severity levels:
- **BLOCK** — must be fixed before merge (broken commands, privacy violation,
  sorry in example code)
- **WARN** — should be fixed; may merge with documented justification (missing
  citation, notation inconsistency)
- **NOTE** — style or clarity improvement; does not block merge
