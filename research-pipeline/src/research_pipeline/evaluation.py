"""Stage 6 — evaluation & attribution. Performance summary, drawdowns, and a factor
attribution that decomposes strategy returns into alpha + factor betas via OLS (numpy).
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def sharpe(returns: pd.Series, periods_per_year: int = 252) -> float:
    r = returns.dropna()
    sd = float(r.std())
    if sd == 0.0 or not np.isfinite(sd) or len(r) < 2:
        return float("nan")
    return float(r.mean() / sd * np.sqrt(periods_per_year))


def turnover(weights: pd.DataFrame) -> float:
    """Average one-way turnover per rebalance: mean over t of ``sum|w_t - w_{t-1}|``."""
    return float(weights.diff().abs().sum(axis=1).iloc[1:].mean())


def max_drawdown(returns: pd.Series) -> float:
    r = returns.dropna()
    if len(r) == 0:
        return float("nan")
    equity = (1.0 + r).cumprod()
    return float((equity / equity.cummax() - 1.0).min())


def performance_summary(returns: pd.Series, periods_per_year: int = 252) -> pd.Series:
    r = returns.dropna()
    n = len(r)
    if n < 2:
        return pd.Series(dtype=float)
    sd = float(r.std())
    ann_return = float((1.0 + r).prod() ** (periods_per_year / n) - 1.0)
    mdd = max_drawdown(r)
    return pd.Series(
        {
            "sharpe": sharpe(r, periods_per_year),
            "ann_return": ann_return,
            "ann_vol": sd * np.sqrt(periods_per_year),
            "max_drawdown": mdd,
            "calmar": ann_return / abs(mdd) if mdd < 0 else float("nan"),
            "hit_rate": float((r > 0).mean()),
            "skew": float(r.skew()),
            "kurtosis": float(r.kurt()),
            "n": float(n),
        }
    )


def factor_attribution(strategy_returns: pd.Series, factor_returns: pd.DataFrame) -> pd.Series:
    """OLS attribution: ``strategy = alpha + Σ beta_k · factor_k + ε`` via ``np.linalg.lstsq``.

    Returns alpha, the factor betas, and R². Separates true alpha from factor exposure —
    the question 'is this signal just disguised beta?'.
    """
    df = pd.concat([strategy_returns.rename("y"), factor_returns], axis=1).dropna()
    if len(df) < len(factor_returns.columns) + 2:
        return pd.Series(dtype=float)
    y = df["y"].to_numpy(dtype=float)
    cols = list(factor_returns.columns)
    x = np.column_stack([np.ones(len(df)), df[cols].to_numpy(dtype=float)])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    resid = y - x @ beta
    ss_res = float(resid @ resid)
    ss_tot = float(((y - y.mean()) ** 2).sum())
    out: dict[str, float] = {"alpha": float(beta[0])}
    for i, c in enumerate(cols):
        out[f"beta_{c}"] = float(beta[i + 1])
    out["r2"] = 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")
    return pd.Series(out)
