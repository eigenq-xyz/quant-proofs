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

import pandas as pd

from .backtest import SignalFn, run_backtest
from .data import PricePanel
from .evaluation import performance_summary
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


def verification_status_line(include_scope: bool = True) -> str:
    """One-line machine-checked-invariants status the study can print.

    States the load-bearing guarantees that hold when the Lean proofs build green: no
    look-ahead in the backtester, no train/test leakage (the out-of-sample embargo is at least
    the holding horizon), the signal is measurable with respect to the information available at
    each date (adapted to the natural price filtration, citing the FTAP development), and the
    verified portfolio solver's projection and convergence. The arrow framing is deliberate: the
    invariants are *proven* in the repo's Lean sources; a green build is what certifies the
    proofs are still intact.
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
