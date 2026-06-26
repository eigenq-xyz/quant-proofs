"""Tests for the EIA storage data-revision leakage-tax study.

The load-bearing test (``test_pit_uses_first_release_not_revised``) plants a KNOWN revision: a
week whose first-release level differs from the revised level by a large, distinctive amount,
and asserts that the PIT signal (built from the first-release vintage) uses the first-release
weekly change, while the NAIVE signal (built from the revised vintage) uses the revised change.
This is exactly the data-revision leakage the study is designed to measure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_study_eia import (  # noqa: E402
    assemble,
    build_signal,
    newey_west_tstat,
    rolling_zscore,
    seasonal_expectation,
    weekly_change,
)
from research_pipeline.data import PricePanel  # noqa: E402


def _synthetic_levels(
    n: int = 260, revise_idx: int = 200, revise_by: float = 50.0
) -> tuple[pd.Series, pd.Series]:
    """A multi-year weekly level series with a clean seasonal shape, returned as
    (first_release, revised). The two are identical EXCEPT at ``revise_idx`` where the revised
    level is bumped by ``revise_by`` Bcf (a large, distinctive, known revision)."""
    weeks = pd.date_range("2016-01-01", periods=n, freq="W-FRI")
    woy = weeks.isocalendar().week.to_numpy().astype(float)
    # seasonal level: high in autumn, low in spring (a smooth cycle) plus mild trend
    level = 2500.0 + 800.0 * np.sin(2 * np.pi * woy / 52.0) + 0.0 * np.arange(n)
    first = pd.Series(level, index=weeks, name="level")
    revised = first.copy()
    revised.iloc[revise_idx] = revised.iloc[revise_idx] + revise_by
    return first, revised


def test_pit_uses_first_release_not_revised() -> None:
    """The PIT signal must reflect the first-release change; NAIVE reflects the revised change.

    A +50 Bcf revision at week k changes the reported change at BOTH week k (level_k - level_{k-1})
    and week k+1 (level_{k+1} - level_k). The first-release and revised changes must therefore
    differ by +50 at week k and -50 at week k+1, and identically everywhere else.
    """
    first, revised = _synthetic_levels(revise_idx=200, revise_by=50.0)
    k = first.index[200]
    k1 = first.index[201]

    ch_first = weekly_change(first)
    ch_revised = weekly_change(revised)

    assert np.isclose(ch_revised.loc[k] - ch_first.loc[k], 50.0)
    assert np.isclose(ch_revised.loc[k1] - ch_first.loc[k1], -50.0)
    # Every other week is untouched.
    other = ch_first.index.difference(pd.DatetimeIndex([k, k1]))
    assert np.allclose(ch_first.loc[other].dropna(), ch_revised.loc[other].dropna())

    # And the built signal (surprise -> position) differs at exactly those weeks, because the
    # PIT arm fed first-release and the NAIVE arm fed revised.
    sig_pit = build_signal(first)
    sig_naive = build_signal(revised)
    common = sig_pit.index.intersection(sig_naive.index)
    dpos = (sig_naive.loc[common, "position"] - sig_pit.loc[common, "position"]).abs()
    moved = set(dpos[dpos > 1e-9].index)
    assert k in moved or k1 in moved, "the planted revision must move the signal"


def test_seasonal_expectation_is_trailing_only() -> None:
    """seasonal_expectation at week w must not depend on any week at or after w."""
    first, _ = _synthetic_levels()
    ch = weekly_change(first)
    full = seasonal_expectation(ch)
    # Truncate after some interior week; the expectation at that week must be unchanged.
    cut = 210
    truncated = seasonal_expectation(ch.iloc[: cut + 1])
    wk = ch.index[cut]
    if np.isfinite(full.loc[wk]):
        assert np.isclose(full.loc[wk], truncated.loc[wk])


def test_rolling_zscore_excludes_current() -> None:
    """rolling_zscore standardizes using a window ending at w-1 (never sees week w)."""
    s = pd.Series(np.arange(300.0))
    z = rolling_zscore(s, lookback=104)
    full = z.iloc[250]
    z_trunc = rolling_zscore(s.iloc[:251], lookback=104).iloc[250]
    assert np.isclose(full, z_trunc)


def test_surprise_sign_is_contrarian_short_on_big_build() -> None:
    """A larger-than-expected BUILD (positive surprise) implies a SHORT (negative position)."""
    first, _ = _synthetic_levels()
    sig = build_signal(first)
    valid = sig.dropna(subset=["surprise", "position"])
    paired = valid[valid["surprise"].abs() > 1e-9]
    # position and surprise must have opposite signs (position = -zscore(surprise)).
    assert (np.sign(paired["position"]) == -np.sign(paired["surprise"])).mean() > 0.95


def test_assemble_enters_after_thursday_release() -> None:
    """Entry must be the first UNG open on/after the Thursday release (week-ending Fri + 6)."""
    first, _ = _synthetic_levels(n=260)
    days = pd.bdate_range("2015-12-01", "2021-12-31")
    px = pd.DataFrame(
        {"open": np.arange(1.0, len(days) + 1.0), "close": np.arange(1.0, len(days) + 1.0)},
        index=days,
    )
    panel = PricePanel(px)
    sig = build_signal(first)
    assert len(sig) > 0, "signal warm-up consumed the whole sample"
    bt = assemble(panel, sig)
    week = sig.index[len(sig) // 2]
    release = week + pd.Timedelta(days=6)
    assert release.weekday() == 3  # Thursday
    entry = bt.entry_by_week.loc[week]
    assert entry >= release, f"entry {entry} precedes the {release.date()} release"
    assert (entry - release).days <= 4  # first trading day on/after release


def test_newey_west_runs() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, 500)
    mean, t, lag = newey_west_tstat(x)
    assert lag >= 1
    assert abs(t) < 5.0
