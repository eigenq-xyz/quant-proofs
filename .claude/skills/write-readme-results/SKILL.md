---
name: write-readme-results
description: >
  Generates the empirical results section of a README or research page from
  committed results/ charts and tables. Writes in AQR research paper style:
  hypothesis stated, data source documented, result reported honestly including
  where it breaks down, in-sample and out-of-sample always separated.
paths:
  - "results/**"
  - "**/README.md"
  - "docs/paper/**"
allowed-tools: Read Write Edit Glob
---

# Readme Results

## Style benchmark

AQR white paper exhibit format: numbered exhibits, tight captions, no marketing
language, limitations always stated.

## Required elements for each result

1. **Hypothesis** — stated before showing data
2. **Data source** — name, access tier, sample period, frequency
3. **In-sample period** declared; **out-of-sample period** declared separately
4. **Result** — central estimate + confidence interval or range
5. **Where it breaks down** — regime, subsample, transaction cost sensitivity
6. **Connection to Lean proof** — which theorem the result validates or relies on

## Exhibit template

```markdown
**Exhibit N: [Descriptive title]**

*Data: [source]. Sample: [start]–[end], [frequency].
[Key statistic]: [definition].*

![chart](results/charts/filename.png)

[Result in 1–2 sentences. Central estimate. Regime breakdown if applicable.]

*Formal guarantee: This result relies on `BacktestProofs.Invariants.[theorem]`,
which proves [what it rules out in plain English].*

**Limitations:** [What this doesn't prove. What would invalidate the result.
Transaction costs: assumed zero / modeled as X bps. Out-of-sample period: [dates].]*
```

## Privacy rule

No GPA, no personal timelines, no "this demonstrates skill for X firm."
Write as if for a public research audience.

AQR and Fama-French are fine as data source names (they publish public datasets).
"This was developed to impress AQR interviewers" is not acceptable.

## Hard rules

- Never cherry-pick the sample period after seeing results
- Never omit transaction costs without explicitly noting "assumes zero transaction costs"
- Never call a backtest result "alpha" without risk adjustment
- In-sample / out-of-sample split must be declared in the methodology section,
  not chosen retroactively

## Example of good vs bad

Bad: "Our strategy significantly outperforms the market with 23% annual returns."

Good: "The delta-hedging strategy earned 23% annualized **in-sample** (2015–2019).
Out-of-sample (2020–2024): 8%, with elevated drawdowns during March 2020.
Transaction costs are assumed zero — at 5 bps per trade, the strategy breaks
even. This does not constitute evidence of live alpha."
