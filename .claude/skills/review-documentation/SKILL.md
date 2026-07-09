---
name: review-documentation
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

This skill is read-only: report issues, don't fix them. The author fixes and
re-requests review.

---

## How to use this checklist

Work through each section that applies. Mark each item:
- **Pass** — verified correct.
- **Fail** — describe the specific file and location of the issue.
- **N/A** — section does not apply.

A documentation change is ready to merge only when every applicable item is **Pass**.

---

## Cross-reference accuracy

Every command or path in the documentation must actually work.

- [ ] Every shell command runs as written from the stated directory. Test
  each one; don't assume it works because it looks plausible. Check install,
  build, test, and any example invocations.
- [ ] Every file path exists in the repository, or is clearly marked as a
  path that will exist after a build step.
- [ ] Every internal (relative Markdown) link resolves to an existing file.
  Check with: `find . -name "*.md" | xargs grep -l "\]\(\./"` and verify each target.
- [ ] Every external URL is reachable and points to the right resource.
  Spot-check at least three external links per document.

---

## Notation consistency

Mathematical notation must stay consistent within a file and across files in
the same subproject.

- [ ] The same symbol denotes the same quantity throughout. Flag any case
  where two symbols cover one concept (e.g., `S_t` and `P_t` both used for
  stock price in different sections).
- [ ] The same concept isn't denoted by two different symbols across files
  in the same subproject (e.g., `B(0,T)` in one file, `P(0,T)` for the bond
  price in another).
- [ ] Conventions are stated explicitly where introduced. For example: "All
  returns are log returns unless stated otherwise" or "Prices are in basis
  points throughout."
- [ ] LaTeX notation renders consistently: inline math uses `$...$`; display
  math uses `$$...$$` or a fenced code block. Don't mix styles in one document.
- [ ] Factor names match their published names: Mkt-RF (not MKT or market),
  SMB, HML, RMW, CMA (Fama-French 5-factor convention); MOM or UMD for momentum.

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

Public documentation must contain zero private context.

- [ ] No GPA, grades, or academic performance metrics anywhere in public files.
- [ ] No personal application timelines or recruiting context.
- [ ] No target firm names in a strategy-framing context (e.g., "this project
  is designed to demonstrate skills for X firm"). AQR and Fama-French are fine
  as data source names — they publish public datasets.
- [ ] No paths to personal files outside the repository (e.g., no references
  to `~/personal/` or any path not under `quant-proofs/`).
- [ ] Positioning language, if present, refers to "academic and industry
  research" or "production quant codebases" — not specific firms or job
  applications.

---

## Proof docstrings

Proof docstrings target a mathematician who does not know Lean, not a Lean expert.

- [ ] Every exported theorem has a `/-- ... -/` docstring.
- [ ] The docstring states the theorem in plain English first, before or
  instead of restating the Lean syntax.
- [ ] The docstring explains why the result matters: what it enables, what
  it prevents (e.g., "this rules out arbitrage in the binomial model"), or
  how it connects to the broader mathematical theory.
- [ ] The docstring cites the mathematical literature for non-trivial results.
- [ ] The docstring skips Lean syntax or tactics — those belong in inline
  comments inside the proof body.
- [ ] A reader who knows Harrison-Pliska (1981) but not Lean 4 could
  understand the docstring. Test this by reading it without looking at the proof.

---

## Example code

All example code must be clearly marked and must actually run.

- [ ] Every code block meant to be runnable is actually runnable. Test it:
  copy the block into a fresh environment and run it.
- [ ] Code that isn't runnable (pseudocode, schematic, illustrative) is
  clearly marked with a comment — `# Pseudocode — not runnable as-is` — or a
  note in the surrounding prose.
- [ ] Example code follows `/write-python-code` conventions: `from __future__
  import annotations`, typed function signatures, no bare `Any`.
- [ ] Example code doesn't import private modules or modules missing from
  the project's `pyproject.toml` dependencies.
- [ ] Example Lean code doesn't use `sorry`. If a proof is incomplete, mark
  the gap explicitly in prose rather than including a `sorry` in an example.

---

## Reporting format

Use this format for each issue found:

```
[SECTION] [SEVERITY] File: path/to/file.md, Line: 42
Issue: <description of what is wrong>
Required fix: <what needs to change>
```

Severity levels:
- **BLOCK** — must be fixed before merge: broken commands, privacy violation,
  sorry in example code.
- **WARN** — should be fixed; may merge with documented justification:
  missing citation, notation inconsistency.
- **NOTE** — style or clarity improvement; does not block merge.
