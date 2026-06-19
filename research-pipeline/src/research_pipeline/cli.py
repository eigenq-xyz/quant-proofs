"""``rp`` — the research-pipeline command line.

The interface a researcher drives the engine through. Parameters are flags (quick
iteration); a config file captures a full run for reproducibility, and flags override
config values. Every run persists to ``results/<id>/`` as ``report.json`` (machine),
``REPORT.md`` (human), and ``config.json`` (the resolved, replayable run config).

    rp list                                             # registered strategies + portfolios
    rp run momentum --lookback 252 --cost-bps 10 --oos --out results/
    rp run -c results/<id>/config.json                  # replay; flags still override
    rp validate                                         # validate-the-validator gate

Universes: ``synthetic`` (offline, default) and ``ken-french-49`` (needs network). Licensed
data is never committed; ``results/`` is gitignored.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from .data import PricePanel, make_synthetic_panel
from .oos import run_walk_forward
from .portfolio import available_portfolios
from .strategy import SignalFn, available_strategies, get_strategy
from .study import StudyReport, print_report, run_research_study
from .validation import boundary_lookahead_discrepancy, leaky_signal

# Strategy parameters that may be passed through to a strategy factory.
_STRATEGY_PARAM_KEYS = ("lookback", "skip", "portfolio")


def _build_panel(universe: str, n_days: int, n_assets: int, seed: int) -> PricePanel:
    if universe == "synthetic":
        return make_synthetic_panel(n_days=n_days, n_assets=n_assets, seed=seed)
    if universe == "ken-french-49":
        from .data_sources import load_ken_french_factors

        rets = load_ken_french_factors("49_Industry_Portfolios_daily")
        return PricePanel(100.0 * (1.0 + rets.fillna(0.0)).cumprod())
    raise SystemExit(f"unknown universe {universe!r} (expected: synthetic, ken-french-49)")


def _resolve_config(args: argparse.Namespace) -> dict[str, Any]:
    """Merge a JSON config file (if given) with explicitly-passed flags (flags win)."""
    cfg: dict[str, Any] = {}
    if getattr(args, "config", None):
        cfg = json.loads(Path(args.config).read_text())
    for key, value in vars(args).items():
        if key in ("func", "config"):
            continue
        if value is not None:
            cfg[key] = value
    return cfg


def _report_to_dict(rep: StudyReport, oos: dict[str, Any] | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "name": rep.name,
        "cross_sectional": rep.cross_sectional,
        "performance": {k: float(v) for k, v in rep.performance.items()},
        "psr": float(rep.psr),
        "dsr": float(rep.dsr),
        "backtest_summary": {k: float(v) for k, v in rep.backtest.summary.items()},
    }
    if rep.cross_sectional and not rep.ic.empty:
        out["ic"] = {str(k): float(v) for k, v in rep.ic.items()}
        out["ic_decay"] = {str(k): float(v) for k, v in rep.decay.items()}
    if rep.combination is not None:
        out["combination"] = {str(k): float(v) for k, v in rep.combination.items()}
    if oos is not None:
        out["oos_sharpe"] = float(oos["oos_sharpe"])
    return out


def _write_report_md(report: dict[str, Any], cfg: dict[str, Any]) -> str:
    lines = [f"# Research run: {report['name']}", ""]
    lines.append("## Configuration")
    lines.append("```json")
    lines.append(json.dumps(cfg, indent=2, sort_keys=True))
    lines.append("```")
    lines.append("\n## Backtest (net of costs)")
    for k, v in report["backtest_summary"].items():
        lines.append(f"- {k}: {v:.4f}")
    lines.append("\n## Performance")
    for k, v in report["performance"].items():
        lines.append(f"- {k}: {v:.4f}")
    lines.append("\n## Significance")
    lines.append(f"- probabilistic_sharpe_ratio: {report['psr']:.3f}")
    lines.append(f"- deflated_sharpe_ratio: {report['dsr']:.3f}")
    if "oos_sharpe" in report:
        lines.append(f"- out-of-sample Sharpe (walk-forward): {report['oos_sharpe']:.3f}")
    if "ic" in report:
        lines.append("\n## Signal statistics (IC)")
        for k, v in report["ic"].items():
            lines.append(f"- {k}: {v:.4f}")
    if "combination" in report:
        lines.append("\n## Combination / incrementality")
        for k, v in report["combination"].items():
            lines.append(f"- {k}: {v:.4f}")
    return "\n".join(lines) + "\n"


def _persist(
    out_dir: Path, name: str, universe: str, report: dict[str, Any], cfg: dict[str, Any]
) -> Path:
    stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
    run_dir = out_dir / f"{name}_{universe}_{stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "report.json").write_text(json.dumps(report, indent=2, sort_keys=True))
    (run_dir / "config.json").write_text(json.dumps(cfg, indent=2, sort_keys=True))
    (run_dir / "REPORT.md").write_text(_write_report_md(report, cfg))
    return run_dir


def cmd_list(args: argparse.Namespace) -> int:
    print("strategies:", ", ".join(available_strategies()))
    print("portfolios:", ", ".join(available_portfolios()))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    cfg = _resolve_config(args)
    name: str = cfg["strategy"]
    universe: str = cfg.get("universe", "synthetic")
    panel = _build_panel(
        universe, cfg.get("n_days", 1500), cfg.get("n_assets", 50), cfg.get("seed", 0)
    )

    params = {k: cfg[k] for k in _STRATEGY_PARAM_KEYS if k in cfg}
    try:
        strat = get_strategy(name, **params)
    except (KeyError, TypeError) as exc:
        raise SystemExit(f"could not build strategy {name!r}: {exc}") from exc

    known_names: list[str] = list(cfg.get("knowns") or [])
    knowns: dict[str, SignalFn] = {n: get_strategy(n).signals for n in known_names}
    rep = run_research_study(
        panel,
        strat.signals,
        name=name,
        cost_bps=cfg.get("cost_bps", 10.0),
        n_trials=cfg.get("n_trials", 1),
        weight_fn=strat.weight_fn,  # type: ignore[attr-defined]
        horizon=cfg.get("horizon", 1),
        knowns=knowns or None,
    )
    print_report(rep)

    oos = None
    if cfg.get("oos"):
        oos = run_walk_forward(
            panel, strat.signals, n_splits=cfg.get("n_splits", 5), embargo=cfg.get("embargo", 5)
        )
        print(f"\n[OOS] walk-forward Sharpe = {oos['oos_sharpe']:.3f}")

    report = _report_to_dict(rep, oos)
    run_dir = _persist(Path(cfg.get("out", "results")), name, universe, report, cfg)
    print(f"\nartifacts -> {run_dir}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Validate-the-validator: confirm the no-look-ahead guard catches an injected leak."""
    panel = make_synthetic_panel(n_days=args.n_days, n_assets=args.n_assets, seed=args.seed)
    leak = boundary_lookahead_discrepancy(leaky_signal, panel)
    from .strategy import get_strategy as _gs

    clean = boundary_lookahead_discrepancy(_gs("momentum").signals, panel)
    print("[validate] no-look-ahead guard (boundary discrepancy; 0 == non-anticipating)")
    print(
        f"  leaky signal (uses next-day return): {leak:.6f}  -> {'CAUGHT' if leak > 0 else 'MISSED'}"
    )
    print(
        f"  clean signal (momentum):             {clean:.6f}  -> {'ok' if clean == 0 else 'LEAK'}"
    )
    return 0 if (leak > 0 and clean == 0) else 1


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="rp", description="research-pipeline command line")
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("list", help="list registered strategies and portfolios")
    pl.set_defaults(func=cmd_list)

    pr = sub.add_parser("run", help="run a strategy study and write artifacts")
    pr.add_argument("strategy", nargs="?", default=None, help="registered strategy name")
    pr.add_argument(
        "-c", "--config", default=None, help="JSON run config to replay (flags override)"
    )
    pr.add_argument("--universe", default=None, help="synthetic (default) | ken-french-49")
    pr.add_argument("--lookback", type=int, default=None)
    pr.add_argument("--skip", type=int, default=None)
    pr.add_argument(
        "--portfolio", default=None, help="dollar_neutral|long_only|long_short_quantile|directional"
    )
    pr.add_argument("--cost-bps", dest="cost_bps", type=float, default=None)
    pr.add_argument(
        "--n-trials",
        dest="n_trials",
        type=int,
        default=None,
        help="variants searched (deflated Sharpe)",
    )
    pr.add_argument("--horizon", type=int, default=None, help="holding horizon in periods")
    pr.add_argument("--knowns", nargs="*", default=None, help="known strategies for incrementality")
    pr.add_argument(
        "--oos", action="store_true", default=None, help="also run a walk-forward OOS study"
    )
    pr.add_argument("--n-splits", dest="n_splits", type=int, default=None)
    pr.add_argument("--embargo", type=int, default=None)
    pr.add_argument("--n-days", dest="n_days", type=int, default=None)
    pr.add_argument("--n-assets", dest="n_assets", type=int, default=None)
    pr.add_argument("--seed", type=int, default=None)
    pr.add_argument("--out", default=None, help="output directory (default: results/)")
    pr.set_defaults(func=cmd_run)

    pv = sub.add_parser("validate", help="validate-the-validator: leak-detection gate")
    pv.add_argument("--n-days", dest="n_days", type=int, default=600)
    pv.add_argument("--n-assets", dest="n_assets", type=int, default=20)
    pv.add_argument("--seed", type=int, default=0)
    pv.set_defaults(func=cmd_validate)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if (
        args.func is cmd_run
        and not getattr(args, "strategy", None)
        and not getattr(args, "config", None)
    ):
        raise SystemExit("run: provide a strategy name or --config")
    result: int = args.func(args)
    return result


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
