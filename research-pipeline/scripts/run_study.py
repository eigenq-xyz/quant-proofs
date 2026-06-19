"""Track 2 — a real QR study driver (Ken French; WRDS/CRSP optional).

Runs the full pipeline on real data with out-of-sample discipline and writes the numbers a
research report needs. Requires network for Ken French; the CRSP cross-section needs your
WRDS credentials (licensed data — never committed).

    python -m scripts.run_study            # Ken French industry portfolios
    python -m scripts.run_study --crsp PATH.parquet   # your gitignored CRSP extract
"""

from __future__ import annotations

import argparse

import pandas as pd

from research_pipeline import momentum_signal, print_report, run_research_study
from research_pipeline.data import PricePanel
from research_pipeline.data_sources import load_crsp_daily, load_ken_french_factors
from research_pipeline.oos import run_walk_forward


def _prices_from_returns(returns: pd.DataFrame) -> PricePanel:
    """Build a price panel from a returns panel (French portfolios are returns)."""
    return PricePanel(100.0 * (1.0 + returns.fillna(0.0)).cumprod())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--crsp", default=None, help="path to a gitignored CRSP parquet extract")
    ap.add_argument(
        "--n-trials", type=int, default=50, help="signals searched (for deflated Sharpe)"
    )
    args = ap.parse_args()

    if args.crsp:
        panel = load_crsp_daily(local_parquet=args.crsp)  # licensed — never commit
        name = "momentum / CRSP cross-section"
    else:
        rets = load_ken_french_factors("49_Industry_Portfolios_daily")  # free
        panel = _prices_from_returns(rets)
        name = "momentum / Ken French 49 industries"

    # In-sample study (all stages + honest significance).
    report = run_research_study(panel, momentum_signal, name=name, n_trials=args.n_trials)
    print_report(report)

    # Out-of-sample walk-forward (the number that actually counts).
    oos = run_walk_forward(panel, momentum_signal, n_splits=5, embargo=5)
    print("\n[OOS] walk-forward (purged/embargoed)")
    print(f"  oos_sharpe = {oos['oos_sharpe']:.3f}")
    print(oos["folds"].to_string())  # type: ignore[union-attr]


if __name__ == "__main__":
    main()
