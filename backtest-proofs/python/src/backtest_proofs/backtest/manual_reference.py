"""Manual Black-Scholes delta-hedge reference calculation.

This module implements the textbook delta-hedge procedure for a written
European call entirely in Python — no Lean FFI, no Strategy abstraction —
but using the **same basis-point integer arithmetic** as the FFI-backed
runner. Its purpose is to provide an *independent* reference against which
the FFI implementation can be cross-checked: the manual reference and the
FFI runner should agree exactly under identical conventions.

Why basis-point integers in the reference? The whole point of the
verified accounting layer is exact integer arithmetic at the ledger. If
the reference used floats, any disagreement with the FFI runner would
be dominated by precision mismatch rather than by genuine algorithmic
differences. Using basis points throughout makes the comparison sharp:
remaining discrepancies (if any) reflect real differences in procedure,
not rounding noise.

Convention notes (matched to the FFI runner):

* Cash, prices, fees, and option values are stored as ``Int`` basis
  points (``$1 = 10_000`` basis points). The :func:`bs_price` and
  :func:`bs_greeks` functions from ``quant_core.pricer`` are used for
  the float-to-bp conversion of option values and deltas.
* Share quantities are integer numbers of shares, rounded from
  ``delta * n_contracts`` at each rebalance.
* Interest accrues on the cash balance between rebalances but **not**
  between the final rebalance and option expiry — settlement is
  treated as instantaneous at the last rebalance time, matching
  :func:`backtest_proofs.backtest.runner.run_delta_hedge`.
* At expiry the writer pays the call payoff ``max(S_T - K, 0) *
  n_contracts`` to the holder and liquidates the remaining share
  position at ``S_T``.

The :class:`ManualHedgeResult` returns a step-by-step NAV series in
basis points so the caller can compare it pointwise to
:attr:`DeltaHedgeResult.portfolio_values`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from backtest_proofs.backtest.data_types import PricePath
from quant_core.pricer.black_scholes import bs_greeks, bs_price
from quant_core.pricer.conventions import to_bp


@dataclass(frozen=True)
class ManualHedgeResult:
    """Step-by-step output of the manual reference hedge.

    Attributes:
        portfolio_values: NAV at each step in basis points (NAV at t=0
            equals zero by construction). Length ``n_steps + 1``.
        deltas: Black-Scholes call delta at each rebalance point.
        shares: Integer share holdings at each step.
        cash_bp: Cash balance at each step in basis points.
        total_hedging_cost: ``(C_0 * n_contracts - final NAV)`` in dollars.
    """

    portfolio_values: list[int]
    deltas: list[float]
    shares: list[int]
    cash_bp: list[int]
    total_hedging_cost: float


def manual_hedge_reference(
    path: PricePath,
    k: float,
    r: float,
    sigma: float,
    n_contracts: int,
) -> ManualHedgeResult:
    """Replay a delta-hedge for a written European call by hand in basis points.

    This routine reimplements the delta-hedge loop independently of the
    Lean-FFI runner so the two can be compared point-by-point. It uses
    the same numeric conventions as the runner (integer basis points
    throughout, integer shares, same expiry-instantaneity convention).

    Procedure:

    1. At ``t = 0``: receive premium ``round(C_0 * n_contracts * 10_000)``
       basis points; buy ``round(Delta_0 * n_contracts)`` shares funded by
       ``round(shares * S_0 * 10_000)`` basis points of cash outflow.
    2. At each rebalance ``i = 1, ..., n_steps - 1``: accrue interest
       on the cash balance over ``Delta t``, recompute Delta, and trade
       ``(new_shares - old_shares)`` shares at the current spot.
    3. At expiry ``i = n_steps``: settle the option (cash debit
       ``max(S_T - K, 0) * n_contracts``), liquidate the remaining
       share position at ``S_T``. No interest accrues over the final
       ``Delta t`` — matches the runner's convention.

    Args:
        path: Underlying price path. ``path.times`` in years, ``path.prices``
            in dollars; first time is 0 and last time is the maturity ``T``.
        k: Strike price in dollars.
        r: Continuously compounded risk-free rate, annualised.
        sigma: Black-Scholes volatility, annualised.
        n_contracts: Number of written call contracts (positive integer).

    Returns:
        :class:`ManualHedgeResult` with the step-by-step NAV series in
        basis points, the deltas and shares at each step, the cash
        balance, and the total hedging cost.
    """
    times = list(path.times)
    prices = list(path.prices)
    n_steps = len(prices) - 1
    if n_steps < 1:
        raise ValueError("path must have at least two time points")
    t_expiry = times[-1]

    # t = 0: receive premium, buy initial delta shares
    s0 = prices[0]
    tau0 = t_expiry - times[0]
    c0 = bs_price(S=s0, K=k, T=tau0, r=r, sigma=sigma, option_type="call")
    g0 = bs_greeks(S=s0, K=k, T=tau0, r=r, sigma=sigma, option_type="call")
    delta0 = g0.delta

    premium_bp = c0.value_bp * n_contracts
    shares = round(delta0 * n_contracts)
    cash_bp = premium_bp - shares * to_bp(s0)

    call_mark_bp = c0.value_bp
    pv0 = cash_bp + shares * to_bp(s0) - n_contracts * call_mark_bp

    portfolio_values = [pv0]
    deltas = [delta0]
    share_series = [shares]
    cash_series = [cash_bp]

    for i in range(1, n_steps + 1):
        dt_step = times[i] - times[i - 1]
        s = prices[i]
        tau = max(t_expiry - times[i], 0.0)
        spot_bp = to_bp(s)

        if i < n_steps:
            # Accrue interest, then rebalance
            cash_bp = int(round(cash_bp * float(np.exp(r * dt_step))))
            g = bs_greeks(
                S=s, K=k, T=tau, r=r, sigma=sigma, option_type="call"
            )
            new_shares = round(g.delta * n_contracts)
            trade_size = new_shares - shares
            cash_bp -= trade_size * spot_bp
            shares = new_shares

            c_now = bs_price(
                S=s, K=k, T=tau, r=r, sigma=sigma, option_type="call"
            )
            call_mark_bp = c_now.value_bp
            pv = cash_bp + shares * spot_bp - n_contracts * call_mark_bp
            new_delta = g.delta
        else:
            # Expiry: no interest accrual (matches runner convention)
            payoff_per_contract_bp = max(spot_bp - to_bp(k), 0)
            cash_bp -= payoff_per_contract_bp * n_contracts
            cash_bp += shares * spot_bp
            shares = 0
            pv = cash_bp
            new_delta = 1.0 if s > k else 0.0

        portfolio_values.append(pv)
        deltas.append(new_delta)
        share_series.append(shares)
        cash_series.append(cash_bp)

    initial_premium_bp = premium_bp
    final_pv_bp = portfolio_values[-1]
    total_cost = (initial_premium_bp - final_pv_bp) / 10_000.0

    return ManualHedgeResult(
        portfolio_values=portfolio_values,
        deltas=deltas,
        shares=share_series,
        cash_bp=cash_series,
        total_hedging_cost=float(total_cost),
    )
