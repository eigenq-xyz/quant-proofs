---
name: write-technical-docs
description: >
  Documentation standards for quant-proofs. Use when writing or reviewing READMEs,
  proof docstrings, notebook exhibits, or any public-facing documentation.
paths:
  - "**/README.md"
  - "**/*.md"
  - "**/*.lean"
  - "**/notebooks/**"
---

# Writing Technical Docs — quant-proofs

---

## README style

Every subproject README follows this structure, in order:

### 1. One-sentence summary (first line, no heading)

State what the project is and what it does. Lead with the mathematical or
technical substance — not with what it "demonstrates" or "explores."

Good:
> `ftap-proofs` is a Lean 4 formalization of the discrete Fundamental Theorem of
> Asset Pricing (Harrison-Pliska 1981), targeting a mathlib PR.

Avoid:
> This project demonstrates the power of formal verification applied to
> quantitative finance.

### 2. What it proves / what it does

For proof projects: state the main theorem in one sentence of plain English,
then the formal statement as a Lean code block. Explain why the result matters
mathematically.

For pipeline projects: describe the pipeline in one paragraph (agents, inputs,
outputs, what is formally verified).

### 3. How to build

Lean:
```
cd <subdir>/lean && lake build
```

Python:
```
cd <subdir> && uv sync --extra dev
```

Every command in the README must be runnable as written from the directory stated.
Test them before committing documentation.

### 4. How to test

Show the exact command. For Lean proofs, include the sorry check:
```
grep -rn sorry --include="*.lean" <subdir>/lean/
```
(An empty result means zero sorry.)

For Python:
```
uv run pytest
uv run mypy --strict src/
```

### 5. Project structure

A short table or tree showing the key files and what each does. Keep it to 10–15
lines — do not list every file. Focus on files a contributor would need to find.

### Rules for all READMEs

- No private content: no personal timelines, no target firm names in strategy
  framing, no grades, no application context.
- Tense: present tense for current state, future tense for planned work.
- Links: use relative paths for links within the repo; absolute URLs for external
  references. Verify links before committing.
- Code blocks: always specify the language identifier (` ```lean`, ` ```python`,
  ` ```bash`).

---

## Proof docstrings (for a non-Lean audience)

Every exported theorem must have a docstring that a mathematician who does not know
Lean can understand. Do not assume Lean familiarity. Do not assume measure theory
unless the theorem is in a clearly measure-theoretic module.

Structure:

```lean
/-- Put-call parity for European options in the Cox-Ross-Rubinstein binomial model.

For a European call and put with the same strike K and expiry T, the no-arbitrage
price satisfies:

    C - P = S - K · B(0, T)

where S is the current stock price and B(0, T) is the price of a zero-coupon bond
maturing at T (the present value of $1 at time T under the risk-neutral measure).

This is the discrete-time analogue of the classical Black-Scholes put-call parity
(Merton 1973). The proof follows from the Fundamental Theorem of Asset Pricing
(Harrison-Pliska 1981; see `FtapProofs.NoArbitrage`): in the absence of arbitrage,
any two portfolios with identical payoffs must have identical prices. The call-minus-
put portfolio replicates the forward on the stock, whose price is S - K · B(0, T).

Reference: Cox, Ross, Rubinstein (1979). "Option Pricing: A Simplified Approach."
Journal of Financial Economics 7(3): 229–263.
-/
theorem putCallParity ...
```

Components:
1. **Plain-English statement** of the theorem (what it says, not the Lean syntax).
2. **Formula** in LaTeX-style math, rendered as a code block if LaTeX is not available.
3. **Why it matters** — connect to the broader mathematical context.
4. **Key references** — cite the paper the result comes from.

Do not include implementation details (tactics, imports used) in the docstring.
Those belong in inline comments inside the proof body.

---

## Exhibit formatting (tables and charts)

### Tables

- Label every column with units in the header: `Return (% ann.)`, `Sharpe (ann.)`,
  `Turnover (% ann.)`.
- Include the sample period and sample size in a caption below the table:
  `Note: Monthly data, Jan 1990 – Dec 2023, N = 408 months.`
- The caption explains what to take away, not just what the table shows:
  Good: "VRP strategy Sharpe ratios are consistently positive across sub-periods,
  declining after 2015."
  Avoid: "Table 1 shows Sharpe ratios for the VRP strategy."

### Charts

Label requirements:
- **X-axis:** label with units (e.g., `Date`, `Strike / Spot`, `Moneyness (%)`)
- **Y-axis:** label with units (e.g., `Cumulative Return (%)`, `Implied Vol (ann. %)`)
- **Title:** short, descriptive, present-tense
- **Legend:** always include when there are multiple series; place inside the plot
  area if space permits

Caption: every chart must have a caption that explains the key takeaway, not just
what is plotted.

### Chart visual conventions

- **Palette:** use seaborn's `colorblind` palette for all multi-series charts.
  ```python
  import seaborn as sns
  sns.set_palette("colorblind")
  ```
  This ensures accessibility for viewers with color vision deficiency.
- **Background:** dark-on-light only. No dark backgrounds, no neon colors.
- **3D plots:** never. They add visual complexity without information. Use a
  heatmap, contour plot, or faceted 2D plots instead.
- **Font size:** minimum 11pt for all axis labels, tick labels, and legend text.
  Smaller text becomes unreadable in print and in slide decks.
- **Figure size:** default `(10, 5)` for single-panel time-series charts; `(12, 6)`
  for multi-panel. Use `tight_layout()` to prevent label clipping.

Standard chart setup:
```python
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_palette("colorblind")
sns.set_style("whitegrid")

fig, ax = plt.subplots(figsize=(10, 5))
# ... plot ...
ax.set_xlabel("Date", fontsize=12)
ax.set_ylabel("Cumulative Return (%)", fontsize=12)
ax.set_title("VRP Strategy Cumulative Returns, 1990–2023", fontsize=13)
ax.legend(fontsize=11)
fig.tight_layout()
```

---

## JupyterBook site conventions (docs/)

The repo uses JupyterBook with the **QuantEcon Book Theme** (`quantecon-book-theme`),
matching the style used in other eigenq-xyz projects. Theme is in
`backtest-proofs/python/pyproject.toml` under `[project.optional-dependencies] docs`.

Build:
```bash
cd backtest-proofs/python && uv sync --extra docs
uv run jupyter-book build ../../docs/
```

Theme-specific conventions:
- `execute_notebooks: "off"` — notebooks are pre-executed; outputs committed to repo
- `myst_enable_extensions: [colon_fence, deflist]` — use `:::` for admonitions
- Mathematical notation rendered via MathJax — use `$...$` inline, `$$...$$` display
- `bibtex_bibfiles: []` — add a `.bib` file here when references are added
- All `.ipynb` notebooks go in `docs/` or `backtest-proofs/notebooks/`; symlink if needed
- Do not add dark-mode styles — the QuantEcon theme handles this
