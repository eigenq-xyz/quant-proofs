"""Stress-window backtest runner for historical crisis periods.

Extracted from test_backtest.py so that both the test suite and the
Quarto paper can import ``run_stress_window`` without pulling in pytest.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd

_SERIES_KEYS = ["underlying_ticker", "expiry", "strike", "option_type"]


def run_stress_window(
    df: pd.DataFrame,
    date_start: str,
    date_end: str,
    r: float,
    label: str,
) -> tuple[list[float], int, int]:
    """Filter *df* to [date_start, date_end] and backtest every call series.

    Args:
        df: OptionMetrics dataframe with the columns loaded by
            :func:`backtest_proofs.etl.wrds_loader.optionmetrics_option_snapshots_from_df`.
        date_start: Inclusive start date, ``"YYYY-MM-DD"``.
        date_end: Inclusive end date, ``"YYYY-MM-DD"``.
        r: Continuously compounded risk-free rate for the window (annualised).
        label: Human-readable window label used in assertion messages.

    Returns:
        ``(ratios, n_obs, n_series)`` where *ratios* is the list of
        cost/premium per qualifying call series, *n_obs* is the number of
        option-day rows in the filtered window, and *n_series* is
        ``len(ratios)``.  Every step certificate is asserted to pass inline
        — a failure surfaces the series and date range immediately.
    """
    import pandas as pd

    from backtest_proofs.backtest.data_types import PricePath
    from backtest_proofs.backtest.runner import run_delta_hedge
    from backtest_proofs.etl.wrds_loader import (
        optionmetrics_option_snapshots_from_df,
    )
    from backtest_proofs.pricer.black_scholes import bs_price

    mask = (pd.to_datetime(df["date"]) >= date_start) & (
        pd.to_datetime(df["date"]) <= date_end
    )
    window = df[mask]

    ratios: list[float] = []
    for (_ticker, _expiry, strike, cp), group in window.groupby(_SERIES_KEYS):
        if cp != "call":
            continue
        group = group.sort_values("date")
        if len(group) < 5:
            continue
        snaps = optionmetrics_option_snapshots_from_df(group)
        if not snaps or any(s.underlying_price is None for s in snaps):
            continue
        first = snaps[0]
        und_prices_raw = [s.underlying_price for s in snaps]
        und_prices: list[float] = [p for p in und_prices_raw if p is not None]
        times = [
            (pd.Timestamp(s.date) - pd.Timestamp(first.date)).days / 365.0
            for s in snaps
        ]
        path = PricePath(times=times, prices=und_prices)
        if path.times[-1] <= 0:
            continue
        result = run_delta_hedge(
            path=path,
            K=float(strike),
            r=r,
            sigma=first.implied_vol,
            n_contracts=1,
        )
        failures = [c for c in result.certificates if not c.invariant_holds]
        assert failures == [], (
            f"{label}: {len(failures)} certificate(s) failed for "
            f"strike={strike} expiry={_expiry}"
        )
        premium = bs_price(
            S=und_prices[0],
            K=float(strike),
            T=path.times[-1],
            r=r,
            sigma=first.implied_vol,
            option_type="call",
        ).value
        if premium > 0:
            ratios.append(result.total_hedging_cost / premium)

    return ratios, len(window), len(ratios)
