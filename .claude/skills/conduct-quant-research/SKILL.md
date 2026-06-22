---
name: conduct-quant-research
description: >
  Empirical quant research methodology. Use when designing a study, reviewing a
  backtest, or evaluating empirical results.
paths:
  - "**/*.py"
  - "**/*.ipynb"
  - "**/notebooks/**"
---

# Conducting Quantitative Research — quant-proofs

---

## Literature review

Before starting any empirical study, search the existing literature.

**Where to look:**

| Source | How to search |
|--------|---------------|
| SSRN | `ssrn.com/search` — working papers, often the latest results |
| arXiv q-fin | `arxiv.org/search/?searchtype=all&query=...&start=0` — filter to `q-fin` |
| JFE / RFS / JF / JFM | Google Scholar, JSTOR — peer-reviewed, highest bar |
| REview of Asset Pricing Studies | More recent empirical methods papers |

**Standard citation format** (use consistently in code comments and docstrings):
> Author Last, First, and Second Author Last, First. "Title." *Journal Name*
> Volume, no. Issue (Year): Pages. https://doi.org/...

For working papers: `Author (Year), "Title," SSRN Working Paper XXXXXXX.`

**What to document before starting:** Write a one-paragraph "prior work" note in the
notebook or module docstring. State: (1) the paper that introduced the signal or
model you are testing, (2) the key empirical result they found, (3) what you are
replicating or extending.

---

## Empirical methodology

Follow this order. Do not skip steps.

### 1. Define the hypothesis

State the hypothesis in one sentence before touching data. The hypothesis should be:
- **Falsifiable:** it predicts something the data could contradict.
- **Specific:** it specifies the sign, approximate magnitude, or direction.
- **Economically motivated:** cite the mechanism (risk premium, limits to arbitrage,
  microstructure).

Example: "The variance risk premium (VRP = implied variance − realized variance)
is negative on average and predicts near-term S&P 500 returns with a positive sign
over a 1-month horizon (Bollerslev, Tauchen, Zhou 2009)."

### 2. Data

- Identify the source hierarchy (see `/source-financial-data`).
- Document the exact date range, universe, and any filters applied.
- Record all preprocessing steps in code, not in memory. The pipeline from raw data
  to analysis-ready data must be reproducible by running a single script or notebook.
- Check for survivorship bias: if your universe is defined by current membership
  (e.g., current S&P 500 constituents), you are looking at survivors only.

### 3. Signal construction

- Define the signal precisely: formula, inputs, and any free parameters.
- Note the **observation frequency** (daily, monthly) and **look-back window**.
- Identify all parameters chosen before seeing the data (if any are chosen after
  looking at performance, they are not out-of-sample).
- Document the signal's distributional properties: mean, standard deviation,
  skewness, any heavy tails or outliers.

### 4. Backtest

See "Backtesting best practices" below.

### 5. Robustness

See "Standard robustness checks" below.

---

## Backtesting best practices

### In-sample / out-of-sample split

- Reserve the last 20–30% of the time series as the out-of-sample period.
- Never look at out-of-sample performance until all in-sample analysis and
  parameter choices are finalized.
- If you iterate on parameters after seeing out-of-sample performance, the
  split is no longer valid. Label the result "in-sample" and repeat the process.

**Recommended minimum:** 10 years in-sample, 5 years out-of-sample for monthly
strategies. For daily strategies, 5 years in-sample, 2 years out-of-sample.

### Avoid look-ahead bias

Look-ahead bias is the use of information that was not available at the time
the trading decision would have been made. Common sources:

- **Point-in-time data:** use data as it was known at each date, not as subsequently
  revised. CRSP and Compustat on WRDS provide point-in-time flags; use them.
- **Rebalancing timing:** if a monthly signal is formed at month-end, the trade
  executes at next-day open, not month-end close.
- **Earnings releases:** earnings data becomes available at the announcement date,
  not the fiscal quarter end date.

Audit look-ahead bias by checking that the signal at time `t` uses only data
with timestamps `≤ t`.

### Transaction costs

Every backtest must account for transaction costs. Ignoring costs produces inflated
results that will not survive live implementation.

Minimum cost model:
- **Bid/ask spread:** use half-spread as the cost of a one-way trade. For S&P 500
  stocks, a reasonable assumption is 2–5 bps per trade. For options, 10–50 bps
  depending on liquidity.
- **Market impact:** for larger position sizes, add a linear market impact term.
  Almgren-Chriss (2001) provides a standard framework.
- **Borrow cost:** for short positions, add the stock borrow rate.

Report net-of-cost results in all tables.

### Sharpe ratio ≠ alpha

A high Sharpe ratio is necessary but not sufficient. Also check:

- **Factor exposure:** regress returns on standard factors (Fama-French 5, Carhart
  momentum). Report alpha and t-statistic on alpha separately.
- **Drawdown:** report maximum drawdown and recovery time.
- **Turnover:** report annualized turnover. High Sharpe + high turnover strategies
  often lose their edge to transaction costs.
- **Leverage:** report the notional leverage implied by the strategy. A 3.0 Sharpe
  at 10x leverage is not a 3.0 Sharpe strategy at 1x.

---

## Connecting results to proofs

The formally verified proofs in `foundations/ftap-proofs/` and `foundations/options-proofs/` provide
mathematical guarantees under specific model assumptions. Use them to interpret
empirical results.

**When a result looks surprising:**

1. Check what the proof assumes. A surprising empirical result in the binomial model
   context may arise because the real market violates a put-call parity assumption
   (dividends, early exercise, liquidity). The proof rules out arbitrage given its
   assumptions; the empirical result may be identifying where those assumptions break.

2. Check what the proof guarantees. If the FTAP proof guarantees the existence of a
   risk-neutral measure under discrete no-arbitrage, and your backtest finds apparent
   arbitrage, the first question is whether the backtest correctly accounts for
   transaction costs and timing — not whether the theorem is wrong.

3. Formal guarantees narrow the hypothesis space. If the proof shows that under
   no-arbitrage, an instrument's price satisfies a particular identity, and the
   empirical data violates that identity after transaction costs, you have evidence
   of either a genuine market inefficiency or a data quality issue. Check the data
   first (see `/source-financial-data`, QUALITY_NOTES.md).

---

## Standard robustness checks

Every empirical result should be accompanied by at least three robustness checks:

### Sub-period analysis

Split the sample into at least two sub-periods (e.g., pre- and post-2008) and
report the key statistics separately. A result that only holds in one sub-period
is much weaker than one that holds across regimes.

### Alternative parameter choices

If the signal has free parameters (window length, threshold, look-back), report
results for at least three parameter values. A result that is highly sensitive to
the exact parameter choice is likely over-fit.

### Different universes

Replicate the key finding in at least one alternative universe (e.g., if the main
result is for S&P 500 stocks, check Russell 2000; if for US equities, check MSCI
Europe). A signal that only works in one narrow universe needs a specific
economic explanation for why.

### Statistical testing

Report t-statistics on mean returns, not just means. Account for autocorrelation
in the standard error (Newey-West with 6–12 lags for monthly data, 21 lags for
daily data). A t-statistic below 2.0 is not publishable evidence; below 3.0,
consider it preliminary.
