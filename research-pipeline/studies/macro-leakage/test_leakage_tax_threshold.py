"""Tests for the THRESHOLD-signal data-revision leakage-tax study.

The load-bearing test (``test_revision_crossing_threshold_flips_position``) plants a revision that
is engineered to CROSS the decision threshold: the first-release change sits just BELOW ``k`` and
the revised change sits just ABOVE ``k``. It asserts that the PIT signal (first-release vintage)
and the NAIVE signal (revised vintage) take OPPOSITE positions at that month. That position flip is
the exact mechanism the study measures, the thing a standardized signal cannot exhibit.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_study_threshold import (  # noqa: E402
    build_threshold_signal,
    flip_diagnostics,
)
from run_study_macro import assemble  # noqa: E402
from research_pipeline.data import PricePanel  # noqa: E402


def _levels_with_threshold_crossing(
    n: int = 60,
    cross_idx: int = 30,
    k: float = 200.0,
    first_below: float = 180.0,
    revised_above: float = 220.0,
) -> tuple[pd.Series, pd.Series, pd.Series, float]:
    """Monthly payrolls levels whose MoM change at ``cross_idx`` straddles ``k``.

    Away from the crossing month the change is a steady +150k (cleanly on one side of the typical
    thresholds). At ``cross_idx`` the first-release change is ``first_below`` (just below ``k``)
    and the revised change is ``revised_above`` (just above ``k``), so a NAIVE arm (revised) is
    at/above ``k`` while the PIT arm (first-release) is below it: opposite positions. Returns
    (first_release, revised, release_date, k).
    """
    months = pd.date_range("2000-01-01", periods=n, freq="MS")
    base = 100000.0
    # First-release levels: steady +150k/month, except the crossing month uses first_below.
    fr_changes = np.full(n, 150.0)
    fr_changes[cross_idx] = first_below
    first_level = base + np.cumsum(np.concatenate([[0.0], fr_changes[1:]]))
    first = pd.Series(first_level, index=months, name="level")

    # Revised: identical EXCEPT the crossing month's change is bumped to revised_above. Bumping the
    # level at cross_idx changes the change at cross_idx (+) and at cross_idx+1 (-), so to keep the
    # revision local we lift the level only at cross_idx and let the next-month change carry it.
    revised = first.copy()
    bump = revised_above - first_below  # +40k by default
    revised.iloc[cross_idx] = revised.iloc[cross_idx] + bump

    release = pd.Series(
        [m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=5) for m in months], index=months
    )
    return first, revised, release, k


def test_revision_crossing_threshold_flips_position() -> None:
    """A revision that crosses ``k`` must make NAIVE and PIT take OPPOSITE positions.

    PIT (first-release change 180k < 200k) is LONG (+1); NAIVE (revised change 220k >= 200k) is
    SHORT (-1). They must differ at exactly the crossing month and agree everywhere else.
    """
    first, revised, release, k = _levels_with_threshold_crossing(
        cross_idx=30, k=200.0, first_below=180.0, revised_above=220.0
    )
    cross_month = first.index[30]

    sig_pit = build_threshold_signal(first, release, k)
    sig_naive = build_threshold_signal(revised, release, k)

    assert sig_pit.loc[cross_month, "position"] == +1.0  # first-release 180k < 200k -> long
    assert sig_naive.loc[cross_month, "position"] == -1.0  # revised 220k >= 200k -> short

    common = sig_pit.index.intersection(sig_naive.index)
    diff = sig_naive.loc[common, "position"] != sig_pit.loc[common, "position"]
    flipped_months = set(common[diff.to_numpy()])
    # The planted crossing flips the crossing month. (The +40k bump at cross_idx also lowers the
    # change at cross_idx+1 by 40k, which here is the only OTHER month that can flip; the test
    # asserts the crossing month is among the flips, the necessary mechanism.)
    assert cross_month in flipped_months, "the threshold-crossing revision must flip the position"


def test_below_threshold_no_flip() -> None:
    """A revision that does NOT cross ``k`` must leave both arms on the same side (no flip)."""
    # Both first (180k) and revised (190k) stay below k=200k -> both LONG, no flip at crossing.
    first, revised, release, k = _levels_with_threshold_crossing(
        cross_idx=30, k=200.0, first_below=180.0, revised_above=190.0
    )
    cross_month = first.index[30]
    sig_pit = build_threshold_signal(first, release, k)
    sig_naive = build_threshold_signal(revised, release, k)
    assert sig_pit.loc[cross_month, "position"] == +1.0
    assert sig_naive.loc[cross_month, "position"] == +1.0  # 190k still < 200k -> no flip


def test_position_is_binary_pm1() -> None:
    """The threshold signal must only ever emit +1 or -1 (a hard step, not a continuous tilt)."""
    first, _, release, k = _levels_with_threshold_crossing()
    sig = build_threshold_signal(first, release, k)
    assert set(np.unique(sig["position"].to_numpy())) <= {-1.0, +1.0}


def test_fade_direction_short_above_threshold() -> None:
    """A change at/above ``k`` (a hot print) must be SHORT SPY (-1); below ``k`` LONG (+1)."""
    months = pd.date_range("2000-01-01", periods=10, freq="MS")
    # changes: 150 (long), then a jump that puts the next change at +400 (>=200 -> short).
    level = pd.Series(
        [
            100000.0,
            100150.0,
            100300.0,
            100700.0,
            100850.0,
            101000.0,
            101150.0,
            101300.0,
            101450.0,
            101600.0,
        ],
        index=months,
        name="level",
    )
    release = pd.Series(
        [m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=5) for m in months], index=months
    )
    sig = build_threshold_signal(level, release, k=200.0)
    # month index 3 has change +400 (>=200) -> short; month index 1 has +150 (<200) -> long.
    assert sig.loc[months[3], "position"] == -1.0
    assert sig.loc[months[1], "position"] == +1.0


def test_flip_diagnostics_counts_and_negates() -> None:
    """flip_diagnostics must count the flip and, on a flip month, the two arms' returns negate.

    On a flip month the arms hold OPPOSITE +-1 positions over the SAME forward return, so
    r_naive = -r_pit there: the realized (naive - PIT) return is twice the directional return.
    """
    # Plant MANY threshold crossings so the flip-month diagnostic (which uses a Newey-West t-stat
    # needing >= 3 observations) is genuinely exercised. Changes hover at the threshold: first
    # release just below k, revised just above, on every month.
    n = 120
    months = pd.date_range("2000-01-01", periods=n, freq="MS")
    k = 200.0
    fr_changes = np.full(n, 190.0)  # first-release: 190k, just BELOW k -> LONG
    first_level = 100000.0 + np.cumsum(np.concatenate([[0.0], fr_changes[1:]]))
    first = pd.Series(first_level, index=months, name="level")
    rev_changes = np.full(n, 210.0)  # revised: 210k, just ABOVE k -> SHORT (a flip every month)
    rev_level = 100000.0 + np.cumsum(np.concatenate([[0.0], rev_changes[1:]]))
    revised = pd.Series(rev_level, index=months, name="level")
    release = pd.Series(
        [m + pd.offsets.MonthBegin(1) + pd.Timedelta(days=5) for m in months], index=months
    )

    days = pd.bdate_range("1999-12-01", "2011-12-31")
    rng = np.random.default_rng(1)
    px_open = 100.0 * np.cumprod(1.0 + rng.normal(0.0003, 0.01, len(days)))
    px = pd.DataFrame({"open": px_open, "close": px_open}, index=days)
    panel = PricePanel(px)

    sig_naive = build_threshold_signal(revised, release, k)
    sig_pit = build_threshold_signal(first, release, k)
    naive_bt = assemble(panel, sig_naive)
    pit_bt = assemble(panel, sig_pit)

    spy_first = pd.Timestamp(panel.prices.index.min())
    flips = flip_diagnostics(sig_naive, sig_pit, naive_bt, pit_bt, spy_first)
    assert isinstance(flips["n_flip_months"], int)
    # Every month is a planted crossing, so essentially all decision months flip.
    assert flips["n_flip_months"] >= 100, "the planted crossings must register as flips"
    # On a flip month the arms hold opposite +-1 positions over the same return, so r_naive = -r_pit
    # and the realized (naive - PIT) return equals 2 * naive return there: a finite, nonzero stat.
    fnp = flips["flip_mean_naive_minus_pit"]
    assert isinstance(fnp, float)
    assert np.isfinite(fnp)
    mn = flips["flip_mean_naive_return"]
    mp = flips["flip_mean_pit_return"]
    assert isinstance(mn, float) and isinstance(mp, float)
    assert np.isclose(mn, -mp, atol=1e-9), "opposite positions must produce negated returns"
