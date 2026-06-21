"""Head-to-head: verified PGD mean-variance vs. naive portfolio construction.

Runs the SAME 12-1 momentum signal on the SAME universe (Ken French 49 industries, free) through
several portfolio constructors and compares net-of-cost results. The point is to show the verified
Lean 4 PGD solver wired LIVE into the pipeline (no fallback) and to report, honestly, whether
covariance-aware mean-variance optimisation actually beats naive construction net of costs.

Constraint note: the verified solver targets the BUDGET simplex (sum w = 1, sum|w| <= leverage_cap).
So the apples-to-apples peers are the other budget books (1/N, long-only momentum tilt). The
dollar-neutral baseline (sum w = 0) is shown for reference but is a different book; the dollar-neutral
verified projection is a tracked optimization-proofs theorem.

REBALANCING (and an honest caveat): ``--rebalance monthly`` (default) recomputes weights on the first
observation of each calendar month and holds them between, so cost is paid only at month boundaries.
This is the realistic setup for a mean-variance book and keeps the run to ~2 min. ``--rebalance daily``
is the full run: a verified solve every trading day, measured at ~10 solves/s => ~40+ min for the PGD
leg alone, AND methodologically unrealistic (a daily-rebalanced MV book churns turnover). Holding
target weights constant between rebalances implies costless intra-month drift-to-target, a standard
simplification that slightly understates turnover; it is applied identically to EVERY constructor, so
the comparison stays fair. If verified PGD still trails the naive books net of costs, that is an honest
finding (MV optimisation often loses to 1/N out of sample -- DeMiguel et al. 2009), not a harness artifact.

Usage:
    # quick monthly comparison (default, ~2 min):
    uv run python -u -m scripts.compare_pgd

    # full DAILY comparison (~40+ min) -- run detached in the background, then watch the heartbeat:
    cd /Users/akhilkarra/ode/eigenq/quant-proofs/research-pipeline
    nohup uv run python -u -m scripts.compare_pgd --rebalance daily \
        > studies/pgd_compare_daily.log 2>&1 &
    tail -f studies/pgd_compare_daily.log      # live: count / rate / elapsed / ETA per constructor

The ``-u`` (and the logging module's per-record flush) make the log live, not buffered. Results are
written to ``studies/results_pgd_comparison_<rebalance>.json``.
"""

from __future__ import annotations

import argparse
import json
import logging
import pathlib
import sys
import time

import pandas as pd

from research_pipeline import momentum_signal
from research_pipeline.backtest import run_backtest
from research_pipeline.data import PricePanel
from research_pipeline.data_sources import load_ken_french_factors
from research_pipeline.evaluation import performance_summary
from research_pipeline.portfolio import (
    long_only_weights,
    make_verified_pgd_weight_fn,
    signal_to_weights,
)
from research_pipeline.stats import deflated_sharpe_ratio, probabilistic_sharpe_ratio

# logging.StreamHandler flushes after every record, so the log is live even when redirected to a file.
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(message)s", datefmt="%H:%M:%S", stream=sys.stdout
)
log = logging.getLogger("compare_pgd")


def equal_weight(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
    """1/N benchmark (sum w = 1): equal weight across names with a valid signal; ignores the score."""
    s = signal_row.dropna()
    if len(s) == 0:
        return pd.Series(0.0, index=signal_row.index)
    return pd.Series(1.0 / len(s), index=s.index).reindex(signal_row.index).fillna(0.0)


def monthly_rebalance(wf):
    """Wrap a constructor so it recomputes weights only at each new calendar month and holds them
    between (cost is then paid only at month boundaries). Cuts the verified-solver call count from one
    per trading day to ~12/year and models a realistic monthly-rebalanced book. Applied to every
    constructor so the comparison is at a common frequency."""
    state: dict = {"key": None, "w": None}

    def wrapped(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
        t = signal_row.name
        key = (t.year, t.month)
        if key != state["key"]:
            state["key"] = key
            state["w"] = wf(signal_row, gross=gross)
        return state["w"].reindex(signal_row.index).fillna(0.0)

    return wrapped


def with_heartbeat(label: str, wf, total: int, every: int = 1000):
    """Wrap a weight function so it logs progress (count / rate / ETA) as the backtest walks dates."""
    state = {"n": 0, "t0": time.time()}

    def wrapped(signal_row: pd.Series, gross: float = 1.0) -> pd.Series:
        n = state["n"] = state["n"] + 1
        if n == 1:
            t_solve = time.time()
            w = wf(signal_row, gross=gross)
            log.info(
                "  [%s] first weights computed in %.3fs (solver online); %d dates to go",
                label,
                time.time() - t_solve,
                total,
            )
            return w
        if n == 100 or n % every == 0:
            el = time.time() - state["t0"]
            rate = n / el if el > 0 else 0.0
            eta = (total - n) / rate if rate > 0 else float("nan")
            date = getattr(signal_row, "name", "?")
            log.info(
                "  [%s] %d/%d dates (%s) | %.0f/s | elapsed %.0fs | ETA %.0fs",
                label,
                n,
                total,
                getattr(date, "date", lambda: date)(),
                rate,
                el,
                eta,
            )
        return wf(signal_row, gross=gross)

    return wrapped


def main() -> None:
    ap = argparse.ArgumentParser(description="verified PGD vs. naive portfolio construction")
    ap.add_argument(
        "--rebalance",
        choices=["monthly", "daily"],
        default="monthly",
        help="rebalance frequency; 'daily' is the full, slow (~40+ min) run",
    )
    ap.add_argument(
        "--leverage", type=float, default=1.5, help="gross-exposure cap for the PGD book"
    )
    ap.add_argument(
        "--every", type=int, default=1000, help="heartbeat: log every N rebalance dates"
    )
    ap.add_argument(
        "--out",
        default=None,
        help="JSON artifact path (default: studies/results_pgd_comparison_<rebalance>.json)",
    )
    args = ap.parse_args()

    t_load = time.time()
    log.info("loading Ken French 49 industry portfolios (daily, free)...")
    rets = load_ken_french_factors("49_Industry_Portfolios_daily")
    panel = PricePanel(100.0 * (1.0 + rets.fillna(0.0)).cumprod())
    log.info(
        "loaded in %.1fs: %d days x %d industries, %s..%s",
        time.time() - t_load,
        panel.prices.shape[0],
        panel.prices.shape[1],
        panel.prices.index[0].date(),
        panel.prices.index[-1].date(),
    )

    # Count rebalance dates so the heartbeat can report a real ETA (mirrors run_backtest's date set).
    sig = momentum_signal(panel)
    fwd = panel.forward_returns(1)
    total = len(sig.dropna(how="all").index.intersection(fwd.index))
    log.info(
        "rebalance=%s | leverage_cap=%.2f | rebalance dates with a valid signal=%d",
        args.rebalance,
        args.leverage,
        total,
    )
    if args.rebalance == "daily":
        log.info(
            "DAILY run: a verified solve every trading day (~40+ min). See the HONEST CAVEAT in "
            "the module docstring before trusting the net-of-cost numbers."
        )

    prep = monthly_rebalance if args.rebalance == "monthly" else (lambda fn: fn)
    constructors = {
        "verified_pgd_mv (sum w=1)": make_verified_pgd_weight_fn(panel, leverage_cap=args.leverage),
        "long_only_momentum (sum w=1)": long_only_weights,
        "equal_weight_1N (sum w=1)": equal_weight,
        "dollar_neutral_baseline (sum w=0)": signal_to_weights,
    }

    rows: dict[str, dict[str, float]] = {}
    for label, wf in constructors.items():
        log.info("=== running constructor: %s (%s rebalance) ===", label, args.rebalance)
        t0 = time.time()
        bt = run_backtest(
            panel,
            momentum_signal,
            cost_bps=10.0,
            weight_fn=with_heartbeat(label, prep(wf), total, every=args.every),
        )
        perf = performance_summary(bt.net_returns)
        rows[label] = {
            "net_sharpe": bt.summary["net_sharpe"],
            "gross_sharpe": bt.summary["gross_sharpe"],
            "ann_return": float(perf.get("ann_return", float("nan"))),
            "ann_vol": float(perf.get("ann_vol", float("nan"))),
            "max_drawdown": float(perf.get("max_drawdown", float("nan"))),
            "avg_turnover": bt.summary["avg_turnover"],
            "psr": probabilistic_sharpe_ratio(bt.net_returns),
            "dsr_n50": deflated_sharpe_ratio(bt.net_returns, n_trials=50),
        }
        log.info(
            "DONE %s in %.1fs | net_sharpe=%.3f gross_sharpe=%.3f turnover=%.4f dsr=%.3f",
            label,
            time.time() - t0,
            rows[label]["net_sharpe"],
            rows[label]["gross_sharpe"],
            rows[label]["avg_turnover"],
            rows[label]["dsr_n50"],
        )

    table = pd.DataFrame(rows).T
    pd.set_option("display.width", 160)
    pd.set_option("display.float_format", lambda v: f"{v:,.4f}")
    log.info(
        "\n========== verified PGD vs. baselines (%s rebalance, net of 10 bps) ==========\n%s",
        args.rebalance,
        table.to_string(),
    )

    out = (
        pathlib.Path(args.out)
        if args.out
        else pathlib.Path(__file__).resolve().parents[1]
        / "studies"
        / f"results_pgd_comparison_{args.rebalance}.json"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"rebalance": args.rebalance, "leverage_cap": args.leverage, "results": rows},
            indent=2,
            default=str,
        )
    )
    log.info("[artifact] wrote %s", out)


if __name__ == "__main__":
    main()
