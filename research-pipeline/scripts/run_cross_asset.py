"""ROADMAP item 5 — bounded cross-asset generalisation study on FREE published AQR data.

The same momentum effect should appear across asset classes if it is structural, not a
single-market artifact. AQR's free data library publishes *already-built* long/short factor
return streams per asset class, which is exactly the cross-asset breadth question without any
per-asset tuning or custom futures/FX/commodity ingestion.

    python -m scripts.run_cross_asset                  # AQR Time-Series Momentum (default)
    python -m scripts.run_cross_asset --dataset vme    # AQR Value-and-Momentum-Everywhere (momentum)
    python -m scripts.run_cross_asset --json studies/out.json

VERIFICATION SCOPE (important): these AQR streams are pre-built factor returns; they do NOT run
through the verified daily event-driven backtester. The no-look-ahead theorem is scoped to the
daily equity backtest. This study is **breadth/generalisation evidence only** — the JSON
artifact records that caveat in its ``verification`` field. Do not call these numbers "verified."
"""

from __future__ import annotations

import argparse
import json
import pathlib

import pandas as pd

from research_pipeline.crossasset import analyze_return_streams
from research_pipeline.data_sources import load_aqr_tsmom, load_aqr_vme_monthly

_CAVEAT = (
    "Pre-built AQR factor return streams, NOT routed through the verified daily backtester. "
    "Breadth/generalisation evidence only; the no-look-ahead guarantee is scoped to the daily "
    "equity backtest."
)


def _df_to_records(df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for idx, row in df.iterrows():
        out[str(idx)] = {str(k): (float(v) if pd.notna(v) else None) for k, v in row.items()}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--dataset",
        choices=["tsmom", "vme"],
        default="tsmom",
        help="AQR dataset: tsmom (Time-Series Momentum) or vme (Value-and-Momentum-Everywhere)",
    )
    ap.add_argument("--json", default=None, help="write machine-readable results here")
    args = ap.parse_args()

    if args.dataset == "tsmom":
        streams_df = load_aqr_tsmom(asset_classes_only=True)
        name = "momentum (TSMOM) across asset classes / AQR (free)"
    else:
        streams_df = load_aqr_vme_monthly(momentum_only=True)
        name = "momentum (VME) across asset classes / AQR (free)"

    streams = {col: streams_df[col].dropna() for col in streams_df.columns}
    summary_df, corr_df = analyze_return_streams(streams, periods_per_year=12)

    print(f"================ cross-asset study: {name} ================")
    print(f"[scope] {_CAVEAT}")
    print(
        f"\n[data] {len(streams)} asset-class return streams, "
        f"{streams_df.index.min().date()} -> {streams_df.index.max().date()}"
    )
    print("\n[per-class] performance + multiple-testing-adjusted deflated Sharpe")
    print(summary_df.round(4).to_string())
    print("\n[cross-asset] correlation of monthly return streams")
    print(corr_df.round(3).to_string())

    out = {
        "name": name,
        "dataset": args.dataset,
        "verification": _CAVEAT,
        "n_asset_classes": len(streams),
        "periods_per_year": 12,
        "date_start": str(streams_df.index.min().date()),
        "date_end": str(streams_df.index.max().date()),
        "per_class_summary": _df_to_records(summary_df),
        "correlation": _df_to_records(corr_df),
    }
    json_path = (
        pathlib.Path(args.json)
        if args.json
        else (pathlib.Path(__file__).resolve().parents[1] / "studies" / "results_crossasset.json")
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[artifact] wrote {json_path}")


if __name__ == "__main__":
    main()
