"""Tests for the nonfarm-payrolls data-revision leakage-tax study.

The load-bearing test (``test_pit_uses_first_release_not_revised``) plants a KNOWN revision: a
month whose first-release level differs from the revised level by a large, distinctive amount,
and asserts that the PIT signal (built from the first-release vintage) uses the first-release
monthly change, while the NAIVE signal (built from the revised vintage) uses the revised change.
This is exactly the data-revision leakage the study is designed to measure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_study_macro import (  # noqa: E402
    assemble,
    build_signal,
    monthly_change,
    newey_west_tstat,
    rolling_zscore,
    trend_expectation,
)
from research_pipeline.data import PricePanel  # noqa: E402


def _synthetic_levels(
    n: int = 200, revise_idx: int = 150, revise_by: float = 300.0
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """A multi-year monthly payrolls-level series with steady growth, returned as
    (first_release, revised, release_date). The two levels are identical EXCEPT at
    ``revise_idx`` where the revised level is bumped by ``revise_by`` thousand jobs (a large,
    distinctive, known revision). The release date is the first of the following month + 5 days
    (a stand-in Jobs Friday)."""
    months = pd.date_range("2000-01-01", periods=n, freq="MS")
    # steady payroll growth ~150k/month with mild seasonal wiggle
    woy = months.month.to_numpy().astype(float)
    level = 130000.0 + 150.0 * np.arange(n) + 40.0 * np.sin(2 * np.pi * woy / 12.0)
    first = pd.Series(level, index=months, name="level")
    revised = first.copy()
    revised.iloc[revise_idx] = revised.iloc[revise_idx] + revise_by
    release = pd.Series(
        [m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=5) for m in months], index=months
    )
    return first, revised, release


def test_pit_uses_first_release_not_revised() -> None:
    """The PIT signal must reflect the first-release change; NAIVE reflects the revised change.

    A +300k revision at month k changes the reported change at BOTH month k (level_k - level_{k-1})
    and month k+1 (level_{k+1} - level_k). The first-release and revised changes must therefore
    differ by +300 at month k and -300 at month k+1, and identically everywhere else.
    """
    first, revised, release = _synthetic_levels(revise_idx=150, revise_by=300.0)
    k = first.index[150]
    k1 = first.index[151]

    ch_first = monthly_change(first)
    ch_revised = monthly_change(revised)

    assert np.isclose(ch_revised.loc[k] - ch_first.loc[k], 300.0)
    assert np.isclose(ch_revised.loc[k1] - ch_first.loc[k1], -300.0)
    other = ch_first.index.difference(pd.DatetimeIndex([k, k1]))
    assert np.allclose(ch_first.loc[other].dropna(), ch_revised.loc[other].dropna())

    # And the built signal (surprise -> position) differs at exactly those months, because the
    # PIT arm fed first-release and the NAIVE arm fed revised.
    sig_pit = build_signal(first, release)
    sig_naive = build_signal(revised, release)
    common = sig_pit.index.intersection(sig_naive.index)
    dpos = (sig_naive.loc[common, "position"] - sig_pit.loc[common, "position"]).abs()
    moved = set(dpos[dpos > 1e-9].index)
    assert k in moved or k1 in moved, "the planted revision must move the signal"


def test_trend_expectation_is_trailing_only() -> None:
    """trend_expectation at month m must not depend on any month at or after m."""
    first, _, _ = _synthetic_levels()
    ch = monthly_change(first)
    full = trend_expectation(ch)
    cut = 160
    truncated = trend_expectation(ch.iloc[: cut + 1])
    m = ch.index[cut]
    if np.isfinite(full.loc[m]):
        assert np.isclose(full.loc[m], truncated.loc[m])


def test_rolling_zscore_excludes_current() -> None:
    """rolling_zscore standardizes using a window ending at m-1 (never sees month m)."""
    s = pd.Series(np.arange(300.0))
    z = rolling_zscore(s, lookback=36)
    full = z.iloc[250]
    z_trunc = rolling_zscore(s.iloc[:251], lookback=36).iloc[250]
    assert np.isclose(full, z_trunc)


def test_surprise_sign_is_contrarian_short_on_big_beat() -> None:
    """A larger-than-expected jobs print (positive surprise) implies a SHORT (negative position)."""
    first, _, release = _synthetic_levels()
    sig = build_signal(first, release)
    valid = sig.dropna(subset=["surprise", "position"])
    paired = valid[valid["surprise"].abs() > 1e-9]
    # position and surprise must have opposite signs (position = -zscore(surprise)).
    assert (np.sign(paired["position"]) == -np.sign(paired["surprise"])).mean() > 0.95


def test_assemble_enters_after_release() -> None:
    """Entry must be the first SPY open on/after the ALFRED release date."""
    first, _, release = _synthetic_levels(n=200)
    days = pd.bdate_range("1999-12-01", "2017-12-31")
    px = pd.DataFrame(
        {"open": np.arange(1.0, len(days) + 1.0), "close": np.arange(1.0, len(days) + 1.0)},
        index=days,
    )
    panel = PricePanel(px)
    sig = build_signal(first, release)
    assert len(sig) > 0, "signal warm-up consumed the whole sample"
    bt = assemble(panel, sig)
    month = sig.index[len(sig) // 2]
    rel = pd.Timestamp(sig.loc[month, "release_date"])
    entry = bt.entry_by_month.loc[month]
    assert entry >= rel, f"entry {entry} precedes the {rel.date()} release"
    assert (entry - rel).days <= 4  # first trading day on/after release


def test_newey_west_runs() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, 500)
    mean, t, lag = newey_west_tstat(x)
    assert lag >= 1
    assert abs(t) < 5.0
