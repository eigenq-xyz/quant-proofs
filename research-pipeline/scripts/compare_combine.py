"""Verified total-portfolio combine across diversifying sleeves vs 1/N.

The companion to ``compare_pgd.py``. That script runs the verified PGD solver on the *noisy
single-name* 49-industry cross-section, where mean-variance famously loses to 1/N. This one runs
the same verified solver on the regime that is *supposed* to favor mean-variance: a handful of
weakly correlated factor sleeves (AQR's free TSMOM or VME momentum return streams) with decades
of monthly data, where the covariance is estimable.

At each month the weights are formed from data up to and including that month and realised the
next month (no look-ahead): ``mu`` = annualised trailing mean, ``Sigma`` = annualised
Ledoit-Wolf-shrunk covariance (the proven-PSD target), solved through the verified budget-simplex
PGD (``sum w = 1``, ``sum|w| <= leverage_cap``). The benchmark is 1/N across the same sleeves
(also ``sum w = 1``), the apples-to-apples budget book. Both pay the same proportional turnover
cost. To show the result is not a single-knob artifact, the verified MV book is swept over a grid
of risk-aversion settings (higher risk aversion trusts ``mu`` less, approaching minimum variance).

Usage:
    uv run python -m scripts.compare_combine                 # TSMOM, 4 sleeves (default)
    uv run python -m scripts.compare_combine --dataset vme   # VME momentum, 8 sleeves

Results are written to ``studies/results_combine_<dataset>.json``. NOT routed through the verified
daily backtester: these are pre-built breadth streams, so the no-look-ahead theorem is scoped to
the daily equity study, not to this combine.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

from research_pipeline.crossasset import combine_sleeves_walkforward, verification_status_line
from research_pipeline.data_sources import load_aqr_tsmom, load_aqr_vme_monthly
from research_pipeline.evaluation import performance_summary
from research_pipeline.stats import deflated_sharpe_ratio, probabilistic_sharpe_ratio


def _summary(net: pd.Series, n_trials: int) -> dict[str, float]:
    perf = performance_summary(net, periods_per_year=12)
    return {
        "sharpe": float(perf.get("sharpe", float("nan"))),
        "ann_return": float(perf.get("ann_return", float("nan"))),
        "ann_vol": float(perf.get("ann_vol", float("nan"))),
        "max_drawdown": float(perf.get("max_drawdown", float("nan"))),
        "psr": probabilistic_sharpe_ratio(net, periods_per_year=12),
        "deflated_sharpe": deflated_sharpe_ratio(net, n_trials=n_trials, periods_per_year=12),
        "n": float(len(net)),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", choices=["tsmom", "vme"], default="tsmom")
    ap.add_argument(
        "--leverage", type=float, default=1.5, help="gross-exposure cap for the MV book"
    )
    ap.add_argument(
        "--cost-bps", type=float, default=10.0, help="proportional cost per unit turnover"
    )
    ap.add_argument(
        "--risk-aversions",
        type=float,
        nargs="+",
        default=[1.0, 5.0, 10.0, 25.0],
        help="risk-aversion grid for the verified MV book (higher trusts mu less)",
    )
    ap.add_argument("--out", default=None, help="JSON artifact path")
    args = ap.parse_args()

    if args.dataset == "tsmom":
        df = load_aqr_tsmom(asset_classes_only=True)
        name = "TSMOM sleeves / AQR (free)"
    else:
        df = load_aqr_vme_monthly(momentum_only=True)
        name = "VME momentum sleeves / AQR (free)"
    streams = {col: df[col].dropna() for col in df.columns}

    # The grid is swept against the SAME n_trials so the deflated Sharpe is comparable: the
    # 1/N book plus one MV book per risk-aversion setting.
    n_trials = len(args.risk_aversions) + 1

    eq = combine_sleeves_walkforward(
        streams, method="equal_weight", leverage_cap=args.leverage, cost_bps=args.cost_bps
    )
    eq_summary = _summary(eq, n_trials)

    mv_rows: dict[str, dict[str, float]] = {}
    for ra in args.risk_aversions:
        mv = combine_sleeves_walkforward(
            streams,
            method="verified_mv",
            leverage_cap=args.leverage,
            cost_bps=args.cost_bps,
            risk_aversion=ra,
        )
        mv_rows[f"verified_mv (risk_aversion={ra:g})"] = _summary(mv, n_trials)

    table = pd.DataFrame({**mv_rows, "equal_weight_1N": eq_summary}).T
    best_mv = max(row["sharpe"] for row in mv_rows.values())

    print(f"================ verified combine vs 1/N: {name} ================")
    print(f"[data] {len(streams)} sleeves, {df.index.min().date()} -> {df.index.max().date()}")
    print(
        f"[setup] budget simplex (sum w = 1, gross <= {args.leverage}); {args.cost_bps:g} bps cost"
    )
    pd.set_option("display.width", 160)
    print(table.round(4).to_string())
    print(
        f"\n[verdict] 1/N Sharpe {eq_summary['sharpe']:.3f}; best verified MV Sharpe {best_mv:.3f} "
        f"({'MV wins' if best_mv > eq_summary['sharpe'] else '1/N wins'} across the risk-aversion grid)."
    )
    print(f"\n[verify] {verification_status_line()}")

    out = {
        "name": name,
        "dataset": args.dataset,
        "n_sleeves": len(streams),
        "leverage_cap": args.leverage,
        "cost_bps": args.cost_bps,
        "date_start": str(df.index.min().date()),
        "date_end": str(df.index.max().date()),
        "equal_weight_1N": eq_summary,
        "verified_mv_by_risk_aversion": mv_rows,
        "best_verified_mv_sharpe": best_mv,
        "one_over_n_sharpe": eq_summary["sharpe"],
        "verification_status": verification_status_line(),
    }
    json_path = (
        pathlib.Path(args.out)
        if args.out
        else pathlib.Path(__file__).resolve().parents[1]
        / "studies"
        / f"results_combine_{args.dataset}.json"
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[artifact] wrote {json_path}")


if __name__ == "__main__":
    main()
