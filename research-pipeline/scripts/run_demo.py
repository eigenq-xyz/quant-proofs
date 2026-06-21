"""End-to-end demo: run the full research-desk workflow offline on synthetic data.

python -m scripts.run_demo
"""

from __future__ import annotations

from research_pipeline import (
    make_synthetic_panel,
    momentum_signal,
    print_report,
    run_cross_asset,
    run_research_study,
)


def main() -> None:
    panel = make_synthetic_panel(n_days=1500, n_assets=50, seed=0)

    # Full single-signal study (all stages, with honest significance).
    report = run_research_study(panel, momentum_signal, name="momentum", cost_bps=10.0, n_trials=20)
    print_report(report)

    # Cross-asset generalisation (the same pipeline across 'asset classes').
    print("\n================ cross-asset generalisation ================")
    panels = {
        "equities": make_synthetic_panel(seed=0),
        "futures": make_synthetic_panel(seed=1, momentum_strength=0.03),
        "fx": make_synthetic_panel(seed=2, momentum_strength=0.02),
    }
    summary_df, corr_df = run_cross_asset(panels, momentum_signal)
    print(summary_df[["net_sharpe", "mean_IC", "avg_turnover"]].round(3).to_string())
    print("\nNet-return correlation across asset classes:")
    print(corr_df.round(2).to_string())


if __name__ == "__main__":
    main()
