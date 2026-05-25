"""QuantLib A-B comparison for Black-Scholes pricing and Greeks.

Compares ``backtest_proofs`` BS pricer output against QuantLib's analytic
European engine at a grid of (spot, time-to-expiry) points drawn from seeded
GBM paths.  Both compute European call prices and deltas under the same BS
assumptions; differences in basis points quantify floating-point implementation
divergence between the two systems.

QuantLib is an optional dependency. Import this module only when
``QuantLib`` is installed (``uv sync --group research`` in backtest-proofs
installs it). The comparison function raises ``ImportError`` with a
descriptive message if QuantLib is not found.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from backtest_proofs.simulator.gbm import simulate_gbm


@dataclass(frozen=True)
class ScenarioSpec:
    """Parameters for one A-B comparison scenario.

    Attributes:
        s0: Initial spot price (dollars).
        k: Strike price (dollars).
        r: Continuously compounded risk-free rate (annualised).
        sigma: Implied volatility (annualised).
        t: Time to expiry in years.
        n_steps: Number of GBM simulation steps (evaluation points per path).
    """

    s0: float
    k: float
    r: float
    sigma: float
    t: float
    n_steps: int = 20


@dataclass
class ComparisonRow:
    """One (scenario, time-step) evaluation point in the A-B comparison.

    Attributes:
        scenario_idx: Index into the scenarios list.
        step: Time step index along the GBM path (0 = inception).
        spot: Underlying spot price at this step (dollars).
        t_rem: Time remaining to expiry (years).
        our_price: BS call price from ``backtest_proofs`` (dollars).
        ql_price: BS call price from QuantLib (dollars).
        price_diff_bp: ``|our_price - ql_price| * 10000 / s0`` (basis points).
        our_delta: BS call delta from ``backtest_proofs``.
        ql_delta: BS call delta from QuantLib.
        delta_diff: ``|our_delta - ql_delta|`` (dimensionless).
    """

    scenario_idx: int
    step: int
    spot: float
    t_rem: float
    our_price: float
    ql_price: float
    price_diff_bp: float
    our_delta: float
    ql_delta: float
    delta_diff: float


def _ql_bs_price_delta(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
) -> tuple[float, float]:
    """Compute BS call price and delta using QuantLib's analytic engine.

    Returns ``(price, delta)``. Returns intrinsic value and 0.0/1.0 delta
    when T ≤ 0.

    Note: sets ``ql.Settings.instance().evaluationDate`` — a process-global
    singleton. Not thread-safe; do not call concurrently (e.g., pytest-xdist).
    """
    try:
        import QuantLib as ql
    except ImportError:
        raise ImportError(
            "QuantLib is required for A-B comparison. "
            "Install with: uv sync --group research"
        ) from None

    if T <= 0:
        price = max(S - K, 0.0)
        delta = 1.0 if S > K else 0.0
        return price, delta

    today = ql.Date(1, 6, 2024)
    ql.Settings.instance().evaluationDate = today

    maturity = today + round(T * 365)
    exercise = ql.EuropeanExercise(maturity)
    payoff = ql.PlainVanillaPayoff(ql.Option.Call, K)
    option = ql.VanillaOption(payoff, exercise)

    calendar = ql.NullCalendar()
    day_count = ql.Actual365Fixed()

    spot_handle = ql.QuoteHandle(ql.SimpleQuote(S))
    flat_rate = ql.YieldTermStructureHandle(
        ql.FlatForward(today, r, day_count)
    )
    flat_vol = ql.BlackVolTermStructureHandle(
        ql.BlackConstantVol(today, calendar, sigma, day_count)
    )

    process = ql.BlackScholesProcess(spot_handle, flat_rate, flat_vol)
    option.setPricingEngine(ql.AnalyticEuropeanEngine(process))

    return option.NPV(), option.delta()


def compare_to_quantlib(
    scenarios: list[ScenarioSpec],
    seed: int = 0,
) -> list[ComparisonRow]:
    """Compare BS price and delta against QuantLib at each GBM path step.

    For each scenario, simulates a GBM path and evaluates both our BS pricer
    and QuantLib's analytic engine at every time step. Returns one
    :class:`ComparisonRow` per (scenario, step) pair.

    Steps where time remaining T_rem ≤ 0 are skipped.

    Args:
        scenarios: List of scenario specifications.
        seed: Base RNG seed; scenario i uses seed ``seed + i * 10000``.

    Returns:
        List of :class:`ComparisonRow` with price and delta comparisons.

    Raises:
        ImportError: If QuantLib is not installed.
    """
    from backtest_proofs.pricer.black_scholes import bs_greeks, bs_price

    rows: list[ComparisonRow] = []
    for i, spec in enumerate(scenarios):
        path = simulate_gbm(
            S0=spec.s0,
            mu=spec.r,
            sigma=spec.sigma,
            T=spec.t,
            n_steps=spec.n_steps,
            seed=seed + i * 10_000,
        )
        for step, (spot, t_elapsed) in enumerate(
            zip(path.prices, path.times, strict=True)
        ):
            t_rem = spec.t - t_elapsed
            if t_rem <= 1e-8:
                continue
            our_p = bs_price(
                S=spot,
                K=spec.k,
                T=t_rem,
                r=spec.r,
                sigma=spec.sigma,
                option_type="call",
            )
            our_g = bs_greeks(
                S=spot,
                K=spec.k,
                T=t_rem,
                r=spec.r,
                sigma=spec.sigma,
                option_type="call",
            )
            ql_price, ql_delta = _ql_bs_price_delta(
                S=spot,
                K=spec.k,
                T=t_rem,
                r=spec.r,
                sigma=spec.sigma,
            )
            rows.append(
                ComparisonRow(
                    scenario_idx=i,
                    step=step,
                    spot=spot,
                    t_rem=t_rem,
                    our_price=our_p.value,
                    ql_price=ql_price,
                    price_diff_bp=abs(our_p.value - ql_price)
                    * 10_000
                    / spec.s0,
                    our_delta=our_g.delta,
                    ql_delta=ql_delta,
                    delta_diff=abs(our_g.delta - ql_delta),
                )
            )
    return rows


def max_price_diff_bp(rows: list[ComparisonRow]) -> float:
    """Return the maximum ``price_diff_bp`` across all comparison rows."""
    if not rows:
        return 0.0
    return max(r.price_diff_bp for r in rows)


def within_threshold(rows: list[ComparisonRow], threshold_bp: float) -> bool:
    """Return ``True`` if all price differences are within *threshold_bp*.

    An empty *rows* list returns ``True`` (vacuously satisfied).
    """
    max_bp = max_price_diff_bp(rows)
    return math.isfinite(max_bp) and max_bp <= threshold_bp
