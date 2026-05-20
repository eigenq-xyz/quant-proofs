"""Tests for synthetic stress-regime backtesting (GBM fallback paths)."""

from __future__ import annotations

from backtest_proofs.backtest.stress_regimes import (
    STRESS_REGIMES,
    run_synthetic_stress,
)


def test_stress_regimes_count_and_positive_sigma() -> None:
    assert len(STRESS_REGIMES) == 4
    for regime in STRESS_REGIMES:
        assert regime.sigma > 0, (
            f"Regime {regime.label!r} has non-positive sigma"
        )


def test_run_synthetic_stress_returns_n_paths_ratios() -> None:
    regime = STRESS_REGIMES[0]
    ratios, count = run_synthetic_stress(
        regime=regime,
        n_paths=10,
        seed=42,
        K=50.0,
    )
    assert count == 10
    assert len(ratios) == 10
