"""Stage 3 — statistical testing. The signal-validation toolkit.

This is the unverified-but-rigorous layer: information-coefficient analysis with
autocorrelation-robust (Newey-West) significance, IC decay, factor-overlap checks,
bootstrap confidence intervals, and the probabilistic / deflated Sharpe ratios
(Bailey & Lopez de Prado) that adjust for sample length and multiple testing.

The discipline here is the point: distinguishing a real edge from a backtest that only
looks like one. numpy / pandas / scipy throughout.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as _st


def _rank_ic_series(signal: pd.DataFrame, fwd_returns: pd.DataFrame) -> pd.Series:
    """Per-date cross-sectional rank (Spearman) IC."""
    dates = signal.index.intersection(fwd_returns.index)
    out: dict[object, float] = {}
    for t in dates:
        a, b = signal.loc[t], fwd_returns.loc[t]
        common = a.dropna().index.intersection(b.dropna().index)
        if len(common) >= 3:
            out[t] = float(a[common].rank().corr(b[common].rank()))
    return pd.Series(out).dropna()


def mean_ic(signal: pd.DataFrame, fwd_returns: pd.DataFrame) -> float:
    ic = _rank_ic_series(signal, fwd_returns)
    return float(ic.mean()) if len(ic) else float("nan")


def newey_west_tstat(x: pd.Series, lags: int | None = None) -> float:
    """HAC (Newey-West, Bartlett kernel) t-statistic of the mean of ``x``.

    Autocorrelation-robust: IC and return series are serially correlated, so a naive
    t-stat overstates significance. ``lags`` defaults to the Newey-West rule of thumb.
    """
    arr = x.dropna().to_numpy(dtype=float)
    n = arr.size
    if n < 3:
        return float("nan")
    if lags is None:
        lags = int(np.floor(4.0 * (n / 100.0) ** (2.0 / 9.0)))
    e = arr - arr.mean()
    var = float(e @ e) / n
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1.0)
        var += 2.0 * w * float(e[lag:] @ e[:-lag]) / n
    se = np.sqrt(var / n)
    return float(arr.mean() / se) if se > 0 else float("nan")


def ic_summary(
    signal: pd.DataFrame, fwd_returns: pd.DataFrame, periods_per_year: int = 252
) -> pd.Series:
    """Headline IC diagnostics: mean, dispersion, annualised IR, HAC t-stat, hit rate."""
    ic = _rank_ic_series(signal, fwd_returns)
    mean = float(ic.mean()) if len(ic) else float("nan")
    sd = float(ic.std()) if len(ic) else float("nan")
    return pd.Series(
        {
            "mean_IC": mean,
            "IC_std": sd,
            "IC_IR_annual": mean / sd * np.sqrt(periods_per_year) if sd > 0 else float("nan"),
            "IC_tstat_NW": newey_west_tstat(ic),
            "hit_rate": float((ic > 0).mean()) if len(ic) else float("nan"),
            "n_periods": float(len(ic)),
        }
    )


def ic_decay(
    signal: pd.DataFrame, panel: "object", horizons: tuple[int, ...] = (1, 5, 21, 63)
) -> pd.Series:
    """Mean IC against forward returns at increasing horizons (fast decay => low capacity)."""
    return pd.Series(
        {h: mean_ic(signal, panel.forward_returns(h)) for h in horizons},  # type: ignore[attr-defined]
        name="mean_IC_by_horizon",
    )


def signal_correlation(sig_a: pd.DataFrame, sig_b: pd.DataFrame) -> float:
    """Average cross-sectional correlation between two signals.

    Use to check a 'new' alpha is not just a known factor in disguise (high overlap => no
    incremental information).
    """
    dates = sig_a.index.intersection(sig_b.index)
    cs: list[float] = []
    for t in dates:
        a, b = sig_a.loc[t], sig_b.loc[t]
        common = a.dropna().index.intersection(b.dropna().index)
        if len(common) >= 3:
            cs.append(float(a[common].corr(b[common])))
    return float(np.nanmean(cs)) if cs else float("nan")


def bootstrap_sharpe_ci(
    returns: pd.Series,
    n_boot: int = 1000,
    periods_per_year: int = 252,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float]:
    """Bootstrap (1-alpha) confidence interval for the annualised Sharpe ratio."""
    r = returns.dropna().to_numpy(dtype=float)
    n = r.size
    if n < 2:
        return (float("nan"), float("nan"))
    rng = np.random.default_rng(seed)
    sharpes = np.empty(n_boot)
    for i in range(n_boot):
        s = r[rng.integers(0, n, n)]
        sd = s.std()
        sharpes[i] = s.mean() / sd * np.sqrt(periods_per_year) if sd > 0 else 0.0
    lo, hi = np.quantile(sharpes, [alpha / 2.0, 1.0 - alpha / 2.0])
    return (float(lo), float(hi))


def probabilistic_sharpe_ratio(
    returns: pd.Series, sr_benchmark: float = 0.0, periods_per_year: int = 252
) -> float:
    """PSR (Bailey & Lopez de Prado): P(true SR > benchmark), adjusting for skew, kurtosis,
    and sample length. ``sr_benchmark`` is annualised."""
    r = returns.dropna().to_numpy(dtype=float)
    n = r.size
    if n < 3:
        return float("nan")
    sd = r.std(ddof=1)
    if sd == 0:
        return float("nan")
    sr = r.mean() / sd  # per-period
    skew = float(_st.skew(r))
    kurt = float(_st.kurtosis(r, fisher=False))
    sr_b = sr_benchmark / np.sqrt(periods_per_year)
    den = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    if den <= 0:
        return float("nan")
    return float(_st.norm.cdf((sr - sr_b) * np.sqrt(n - 1) / den))


def deflated_sharpe_ratio(returns: pd.Series, n_trials: int, periods_per_year: int = 252) -> float:
    """DSR: PSR against the expected-maximum Sharpe from ``n_trials`` independent backtests.

    Deflates significance for multiple testing — central when many signals / asset classes
    are searched (e.g. the cross-asset study).
    """
    r = returns.dropna().to_numpy(dtype=float)
    n = r.size
    if n < 3 or n_trials < 1:
        return float("nan")
    sd = r.std(ddof=1)
    if sd == 0:
        return float("nan")
    sr = r.mean() / sd
    if n_trials == 1:
        sr_star = 0.0
    else:
        emc = 0.5772156649015329  # Euler-Mascheroni
        z1 = _st.norm.ppf(1.0 - 1.0 / n_trials)
        z2 = _st.norm.ppf(1.0 - 1.0 / (n_trials * np.e))
        expected_max = (1.0 - emc) * z1 + emc * z2  # E[max] of n_trials standard normals
        sr_star = expected_max / np.sqrt(n - 1)
    skew = float(_st.skew(r))
    kurt = float(_st.kurtosis(r, fisher=False))
    den = np.sqrt(1.0 - skew * sr + (kurt - 1.0) / 4.0 * sr**2)
    if den <= 0:
        return float("nan")
    return float(_st.norm.cdf((sr - sr_star) * np.sqrt(n - 1) / den))


def permutation_ic_test(
    signal: pd.DataFrame, fwd_returns: pd.DataFrame, n_perm: int = 200, seed: int = 0
) -> tuple[float, float]:
    """Placebo test: permute the cross-sectional asset labels of the signal, destroying any
    real signal-return alignment, and ask how often the permuted |mean IC| matches the
    observed. Returns ``(observed_mean_IC, p_value)``. A genuine alpha => small p.
    """
    observed = abs(mean_ic(signal, fwd_returns))
    rng = np.random.default_rng(seed)
    cols = list(signal.columns)
    ge = 0
    for _ in range(n_perm):
        permuted = signal.rename(columns=dict(zip(cols, list(rng.permutation(cols)))))
        if abs(mean_ic(permuted, fwd_returns)) >= observed:
            ge += 1
    return float(observed), float((ge + 1) / (n_perm + 1))
