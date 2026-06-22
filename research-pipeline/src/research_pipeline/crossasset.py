"""Cross-asset generalisation study.

Run the *same* signal across asset classes and compare. A structural effect should appear
wherever its driver exists; single-market-only results are a data-mining red flag. Going
cross-asset multiplies the multiple-testing problem, so deflated-Sharpe discipline matters more
here (see ``stats.deflated_sharpe_ratio``).

Two entry points, by what the data gives you:

- ``run_cross_asset(panels, signal_fn)`` — raw price ``PricePanel``s per asset class, routed
  through the **verified** daily event-driven backtester (``run_backtest``). Use when you own
  the underlying cross-section.
- ``analyze_return_streams(streams)`` — already-built factor *return streams* per asset class
  (e.g. AQR's free TSMOM / Value-and-Momentum-Everywhere monthly factors). These do **not** run
  through the verified backtester.

VERIFICATION-SCOPE CAVEAT (read before quoting these numbers): the no-look-ahead theorem covers
the daily event-driven backtester only. ``analyze_return_streams`` consumes pre-built return
streams that never touch that engine, so its output is **breadth/generalisation evidence**, not
a verified result. Never let "verified" stretch over runs the proof did not cover; scope that
claim to the daily equity backtest.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
import pandas as pd

from .backtest import SignalFn, run_backtest
from .data import PricePanel
from .evaluation import performance_summary
from .portfolio import _ledoit_wolf_shrink, verified_pgd_weights
from .stats import deflated_sharpe_ratio


def run_cross_asset(
    panels: dict[str, PricePanel],
    signal_fn: SignalFn,
    cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (summary table per asset class, correlation matrix of net-return streams).

    Routes each raw price panel through the verified daily backtester, so this path inherits the
    no-look-ahead guarantee.
    """
    summaries: dict[str, dict[str, float]] = {}
    net_streams: dict[str, pd.Series] = {}
    for name, panel in panels.items():
        res = run_backtest(panel, signal_fn, cost_bps=cost_bps)
        summaries[name] = res.summary
        net_streams[name] = res.net_returns
    summary_df = pd.DataFrame(summaries).T
    corr_df = pd.DataFrame(net_streams).corr()
    return summary_df, corr_df


def analyze_return_streams(
    streams: dict[str, pd.Series],
    periods_per_year: int = 12,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Per-asset-class performance + multiple-testing-adjusted significance from return streams.

    ``streams`` maps an asset-class name to its periodic return series (decimals), e.g. AQR's
    per-asset-class TSMOM or VME momentum factors (``periods_per_year=12`` for monthly). For each
    class this computes the standard performance summary (annualised Sharpe, return, vol,
    drawdown, ...) and a **deflated Sharpe ratio** whose ``n_trials`` equals the number of asset
    classes tested, so significance is honest about searching across classes. Also returns the
    cross-asset correlation table of the return streams, the evidence for a common-factor /
    structural reading of the effect.

    Returns ``(summary_df, corr_df)``: ``summary_df`` is indexed by asset class with the
    performance columns plus ``deflated_sharpe``; ``corr_df`` is the pairwise correlation matrix.

    NOT routed through the verified backtester. These are pre-built factor return streams, so the
    output is generalisation evidence, not a verified no-look-ahead result.
    """
    if not streams:
        raise ValueError("analyze_return_streams requires at least one return stream")
    n_trials = len(streams)
    summaries: dict[str, dict[str, float]] = {}
    for name, series in streams.items():
        perf = performance_summary(series, periods_per_year=periods_per_year)
        row = {str(k): float(v) for k, v in perf.items()}
        row["deflated_sharpe"] = deflated_sharpe_ratio(
            series, n_trials=n_trials, periods_per_year=periods_per_year
        )
        summaries[name] = row
    summary_df = pd.DataFrame(summaries).T
    corr_df = pd.DataFrame(streams).corr()
    return summary_df, corr_df


def reproduction_table(
    realized: pd.DataFrame,
    published: Mapping[str, float],
    tol_ratio: float = 2.0,
) -> pd.DataFrame:
    """Place each sleeve's realized Sharpe beside the figure reported in the source paper.

    ``realized`` is the per-asset-class summary from :func:`analyze_return_streams` (its
    ``sharpe`` column is read); ``published`` maps the same asset-class names to the annualised
    Sharpe ratio reported in the source paper. The reproduction bar is deliberately **sign and
    rough magnitude**, not exact decimals: AQR's live dataset extends the published sample by
    a decade or more, and construction details (rebalance lag, volatility scaling, universe)
    differ from the paper. A sleeve counts as *reproduced* when its realized Sharpe shares the
    sign of the published figure and lands within a factor of ``tol_ratio`` of it, i.e. the
    realized/published ratio is in ``[1 / tol_ratio, tol_ratio]`` (default 2x).

    Returns a table indexed by the asset classes present in BOTH ``realized`` and ``published``,
    with columns ``realized_sharpe``, ``published_sharpe``, ``ratio``, ``sign_match``,
    ``magnitude_match`` and ``reproduced``. The reproduced count is
    ``int(table["reproduced"].sum())``.
    """
    if tol_ratio < 1.0:
        raise ValueError("tol_ratio must be >= 1.0 (it is a two-sided multiplicative band)")
    if "sharpe" not in realized.columns:
        raise ValueError(
            "realized must carry a 'sharpe' column (the analyze_return_streams summary)"
        )
    realized_sharpe = {str(k): float(v) for k, v in realized["sharpe"].items()}
    rows: dict[str, dict[str, float | bool]] = {}
    for name, pub in published.items():
        if name not in realized_sharpe:
            continue  # only compare sleeves we actually realized
        real = realized_sharpe[name]
        pubf = float(pub)
        same_sign = pubf != 0.0 and real != 0.0 and ((real > 0.0) == (pubf > 0.0))
        ratio = real / pubf if pubf != 0.0 else float("nan")
        magnitude = same_sign and (1.0 / tol_ratio) <= ratio <= tol_ratio
        rows[name] = {
            "realized_sharpe": real,
            "published_sharpe": pubf,
            "ratio": ratio,
            "sign_match": bool(same_sign),
            "magnitude_match": bool(magnitude),
            "reproduced": bool(same_sign and magnitude),
        }
    if not rows:
        raise ValueError("no overlapping asset classes between realized and published")
    cols = [
        "realized_sharpe",
        "published_sharpe",
        "ratio",
        "sign_match",
        "magnitude_match",
        "reproduced",
    ]
    return pd.DataFrame.from_dict(rows, orient="index")[cols]


def combine_sleeves_walkforward(
    streams: Mapping[str, pd.Series],
    method: str = "verified_mv",
    lookback: int = 60,
    min_obs: int = 36,
    leverage_cap: float = 1.5,
    shrink: float = 0.1,
    periods_per_year: int = 12,
    risk_aversion: float = 1.0,
    cost_bps: float = 10.0,
) -> pd.Series:
    """Walk-forward NET return stream of a portfolio *of sleeves*: verified MV vs equal weight.

    This is the diversifying-sleeve home of the verified solver, the complement to the noisy
    single-name 49-industry contrast (where the same optimiser loses to 1/N). The sleeves here
    are the AQR factor return streams: few, weakly correlated, with decades of monthly data, so
    the covariance is estimable and mean-variance is supposed to help.

    The sleeves are aligned to a balanced panel (months where every sleeve is present). At each
    month ``t`` with at least ``min_obs`` trailing observations, the weights are formed from data
    up to and including ``t`` and realised on ``t+1`` (no look-ahead):

    - ``method="verified_mv"`` solves the **verified** budget-simplex MV problem through
      :func:`verified_pgd_weights` with ``mu`` = annualised trailing mean and ``Sigma`` =
      annualised Ledoit-Wolf-shrunk covariance (the proven-PSD target). ``mu`` and ``Sigma`` are
      put on the same annual horizon so the risk term is not ~``periods_per_year`` times too
      small; ``risk_aversion`` further scales the risk term.
    - ``method="equal_weight"`` is the 1/N-across-sleeves benchmark (also ``sum w = 1``), the
      apples-to-apples budget book.

    Returns the net (of ``cost_bps`` per unit one-way turnover) monthly return stream. Raises if
    the verified solver is unavailable (no silent fallback). NOT routed through the verified
    daily backtester: this is portfolio construction across pre-built breadth streams.
    """
    if method not in ("verified_mv", "equal_weight"):
        raise ValueError("method must be 'verified_mv' or 'equal_weight'")
    panel = pd.DataFrame(streams).dropna()
    if panel.shape[1] < 2:
        raise ValueError("need at least 2 sleeves to combine")
    if panel.shape[0] <= min_obs + 1:
        raise ValueError(f"need more than min_obs+1={min_obs + 1} aligned observations")
    sleeves = list(panel.columns)
    idx = panel.index
    prev_w = pd.Series(0.0, index=sleeves)
    net: dict[pd.Timestamp, float] = {}
    for i in range(min_obs, len(idx) - 1):
        t_next = idx[i + 1]
        window = panel.iloc[: i + 1].iloc[-lookback:]  # returns up to and including idx[i]
        if method == "equal_weight":
            w = pd.Series(1.0 / len(sleeves), index=sleeves)
        else:
            mu = window.mean() * periods_per_year
            sample = np.cov(window.to_numpy(dtype=float), rowvar=False) * (
                risk_aversion * periods_per_year
            )
            cov_df = pd.DataFrame(
                _ledoit_wolf_shrink(sample, shrink), index=sleeves, columns=sleeves
            )
            w = verified_pgd_weights(mu, cov_df, leverage_cap=leverage_cap)
        gross_ret = float((w * panel.loc[t_next]).sum())
        turnover = float((w - prev_w).abs().sum())
        net[t_next] = gross_ret - cost_bps / 1e4 * turnover
        prev_w = w
    return pd.Series(net, dtype=float).sort_index()


def verification_status_line(include_scope: bool = True) -> str:
    """One-line machine-checked-invariants status the study can print.

    Two levels, kept distinct in the emitted text. Machine-checked (proved sorry-free AND
    exercised by the backtester): no look-ahead, no train/test leakage (the out-of-sample
    embargo is at least the holding horizon), and signal measurability against the information
    available at each date (adapted to the natural price filtration, citing the FTAP
    development). Proved-in-Lean but one step removed: the projection and convergence of the PGD
    portfolio solver are sorry-free in ``optimization-proofs``, but the running solver is a
    Python implementation of that proven algorithm and the proofs are not yet wired into the CI
    matrix, so the line says "proven sorry-free in Lean" rather than "machine-checked" for it.
    The arrow framing is deliberate: a green build is what certifies the proofs are still intact.
    """
    line = (
        "Verification: Lean build green => no look-ahead, no train/test leakage "
        "(out-of-sample embargo at least the holding horizon), and signal measurable against the "
        "information set at each date (adapted to the natural price filtration, citing the FTAP "
        "development) are machine-checked; the projection and convergence of the PGD portfolio "
        "solver are proven sorry-free in Lean (optimization-proofs)."
    )
    if include_scope:
        line += (
            " Scope: the no-look-ahead guarantee covers the daily equity backtester; the "
            "cross-asset streams are breadth evidence, not verified runs."
        )
    return line
