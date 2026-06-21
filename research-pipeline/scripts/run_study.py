"""Track 2 — a real QR study driver (Ken French free data; WRDS/CRSP optional).

Runs the full pipeline on real data with out-of-sample discipline and writes the numbers a
research report needs, plus a machine-readable ``studies/results_<universe>.json`` so the
report is reproducible from one command.

    python -m scripts.run_study                       # Ken French 49 industries (free)
    python -m scripts.run_study --crsp PATH.parquet   # your gitignored CRSP extract
    python -m scripts.run_study --json studies/out.json

The CRSP cross-section needs your WRDS credentials or a local extract (licensed data — never
committed); see ``studies/WRDS_DATA_REQUEST.md``.
"""

from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

from research_pipeline import momentum_signal, print_report, run_research_study
from research_pipeline.data import PricePanel
from research_pipeline.data_sources import load_crsp_daily, load_ken_french_factors
from research_pipeline.evaluation import factor_attribution
from research_pipeline.oos import leakage_gap, run_walk_forward, walk_forward_splits


def _prices_from_returns(returns: pd.DataFrame) -> PricePanel:
    """Build a price panel from a returns panel (French portfolios are returns)."""
    return PricePanel(100.0 * (1.0 + returns.fillna(0.0)).cumprod())


def _series_to_dict(s: pd.Series) -> dict[str, float]:
    return {str(k): (float(v) if pd.notna(v) else None) for k, v in s.items()}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crsp", default=None, help="path to a gitignored CRSP parquet extract")
    ap.add_argument(
        "--n-trials", type=int, default=50, help="signals searched (for deflated Sharpe)"
    )
    ap.add_argument("--n-splits", type=int, default=5, help="walk-forward folds")
    ap.add_argument("--embargo", type=int, default=5, help="embargo (purge) gap in days")
    ap.add_argument("--json", default=None, help="write machine-readable results here")
    args = ap.parse_args()

    if args.crsp:
        panel = load_crsp_daily(local_parquet=args.crsp)  # licensed — never commit
        name = "momentum / CRSP cross-section"
        slug = "crsp"
        factors = None
    else:
        rets = load_ken_french_factors("49_Industry_Portfolios_daily")  # free
        panel = _prices_from_returns(rets)
        name = "momentum / Ken French 49 industries"
        slug = "ken_french_49ind"
        # Fama-French 5 factors + momentum for attribution (free).
        ff5 = load_ken_french_factors("F-F_Research_Data_5_Factors_2x3_daily")
        mom = load_ken_french_factors("F-F_Momentum_Factor_daily")
        factors = ff5.join(mom, how="inner").drop(columns=["RF"], errors="ignore")

    # In-sample study (all stages + honest significance).
    report = run_research_study(panel, momentum_signal, name=name, n_trials=args.n_trials)
    print_report(report)

    # Factor attribution: is the edge alpha, or disguised beta to known factors?
    attribution = pd.Series(dtype=float)
    if factors is not None:
        attribution = factor_attribution(report.backtest.net_returns, factors)
        if not attribution.empty:
            print("\n[6] Factor attribution (net returns vs FF5 + momentum)")
            print(attribution.round(5).to_string())

    # Out-of-sample walk-forward (the number that actually counts).
    oos = run_walk_forward(panel, momentum_signal, n_splits=args.n_splits, embargo=args.embargo)
    splits = walk_forward_splits(panel.prices.index, args.n_splits, args.embargo)
    gap = leakage_gap(panel.prices.index, splits, horizon=1)
    print("\n[OOS] walk-forward (purged/embargoed)")
    print(f"  oos_sharpe = {oos['oos_sharpe']:.3f}   (min leakage slack = {gap}; >=1 == clean)")
    print(oos["folds"].to_string())  # type: ignore[union-attr]

    # Machine-readable artifact for reproducible reporting.
    out = {
        "name": name,
        "universe": slug,
        "n_trials": args.n_trials,
        "ic": _series_to_dict(report.ic),
        "ic_decay": _series_to_dict(report.decay),
        "quantile_spread": _series_to_dict(report.monotonicity),
        "ic_stability": _series_to_dict(report.ic_stability),
        "backtest": report.backtest.summary,
        "performance": _series_to_dict(report.performance),
        "psr": float(report.psr),
        "dsr": float(report.dsr),
        "factor_attribution": _series_to_dict(attribution),
        "oos_sharpe": float(oos["oos_sharpe"]),  # type: ignore[arg-type]
        "oos_min_leakage_slack": int(gap),
        "oos_folds": oos["folds"].astype(str).to_dict("records"),  # type: ignore[union-attr]
    }
    json_path = (
        pathlib.Path(args.json)
        if args.json
        else (pathlib.Path(__file__).resolve().parents[1] / "studies" / f"results_{slug}.json")
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[artifact] wrote {json_path}")


if __name__ == "__main__":
    main()
