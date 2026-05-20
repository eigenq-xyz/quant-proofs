"""Tests for the QuantLib A-B pricer comparison.

All tests are gated on QuantLib being importable so that core CI passes
without the optional research dependency installed.
"""

import pytest

ql = pytest.importorskip("QuantLib", reason="QuantLib not installed")

from backtest_proofs.backtest.quantlib_compare import (  # noqa: E402
    ComparisonRow,
    ScenarioSpec,
    compare_to_quantlib,
    max_price_diff_bp,
    within_threshold,
)

_SEED = 20260519

_SCENARIOS = [
    ScenarioSpec(s0=49.0, k=50.0, r=0.05, sigma=0.20, t=20 / 52, n_steps=20),
    ScenarioSpec(s0=100.0, k=100.0, r=0.03, sigma=0.15, t=0.5, n_steps=20),
    ScenarioSpec(s0=50.0, k=55.0, r=0.05, sigma=0.25, t=0.25, n_steps=10),
    ScenarioSpec(s0=200.0, k=190.0, r=0.04, sigma=0.30, t=1.0, n_steps=20),
    ScenarioSpec(s0=80.0, k=80.0, r=0.02, sigma=0.18, t=0.75, n_steps=15),
]


class TestQuantLibCompare:
    def test_returns_rows_for_all_scenarios(self) -> None:
        rows = compare_to_quantlib(_SCENARIOS, seed=_SEED)
        assert len(rows) > 0
        scenario_idxs = {r.scenario_idx for r in rows}
        assert scenario_idxs == set(range(len(_SCENARIOS)))

    def test_row_fields_finite(self) -> None:
        rows = compare_to_quantlib(_SCENARIOS, seed=_SEED)
        for row in rows:
            assert isinstance(row, ComparisonRow)
            assert row.our_price >= 0
            assert row.ql_price >= 0
            assert row.price_diff_bp >= 0
            assert 0.0 <= row.our_delta <= 1.0
            assert 0.0 <= row.ql_delta <= 1.0

    def test_prices_within_5bp(self) -> None:
        """Our BS price matches QuantLib within 5 basis points.

        QuantLib uses integer calendar days internally (``round(T * 365)``),
        while our pricer accepts fractional-year T directly.  The resulting
        day-count rounding introduces up to ~3 bp of deviation on a 1-year
        ATM option.  The paper reports the exact max deviation; 5 bp is the
        acceptance gate for the automated test.
        """
        rows = compare_to_quantlib(_SCENARIOS, seed=_SEED)
        assert within_threshold(rows, threshold_bp=5.0), (
            f"Max price deviation {max_price_diff_bp(rows):.4f} bp exceeds 5 bp"
        )

    def test_deltas_close(self) -> None:
        """Our BS delta matches QuantLib delta to within 0.002.

        The same day-count rounding that introduces up to ~3 bp of price
        deviation (see ``test_prices_within_5bp``) also shifts delta by a
        small but nonzero amount.  0.002 is the empirically observed ceiling;
        the paper reports the exact value.
        """
        rows = compare_to_quantlib(_SCENARIOS, seed=_SEED)
        max_delta_diff = max(r.delta_diff for r in rows)
        assert max_delta_diff < 0.002, (
            f"Max delta diff {max_delta_diff:.6f} exceeds 0.002"
        )
