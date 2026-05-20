"""Synthetic stress-regime backtesting using GBM fallback paths.

When WRDS/OptionMetrics data is unavailable, Figure 7 (stress cost
distributions) falls back to GBM paths calibrated to regime-specific
volatility parameters derived from publicly documented peak VIX values.
"""

from __future__ import annotations

from dataclasses import dataclass

from quant_core.pricer.black_scholes import bs_price
from quant_core.simulator.gbm import simulate_gbm

from backtest_proofs.backtest.data_types import PricePath
from backtest_proofs.backtest.runner import run_delta_hedge


@dataclass(frozen=True)
class RegimeParameters:
    """Parameters for a named historical stress regime.

    Attributes:
        label: Short human-readable name for the regime.
        sigma: Annualised GBM volatility (fraction, e.g. 0.80 for 80 %).
        r: Continuously compounded risk-free rate (annualised).
        start_date: Inclusive window start, ``"YYYY-MM-DD"``.
        end_date: Inclusive window end, ``"YYYY-MM-DD"``.
        peak_vix: Documented peak VIX level during the regime.
        description: One-line description of the event.
    """

    label: str
    sigma: float
    r: float
    start_date: str
    end_date: str
    peak_vix: float
    description: str


STRESS_REGIMES: list[RegimeParameters] = [
    RegimeParameters(
        label="COVID-2020",
        sigma=0.80,
        r=0.0025,
        start_date="2020-02-19",
        end_date="2020-03-23",
        peak_vix=82.69,
        description="Covid-19 market selloff",
    ),
    RegimeParameters(
        label="GFC-2008",
        sigma=0.75,
        r=0.01,
        start_date="2008-09-15",
        end_date="2008-11-21",
        peak_vix=80.86,
        description="Global financial crisis",
    ),
    RegimeParameters(
        label="Volmageddon-2018",
        sigma=0.35,
        r=0.015,
        start_date="2018-01-22",
        end_date="2018-02-16",
        peak_vix=37.32,
        description="Short-volatility unwind",
    ),
    RegimeParameters(
        label="FlashCrash-2015",
        sigma=0.40,
        r=0.005,
        start_date="2015-08-17",
        end_date="2015-08-28",
        peak_vix=40.74,
        description="August 2015 ETF flash crash",
    ),
]


def run_synthetic_stress(
    regime: RegimeParameters,
    n_paths: int,
    seed: int,
    K: float,
    r_override: float | None = None,
    n_steps: int = 20,
    n_contracts: int = 100_000,
    S0: float = 49.0,
) -> tuple[list[float], int]:
    """Run a synthetic stress backtest using GBM paths for one regime.

    Each path is an independent GBM draw; the seed is offset by path index
    so paths are independent while the ensemble remains reproducible.

    Args:
        regime: Stress regime parameters (volatility, dates, peak VIX).
        n_paths: Number of independent GBM paths to simulate.
        seed: Base RNG seed; path ``i`` uses ``seed + i``.
        K: Option strike (dollars).
        r_override: If provided, overrides ``regime.r`` for both pricing
            and hedging. Useful for sensitivity analysis.
        n_steps: Rebalancing steps per path (default 20, matching Hull
            Table 19.2 weekly convention over ~20 weeks).
        n_contracts: Number of written call contracts per path.
        S0: Initial underlying spot price (dollars).

    Returns:
        ``(ratios, n_paths)`` where ``ratios`` is the list of
        cost/premium ratios (one per path) and the second element is
        ``n_paths``, matching the ``run_stress_window`` return signature.
    """
    r = r_override if r_override is not None else regime.r
    T = n_steps / 52.0  # weekly steps, annualised

    premium = bs_price(
        S=S0,
        K=K,
        T=T,
        r=r,
        sigma=regime.sigma,
        option_type="call",
    ).value

    ratios: list[float] = []
    for i in range(n_paths):
        path: PricePath = simulate_gbm(
            S0=S0,
            mu=r,
            sigma=regime.sigma,
            T=T,
            n_steps=n_steps,
            seed=seed + i,
        )
        result = run_delta_hedge(
            path=path,
            K=K,
            r=r,
            sigma=regime.sigma,
            n_contracts=n_contracts,
        )
        if premium > 0:
            ratios.append(
                result.total_hedging_cost / (premium * n_contracts)
            )

    return ratios, n_paths
