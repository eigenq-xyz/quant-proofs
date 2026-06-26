"""Variance Risk Premium (VRP) delta-hedged short-volatility study (Stage 1).

A literature-grounded short-volatility / variance-risk-premium study on the S&P 500
index, built entirely on free data (FRED VIX, Yahoo SPX, FRED 3-month T-bill).

Economic thesis
---------------
Implied variance (VIX^2) systematically exceeds subsequently realized variance:
the *variance risk premium* (Bollerslev-Tauchen-Zhou 2009, Carr-Wu 2009). A
seller of index volatility who delta-hedges the directional exposure harvests
this premium, at the cost of severe negative skew (Coval-Shumway 2001): the
short-vol payoff is short the tail, and tails arrive in crises.

Strategy (Stage 1, simulated)
-----------------------------
Each month, sell a 30-day at-the-money straddle on the index, priced with
Black-Scholes using VIX as the implied volatility input, and delta-hedge on a
configurable schedule. An ATM straddle has delta ~ 0 at inception, so the
residual delta hedged with the index is small; the position is short gamma /
short vega. The delta-hedged short-straddle P&L over the holding period equals
(in the BS replication limit) the integrated *implied minus realized variance*,
scaled by the dollar-gamma of the straddle. We implement the standard discrete
delta-hedging P&L for rigor rather than relying on the closed-form approximation.

Realistic frictions (this revision)
------------------------------------
The original Stage-1 engine charged transaction cost only on the option premium
(0.5% round-trip) and left the ~21 daily stock rebalances frictionless, which
inflated the net Sharpe to ~2.9 (literature VRP Sharpes are ~0.5 to 1.0). This
revision adds three realistic frictions, each configurable in ``HedgeConfig``:

1. **Per-rebalance hedge cost.** Every change in the stock hedge (the initial
   hedge, each intermediate rebalance, and the final liquidation) is charged a
   proportional cost ``tc_hedge_bps * |d_shares| * S_k``. The default sweep runs
   1, 2, 5, and 10 bps per rebalance.
2. **Entry half-spread.** The straddle is sold at a bid below the VIX-implied
   mid: ``premium_received = mid * (1 - entry_half_spread)``. The default
   headline assumes a 1% half-spread.
3. **Hedge frequency.** Daily, every-2-days, or weekly rebalancing. Less frequent
   hedging lowers turnover cost but raises hedging error (residual gamma P&L
   between rebalances); the study reports the tradeoff.

The closing-leg cost on the option (buying back at the offer) is folded into a
round-trip option spread: ``tc_option_roundtrip`` charges the modeled premium
spread once at close, complementing the entry half-spread.

Black-Scholes pricing/Greeks here are an inline re-implementation of the verified
primitives in ``foundations/quant-core/python/src/quant_core/pricer/black_scholes.py``
(``bs_price``, ``bs_greeks``). We inline to keep this study a single dependency-light
file; the quant-core module is the verified reference.

Signal F_t-measurability
------------------------
The VRP signal at month t is a function of VIX and realized returns observed up to
and including t, so it is F_t-measurable (no look-ahead). This is machine-checked,
sorry-free, by ``vrpSignal_adapted`` in
``research-pipeline/lean/ResearchPipeline/Measurability.lean``: because the signal reads
two observable processes (prices, via the trailing realized variance, and the squared
VIX), it is adapted to any filtration carrying both, the joint market-information
filtration. The statistical and P&L layers below are empirical and unverified.

Methodology
-----------
- In-sample (IS): 1990-2009. Out-of-sample (OOS): 2010-2025. Declared upfront.
- Transaction costs: per-rebalance bps on the stock hedge + an entry half-spread
  and a round-trip option spread on the straddle. Gross and net reported.
- Benchmarks: long index (buy & hold) and static short straddle WITHOUT delta
  hedging, to isolate the hedging contribution.
- Reported per sample: annualized mean return, Sharpe, max drawdown, skew,
  kurtosis, Newey-West HAC t-stat, and VRP-signal vs forward-return correlation.
- Cost sensitivity: net Sharpe vs per-rebalance bps, and vs hedge frequency.

Usage
-----
    python3.12 research-pipeline/studies/vrp/run_study.py
"""

from __future__ import annotations

import io
import json
import math
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

import numpy as np
import pandas as pd
from scipy.stats import norm

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #

IS_START = "1990-01-01"
IS_END = "2009-12-31"
OOS_START = "2010-01-01"
OOS_END = "2025-12-31"

TRADING_DAYS = 252
RV_WINDOW = 21  # trading days for realized variance
HOLD_DAYS = 21  # ~30 calendar days, one trading month
TENOR_YEARS = 30.0 / 365.0  # option tenor at inception

RESULTS_DIR = Path(__file__).parent / "results"


@dataclass(frozen=True)
class HedgeConfig:
    """Friction and rebalancing configuration for one backtest run.

    Parameters
    ----------
    tc_hedge_bps:
        Proportional transaction cost charged on each stock-hedge trade, in basis
        points of traded notional: ``cost = (tc_hedge_bps / 1e4) * |d_shares| * S``.
        Applied to the initial hedge, every rebalance, and the final liquidation.
    entry_half_spread:
        Fraction of the Black-Scholes mid by which the sale price of the straddle
        sits below mid at entry (the seller crosses the half-spread). The premium
        received is ``mid * (1 - entry_half_spread)``.
    tc_option_roundtrip:
        Fraction of the entry mid charged once at close, modeling the cost of
        buying the straddle back at the offer (the other half of the option
        round-trip). Set to ``2 * entry_half_spread`` for a symmetric round-trip
        when the close mid is comparable to entry; here it is parameterized
        independently and applied to the entry premium for simplicity.
    rebalance_every:
        Hedge rebalancing interval in trading days. ``1`` = daily, ``2`` =
        every two days, ``5`` = weekly. The hedge is also squared up at expiry
        regardless of the schedule.
    label:
        Human-readable name for reporting.
    """

    tc_hedge_bps: float = 2.0
    entry_half_spread: float = 0.01
    tc_option_roundtrip: float = 0.005
    rebalance_every: int = 1
    label: str = "headline"


# Headline assumption: 2 bps/rebalance, 1% entry half-spread, daily hedge.
HEADLINE = HedgeConfig(
    tc_hedge_bps=2.0,
    entry_half_spread=0.01,
    tc_option_roundtrip=0.005,
    rebalance_every=1,
    label="headline (2bps/reb, 1% half-spread, daily)",
)


# --------------------------------------------------------------------------- #
# Black-Scholes (inline; verified reference: quant_core.pricer.black_scholes)
# --------------------------------------------------------------------------- #


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float) -> tuple[float, float]:
    vol_sqrt_t = sigma * math.sqrt(T)
    d1 = (math.log(S / K) + (r + 0.5 * sigma**2) * T) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return d1, d2


def bs_call_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """European call price. Mirrors quant_core.pricer.black_scholes.bs_price."""
    if T <= 0:
        return max(S - K, 0.0)
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    return float(S * norm.cdf(d1) - K * math.exp(-r * T) * norm.cdf(d2))


def bs_put_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """European put price. Mirrors quant_core.pricer.black_scholes.bs_price."""
    if T <= 0:
        return max(K - S, 0.0)
    d1, d2 = _d1_d2(S, K, T, r, sigma)
    return float(K * math.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1))


def bs_call_delta(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Call delta. Mirrors quant_core.pricer.black_scholes.bs_greeks."""
    if T <= 0:
        return 1.0 if S > K else 0.0
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return float(norm.cdf(d1))


def bs_put_delta(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Put delta. Mirrors quant_core.pricer.black_scholes.bs_greeks."""
    if T <= 0:
        return -1.0 if S < K else 0.0
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return float(norm.cdf(d1) - 1.0)


def straddle_price(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return bs_call_price(S, K, T, r, sigma) + bs_put_price(S, K, T, r, sigma)


def straddle_delta(S: float, K: float, T: float, r: float, sigma: float) -> float:
    return bs_call_delta(S, K, T, r, sigma) + bs_put_delta(S, K, T, r, sigma)


# --------------------------------------------------------------------------- #
# Data loading (free sources, no API key)
# --------------------------------------------------------------------------- #


def _fred_csv(series_id: str) -> pd.Series:
    """Load a FRED series via the public CSV endpoint (no API key)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310
        raw = resp.read().decode("utf-8")
    df = pd.read_csv(io.StringIO(raw))
    date_col, val_col = df.columns[0], df.columns[1]
    df[date_col] = pd.to_datetime(df[date_col])
    df[val_col] = pd.to_numeric(df[val_col], errors="coerce")
    s = df.set_index(date_col)[val_col].dropna()
    s.name = series_id
    return s


def load_data() -> pd.DataFrame:
    """Build the daily panel: SPX close, VIX close, risk-free rate."""
    import yfinance as yf  # type: ignore[import-untyped]

    spx_raw = yf.download(
        "^GSPC", start=IS_START, end="2026-06-01", progress=False, auto_adjust=True
    )
    if spx_raw is None or spx_raw.empty:
        raise RuntimeError("yfinance returned no SPX data")
    # yfinance returns MultiIndex columns (field, ticker); flatten to Close.
    if isinstance(spx_raw.columns, pd.MultiIndex):
        spx = spx_raw["Close"]["^GSPC"]
    else:
        spx = spx_raw["Close"]
    spx = spx.astype(float)
    spx.index = pd.to_datetime(spx.index).tz_localize(None)
    spx.name = "spx"

    vix = _fred_csv("VIXCLS")
    vix.name = "vix"

    rf = _fred_csv("DTB3")  # 3-month T-bill, percent annualized
    rf.name = "rf"

    panel = pd.concat([spx, vix, rf], axis=1)
    panel = panel.loc[panel.index >= pd.Timestamp(IS_START)]
    # SPX and VIX must both exist; forward-fill risk-free across non-print days.
    panel["rf"] = panel["rf"].ffill()
    panel = panel.dropna(subset=["spx", "vix"])
    panel["rf"] = panel["rf"].ffill().fillna(2.0)
    return cast("pd.DataFrame", panel)


# --------------------------------------------------------------------------- #
# Signal and backtest
# --------------------------------------------------------------------------- #


@dataclass
class MonthTrade:
    entry_date: str
    sample: str  # "IS" or "OOS"
    vrp: float  # implied var - realized var (monthly units), the signal
    fwd_realized_var: float  # realized variance over the holding month (monthly)
    implied_var: float  # VIX^2 scaled to the holding month
    notional: float
    premium: float  # premium received at entry (net of entry half-spread)
    hedge_cost: float  # total stock-hedge transaction cost over the month
    option_cost: float  # entry half-spread + round-trip option spread (dollars)
    pnl_hedged_gross: float  # before any transaction cost
    pnl_hedged_net: float  # after hedge + option costs
    pnl_static_gross: float  # short straddle, NO delta hedge
    index_ret: float  # long-index buy & hold return over the month


def realized_variance_annualized(log_rets: np.ndarray) -> float:
    """Annualized realized variance from daily log returns (sum-of-squares form)."""
    return float(np.sum(log_rets**2) * (TRADING_DAYS / len(log_rets)))


def run_backtest(panel: pd.DataFrame, cfg: HedgeConfig) -> list[MonthTrade]:
    """Monthly delta-hedged short-straddle backtest with realistic frictions.

    Parameters
    ----------
    panel:
        Daily panel with columns ``spx``, ``vix``, ``rf`` (rf in percent).
    cfg:
        Friction and rebalancing configuration.
    """
    px = panel["spx"].to_numpy()
    vix = panel["vix"].to_numpy()
    rf = (panel["rf"].to_numpy()) / 100.0  # percent -> decimal
    dates = panel.index
    log_ret = np.diff(np.log(px), prepend=np.log(px[0]))

    tc_hedge = cfg.tc_hedge_bps / 1e4  # bps -> fraction of notional

    trades: list[MonthTrade] = []
    n = len(px)
    # Month entry points: every HOLD_DAYS, after the RV warmup window.
    start = RV_WINDOW
    for t in range(start, n - HOLD_DAYS, HOLD_DAYS):
        entry = dates[t]
        sample = "IS" if entry <= pd.Timestamp(IS_END) else "OOS"

        S0 = float(px[t])
        sigma = float(vix[t]) / 100.0  # VIX is percent annualized vol
        r0 = float(rf[t])
        if sigma <= 0 or not math.isfinite(sigma):
            continue

        # Signal: VRP(t) = implied var (monthly) - trailing realized var (monthly).
        implied_var_ann = sigma**2
        trailing_rv_ann = realized_variance_annualized(log_ret[t - RV_WINDOW + 1 : t + 1])
        vrp_monthly = (implied_var_ann - trailing_rv_ann) * (HOLD_DAYS / TRADING_DAYS)
        implied_var_monthly = implied_var_ann * (HOLD_DAYS / TRADING_DAYS)

        # Notional: scale to 1 unit of index ($1 of index exposure per straddle).
        K = S0  # ATM
        notional = 1.0 / S0  # number of straddles so that S0 * notional = $1 exposure

        mid0 = straddle_price(S0, K, TENOR_YEARS, r0, sigma) * notional
        # Sell at the bid: premium received is below the BS mid by the half-spread.
        premium0 = mid0 * (1.0 - cfg.entry_half_spread)

        # --- Discrete delta hedging over the holding month -------------------
        # We are SHORT the straddle. Hold a stock position = +straddle_delta so
        # the net position is delta-flat. Rebalance every ``cfg.rebalance_every``
        # trading days; each hedge trade pays a proportional cost.
        cash = premium0  # premium received, invested at the risk-free rate
        hedge_cost = 0.0
        T_left = TENOR_YEARS
        stock_pos = straddle_delta(S0, K, T_left, r0, sigma) * notional
        cash -= stock_pos * S0  # buy the initial hedge
        hedge_cost += tc_hedge * abs(stock_pos) * S0  # cost on the initial hedge

        dt = 1.0 / TRADING_DAYS
        for k in range(1, HOLD_DAYS + 1):
            tk = t + k
            Sk = float(px[tk])
            sig_k = float(vix[tk]) / 100.0
            rk = float(rf[tk])
            if sig_k <= 0 or not math.isfinite(sig_k):
                sig_k = sigma
            cash *= math.exp(rk * dt)  # accrue interest
            T_left = max(TENOR_YEARS - k * dt, 1e-6)
            # Rebalance only on the schedule (and never on the last step; expiry
            # liquidation handles the close).
            if k < HOLD_DAYS and (k % cfg.rebalance_every == 0):
                new_delta = straddle_delta(Sk, K, T_left, rk, sig_k) * notional
                d_shares = new_delta - stock_pos
                cash -= d_shares * Sk  # rebalance hedge
                hedge_cost += tc_hedge * abs(d_shares) * Sk  # cost on the rebalance
                stock_pos = new_delta

        # Settle at expiry: buy back the straddle (close short) and liquidate stock.
        ST = float(px[t + HOLD_DAYS])
        straddle_payoff = (max(ST - K, 0.0) + max(K - ST, 0.0)) * notional
        cash += stock_pos * ST  # liquidate hedge
        hedge_cost += tc_hedge * abs(stock_pos) * ST  # cost to unwind the hedge
        cash -= straddle_payoff  # close the short straddle at intrinsic value
        pnl_hedged_gross = cash  # before any transaction cost

        # Option cost: round-trip spread on the straddle (the closing leg). The
        # entry half-spread is already reflected in premium0; charge the other
        # leg here so net P&L reflects a full option round-trip.
        option_cost = cfg.tc_option_roundtrip * mid0
        pnl_hedged_net = pnl_hedged_gross - hedge_cost - option_cost

        # --- Static short straddle (NO delta hedge) --------------------------
        # Receive premium (grown at rf), pay intrinsic at expiry. No stock.
        cash_static = mid0 * math.exp(r0 * (HOLD_DAYS / TRADING_DAYS))
        cash_static -= straddle_payoff
        pnl_static_gross = cash_static

        index_ret = ST / S0 - 1.0

        trades.append(
            MonthTrade(
                entry_date=str(entry.date()),
                sample=sample,
                vrp=vrp_monthly,
                fwd_realized_var=realized_variance_annualized(log_ret[t + 1 : t + HOLD_DAYS + 1])
                * (HOLD_DAYS / TRADING_DAYS),
                implied_var=implied_var_monthly,
                notional=notional,
                premium=premium0,
                hedge_cost=hedge_cost,
                option_cost=option_cost,
                pnl_hedged_gross=pnl_hedged_gross,
                pnl_hedged_net=pnl_hedged_net,
                pnl_static_gross=pnl_static_gross,
                index_ret=index_ret,
            )
        )
    return trades


# --------------------------------------------------------------------------- #
# Statistics
# --------------------------------------------------------------------------- #


def newey_west_tstat(x: np.ndarray, lags: int = 3) -> float:
    """Newey-West HAC t-stat for the mean of a return series."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    if n < 2:
        return float("nan")
    mu = x.mean()
    e = x - mu
    gamma0 = np.dot(e, e) / n
    var = gamma0
    for lag in range(1, lags + 1):
        w = 1.0 - lag / (lags + 1)
        cov = np.dot(e[lag:], e[:-lag]) / n
        var += 2.0 * w * cov
    se = math.sqrt(var / n)
    return float(mu / se) if se > 0 else float("nan")


def max_drawdown(returns: np.ndarray) -> float:
    """Max drawdown of a compounded equity curve from a return series."""
    curve = np.cumprod(1.0 + returns)
    peak = np.maximum.accumulate(curve)
    dd = curve / peak - 1.0
    return float(dd.min())


def sharpe(returns: np.ndarray, periods_per_year: float) -> float:
    """Annualized Sharpe of a per-period return series (zero benchmark)."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if len(r) < 2:
        return float("nan")
    sd = r.std(ddof=1)
    if sd <= 0:
        return float("nan")
    return float((r.mean() * periods_per_year) / (sd * math.sqrt(periods_per_year)))


def summarize(returns: np.ndarray, periods_per_year: float) -> dict[str, float]:
    """Annualized stats for a monthly return series."""
    r = np.asarray(returns, dtype=float)
    r = r[np.isfinite(r)]
    if len(r) == 0:
        return {}
    mu = r.mean()
    sd = r.std(ddof=1) if len(r) > 1 else float("nan")
    ann_ret = mu * periods_per_year
    ann_vol = sd * math.sqrt(periods_per_year)
    shp = ann_ret / ann_vol if ann_vol > 0 else float("nan")
    from scipy.stats import kurtosis, skew

    return {
        "n_months": int(len(r)),
        "mean_monthly": float(mu),
        "ann_return": float(ann_ret),
        "ann_vol": float(ann_vol),
        "sharpe": float(shp),
        "max_drawdown": max_drawdown(r),
        "skew": float(skew(r)),
        "excess_kurtosis": float(kurtosis(r)),
        "nw_tstat": newey_west_tstat(r),
        "min_month": float(r.min()),
    }


def analyze(trades: list[MonthTrade], cfg: HedgeConfig) -> dict[str, object]:
    df = pd.DataFrame([asdict(t) for t in trades])
    ppy = TRADING_DAYS / HOLD_DAYS  # ~12 holding periods per year

    out: dict[str, object] = {
        "config": {
            "is_window": [IS_START, IS_END],
            "oos_window": [OOS_START, OOS_END],
            "rv_window_days": RV_WINDOW,
            "hold_days": HOLD_DAYS,
            "tenor_years": TENOR_YEARS,
            "tc_hedge_bps": cfg.tc_hedge_bps,
            "entry_half_spread": cfg.entry_half_spread,
            "tc_option_roundtrip": cfg.tc_option_roundtrip,
            "rebalance_every": cfg.rebalance_every,
            "n_trades": int(len(df)),
            "periods_per_year": ppy,
        }
    }

    for sample in ("IS", "OOS", "ALL"):
        sub = df if sample == "ALL" else df[df["sample"] == sample]
        if sub.empty:
            continue
        # Return per period = P&L per $1 index exposure (already normalized).
        out[sample] = {
            "hedged_short_vol_gross": summarize(sub["pnl_hedged_gross"].to_numpy(), ppy),
            "hedged_short_vol_net": summarize(sub["pnl_hedged_net"].to_numpy(), ppy),
            "static_short_straddle": summarize(sub["pnl_static_gross"].to_numpy(), ppy),
            "long_index_bh": summarize(sub["index_ret"].to_numpy(), ppy),
            "vrp_signal_vs_fwd_realized_corr": float(
                np.corrcoef(sub["vrp"], sub["fwd_realized_var"])[0, 1]
            ),
            "vrp_signal_vs_hedged_pnl_corr": float(
                np.corrcoef(sub["vrp"], sub["pnl_hedged_net"])[0, 1]
            ),
            "mean_vrp_monthly": float(sub["vrp"].mean()),
            "pct_vrp_positive": float((sub["vrp"] > 0).mean()),
            "mean_hedge_cost": float(sub["hedge_cost"].mean()),
            "mean_option_cost": float(sub["option_cost"].mean()),
        }

    # Worst months (crisis identification).
    worst = df.nsmallest(5, "pnl_hedged_net")[["entry_date", "pnl_hedged_net", "index_ret"]]
    out["worst_5_hedged_months"] = worst.to_dict(orient="records")
    return out


# --------------------------------------------------------------------------- #
# Sensitivity sweeps
# --------------------------------------------------------------------------- #


@dataclass
class SweepRow:
    """One sensitivity-sweep cell: net Sharpe / return by sample under a config."""

    label: str
    tc_hedge_bps: float
    entry_half_spread: float
    rebalance_every: int
    is_sharpe: float
    oos_sharpe: float
    is_ann_return: float
    oos_ann_return: float
    is_skew: float
    oos_skew: float
    mean_hedge_cost: float = field(default=float("nan"))


def _split_returns(trades: list[MonthTrade]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    df = pd.DataFrame([asdict(t) for t in trades])
    is_r = df.loc[df["sample"] == "IS", "pnl_hedged_net"].to_numpy()
    oos_r = df.loc[df["sample"] == "OOS", "pnl_hedged_net"].to_numpy()
    hc = df["hedge_cost"].to_numpy()
    return is_r, oos_r, hc


def sweep_one(panel: pd.DataFrame, cfg: HedgeConfig) -> SweepRow:
    """Run the backtest under ``cfg`` and reduce to a sweep row."""
    from scipy.stats import skew as _skew

    ppy = TRADING_DAYS / HOLD_DAYS
    trades = run_backtest(panel, cfg)
    is_r, oos_r, hc = _split_returns(trades)
    return SweepRow(
        label=cfg.label,
        tc_hedge_bps=cfg.tc_hedge_bps,
        entry_half_spread=cfg.entry_half_spread,
        rebalance_every=cfg.rebalance_every,
        is_sharpe=sharpe(is_r, ppy),
        oos_sharpe=sharpe(oos_r, ppy),
        is_ann_return=float(is_r.mean() * ppy),
        oos_ann_return=float(oos_r.mean() * ppy),
        is_skew=float(_skew(is_r)),
        oos_skew=float(_skew(oos_r)),
        mean_hedge_cost=float(np.mean(hc)),
    )


def cost_sweep(panel: pd.DataFrame) -> list[SweepRow]:
    """Sweep per-rebalance hedge cost (bps) at the headline half-spread / freq."""
    rows: list[SweepRow] = []
    for bps in (0.0, 1.0, 2.0, 5.0, 10.0):
        cfg = HedgeConfig(
            tc_hedge_bps=bps,
            entry_half_spread=HEADLINE.entry_half_spread,
            tc_option_roundtrip=HEADLINE.tc_option_roundtrip,
            rebalance_every=1,
            label=f"{bps:g}bps/reb, 1% half-spread, daily",
        )
        rows.append(sweep_one(panel, cfg))
    return rows


def frequency_sweep(panel: pd.DataFrame) -> list[SweepRow]:
    """Sweep hedge frequency (daily / 2-day / weekly) at headline costs."""
    rows: list[SweepRow] = []
    for every, name in ((1, "daily"), (2, "every 2 days"), (5, "weekly")):
        cfg = HedgeConfig(
            tc_hedge_bps=HEADLINE.tc_hedge_bps,
            entry_half_spread=HEADLINE.entry_half_spread,
            tc_option_roundtrip=HEADLINE.tc_option_roundtrip,
            rebalance_every=every,
            label=f"2bps/reb, 1% half-spread, {name}",
        )
        rows.append(sweep_one(panel, cfg))
    return rows


def half_spread_sweep(panel: pd.DataFrame) -> list[SweepRow]:
    """Sweep entry half-spread (1-3% of premium) at headline cost / freq."""
    rows: list[SweepRow] = []
    for hs in (0.0, 0.01, 0.02, 0.03):
        cfg = HedgeConfig(
            tc_hedge_bps=HEADLINE.tc_hedge_bps,
            entry_half_spread=hs,
            tc_option_roundtrip=2.0 * hs,
            rebalance_every=1,
            label=f"2bps/reb, {hs:.0%} half-spread, daily",
        )
        rows.append(sweep_one(panel, cfg))
    return rows


def combined_sweep(panel: pd.DataFrame) -> list[SweepRow]:
    """Joint friction scenarios: higher per-rebalance cost AND a wide option spread,
    charged together. The bps and half-spread sweeps each hold the other friction light,
    so they only bracket a realistic combination; these rows compute it directly. The
    round-trip option spread is twice the entry half-spread (a symmetric close)."""
    rows: list[SweepRow] = []
    for bps, hs in ((5.0, 0.03), (10.0, 0.05)):
        cfg = HedgeConfig(
            tc_hedge_bps=bps,
            entry_half_spread=hs,
            tc_option_roundtrip=2.0 * hs,
            rebalance_every=1,
            label=f"{bps:.0f}bps/reb, {hs:.0%} half-spread, daily",
        )
        rows.append(sweep_one(panel, cfg))
    return rows


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #


def main() -> None:
    print("Loading free data (FRED VIX/DTB3, Yahoo SPX)...")
    panel = load_data()
    print(
        f"  panel: {len(panel)} daily rows, "
        f"{panel.index.min().date()} -> {panel.index.max().date()}"
    )

    print(f"Running headline backtest [{HEADLINE.label}]...")
    trades = run_backtest(panel, HEADLINE)
    print(f"  {len(trades)} monthly trades")

    results = analyze(trades, HEADLINE)

    print("Running cost / frequency / half-spread sensitivity sweeps...")
    cost_rows = cost_sweep(panel)
    freq_rows = frequency_sweep(panel)
    hs_rows = half_spread_sweep(panel)
    combined_rows = combined_sweep(panel)
    results["cost_sweep"] = [asdict(r) for r in cost_rows]
    results["frequency_sweep"] = [asdict(r) for r in freq_rows]
    results["half_spread_sweep"] = [asdict(r) for r in hs_rows]
    results["combined_sweep"] = [asdict(r) for r in combined_rows]

    results["generated_utc"] = datetime.now(UTC).isoformat()
    results["headline_config"] = asdict(HEADLINE)
    results["data_sources"] = {
        "spx": "Yahoo Finance ^GSPC (auto_adjust)",
        "vix": "FRED VIXCLS (public CSV, no key)",
        "rf": "FRED DTB3 3M T-bill (public CSV, no key)",
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "results_vrp.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    # Persist the per-trade panel too, for inspection.
    pd.DataFrame([asdict(t) for t in trades]).to_csv(RESULTS_DIR / "vrp_trades.csv", index=False)

    print(f"\nWrote {out_path}\n")
    _print_report(results, cost_rows, freq_rows, hs_rows, combined_rows)


def _fmt(d: dict[str, float], key: str) -> str:
    v = d.get(key, float("nan"))
    return f"{v:.4f}" if isinstance(v, float) else str(v)


def _print_report(
    results: dict[str, object],
    cost_rows: list[SweepRow],
    freq_rows: list[SweepRow],
    hs_rows: list[SweepRow],
    combined_rows: list[SweepRow],
) -> None:
    print("=" * 78)
    print("VRP DELTA-HEDGED SHORT-VOLATILITY STUDY: SUMMARY (realistic frictions)")
    print(f"Headline: {HEADLINE.label}")
    print("=" * 78)
    for sample in ("IS", "OOS"):
        if sample not in results:
            continue
        s = cast("dict[str, object]", results[sample])
        print(f"\n[{sample}]  ({'1990-2009' if sample == 'IS' else '2010-2025'})")
        for strat in (
            "hedged_short_vol_net",
            "hedged_short_vol_gross",
            "static_short_straddle",
            "long_index_bh",
        ):
            st = cast("dict[str, float]", s[strat])
            print(
                f"  {strat:26s} ann_ret={_fmt(st, 'ann_return'):>9} "
                f"Sharpe={_fmt(st, 'sharpe'):>8} maxDD={_fmt(st, 'max_drawdown'):>9} "
                f"skew={_fmt(st, 'skew'):>8} kurt={_fmt(st, 'excess_kurtosis'):>8} "
                f"NW_t={_fmt(st, 'nw_tstat'):>7}"
            )
        corr = cast("float", s["vrp_signal_vs_fwd_realized_corr"])
        mvrp = cast("float", s["mean_vrp_monthly"])
        ppos = cast("float", s["pct_vrp_positive"])
        hc = cast("float", s["mean_hedge_cost"])
        oc = cast("float", s["mean_option_cost"])
        print(
            f"  VRP signal vs fwd realized-var corr: {corr:.3f}  "
            f"mean monthly VRP: {mvrp:.5f}  %VRP>0: {ppos:.1%}"
        )
        print(
            f"  mean hedge cost/trade: {hc:.5f}  "
            f"mean option cost/trade: {oc:.5f}  (per $1 exposure)"
        )

    print("\nCOST SENSITIVITY (net Sharpe vs per-rebalance bps; 1% half-spread, daily):")
    print(
        f"  {'bps/reb':>8} {'IS Sharpe':>10} {'OOS Sharpe':>11} "
        f"{'IS ann':>8} {'OOS ann':>8} {'hedge$':>8}"
    )
    for r in cost_rows:
        print(
            f"  {r.tc_hedge_bps:>8.0f} {r.is_sharpe:>10.2f} {r.oos_sharpe:>11.2f} "
            f"{r.is_ann_return:>8.1%} {r.oos_ann_return:>8.1%} {r.mean_hedge_cost:>8.5f}"
        )

    print("\nFREQUENCY SENSITIVITY (2bps/reb, 1% half-spread):")
    print(
        f"  {'schedule':>14} {'IS Sharpe':>10} {'OOS Sharpe':>11} "
        f"{'IS ann':>8} {'OOS ann':>8} {'hedge$':>8}"
    )
    names = {1: "daily", 2: "every 2 days", 5: "weekly"}
    for r in freq_rows:
        print(
            f"  {names.get(r.rebalance_every, str(r.rebalance_every)):>14} "
            f"{r.is_sharpe:>10.2f} {r.oos_sharpe:>11.2f} "
            f"{r.is_ann_return:>8.1%} {r.oos_ann_return:>8.1%} {r.mean_hedge_cost:>8.5f}"
        )

    print("\nHALF-SPREAD SENSITIVITY (2bps/reb, daily):")
    print(
        f"  {'half-spread':>12} {'IS Sharpe':>10} {'OOS Sharpe':>11} {'IS ann':>8} {'OOS ann':>8}"
    )
    for r in hs_rows:
        print(
            f"  {r.entry_half_spread:>12.0%} {r.is_sharpe:>10.2f} {r.oos_sharpe:>11.2f} "
            f"{r.is_ann_return:>8.1%} {r.oos_ann_return:>8.1%}"
        )

    print("\nCOMBINED FRICTION (higher hedge cost AND wide option spread, daily):")
    print(f"  {'config':>26} {'IS Sharpe':>10} {'OOS Sharpe':>11} {'IS ann':>8} {'OOS ann':>8}")
    for r in combined_rows:
        print(
            f"  {r.label:>26} {r.is_sharpe:>10.2f} {r.oos_sharpe:>11.2f} "
            f"{r.is_ann_return:>8.1%} {r.oos_ann_return:>8.1%}"
        )

    print("\nWorst 5 hedged months (net P&L per $1 index exposure):")
    worst = cast("list[dict[str, object]]", results["worst_5_hedged_months"])
    for w in worst:
        pnl = cast("float", w["pnl_hedged_net"])
        ret = cast("float", w["index_ret"])
        print(f"  {w['entry_date']}  pnl={pnl:+.5f}  idx_ret={ret:+.4f}")
    print("=" * 78)


if __name__ == "__main__":
    main()
