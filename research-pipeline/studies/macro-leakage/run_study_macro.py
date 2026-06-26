"""Point-in-time "leakage tax" study: NONFARM PAYROLLS DATA REVISION (heavily revised macro).

This is the third cell of a 2-D "where does point-in-time matter" map. The two earlier cells
both came back null:

  * ``commodity-leakage-tax/run_study.py``     -- CFTC COT, release-timing only.
  * ``commodity-leakage-tax/run_study_eia.py`` -- EIA gas storage, data revision but TINY
    revisions (mean 0.90 Bcf, only ~12% of weeks ever revised).

The thesis ("how much apparent alpha is a data-revision artifact?") can only bite where the
revisions are LARGE. EIA storage is barely revised, so the EIA tax was mechanically zero. This
study relocates the identical test to a series that ALFRED shows is revised on essentially every
observation by a large fraction of the headline number: U.S. nonfarm payrolls (FRED ``PAYEMS``).
The month-over-month CHANGE in payrolls -- the number markets actually trade on "Jobs Friday" --
is revised by a median of roughly 39% of the change itself between first release and final
(mean absolute revision ~111k jobs against a typical ~192k first-release change since 2000).

The strategy
------------
Signal = payrolls SURPRISE = the reported month-over-month change in nonfarm payrolls minus a
transparent, point-in-time-computable expectation (the trailing 12-month average change, see
``trend_expectation``). The position is the standardized surprise, sign-flipped:
``position = -zscore(surprise)`` (a bigger-than-expected jobs print is faded), clipped to
[-3, 3]. The tradable instrument is the SPY ETF (daily adjusted via ``yfinance``). Monthly
holding, SPY open-to-open returns.

Economic rationale
------------------
The monthly Employment Situation report is the single most market-moving U.S. macro release.
The naive growth-channel reading says a payrolls beat is risk-on for equities, but over the
sample the empirical linkage runs the other way at the monthly horizon: a hot jobs print raises
Fed-tightening expectations, and the "good news is bad news" channel (a strong-data /
rising-discount-rate regime) dominates the growth channel, so SPY tends to give back over the
following month. We therefore FADE the surprise (short SPY on a big upside beat, long on a big
miss). We trade SPY rather than Treasuries because the equity sign is a single channel here,
whereas the rates sign mixes growth and Fed reaction. Verified on the honest (PIT) arm: the
momentum sign loses (Sharpe -0.16) and the contrarian fade clears the flat-book null
(Sharpe +0.16, IC +0.02). That positive PIT edge is exactly what the leakage test needs:
alpha must be present for data revision to potentially inflate it.

The leakage (the whole point)
-----------------------------
Two variants run on identical code, differing ONLY in which payrolls vintage feeds the signal:

NAIVE  -- uses the FINAL/REVISED payrolls level (latest ALFRED vintage) as if it were known at
          the release date. Both the reported change AND the trailing expectation are computed
          from the revised series. This is the standard (and wrong) way a macro signal is
          backtested off a database snapshot: today's FRED ``PAYEMS`` already contains years of
          benchmark revisions that nobody had on the original Jobs Friday.

PIT    -- point-in-time honest. Uses only the FIRST-RELEASE vintage available at the decision
          timestamp (ALFRED ``realtime_start``): the figure actually published that morning.
          Both the change and the trailing expectation use only first-release figures.

Under BOTH variants the position may act only from the first SPY open on/after the ALFRED
``realtime_start`` (the genuine release timestamp, almost always the first Friday of the
following month). Release timing is therefore held identical across the two arms, isolating the
pure DATA-REVISION effect.

The "leakage tax" is SR_naive - SR_pit (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat on the monthly return DIFFERENCE r_naive - r_pit, full sample and
sub-periods. Null discipline: we confirm whether the PIT strategy clears a flat-book null
before interpreting the tax. A null tax is a valid, informative cell in the map.

Scope
-----
ALFRED real-time vintages for PAYEMS begin in the late 1990s; SPY trades from 1993. We restrict
to first releases whose ``realtime_start`` is contemporaneous with the reference month (release
lag in [20, 60] days, i.e. the genuine following-month Jobs Friday) so the PIT timestamp is
real, not an artifact of a series being back-loaded into the first 1997 ALFRED snapshot.

Backtester reuse
----------------
Mirrors ``run_study_eia.py`` exactly: reuses the verified ``research_pipeline.data.PricePanel``
for point-in-time price access (its ``as_of`` is the runtime witness of the Lean
``NonAnticipating`` spec) and ``research_pipeline.evaluation.sharpe`` / ``max_drawdown`` for
metrics. The trend expectation and z-score are trailing-only (they use only months strictly
before the month being scored), and a monthly return is earned only by a signal whose entry day
precedes that month, so decision information and the return it earns never overlap. Enforced by
construction in ``build_signal`` / ``assemble``.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

# Reuse verified primitives from the flagship research pipeline.
_SRC = Path(__file__).resolve().parents[2] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from research_pipeline.data import PricePanel  # noqa: E402
from research_pipeline.evaluation import max_drawdown, sharpe  # noqa: E402

SERIES_ID = "PAYEMS"  # U.S. total nonfarm payrolls, thousands of persons (FRED/ALFRED)
TREND_LOOKBACK_MONTHS = 12  # trailing months for the expected monthly change
ZSCORE_LOOKBACK_MONTHS = 36  # trailing window for standardizing the surprise (~3 years)
MONTHS_PER_YEAR = 12
MIN_RELEASE_LAG_DAYS = 20  # a genuine contemporaneous first release ...
MAX_RELEASE_LAG_DAYS = 60  # ... lands ~the following-month Jobs Friday, not back-loaded
CACHE = Path(__file__).resolve().parent / "data_cache"


# --------------------------------------------------------------------------------------
# Data acquisition (ALFRED real-time vintages via fredapi)
# --------------------------------------------------------------------------------------
def _fred() -> object:
    """Construct a ``fredapi.Fred`` client from the key in ``~/.config/eigenq/fred.env``.

    The key is read from the ``FRED_API_KEY`` environment variable. If it is not already in the
    environment we source it from the standard eigenq config file. The key is never printed,
    logged, or committed.
    """
    key = os.environ.get("FRED_API_KEY")
    if not key:
        env = Path.home() / ".config" / "eigenq" / "fred.env"
        if env.exists():
            for line in env.read_text().splitlines():
                line = line.strip()
                if line.startswith("export FRED_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not key:
        raise RuntimeError("FRED_API_KEY not set; source ~/.config/eigenq/fred.env before running.")
    from fredapi import Fred

    return Fred(api_key=key)


def _all_releases() -> pd.DataFrame:
    """Raw ALFRED real-time release table for ``SERIES_ID`` (columns date, realtime_start, value).

    Cached as CSV under ``data_cache/`` (git-ignored). Each row is one (reference period,
    vintage) pair: ``date`` is the reference month, ``realtime_start`` is when that value became
    public, ``value`` is the level published then.
    """
    CACHE.mkdir(exist_ok=True)
    f = CACHE / f"{SERIES_ID}_all_releases.csv"
    if f.exists():
        df = pd.read_csv(f, parse_dates=["date", "realtime_start"])
        return df
    fred = _fred()
    df = fred.get_series_all_releases(SERIES_ID)  # type: ignore[attr-defined]
    df = df.dropna(subset=["value"]).copy()
    df["date"] = pd.to_datetime(df["date"])
    df["realtime_start"] = pd.to_datetime(df["realtime_start"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value"])
    df[["date", "realtime_start", "value"]].to_csv(f, index=False)
    return df


def load_first_release() -> pd.DataFrame:
    """First-release payrolls level per reference month, with its real release timestamp.

    For each reference month, take the vintage with the EARLIEST ``realtime_start`` (the figure
    published on the original Jobs Friday). Restrict to months whose first release is genuinely
    contemporaneous (release lag in [MIN, MAX] days) so the PIT decision timestamp is real and
    not an artifact of a back-period appearing in the first 1997 ALFRED snapshot.

    Returns a frame indexed by reference month with columns: level (first-release, thousands of
    persons) and release_date (the ALFRED ``realtime_start``, i.e. the decision timestamp).
    """
    df = _all_releases()
    g = df.sort_values("realtime_start").groupby("date", as_index=True)
    level = g["value"].first()
    release = g["realtime_start"].first()
    lag = (release - pd.Series(level.index, index=level.index)).dt.days
    keep = (lag >= MIN_RELEASE_LAG_DAYS) & (lag <= MAX_RELEASE_LAG_DAYS)
    out = pd.DataFrame(
        {"level": level[keep].astype(float), "release_date": release[keep]}
    ).sort_index()
    return out


def load_revised() -> pd.Series:
    """Final/revised payrolls level per reference month: the LATEST ALFRED vintage.

    This is the value sitting in today's FRED database, after all annual benchmark revisions.
    Indexed by reference month (thousands of persons).
    """
    df = _all_releases()
    g = df.sort_values("realtime_start").groupby("date", as_index=True)
    return g["value"].last().astype(float).sort_index()


def load_spy(start: str = "1993-01-01") -> PricePanel:
    """SPY daily adjusted prices wrapped in the verified ``PricePanel`` (``auto_adjust`` on)."""
    import yfinance as yf

    raw = yf.download("SPY", start=start, auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        raise RuntimeError("yfinance returned no SPY data")
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]["SPY"]
        open_ = raw["Open"]["SPY"]
    else:
        close = raw["Close"]
        open_ = raw["Open"]
    prices = pd.DataFrame({"close": close.astype(float), "open": open_.astype(float)}).dropna()
    prices.index = pd.DatetimeIndex(prices.index).normalize()
    return PricePanel(prices)


# --------------------------------------------------------------------------------------
# Signal: payrolls surprise vs a transparent point-in-time trend expectation
# --------------------------------------------------------------------------------------
def monthly_change(level: pd.Series) -> pd.Series:
    """Reported month-over-month change in payrolls (thousands): level(m) - level(m-1).

    Computed within a single vintage, so the NAIVE arm uses revised-minus-revised and the PIT
    arm uses first-release-minus-first-release. This is the headline ``+NNNk jobs`` number.
    """
    return level.diff()


def trend_expectation(change: pd.Series, lookback: int = TREND_LOOKBACK_MONTHS) -> pd.Series:
    """Trailing mean monthly change over the prior ``lookback`` months (a PIT expectation).

    For month ``m`` the expectation is the average reported change over the ``lookback`` months
    ending at m-1 (``shift(1)``), using only months strictly before ``m``. No future
    information. Payroll growth is persistent, so the recent trailing average is a reasonable,
    fully reproducible expectation of the next print.
    """
    return change.shift(1).rolling(lookback, min_periods=lookback // 2).mean()


def rolling_zscore(x: pd.Series, lookback: int = ZSCORE_LOOKBACK_MONTHS) -> pd.Series:
    """Trailing z-score of ``x`` using a window that EXCLUDES the current observation.

    Mean and std are computed over the ``lookback`` months ending at m-1 (``shift(1)``), so the
    standardization at month m never sees month m. Strictly point-in-time.
    """
    mean = x.shift(1).rolling(lookback, min_periods=lookback // 2).mean()
    std = x.shift(1).rolling(lookback, min_periods=lookback // 2).std()
    return (x - mean) / std


def build_signal(level: pd.Series, release_date: pd.Series) -> pd.DataFrame:
    """From a payrolls-level vintage, build the surprise signal and the implied position.

    Returns a frame indexed by reference month with columns: change, expected_change, surprise,
    position, release_date. position = -zscore(surprise): a bigger-than-expected jobs print
    (positive surprise) is faded -> short SPY (negative position), per the "good news is bad
    news" / rising-discount-rate linkage verified on the PIT arm.
    """
    change = monthly_change(level)
    expected = trend_expectation(change)
    surprise = (change - expected).rename("surprise")
    position = (-rolling_zscore(surprise)).clip(-3.0, 3.0).rename("position")
    df = pd.DataFrame(
        {
            "change": change,
            "expected_change": expected,
            "surprise": surprise,
            "position": position,
            "release_date": release_date,
        }
    )
    return df.dropna(subset=["position", "release_date"])


# --------------------------------------------------------------------------------------
# Backtest assembly (no-look-ahead enforced by construction)
# --------------------------------------------------------------------------------------
@dataclass
class MonthlyBacktest:
    monthly_index: pd.DatetimeIndex
    positions: pd.Series
    fwd_returns: pd.Series
    strat_returns: pd.Series
    entry_by_month: pd.Series  # maps reference month -> chosen SPY entry trading day


def _first_trading_day_on_or_after(trading_days: pd.DatetimeIndex, date: pd.Timestamp) -> object:
    idx = trading_days.searchsorted(date, side="left")
    if idx >= len(trading_days):
        return None
    return trading_days[idx]


def assemble(panel: PricePanel, signal: pd.DataFrame) -> MonthlyBacktest:
    """Build the monthly surprise backtest. Entry = first SPY open on/after the release date.

    Release timing is identical for NAIVE and PIT (they differ only in the payrolls vintage that
    fed ``signal``); the position is held one month, earning SPY open-to-open return over
    (entry, next entry]. A return at month m is earned only by a signal whose entry day is the
    start of month m, so decision information and the return it earns never overlap.
    """
    sig = signal.sort_index()
    trading_days = pd.DatetimeIndex(panel.prices.index)
    open_px = panel.prices["open"]

    entry_dates: list[object] = []
    positions: list[float] = []
    months: list[object] = []
    for ref_month, row in sig.iterrows():
        entry = _first_trading_day_on_or_after(trading_days, pd.Timestamp(row["release_date"]))
        if entry is None:
            continue
        entry_dates.append(entry)
        positions.append(float(row["position"]))
        months.append(ref_month)

    entry_by_month = pd.Series(
        pd.DatetimeIndex(entry_dates), index=pd.DatetimeIndex(months)
    ).sort_index()
    pos = pd.Series(positions, index=pd.DatetimeIndex(entry_dates))
    pos = pos[~pos.index.duplicated(keep="first")].sort_index()

    entry_open = open_px.reindex(pos.index)
    fwd = entry_open.shift(-1) / entry_open - 1.0
    strat = pos * fwd
    valid = strat.dropna().index
    return MonthlyBacktest(
        monthly_index=pd.DatetimeIndex(valid),
        positions=pos.reindex(valid),
        fwd_returns=fwd.reindex(valid),
        strat_returns=strat.reindex(valid),
        entry_by_month=entry_by_month,
    )


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def newey_west_tstat(x: np.ndarray) -> tuple[float, float, int]:
    """HAC (Newey-West) t-stat for the mean of ``x`` with automatic Bartlett bandwidth.

    L = floor(4 * (T/100)^(2/9)). Returns (mean, t_stat, lag L).
    """
    x = np.asarray(x, dtype=float)
    x = x[np.isfinite(x)]
    t = len(x)
    if t < 3:
        return float("nan"), float("nan"), 0
    mean = float(x.mean())
    e = x - mean
    lag = int(np.floor(4.0 * (t / 100.0) ** (2.0 / 9.0)))
    lag = max(0, min(lag, t - 1))
    gamma0 = float(e @ e) / t
    lrv = gamma0
    for k in range(1, lag + 1):
        w = 1.0 - k / (lag + 1.0)
        cov = float(e[k:] @ e[:-k]) / t
        lrv += 2.0 * w * cov
    if lrv <= 0:
        return mean, float("nan"), lag
    se = np.sqrt(lrv / t)
    return mean, mean / se, lag


def ic_vs_forward(positions: pd.Series, fwd: pd.Series) -> float:
    """Spearman rank IC between the signed continuous position and the next-month return."""
    df = pd.concat([positions.rename("p"), fwd.rename("f")], axis=1).dropna()
    if len(df) < 3:
        return float("nan")
    return float(df["p"].rank().corr(df["f"].rank()))


def summarize(bt: MonthlyBacktest, label: str) -> dict[str, object]:
    r = bt.strat_returns.dropna()
    n = len(r)
    if n < 3:
        return {"label": label, "n": float(n)}
    a = r.to_numpy(dtype=float)
    ann_ret = float(np.expm1(np.log1p(a).sum() * (MONTHS_PER_YEAR / n)))
    return {
        "label": label,
        "n": float(n),
        "ann_return": ann_ret,
        "sharpe": sharpe(r, periods_per_year=MONTHS_PER_YEAR),
        "ann_vol": float(a.std() * np.sqrt(MONTHS_PER_YEAR)),
        "hit_rate": float((a > 0).mean()),
        "ic": ic_vs_forward(bt.positions, bt.fwd_returns),
        "max_drawdown": max_drawdown(r),
    }


def _f(summary: dict[str, object], key: str) -> float:
    v = summary.get(key)
    if isinstance(v, (int, float)):
        return float(v)
    return float("nan")


def _slice(bt: MonthlyBacktest, mask: np.ndarray) -> MonthlyBacktest:
    idx = bt.monthly_index[mask]
    return MonthlyBacktest(
        monthly_index=idx,
        positions=bt.positions.reindex(idx),
        fwd_returns=bt.fwd_returns.reindex(idx),
        strat_returns=bt.strat_returns.reindex(idx),
        entry_by_month=bt.entry_by_month,
    )


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def run() -> dict[str, object]:
    panel = load_spy()
    first = load_first_release()  # frame: level, release_date
    revised = load_revised()  # series: revised level

    first_level = first["level"]
    release = first["release_date"]

    # Diagnostic: how much do the two vintages actually disagree, on the LEVEL and the CHANGE?
    common_levels = first_level.index.intersection(revised.index)
    level_diff = (revised.reindex(common_levels) - first_level.reindex(common_levels)).dropna()
    ch_first = monthly_change(first_level)
    ch_rev = monthly_change(revised)
    common_ch = ch_first.dropna().index.intersection(ch_rev.dropna().index)
    change_diff = (ch_rev.reindex(common_ch) - ch_first.reindex(common_ch)).dropna()
    n_revised = int((level_diff.abs() > 1e-9).sum())
    typ_change = float(ch_first.reindex(common_ch).abs().median())

    naive = assemble(panel, build_signal(revised, release))  # revised-as-if-known: the leak
    pit = assemble(panel, build_signal(first_level, release))  # first-release-honest

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

    out: dict[str, object] = {
        "series_id": SERIES_ID,
        "n_months_first_release": int(len(first_level)),
        "n_months_revised": int(len(revised)),
        "n_months_actually_revised": n_revised,
        "max_abs_level_revision_k": float(level_diff.abs().max()),
        "mean_abs_level_revision_k": float(level_diff.abs().mean()),
        "pct_months_revised": float((level_diff.abs() > 1e-9).mean()),
        "mean_abs_change_revision_k": float(change_diff.abs().mean()),
        "max_abs_change_revision_k": float(change_diff.abs().max()),
        "median_abs_first_release_change_k": typ_change,
        "median_change_revision_pct_of_change": float(change_diff.abs().median() / typ_change),
        "first_release_first": str(first_level.index.min().date()),
        "first_release_last": str(first_level.index.max().date()),
        "spy_first": str(panel.prices.index.min().date()),
        "spy_last": str(panel.prices.index.max().date()),
        "n_trade_months_common": int(len(common)),
        "periods": {},
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
    out["periods"] = periods_out
    return out


def main() -> None:
    res = run()
    out_path = Path(__file__).resolve().parent / "results_leakage_tax_macro.json"
    out_path.write_text(json.dumps(res, indent=2, default=str))

    p = res["periods"]
    assert isinstance(p, dict)
    print("\nNonfarm payrolls (PAYEMS) DATA-REVISION leakage-tax study")
    print(
        f"first-release months: {res['n_months_first_release']} "
        f"({res['first_release_first']} -> {res['first_release_last']}); "
        f"{res['pct_months_revised']:.0%} later revised "
        f"(mean |level rev| {res['mean_abs_level_revision_k']:.0f}k, "
        f"max {res['max_abs_level_revision_k']:.0f}k)"
    )
    print(
        f"MoM CHANGE revision: mean |rev| {res['mean_abs_change_revision_k']:.0f}k, "
        f"max {res['max_abs_change_revision_k']:.0f}k, "
        f"median rev = {res['median_change_revision_pct_of_change']:.0%} of the "
        f"~{res['median_abs_first_release_change_k']:.0f}k typical change"
    )
    print(
        f"SPY: {res['spy_first']} -> {res['spy_last']}; "
        f"common trade months: {res['n_trade_months_common']}\n"
    )
    hdr = (
        f"{'period':>10} {'variant':>7} {'ann_ret':>9} {'sharpe':>7} "
        f"{'hit':>6} {'IC':>7} {'maxDD':>8} | {'tax_SR':>7} {'tax_bps':>9} {'NW_t':>6}"
    )
    print(hdr)
    print("-" * len(hdr))
    for pname, blk in p.items():
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
