"""Point-in-time "leakage tax" study: THRESHOLD / LEVEL signal on nonfarm payrolls.

This is the fourth cell of the "where does point-in-time matter" map, and it tests the axis the
three prior nulls all pointed at: SIGNAL FUNCTIONAL FORM.

The story so far
----------------
  * ``commodity-leakage-tax/run_study.py``     -- CFTC COT, release-timing only -> null.
  * ``commodity-leakage-tax/run_study_eia.py`` -- EIA gas storage, data revision but TINY
    revisions -> null (no revision to leak).
  * ``run_study_macro.py``                     -- PAYEMS payrolls, HUGE revisions, real PIT edge,
    yet STILL null. Diagnosis: the signal is a STANDARDIZED, CLIPPED z-score. A 45%-of-change
    revision, once de-trended and divided by its trailing dispersion, moves the z-score by only a
    few tenths; both arms take near-identical CONTINUOUS positions, so their return streams barely
    diverge. The standardization absorbs the revision.

The hypothesis this study isolates
----------------------------------
The leakage tax needs THREE conditions jointly: (1) large revisions, (2) a real edge, and
(3) a revision-SENSITIVE signal functional form. The payrolls study satisfied (1) and (2) but not
(3). Here we hold (1) and (2) fixed (SAME PAYEMS series, SAME PIT-vs-naive vintage machinery) and
flip (3): replace the smooth standardized z-score with a DISCONTINUOUS THRESHOLD rule.

The signal
----------
Binary regime. Decision on the reported month-over-month change in payrolls vs a fixed threshold
``k`` (thousands of jobs):

    position = -1 (SHORT SPY) if MoM change >= k          # big jobs print -> fade
    position = +1 (LONG SPY)  if MoM change <  k

The economic direction is identical to the standardized study (fade a hot jobs print: "good news
is bad news" / rising-discount-rate channel dominates the monthly equity reaction), so the only
thing that changes versus the prior null is the FUNCTIONAL FORM: a hard step at ``k`` instead of a
smooth, clipped, standardized tilt. This is the form that can FLIP: if the first-release change is
just below ``k`` and the revised change is just above (or vice-versa), the two arms take OPPOSITE
positions. That flip is the mechanistic driver of any revision leakage.

NAIVE uses the revised MoM change vs ``k``; PIT uses the first-release MoM change vs ``k``. As in
the sibling study, RELEASE TIMING is held identical (entry = first SPY open on/after the genuine
ALFRED ``realtime_start``), so the only difference between the arms is which vintage's change is
compared to the threshold.

Threshold choice
----------------
``k`` is set near the TYPICAL first-release change so that the boundary sits where many months
actually land and revisions cross it often (a threshold far in the tail is never flipped and is
mechanically null for an uninteresting reason). The study SWEEPS several candidate ``k`` values,
reports the flip rate at each, and runs the full leakage-tax battery at the ``k`` whose flip rate
is highest among economically plausible thresholds (the most adversarial case for finding a tax).
The median first-release change over the sample is ~197k; the default sweep brackets it.

The headline diagnostic: FLIP RATE
----------------------------------
flip_rate = fraction of decision months where naive and PIT take DIFFERENT positions (the revision
crossed ``k``). This is reported FIRST and is the quantity the standardized study could not
exhibit at all (its positions never strictly flipped, they only nudged). We also report, on the
flip months only, the realized SPY forward return and the naive-minus-PIT return, to see whether
the flips actually cost or help.

The leakage tax (same metrics as the sibling)
---------------------------------------------
SR_naive vs SR_pit, tax in Sharpe and bps/yr, Newey-West HAC t-stat on the monthly return
DIFFERENCE r_naive - r_pit, full sample and sub-periods, plus the flat-book null check on the PIT
arm. Either outcome is a valid result: a nonzero tax confirms functional form is the binding axis;
a continued null even WITH flips is a stronger, more surprising finding.

Reuse
-----
This file deliberately imports the ALFRED-vintage loading (``load_first_release``,
``load_revised``, ``monthly_change``), the ``PricePanel`` SPY loader (``load_spy``), the
``newey_west_tstat``, the per-arm ``summarize``, the period-slicing, and the entry/assembly
machinery from ``run_study_macro``. Only the SIGNAL (``build_threshold_signal``) is new.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse verified primitives from the flagship research pipeline.
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

# Reuse the sibling study's data loading, stats, and assembly verbatim.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from run_study_macro import (  # noqa: E402
    MonthlyBacktest,
    _f,
    _slice,
    assemble,
    load_first_release,
    load_revised,
    load_spy,
    monthly_change,
    newey_west_tstat,
    summarize,
)
from research_pipeline.data import PricePanel  # noqa: E402

SERIES_ID = "PAYEMS"
# Candidate thresholds (thousands of jobs) bracketing the ~197k median first-release change.
# Near the median is where the most months sit close to the boundary, so revisions cross it most.
THRESHOLD_SWEEP_K: tuple[float, ...] = (0.0, 100.0, 150.0, 197.0, 200.0, 250.0)


# --------------------------------------------------------------------------------------
# Signal: discontinuous threshold regime (the one new piece vs run_study_macro)
# --------------------------------------------------------------------------------------
def build_threshold_signal(level: pd.Series, release_date: pd.Series, k: float) -> pd.DataFrame:
    """Binary threshold regime from a payrolls-level vintage.

    The reported MoM change is compared to ``k``: ``position = -1`` (short SPY) when the change is
    at or above ``k`` (a hot print, faded), else ``position = +1`` (long SPY). The position is a
    HARD STEP at ``k``, so a revision that moves the change across ``k`` flips the sign. Feeding
    the revised level gives the NAIVE arm; feeding the first-release level gives the PIT arm.

    Returns a frame indexed by reference month with columns: change, position, release_date.
    """
    change = monthly_change(level)
    position = pd.Series(
        np.where(change.to_numpy() >= k, -1.0, 1.0), index=change.index, name="position"
    )
    df = pd.DataFrame({"change": change, "position": position, "release_date": release_date})
    # Drop the first month (no change) and any month without a release timestamp.
    return df.dropna(subset=["change", "release_date"])


# --------------------------------------------------------------------------------------
# Flip-rate diagnostics (the headline quantity the standardized study could not show)
# --------------------------------------------------------------------------------------
def flip_diagnostics(
    naive_sig: pd.DataFrame,
    pit_sig: pd.DataFrame,
    naive_bt: MonthlyBacktest,
    pit_bt: MonthlyBacktest,
    spy_first_day: pd.Timestamp,
) -> dict[str, object]:
    """Flip rate (signal level) and the realized cost of flips (return level).

    A flip is a decision month where the naive and PIT positions DIFFER (the revision crossed the
    threshold). The HEADLINE flip rate is computed over the TRADABLE decision set, months whose
    release date falls on/after SPY's first trading day, because pre-1993 reference months are not
    tradable (their release predates SPY and all collapse onto SPY's first day in ``assemble``).
    We also report the full-series flip rate for context. At the return level we restrict to flip
    months that actually traded and report mean SPY forward return and mean (naive - PIT) return on
    those months, with a Newey-West t-stat on the latter.
    """
    common_all = naive_sig.index.intersection(pit_sig.index)
    pn_all = naive_sig.loc[common_all, "position"]
    pp_all = pit_sig.loc[common_all, "position"]
    flipped_all = pn_all != pp_all
    n_common_all = int(len(common_all))
    n_flip_all = int(flipped_all.sum())

    # Tradable subset: release date on/after SPY's first trading day.
    rel = pit_sig.loc[common_all, "release_date"]
    tradable = pd.DatetimeIndex(rel.to_numpy()) >= spy_first_day
    common = common_all[tradable]
    pn = naive_sig.loc[common, "position"]
    pp = pit_sig.loc[common, "position"]
    flipped = pn != pp
    n_common = int(len(common))
    n_flip = int(flipped.sum())

    flip_months = pd.DatetimeIndex(common[flipped.to_numpy()])

    # Realized impact, restricted to flip months that actually traded in BOTH arms. The backtest
    # is indexed by ENTRY trading day, not reference month, so map flip reference months through
    # ``entry_by_month`` to entry days before intersecting with the traded set. (A flip month is
    # the SAME reference month in both arms; release timing is held identical, so its entry day is
    # identical, and we map via the PIT arm.)
    e_by_m = pit_bt.entry_by_month
    flip_in_index = flip_months.intersection(pd.DatetimeIndex(e_by_m.index))
    flip_entry = pd.DatetimeIndex(e_by_m.reindex(flip_in_index).dropna().to_numpy())
    traded = naive_bt.monthly_index.intersection(pit_bt.monthly_index)
    flip_traded = flip_entry.intersection(traded)
    rn = naive_bt.strat_returns.reindex(flip_traded).dropna()
    rp = pit_bt.strat_returns.reindex(flip_traded).dropna()
    # SPY forward return on flip months (same in both arms; use the PIT arm's fwd).
    fwd_flip = pit_bt.fwd_returns.reindex(flip_traded).dropna()
    diff_flip = (rn - rp).reindex(flip_traded).dropna()
    mean_d, t_d, lag = newey_west_tstat(diff_flip.to_numpy())

    return {
        "threshold_k": float("nan"),  # filled by caller
        "n_common_decision_months": n_common,  # tradable (release on/after SPY start)
        "n_flip_months": n_flip,
        "flip_rate": float(n_flip / n_common) if n_common else float("nan"),
        "n_common_decision_months_full_series": n_common_all,
        "n_flip_months_full_series": n_flip_all,
        "flip_rate_full_series": float(n_flip_all / n_common_all) if n_common_all else float("nan"),
        "n_flip_months_traded": int(len(flip_traded)),
        "flip_mean_spy_fwd_return": float(fwd_flip.mean()) if len(fwd_flip) else float("nan"),
        "flip_mean_naive_return": float(rn.mean()) if len(rn) else float("nan"),
        "flip_mean_pit_return": float(rp.mean()) if len(rp) else float("nan"),
        "flip_mean_naive_minus_pit": mean_d,
        "flip_diff_nw_tstat": t_d,
        "flip_diff_nw_lag": lag,
    }


# --------------------------------------------------------------------------------------
# Leakage-tax battery at a single threshold (mirrors run_study_macro.run)
# --------------------------------------------------------------------------------------
def leakage_tax_at_threshold(
    panel: PricePanel,
    revised: pd.Series,
    first_level: pd.Series,
    release: pd.Series,
    k: float,
) -> dict[str, object]:
    """Full PIT-vs-naive leakage-tax battery for one threshold ``k`` (same metrics as sibling)."""
    naive_sig = build_threshold_signal(revised, release, k)
    pit_sig = build_threshold_signal(first_level, release, k)
    naive = assemble(panel, naive_sig)
    pit = assemble(panel, pit_sig)

    spy_first_day = pd.Timestamp(panel.prices.index.min())
    flips = flip_diagnostics(naive_sig, pit_sig, naive, pit, spy_first_day)
    flips["threshold_k"] = float(k)

    common = naive.monthly_index.intersection(pit.monthly_index)
    rn = naive.strat_returns.reindex(common)
    rp = pit.strat_returns.reindex(common)
    diff = (rn - rp).dropna()

    periods: dict[str, pd.Series] = {
        "full": pd.Series(True, index=common),
        "pre_2008": pd.Series(common < pd.Timestamp("2008-01-01"), index=common),
        "2008_2016": pd.Series(
            (common >= pd.Timestamp("2008-01-01")) & (common < pd.Timestamp("2016-01-01")),
            index=common,
        ),
        "2016_2026": pd.Series(common >= pd.Timestamp("2016-01-01"), index=common),
    }

    periods_out: dict[str, object] = {}
    for pname, pmask in periods.items():
        sel = common[pmask.to_numpy()]
        nsub = _slice(naive, naive.monthly_index.isin(sel))
        psub = _slice(pit, pit.monthly_index.isin(sel))
        d = diff.reindex(sel).dropna()
        mean_d, t_d, lag = newey_west_tstat(d.to_numpy())
        sn = summarize(nsub, f"naive_{pname}")
        sp = summarize(psub, f"pit_{pname}")
        tax_sharpe = _f(sn, "sharpe") - _f(sp, "sharpe")
        tax_bps = (_f(sn, "ann_return") - _f(sp, "ann_return")) * 1e4
        periods_out[pname] = {
            "naive": sn,
            "pit": sp,
            "tax_sharpe": tax_sharpe,
            "tax_bps_per_year": tax_bps,
            "diff_mean_monthly": mean_d,
            "diff_nw_tstat": t_d,
            "diff_nw_lag": lag,
            "pit_clears_null": bool(_f(sp, "sharpe") > 0.0),
        }

    return {
        "threshold_k": float(k),
        "n_trade_months_common": int(len(common)),
        "flips": flips,
        "periods": periods_out,
    }


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def run() -> dict[str, object]:
    panel = load_spy()
    first = load_first_release()
    revised = load_revised()
    first_level = first["level"]
    release = first["release_date"]

    # Revision-magnitude context (reused logic from the sibling, for the report).
    ch_first = monthly_change(first_level)
    ch_rev = monthly_change(revised)
    common_ch = ch_first.dropna().index.intersection(ch_rev.dropna().index)
    typ_change = float(ch_first.reindex(common_ch).abs().median())
    change_diff = (ch_rev.reindex(common_ch) - ch_first.reindex(common_ch)).dropna()

    # Sweep thresholds; record the flip rate at each so we can pick the most adversarial.
    sweep: list[dict[str, object]] = []
    for k in THRESHOLD_SWEEP_K:
        res_k = leakage_tax_at_threshold(panel, revised, first_level, release, k)
        sweep.append(res_k)

    # Headline threshold. The leakage tax is only economically meaningful where the PIT (honest)
    # arm has a real edge (condition 2 of the three-condition thesis), so prefer the highest-flip
    # threshold AMONG those whose full-sample PIT Sharpe clears the flat-book null. If none clears,
    # fall back to the highest flip rate overall and flag it.
    def _flip_rate(r: dict[str, object]) -> float:
        flips = r["flips"]
        assert isinstance(flips, dict)
        return _f(flips, "flip_rate")

    def _pit_clears_full(r: dict[str, object]) -> bool:
        periods = r["periods"]
        assert isinstance(periods, dict)
        full = periods["full"]
        assert isinstance(full, dict)
        return bool(full.get("pit_clears_null", False))

    edge_bearing = [r for r in sweep if _pit_clears_full(r)]
    if edge_bearing:
        headline = max(edge_bearing, key=_flip_rate)
        headline_basis = (
            "highest flip rate among edge-bearing thresholds (PIT clears flat-book null)"
        )
    else:
        headline = max(sweep, key=_flip_rate)
        headline_basis = "highest flip rate overall (no threshold's PIT arm cleared the null)"

    out: dict[str, object] = {
        "series_id": SERIES_ID,
        "signal": "binary threshold regime: position = -1 if MoM change >= k else +1 (fade hot print)",
        "median_abs_first_release_change_k": typ_change,
        "mean_abs_change_revision_k": float(change_diff.abs().mean()),
        "max_abs_change_revision_k": float(change_diff.abs().max()),
        "first_release_first": str(first_level.index.min().date()),
        "first_release_last": str(first_level.index.max().date()),
        "spy_first": str(panel.prices.index.min().date()),
        "spy_last": str(panel.prices.index.max().date()),
        "threshold_sweep_k": list(THRESHOLD_SWEEP_K),
        "headline_threshold_k": _f(headline, "threshold_k"),
        "headline_basis": headline_basis,
        "sweep": sweep,
        "headline": headline,
    }
    return out


def _fmt_sweep_row(r: dict[str, object]) -> str:
    flips = r["flips"]
    assert isinstance(flips, dict)
    periods = r["periods"]
    assert isinstance(periods, dict)
    full = periods["full"]
    assert isinstance(full, dict)
    sn = full["naive"]
    sp = full["pit"]
    sr_n = _f(sn, "sharpe") if isinstance(sn, dict) else float("nan")
    sr_p = _f(sp, "sharpe") if isinstance(sp, dict) else float("nan")
    return (
        f"{_f(r, 'threshold_k'):>7.0f} "
        f"{_f(flips, 'flip_rate'):>8.1%} "
        f"{int(_f(flips, 'n_flip_months')):>6d} "
        f"{sr_n:>+7.2f} "
        f"{sr_p:>+7.2f} "
        f"{_f(full, 'tax_sharpe'):>+7.2f} "
        f"{_f(full, 'tax_bps_per_year'):>+9.0f} "
        f"{_f(full, 'diff_nw_tstat'):>+6.2f}"
    )


def main() -> None:
    res = run()
    out_path = Path(__file__).resolve().parent / "results_leakage_tax_threshold.json"
    out_path.write_text(json.dumps(res, indent=2, default=str))

    print("\nNonfarm payrolls (PAYEMS) THRESHOLD-signal data-revision leakage-tax study")
    print(
        f"first-release months: {res['first_release_first']} -> {res['first_release_last']}; "
        f"typical |MoM change| ~{_f(res, 'median_abs_first_release_change_k'):.0f}k; "
        f"mean |change revision| {_f(res, 'mean_abs_change_revision_k'):.0f}k "
        f"(max {_f(res, 'max_abs_change_revision_k'):.0f}k)"
    )
    print(f"SPY: {res['spy_first']} -> {res['spy_last']}; signal = {res['signal']}\n")

    print("Threshold sweep (flipRate over tradable months; SR/tax full-sample):")
    hdr = (
        f"{'k(jobs)':>7} {'flipRate':>8} {'#flip':>6} "
        f"{'SR_nv':>7} {'SR_pit':>7} {'tax_SR':>7} {'tax_bps':>9} {'NW_t':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    sweep = res["sweep"]
    assert isinstance(sweep, list)
    for r in sweep:
        assert isinstance(r, dict)
        print(_fmt_sweep_row(r))

    headline = res["headline"]
    assert isinstance(headline, dict)
    flips = headline["flips"]
    assert isinstance(flips, dict)
    print(f"\nHeadline threshold k = {_f(headline, 'threshold_k'):.0f}k -- {res['headline_basis']}")
    print(
        f"  flip rate (tradable) = {_f(flips, 'flip_rate'):.1%} "
        f"({int(_f(flips, 'n_flip_months'))} of {int(_f(flips, 'n_common_decision_months'))} months); "
        f"full-series flip rate = {_f(flips, 'flip_rate_full_series'):.1%} "
        f"({int(_f(flips, 'n_flip_months_full_series'))} of "
        f"{int(_f(flips, 'n_common_decision_months_full_series'))})"
    )
    print(
        f"On flip months (n traded = {int(_f(flips, 'n_flip_months_traded'))}): "
        f"mean SPY fwd ret {_f(flips, 'flip_mean_spy_fwd_return'):+.4f}, "
        f"mean naive ret {_f(flips, 'flip_mean_naive_return'):+.4f}, "
        f"mean PIT ret {_f(flips, 'flip_mean_pit_return'):+.4f}, "
        f"mean (naive-PIT) {_f(flips, 'flip_mean_naive_minus_pit'):+.4f} "
        f"(NW t {_f(flips, 'flip_diff_nw_tstat'):+.2f})\n"
    )

    periods = headline["periods"]
    assert isinstance(periods, dict)
    hdr2 = (
        f"{'period':>10} {'variant':>7} {'ann_ret':>9} {'sharpe':>7} "
        f"{'hit':>6} {'IC':>7} {'maxDD':>8} | {'tax_SR':>7} {'tax_bps':>9} {'NW_t':>6}"
    )
    print(f"Headline threshold k={_f(headline, 'threshold_k'):.0f}k -- full leakage-tax battery:")
    print(hdr2)
    print("-" * len(hdr2))
    for pname, blk in periods.items():
        assert isinstance(blk, dict)
        for variant in ("naive", "pit"):
            s = blk[variant]
            assert isinstance(s, dict)
            tax_sr = f"{_f(blk, 'tax_sharpe'):+.2f}" if variant == "naive" else ""
            tax_bps = f"{_f(blk, 'tax_bps_per_year'):+.0f}" if variant == "naive" else ""
            nwt = f"{_f(blk, 'diff_nw_tstat'):+.2f}" if variant == "naive" else ""
            print(
                f"{pname:>10} {variant:>7} {_f(s, 'ann_return'):>+9.4f} "
                f"{_f(s, 'sharpe'):>+7.2f} {_f(s, 'hit_rate'):>6.2f} "
                f"{_f(s, 'ic'):>+7.3f} {_f(s, 'max_drawdown'):>+8.3f} "
                f"| {tax_sr:>7} {tax_bps:>9} {nwt:>6}"
            )
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
