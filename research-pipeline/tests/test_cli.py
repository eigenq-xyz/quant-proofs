"""CLI smoke + artifact tests — drive ``main`` offline (synthetic universe) end to end."""

from __future__ import annotations

import json
from pathlib import Path

from research_pipeline.cli import main


def test_list_runs(capsys) -> None:  # type: ignore[no-untyped-def]
    assert main(["list"]) == 0
    out = capsys.readouterr().out
    assert "momentum" in out
    assert "dollar_neutral" in out


def test_run_writes_artifacts(tmp_path: Path) -> None:
    rc = main(
        [
            "run",
            "momentum",
            "--universe",
            "synthetic",
            "--n-days",
            "400",
            "--n-assets",
            "15",
            "--seed",
            "0",
            "--n-trials",
            "10",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    runs = list(tmp_path.glob("momentum_synthetic_*"))
    assert len(runs) == 1
    run_dir = runs[0]
    for fname in ("report.json", "config.json", "REPORT.md"):
        assert (run_dir / fname).exists()
    report = json.loads((run_dir / "report.json").read_text())
    assert report["name"] == "momentum"
    assert "net_sharpe" in report["backtest_summary"]
    assert "ic" in report  # cross-sectional panel


def test_run_replays_config_with_override(tmp_path: Path) -> None:
    cfg = {
        "strategy": "momentum",
        "universe": "synthetic",
        "n_days": 400,
        "n_assets": 15,
        "seed": 1,
        "cost_bps": 10.0,
    }
    cfg_path = tmp_path / "run.json"
    cfg_path.write_text(json.dumps(cfg))
    # Flag overrides the config's cost_bps.
    rc = main(["run", "-c", str(cfg_path), "--cost-bps", "25", "--out", str(tmp_path)])
    assert rc == 0
    run_dir = next(iter(tmp_path.glob("momentum_synthetic_*")))
    saved_cfg = json.loads((run_dir / "config.json").read_text())
    assert saved_cfg["cost_bps"] == 25.0


def test_run_with_oos_and_knowns(tmp_path: Path) -> None:
    rc = main(
        [
            "run",
            "momentum",
            "--n-days",
            "500",
            "--n-assets",
            "15",
            "--oos",
            "--knowns",
            "reversal",
            "--out",
            str(tmp_path),
        ]
    )
    assert rc == 0
    run_dir = next(iter(tmp_path.glob("momentum_synthetic_*")))
    report = json.loads((run_dir / "report.json").read_text())
    assert "oos_sharpe" in report
    assert "combination" in report


def test_validate_catches_leak(capsys) -> None:  # type: ignore[no-untyped-def]
    rc = main(["validate", "--n-days", "400", "--n-assets", "15"])
    out = capsys.readouterr().out
    assert "CAUGHT" in out
    assert rc == 0
