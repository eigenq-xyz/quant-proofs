"""Bounded cross-asset generalisation study on FREE published AQR data.

EXPLORATORY — not a load-bearing result. See extensions/research-ideas/README.md for
why this lives here and not in research-pipeline/studies/.

The same momentum effect should appear across asset classes if it is structural, not a
single-market artifact. AQR's free data library publishes *already-built* long/short factor
return streams per asset class, which is exactly the cross-asset breadth question without any
per-asset tuning or custom futures/FX/commodity ingestion.

    cd extensions/research-ideas && python run_cross_asset.py                # AQR Time-Series Momentum (default)
    cd extensions/research-ideas && python run_cross_asset.py --dataset vme  # AQR Value-and-Momentum-Everywhere
    cd extensions/research-ideas && python run_cross_asset.py --json out.json

VERIFICATION SCOPE (important): these AQR streams are pre-built factor returns; they do NOT run
through the verified daily event-driven backtester. The no-look-ahead theorem is scoped to the
daily equity backtest. This study is **breadth/generalisation evidence only** — the JSON
artifact records that caveat in its ``verification`` field. Do not call these numbers "verified."
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from datetime import UTC, datetime

import numpy as np
import pandas as pd

# research_pipeline is an installed package from research-pipeline/src/; crossasset.py
# is a local sibling module here, not part of that package (see README.md for why).
_RESEARCH_PIPELINE_SRC = (
    pathlib.Path(__file__).resolve().parents[2] / "research-pipeline" / "src"
)
if str(_RESEARCH_PIPELINE_SRC) not in sys.path:
    sys.path.insert(0, str(_RESEARCH_PIPELINE_SRC))
if str(pathlib.Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from crossasset import (  # noqa: E402
    analyze_return_streams,
    reproduction_table,
    verification_status_line,
)
from research_pipeline.data_sources import (  # noqa: E402
    TSMOM_PUBLISHED_DIVERSIFIED_SHARPE,
    TSMOM_PUBLISHED_SOURCE,
    VME_PUBLISHED_MOMENTUM_SHARPE,
    VME_PUBLISHED_SOURCE,
    load_aqr_tsmom,
    load_aqr_vme_monthly,
)
from research_pipeline.evaluation import sharpe  # noqa: E402

_CAVEAT = (
    "Pre-built AQR factor return streams, NOT routed through the verified daily backtester. "
    "Breadth/generalisation evidence only; the no-look-ahead guarantee is scoped to the daily "
    "equity backtest."
)


def _df_to_records(df: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    out: dict[str, dict[str, float | None]] = {}
    for idx, row in df.iterrows():
        out[str(idx)] = {
            str(k): (float(v) if pd.notna(v) else None) for k, v in row.items()
        }
    return out


def _repro_records(df: pd.DataFrame) -> dict[str, dict[str, float | bool | None]]:
    """Serialize the reproduction table, preserving booleans (not coercing them to 1.0/0.0)."""
    out: dict[str, dict[str, float | bool | None]] = {}
    for idx, row in df.iterrows():
        rec: dict[str, float | bool | None] = {}
        for k, v in row.items():
            if isinstance(v, (bool, np.bool_)):
                rec[str(k)] = bool(v)
            elif pd.isna(v):
                rec[str(k)] = None
            else:
                rec[str(k)] = float(v)
        out[str(idx)] = rec
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

    # ---- Validate by reproduction: realized Sharpe beside the published figure -------------
    # Bar = sign + rough magnitude (within a 2x band), not exact decimals (vintages differ).
    if args.dataset == "vme":
        # Genuine per-market reproduction: AMP (2013) Table I tabulates each market's momentum
        # Factor Sharpe, so every realized sleeve has a published anchor.
        repro_df = reproduction_table(summary_df, VME_PUBLISHED_MOMENTUM_SHARPE)
        published_source = VME_PUBLISHED_SOURCE
        repro_note = "Per-market momentum Factor Sharpe vs Asness-Moskowitz-Pedersen (2013), Table I."
    else:
        # MOP (2012) does NOT tabulate per-sleeve TSMOM Sharpes; only the diversified all-asset
        # composite is published (">1.0"). Reproduce that composite. The per-sleeve figures above
        # are computed from AQR data, not quoted from the paper.
        diversified = load_aqr_tsmom(asset_classes_only=False)
        if "TSMOM" not in diversified.columns:
            raise SystemExit(
                "AQR TSMOM file has no diversified 'TSMOM' column to reproduce"
            )
        comp = diversified["TSMOM"].dropna()
        comp_summary = pd.DataFrame(
            {"sharpe": [sharpe(comp, periods_per_year=12)]}, index=["diversified"]
        )
        repro_df = reproduction_table(
            comp_summary, {"diversified": TSMOM_PUBLISHED_DIVERSIFIED_SHARPE}
        )
        published_source = TSMOM_PUBLISHED_SOURCE
        repro_note = (
            "Diversified all-asset TSMOM Sharpe vs Moskowitz-Ooi-Pedersen (2012), reported as "
            ">1.0 (a lower bound); per-sleeve TSMOM Sharpes are computed from AQR data, not published."
        )
    n_reproduced = int(repro_df["reproduced"].sum())
    n_compared = int(len(repro_df))
    verification = verification_status_line()

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
    print(
        "\n[reproduction] realized Sharpe vs published (sign + rough magnitude, 2x band)"
    )
    print(repro_df.round(3).to_string())
    print(f"[reproduction] {n_reproduced}/{n_compared} reproduced. {repro_note}")
    print(f"[reproduction] source: {published_source}")
    print(f"\n[verify] {verification}")

    out = {
        "_meta": {
            "generated_by": "extensions/research-ideas/run_cross_asset.py",
            "generated_at": datetime.now(UTC).isoformat(),
            "reproduce": f"cd extensions/research-ideas && python run_cross_asset.py --dataset {args.dataset}",
            "verified": False,
            "notes": _CAVEAT,
        },
        "name": name,
        "dataset": args.dataset,
        "verification": _CAVEAT,
        "n_asset_classes": len(streams),
        "periods_per_year": 12,
        "date_start": str(streams_df.index.min().date()),
        "date_end": str(streams_df.index.max().date()),
        "per_class_summary": _df_to_records(summary_df),
        "correlation": _df_to_records(corr_df),
        "reproduction": _repro_records(repro_df),
        "n_reproduced": n_reproduced,
        "n_compared": n_compared,
        "reproduction_note": repro_note,
        "published_source": published_source,
        "verification_status": verification,
    }
    json_path = (
        pathlib.Path(args.json)
        if args.json
        else (
            pathlib.Path(__file__).resolve().parent
            / f"results_crossasset_{args.dataset}.json"
            if args.dataset != "tsmom"
            else pathlib.Path(__file__).resolve().parent / "results_crossasset.json"
        )
    )
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\n[artifact] wrote {json_path}")


if __name__ == "__main__":
    main()
