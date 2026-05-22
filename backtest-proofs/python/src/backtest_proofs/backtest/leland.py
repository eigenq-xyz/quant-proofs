"""Leland (1985) rehedge-frequency variance sweep.

Bertsimas, Kogan & Lo (2000) show that the variance of discrete delta-hedge
cost scales as:

    Var(cost) ∝ Γ² S² σ² Δt  ∝  1/N

where N is the number of rebalancing steps over the life of the option.
Equivalently, std(cost) ∝ 1/√N, so std(cost) × √N is approximately constant.

``leland_variance_sweep`` estimates this empirically for a grid of N values by
simulating ``n_paths`` seeded GBM paths and running :func:`run_delta_hedge`
with each rebalancing frequency.  The result can be plotted as std(cost) vs
1/√N to verify the theoretical scaling.

Reference: Leland (1985) "Option Pricing and Replication with Transactions
Costs", *Journal of Finance* 40(4). BKL scaling: Bertsimas, Kogan & Lo (2000)
"When is time continuous?", *Journal of Financial Economics* 55(2).
"""

from __future__ import annotations

import concurrent.futures
import os

import numpy as np

from backtest_proofs.backtest.data_types import PricePath
from backtest_proofs.backtest.runner import run_delta_hedge
from backtest_proofs.simulator.gbm import simulate_gbm


def leland_paths_sweep(
    s0: float,
    k: float,
    r: float,
    sigma: float,
    t: float,
    n_paths: int,
    frequencies: list[int],
    seed: int,
    n_contracts: int = 1,
) -> dict[int, list[float]]:
    """Simulate hedging costs for each rebalancing frequency N, returning raw paths.

    Unlike :func:`leland_variance_sweep` and :func:`leland_bias_sweep` (which
    collapse paths to summary statistics), this function returns the full list
    of hedging costs per frequency so that the caller can apply bootstrap
    resampling for pointwise confidence intervals.

    Same seed scheme as :func:`leland_variance_sweep`: path *i* at frequency
    *N* uses seed ``seed + N * 10_000 + i``, ensuring independence across
    frequencies and reproducibility.

    Args:
        s0: Initial spot price (dollars).
        k: Strike price (dollars).
        r: Continuously compounded risk-free rate (annualised).
        sigma: Implied volatility (annualised).
        t: Time to expiry in years.
        n_paths: Number of GBM paths per frequency.
        frequencies: List of rebalancing step counts N to sweep.
        seed: Base RNG seed.
        n_contracts: Number of written call contracts (default 1).

    Returns:
        ``{N: [cost_0, cost_1, ..., cost_{n_paths-1}]}`` — raw hedging costs.
    """
    result: dict[int, list[float]] = {}
    for n_steps in frequencies:
        costs: list[float] = []
        for path_idx in range(n_paths):
            path_seed = seed + n_steps * 10_000 + path_idx
            path = simulate_gbm(
                S0=s0,
                mu=r,
                sigma=sigma,
                T=t,
                n_steps=n_steps,
                seed=path_seed,
            )
            hedge_result = run_delta_hedge(
                path=PricePath(times=path.times, prices=path.prices),
                K=k,
                r=r,
                sigma=sigma,
                n_contracts=n_contracts,
            )
            costs.append(hedge_result.total_hedging_cost)
        result[n_steps] = costs
    return result


def _simulate_one_frequency(
    n_steps: int,
    s0: float,
    k: float,
    r: float,
    sigma: float,
    t: float,
    n_paths: int,
    seed: int,
    n_contracts: int,
) -> tuple[int, list[float]]:
    """Simulate hedging costs for a single rebalancing frequency (worker function).

    Designed for use with :func:`leland_paths_sweep_parallel`. Each call is
    fully independent — the seed scheme ``seed + n_steps * 10_000 + path_idx``
    ensures orthogonal RNG streams across both frequencies and paths.
    """
    costs: list[float] = []
    for path_idx in range(n_paths):
        path_seed = seed + n_steps * 10_000 + path_idx
        path = simulate_gbm(
            S0=s0, mu=r, sigma=sigma, T=t, n_steps=n_steps, seed=path_seed
        )
        hedge_result = run_delta_hedge(
            path=PricePath(times=path.times, prices=path.prices),
            K=k, r=r, sigma=sigma, n_contracts=n_contracts,
        )
        costs.append(hedge_result.total_hedging_cost)
    return n_steps, costs


def leland_paths_sweep_parallel(
    s0: float,
    k: float,
    r: float,
    sigma: float,
    t: float,
    n_paths: int,
    frequencies: list[int],
    seed: int,
    n_contracts: int = 1,
    max_workers: int | None = None,
) -> dict[int, list[float]]:
    """Parallel version of :func:`leland_paths_sweep`.

    Dispatches each frequency as an independent task to a
    :class:`concurrent.futures.ProcessPoolExecutor`.  All frequencies are
    independent (orthogonal seed blocks), so wall-clock time scales as
    roughly ``len(frequencies) / max_workers``.

    Args:
        s0: Initial spot price (dollars).
        k: Strike price (dollars).
        r: Continuously compounded risk-free rate (annualised).
        sigma: Implied volatility (annualised).
        t: Time to expiry in years.
        n_paths: Number of GBM paths per frequency.
        frequencies: List of rebalancing step counts N to sweep.
        seed: Base RNG seed; path i at frequency N uses ``seed + N*10_000 + i``.
        n_contracts: Number of written call contracts (default 1).
        max_workers: Number of parallel workers. Defaults to
            ``min(len(frequencies), os.cpu_count() or 4)``.

    Returns:
        ``{N: [cost_0, ..., cost_{n_paths-1}]}`` — same format as
        :func:`leland_paths_sweep`.
    """
    if max_workers is None:
        max_workers = min(len(frequencies), os.cpu_count() or 4)

    result: dict[int, list[float]] = {}
    futures_map = {}

    with concurrent.futures.ProcessPoolExecutor(max_workers=max_workers) as executor:
        for n_steps in frequencies:
            fut = executor.submit(
                _simulate_one_frequency,
                n_steps, s0, k, r, sigma, t, n_paths, seed, n_contracts,
            )
            futures_map[fut] = n_steps

        for fut in concurrent.futures.as_completed(futures_map):
            n_steps_done, costs = fut.result()
            result[n_steps_done] = costs

    return result


def leland_bias_sweep(
    s0: float,
    k: float,
    r: float,
    sigma: float,
    t: float,
    n_paths: int,
    frequencies: list[int],
    seed: int,
    n_contracts: int = 1,
) -> dict[int, float]:
    """Estimate mean(hedge cost) for each rebalancing frequency N.

    Same path seed scheme as :func:`leland_variance_sweep`.  Use together
    to get both the mean and std from the same simulation budget.

    Args:
        s0: Initial spot price (dollars).
        k: Strike price (dollars).
        r: Continuously compounded risk-free rate (annualised).
        sigma: Implied volatility (annualised).
        t: Time to expiry in years.
        n_paths: Number of GBM paths per frequency.
        frequencies: List of rebalancing step counts N to sweep.
        seed: Base RNG seed (same scheme as :func:`leland_variance_sweep`).
        n_contracts: Number of written call contracts (default 1).

    Returns:
        ``{N: mean(cost)}`` dict, one entry per element of *frequencies*.
    """
    result: dict[int, float] = {}
    for n_steps in frequencies:
        costs: list[float] = []
        for path_idx in range(n_paths):
            path_seed = seed + n_steps * 10_000 + path_idx
            path = simulate_gbm(
                S0=s0,
                mu=r,
                sigma=sigma,
                T=t,
                n_steps=n_steps,
                seed=path_seed,
            )
            hedge_result = run_delta_hedge(
                path=PricePath(
                    times=path.times,
                    prices=path.prices,
                ),
                K=k,
                r=r,
                sigma=sigma,
                n_contracts=n_contracts,
            )
            costs.append(hedge_result.total_hedging_cost)
        result[n_steps] = float(np.mean(costs))
    return result


def leland_variance_sweep(
    s0: float,
    k: float,
    r: float,
    sigma: float,
    t: float,
    n_paths: int,
    frequencies: list[int],
    seed: int,
    n_contracts: int = 1,
) -> dict[int, float]:
    """Estimate std(hedge cost) for each rebalancing frequency N.

    For each N in *frequencies*:
    1. Simulate *n_paths* independent GBM paths (risk-neutral drift = r),
       each with exactly N equally spaced time steps over [0, t].
    2. Run :func:`run_delta_hedge` for one written call on each path.
    3. Return the sample standard deviation of the total hedging cost.

    BKL theory predicts std(cost) ∝ 1/√N, so the returned values should
    approximately satisfy ``std_n × √N = const`` across all N.

    Args:
        s0: Initial spot price (dollars).
        k: Strike price (dollars).
        r: Continuously compounded risk-free rate (annualised).
        sigma: Implied volatility (annualised).
        t: Time to expiry in years.
        n_paths: Number of GBM paths per frequency (seeded deterministically).
        frequencies: List of rebalancing step counts N to sweep.
        seed: Base RNG seed; path i for frequency N uses seed ``seed + N * 10000 + i``.
        n_contracts: Number of written call contracts (default 1). Use a large
            value (e.g. 100_000) so that basis-point rounding noise in the
            Lean FFI is negligible relative to the hedge cost signal.

    Returns:
        ``{N: std(cost)}`` dict, one entry per element of *frequencies*.
    """
    result: dict[int, float] = {}
    for n_steps in frequencies:
        costs: list[float] = []
        for path_idx in range(n_paths):
            path_seed = seed + n_steps * 10_000 + path_idx
            path = simulate_gbm(
                S0=s0,
                mu=r,
                sigma=sigma,
                T=t,
                n_steps=n_steps,
                seed=path_seed,
            )
            hedge_result = run_delta_hedge(
                path=PricePath(
                    times=path.times,
                    prices=path.prices,
                ),
                K=k,
                r=r,
                sigma=sigma,
                n_contracts=n_contracts,
            )
            costs.append(hedge_result.total_hedging_cost)
        result[n_steps] = float(np.std(costs, ddof=1))
    return result
