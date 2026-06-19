# Research Study — <signal> on <universe> (template)

> Fill from `python -m scripts.run_study`. This report is only as trustworthy as the
> pipeline that produced it — see **Pipeline validation** below before reading results.

## 1. Hypothesis
What inefficiency, why it should exist (risk premium / behavioral / structural), and what
predicts forward returns. State it before looking at results.

## 2. Data
- Source: Ken French (free) / WRDS-CRSP (licensed — **not committed**, gitignored extract).
- Universe, period, frequency, point-in-time handling.

## 3. Method
- Signal construction (non-anticipating — see §6).
- Portfolio construction (dollar-neutral baseline / verified PGD).
- Costs: <bps> proportional (+ impact model if used).
- **Out-of-sample:** expanding walk-forward, embargo = <k> days (no leakage across splits).

## 4. Pipeline validation (cite Track 1)
Before trusting any number here, the pipeline was validated (`pytest`, `validation.py`):
- detects planted alpha at strong SNR (detection rate > 0.9);
- false-positive rate on pure noise near the nominal 5%;
- the no-look-ahead guard catches an injected one-day leak;
- estimators match `statsmodels` / `scipy` references.

## 5. Results
| Metric | In-sample | Out-of-sample |
|--------|-----------|---------------|
| mean IC | | |
| IC t-stat (Newey-West) | | |
| net Sharpe | | |
| max drawdown | | |
| turnover | | |
| **deflated Sharpe** (n_trials=<N>) | | |

- IC decay by horizon: <…>
- Factor attribution (alpha vs market/size/value/momentum betas, R²): <…>
- Cross-asset generalisation: <…>

## 6. Conclusion & limitations
State the verdict honestly — including if the edge is marginal or vanishes net-of-cost / OOS
/ after deflation. A truthful negative is a result. Note capacity, regime dependence, and what
would change the conclusion.
