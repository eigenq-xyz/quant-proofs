---
name: docs-research
description: >
  Builds the research paper site from committed results/ charts and tables.
  Produces a publication-quality HTML site showing empirical findings and their
  connection to Lean proofs. Audience: quant researchers who know finance but
  not Lean 4.
paths:
  - "results/**"
  - "docs/paper/**"
allowed-tools: Bash(uv run *) Read Write Edit
---

# Docs Research

## Build command

```bash
cd backtest-proofs/python
uv sync --extra docs       # installs jupyter-book + quantecon-book-theme
uv run jupyter-book build ../../docs/
```

**Theme:** `quantecon-book-theme` — configured in `docs/_config.yml`. Same theme used across eigenq-xyz projects. Do not change the theme without updating all docs.

The root JupyterBook at `docs/` is already configured. Add paper sections to
`docs/_toc.yml` as results become available.

## Audience

Write for a quant researcher or portfolio manager: knows options pricing, factor
models, and backtesting — does not know Lean 4. Explain formal proofs in terms
of what they *rule out*, not how they work internally.

Bad: "The `settlement_value_formula` theorem in `BacktestProofs.OptionInvariants`
uses a tactic proof with `omega` to discharge the integer arithmetic."

Good: "The accounting layer is formally proved to be self-consistent: no matter
how complex the hedging strategy, settlement cannot silently mis-report PnL.
This eliminates a class of backtesting bugs that only appear at expiry."

## Exhibit format

```markdown
**Exhibit 1: Put-call parity deviation, SPX options 2015–2024**

*Data: OptionMetrics via WRDS. Sample: Jan 2015–Dec 2024, monthly close.
Deviation = (C - P) - (S - K·e^{-rT}), winsorized at 1%/99%.*

[chart]

Mean deviation: X bps. Crisis regime (VIX > 30): Y bps. The Lean proof
guarantees this deviation is not an accounting artefact — it reflects
genuine market friction.
```

Required elements: numbered exhibit, data source, sample period, statistic definition,
connection to the Lean proof.

## Current status

`results/` and `docs/paper/` do not yet exist. Add entries to `docs/_toc.yml`
when content is ready:
```yaml
- file: paper/parity-deviation
- file: paper/backtest-results
```
