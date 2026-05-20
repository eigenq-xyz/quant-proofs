"""Tests for the Leland (1985) rehedge-frequency variance sweep."""

import math

from backtest_proofs.backtest.leland import leland_variance_sweep

# Fixed scenario matching MC convergence parameters in test_backtest.py
_S0 = 49.0
_K = 50.0
_R = 0.05
_SIGMA = 0.20
_T = 20 / 52
_N_PATHS = 200  # enough for stable std estimates; fast in CI
_SEED = 20260519
_FREQUENCIES = [5, 10, 20, 40]
# Large n_contracts suppresses Lean basis-point integer rounding noise so the
# BKL signal dominates.  The paper chunk uses 100_000; 10_000 is sufficient
# for tests without requiring long CI runtimes.
_N_CONTRACTS = 10_000


class TestLelandVarianceSweep:
    def test_returns_all_frequencies(self) -> None:
        result = leland_variance_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=_N_PATHS, frequencies=_FREQUENCIES, seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        assert set(result.keys()) == set(_FREQUENCIES)

    def test_std_is_positive(self) -> None:
        result = leland_variance_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=_N_PATHS, frequencies=_FREQUENCIES, seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        for n, std in result.items():
            assert std > 0, f"std for N={n} is non-positive: {std}"

    def test_bkl_scaling_holds(self) -> None:
        """std × √N is approximately constant across frequencies (BKL theorem).

        Tolerance is loose (50%) because we use a small n_paths for CI speed.
        The paper figure uses n_paths=500 which gives tighter agreement.
        """
        result = leland_variance_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=_N_PATHS, frequencies=_FREQUENCIES, seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        scaled = {n: std * math.sqrt(n) for n, std in result.items()}
        values = list(scaled.values())
        mean_scaled = sum(values) / len(values)
        for n, sv in scaled.items():
            assert abs(sv - mean_scaled) / mean_scaled < 0.50, (
                f"BKL scaling violated at N={n}: "
                f"std×√N={sv:.4f}, mean={mean_scaled:.4f}"
            )

    def test_std_decreases_with_frequency(self) -> None:
        """Higher rebalancing frequency → lower hedge cost variance."""
        result = leland_variance_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=_N_PATHS, frequencies=[5, 20], seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        assert result[5] > result[20], (
            f"Expected std(5) > std(20); got {result[5]:.4f} vs {result[20]:.4f}"
        )
