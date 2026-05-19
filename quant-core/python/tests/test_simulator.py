"""Tests for the GBM simulator and PricePath type."""

import pytest

from quant_core.simulator.data_types import PricePath
from quant_core.simulator.gbm import simulate_gbm


class TestPricePath:
    def test_basic_construction(self) -> None:
        path = PricePath(times=[0.0, 0.5, 1.0], prices=[100.0, 105.0, 98.0])
        assert path.n_steps == 2
        assert path.dt == pytest.approx(0.5)

    def test_length_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="same length"):
            PricePath(times=[0.0, 1.0], prices=[100.0])

    def test_too_short_raises(self) -> None:
        with pytest.raises(ValueError, match="at least 2"):
            PricePath(times=[0.0], prices=[100.0])


class TestSimulateGBM:
    def test_length(self) -> None:
        path = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52)
        assert len(path.prices) == 53
        assert len(path.times) == 53

    def test_initial_price(self) -> None:
        path = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52)
        assert path.prices[0] == pytest.approx(100.0)

    def test_reproducible_with_seed(self) -> None:
        p1 = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52, seed=42)
        p2 = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52, seed=42)
        assert p1.prices == p2.prices

    def test_different_seeds_differ(self) -> None:
        p1 = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52, seed=1)
        p2 = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=52, seed=2)
        assert p1.prices != p2.prices

    def test_all_prices_positive(self) -> None:
        path = simulate_gbm(S0=100.0, mu=0.05, sigma=0.20, T=1.0, n_steps=252, seed=0)
        assert all(p > 0 for p in path.prices)
