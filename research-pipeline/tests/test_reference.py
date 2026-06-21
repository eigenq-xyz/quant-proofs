"""Ground-truth checks: our hand-rolled estimators vs trusted references / closed forms."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research_pipeline import factor_attribution
from research_pipeline.stats import _rank_ic_series, newey_west_tstat


def test_newey_west_lag0_equals_plain_tstat() -> None:
    rng = np.random.default_rng(0)
    x = pd.Series(rng.normal(0.5, 1.0, 500))
    arr = x.to_numpy()
    plain = arr.mean() / (arr.std() / np.sqrt(len(arr)))  # population std, lag 0
    assert abs(newey_west_tstat(x, lags=0) - plain) < 1e-9


def test_newey_west_widens_se_under_positive_autocorrelation() -> None:
    rng = np.random.default_rng(1)
    e = rng.normal(0, 1, 4000)
    y = np.zeros(4000)
    for t in range(1, 4000):
        y[t] = 0.6 * y[t - 1] + e[t]  # positively autocorrelated
    s = pd.Series(y + 0.1)
    # HAC accounts for autocorrelation => |t| no larger than the naive lag-0 t-stat.
    assert abs(newey_west_tstat(s, lags=20)) <= abs(newey_west_tstat(s, lags=0)) + 1e-9


def test_rank_ic_matches_scipy_spearman() -> None:
    sp = pytest.importorskip("scipy.stats")
    rng = np.random.default_rng(2)
    sig = pd.DataFrame(rng.normal(size=(1, 30)), index=["d"], columns=range(30))
    fwd = pd.DataFrame(rng.normal(size=(1, 30)), index=["d"], columns=range(30))
    ours = _rank_ic_series(sig, fwd).iloc[0]
    ref = sp.spearmanr(sig.iloc[0].to_numpy(), fwd.iloc[0].to_numpy()).statistic
    assert abs(ours - ref) < 1e-9


def test_factor_attribution_matches_statsmodels() -> None:
    sm = pytest.importorskip("statsmodels.api")
    rng = np.random.default_rng(3)
    f1 = pd.Series(rng.normal(0, 0.01, 600))
    f2 = pd.Series(rng.normal(0, 0.01, 600))
    y = 0.0003 + 0.8 * f1 - 0.3 * f2 + pd.Series(rng.normal(0, 1e-4, 600))
    ours = factor_attribution(y, pd.DataFrame({"f1": f1, "f2": f2}))
    res = sm.OLS(y.to_numpy(), sm.add_constant(pd.DataFrame({"f1": f1, "f2": f2}).to_numpy())).fit()
    assert abs(ours["alpha"] - res.params[0]) < 1e-9
    assert abs(ours["beta_f1"] - res.params[1]) < 1e-9
    assert abs(ours["r2"] - res.rsquared) < 1e-9
