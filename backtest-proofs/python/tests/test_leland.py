"""Tests for the Leland (1985) rehedge-frequency variance sweep."""

import math

from backtest_proofs.backtest.leland import leland_bias_sweep, leland_variance_sweep
from backtest_proofs.pricer.black_scholes import bs_price

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


class TestLelandBiasSweep:
    """Unit tests for leland_bias_sweep (mean hedge cost vs BS price).

    The O(Δt) downward correction to the Black-Scholes price under discrete
    rebalancing [@leland1985] predicts:
    - E[hedge cost] < BS price (negative bias)
    - The bias shrinks as N increases (converges to BS price)

    These tests use small n_paths=30 for CI speed; the paper uses n_paths=500.
    """

    def test_mean_within_10pct_of_bs(self) -> None:
        """Mean hedge cost at N=20 is within 10% of the BS reference price.

        The O(Δt) bias is small for N=20 (≈ weekly rebalancing over 20 weeks),
        so the mean should land close to the BS price.
        """
        bs_ref = bs_price(
            S=_S0, K=_K, T=_T, r=_R, sigma=_SIGMA, option_type="call"
        ).value * _N_CONTRACTS
        result = leland_bias_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=30, frequencies=[20], seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        mean_cost = result[20]
        assert abs(mean_cost - bs_ref) / bs_ref < 0.10, (
            f"Mean cost {mean_cost:.4f} deviates from BS ref {bs_ref:.4f} "
            f"by {abs(mean_cost - bs_ref) / bs_ref * 100:.1f}% (tolerance 10%)"
        )

    def test_mean_below_bs_price(self) -> None:
        """Mean hedge cost at N=20 is below the BS price (O(Δt) downward bias).

        Under discrete rebalancing with no transaction costs, the expected
        hedge cost lies below the Black-Scholes price [@leland1985, §II].
        A positive mean bias would indicate an accounting bug or wrong sign.

        Uses n_paths=30 for CI speed; tolerance is set wide because 30 paths
        may not give a reliable estimate of the mean at small N.
        """
        bs_ref = bs_price(
            S=_S0, K=_K, T=_T, r=_R, sigma=_SIGMA, option_type="call"
        ).value * _N_CONTRACTS
        result = leland_bias_sweep(
            s0=_S0, k=_K, r=_R, sigma=_SIGMA, t=_T,
            n_paths=30, frequencies=[20], seed=_SEED,
            n_contracts=_N_CONTRACTS,
        )
        mean_cost = result[20]
        assert mean_cost < bs_ref, (
            f"Expected mean cost {mean_cost:.4f} < BS ref {bs_ref:.4f} "
            f"(O(Δt) downward bias); got positive bias. "
            f"This may indicate an accounting sign error."
        )
