"""Tests for the COT leakage-tax study.

The load-bearing test injects a known COT report (an extreme positioning value with a known
Tuesday as-of date) and asserts that under the PIT convention the implied position does NOT
enter before the following Monday's open (i.e. strictly after the Friday 3:30pm ET release),
whereas the NAIVE convention enters on the Tuesday itself.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_study import (  # noqa: E402
    LOOKBACK_WEEKS,
    assemble,
    newey_west_tstat,
    positioning_percentile,
)
from research_pipeline.data import PricePanel  # noqa: E402


def _synthetic_panel() -> PricePanel:
    # A long daily trading calendar covering the injected report's neighbourhood.
    days = pd.bdate_range("2018-01-01", "2018-12-31")
    px = pd.DataFrame(
        {"open": np.arange(1.0, len(days) + 1.0), "close": np.arange(1.0, len(days) + 1.0)},
        index=days,
    )
    return PricePanel(px)


def _synthetic_cot(as_of_tuesday: pd.Timestamp, extreme: bool = True) -> pd.DataFrame:
    """A run of weekly Tuesday reports ending at ``as_of_tuesday`` with a final extreme value
    so the percentile signal is well-defined and non-zero on the last report."""
    n = LOOKBACK_WEEKS + 2
    dates = pd.date_range(end=as_of_tuesday, periods=n, freq="W-TUE")
    net = np.linspace(0.0, 100.0, n) if extreme else np.zeros(n)
    cot = pd.DataFrame({"as_of": dates, "mm_long": net + 1000.0, "mm_short": 1000.0, "mm_net": net})
    cot["release_date"] = cot["as_of"] + pd.Timedelta(days=3)
    return cot


def test_pit_signal_not_visible_before_monday_after_release() -> None:
    """A Tuesday snapshot must not produce a position before the following Monday open."""
    as_of = pd.Timestamp("2018-06-12")  # a Tuesday
    assert as_of.weekday() == 1
    release = as_of + pd.Timedelta(days=3)  # Friday 2018-06-15
    assert release.weekday() == 4
    following_monday = pd.Timestamp("2018-06-18")
    assert following_monday.weekday() == 0

    panel = _synthetic_panel()
    cot = _synthetic_cot(as_of)

    pit = assemble(panel, cot, pit=True)
    naive = assemble(panel, cot, pit=False)

    # The entry day chosen for the injected report (keyed by its as-of date), regardless of
    # whether that week earns a return in the trimmed series.
    pit_entry = pit.entry_by_as_of.loc[as_of]
    naive_entry = naive.entry_by_as_of.loc[as_of]

    # PIT entry is on/after the following Monday (strictly after the Friday release);
    # NAIVE entry is on/around the Tuesday (it assumed Tuesday knowledge).
    assert pit_entry >= following_monday, (
        f"PIT entered at {pit_entry}, before the {following_monday.date()} release window"
    )
    assert naive_entry <= release, (
        f"NAIVE entry {naive_entry} should be on/around the Tuesday, before release"
    )
    # The PIT entry is strictly later than the naive entry: that gap is the leakage.
    assert pit_entry > naive_entry


def test_naive_acts_on_tuesday_knowledge() -> None:
    as_of = pd.Timestamp("2018-06-12")
    panel = _synthetic_panel()
    cot = _synthetic_cot(as_of)
    naive = assemble(panel, cot, pit=False)
    # First trading day on/after the Tuesday as-of is the Tuesday itself (a business day).
    assert naive.entry_by_as_of.loc[as_of] == as_of


def test_percentile_is_trailing_only() -> None:
    """positioning_percentile must not depend on any future observation."""
    s = pd.Series(np.arange(100.0))
    full = positioning_percentile(s)
    # Truncating the series after index 60 must not change the percentile at index 60.
    truncated = positioning_percentile(s.iloc[:61])
    assert np.isclose(full.iloc[60], truncated.iloc[60])


def test_contrarian_sign() -> None:
    from run_study import contrarian_position

    pos = contrarian_position(pd.Series([0.0, 0.5, 1.0]))
    # crowd extremely long (pctile 1) -> short (-1); extremely short (pctile 0) -> long (+1)
    assert pos.iloc[0] == 1.0
    assert pos.iloc[1] == 0.0
    assert pos.iloc[2] == -1.0


def test_newey_west_runs() -> None:
    rng = np.random.default_rng(0)
    x = rng.normal(0.0, 1.0, 500)
    mean, t, lag = newey_west_tstat(x)
    assert lag >= 1
    assert abs(t) < 5.0  # zero-mean noise should not be hugely significant
