"""Point-in-time "leakage tax" study: EIA natural-gas storage DATA REVISION.

Sibling of ``run_study.py`` (the CFTC COT release-timing variant). That study tested only
*release timing* (a report's snapshot becomes public with a fixed lag). This study tests the
harder, more genuine form of look-ahead in the *data itself*: the EIA Weekly Natural Gas
Storage Report figure is **revised after its first release**. The number you could actually
trade on Thursday morning is the first-release estimate; the number sitting in today's
database is the revised one. Backtesting on the revised series silently leaks the future.

The strategy
------------
Signal = storage SURPRISE = reported weekly change in Total Lower-48 working gas minus a
transparent, point-in-time-computable seasonal expectation (the trailing same-week-of-year
historical average change, see ``seasonal_expectation``). No external consensus feed is
required, so there is nothing fragile to scrape. A larger-than-expected BUILD is bearish for
natural gas (more supply in storage), a larger-than-expected DRAW is bullish. The position is
the standardized surprise, sign-flipped: ``position = -zscore(surprise)``. Tradable instrument
is the UNG ETF (daily adjusted via ``yfinance``; ``auto_adjust`` handles the 2020 reverse
split). Weekly holding, UNG open-to-open returns.

The leakage (the whole point)
-----------------------------
Two variants run on identical code, differing ONLY in which storage vintage feeds the signal:

NAIVE  -- uses the FINAL/REVISED storage levels (``ngshistory.xls``) as if they were known at
          release. Both the reported change AND the trailing seasonal expectation are computed
          from the revised series. This is the standard (and wrong) way these signals are
          backtested off a database snapshot.

PIT    -- point-in-time honest. Uses the FIRST-RELEASE levels (``revisions.xls`` original
          estimate, the figure actually published Thursday 10:30am ET) for every week that
          appears in the revisions file; for weeks never revised, first-release == database.
          Both the change and the trailing expectation use only first-release figures.

Under BOTH variants the position may act only from the first UNG open on/after the Thursday
10:30am ET release (week-ending Friday + 6 days = the following Thursday), so this study holds
*release timing identical* across the two arms and isolates the pure DATA-REVISION effect.

The "leakage tax" is SR_naive - SR_pit (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat on the weekly return DIFFERENCE r_naive - r_pit, full sample and
sub-periods.

Scope and limitation
--------------------
The revisions file begins November 2015 (EIA started publishing the revision history then), so
the honest first-release series only exists from week-ending 2015-06-19 onward. The study
therefore covers ~2015-2026. Earlier weeks cannot be made point-in-time from this source.

Backtester reuse
----------------
Mirrors ``run_study.py`` exactly: reuses the verified ``research_pipeline.data.PricePanel``
for point-in-time price access (its ``as_of`` is the runtime witness of the Lean
``NonAnticipating`` spec) and ``research_pipeline.evaluation.sharpe`` / ``max_drawdown`` for
metrics. The seasonal expectation and z-score are trailing-only (they use only weeks strictly
before the week being scored), and a weekly return is earned only by a signal whose entry day
precedes that week, so decision information and the return it earns never overlap. Enforced by
construction in ``build_signal`` / ``assemble``.
"""

from __future__ import annotations

import io
import json
import ssl
import sys
import urllib.request
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

REVISIONS_URL = "https://ir.eia.gov/ngs/revisions.xls"  # first-release (original) estimates
HISTORY_URL = "https://ir.eia.gov/ngs/ngshistory.xls"  # current/revised database
SEASONAL_LOOKBACK_YEARS = 5  # trailing years used for the same-week seasonal average
ZSCORE_LOOKBACK_WEEKS = 104  # trailing window for standardizing the surprise (~2 years)
WEEKS_PER_YEAR = 52
CACHE = Path(__file__).resolve().parent / "data_cache"


# --------------------------------------------------------------------------------------
# Data acquisition
# --------------------------------------------------------------------------------------
def _http_get(url: str) -> bytes:
    """Fetch ``url`` with a verified TLS context (prefers ``requests``; urllib+certifi else)."""
    try:
        import requests

        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return bytes(resp.content)
    except ImportError:
        pass
    try:
        import certifi

        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, timeout=120, context=ctx) as resp:  # noqa: S310
        return bytes(resp.read())


def _cached_bytes(url: str, name: str) -> bytes:
    CACHE.mkdir(exist_ok=True)
    f = CACHE / name
    if f.exists():
        return f.read_bytes()
    raw = _http_get(url)
    f.write_bytes(raw)
    return raw


def load_first_release() -> pd.Series:
    """First-release Total Lower-48 working-gas levels (Bcf), indexed by week-ending Friday.

    Source: ``revisions.xls`` sheet ``original_data``. This file is a continuous weekly series
    of the ORIGINAL estimate published in the Weekly Natural Gas Storage Report, with an
    ``Explanation`` column flagging the weeks later revised. The 'Total Lower 48' column is the
    figure the market actually saw on the release Thursday.
    """
    raw = _cached_bytes(REVISIONS_URL, "revisions.xls")
    df = pd.read_excel(io.BytesIO(raw), sheet_name="original_data", header=1)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[["Week ending", "Total Lower 48"]].dropna()
    s = pd.Series(
        pd.to_numeric(df["Total Lower 48"], errors="coerce").to_numpy(),
        index=pd.DatetimeIndex(pd.to_datetime(df["Week ending"])),
        name="level",
    ).dropna()
    return s[~s.index.duplicated(keep="first")].sort_index()


def load_revised() -> pd.Series:
    """Current/revised Total Lower-48 working-gas levels (Bcf), indexed by week-ending Friday.

    Source: ``ngshistory.xls`` sheet ``html_report_history`` (the live EIA database). For any
    week that was revised, this is the final value; for un-revised weeks it equals the
    first-release value.
    """
    raw = _cached_bytes(HISTORY_URL, "ngshistory.xls")
    df = pd.read_excel(io.BytesIO(raw), sheet_name="html_report_history", header=6)
    df.columns = [str(c).strip() for c in df.columns]
    df = df[["Week ending", "Total Lower 48"]].dropna()
    s = pd.Series(
        pd.to_numeric(df["Total Lower 48"], errors="coerce").to_numpy(),
        index=pd.DatetimeIndex(pd.to_datetime(df["Week ending"])),
        name="level",
    ).dropna()
    return s[~s.index.duplicated(keep="first")].sort_index()


def load_ung(start: str = "2010-01-01") -> PricePanel:
    """UNG daily adjusted prices wrapped in the verified ``PricePanel`` (``auto_adjust`` handles
    the 2020 1:4 reverse split)."""
    import yfinance as yf

    raw = yf.download("UNG", start=start, auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        raise RuntimeError("yfinance returned no UNG data")
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]["UNG"]
        open_ = raw["Open"]["UNG"]
    else:
        close = raw["Close"]
        open_ = raw["Open"]
    prices = pd.DataFrame({"close": close.astype(float), "open": open_.astype(float)}).dropna()
    prices.index = pd.DatetimeIndex(prices.index).normalize()
    return PricePanel(prices)


# --------------------------------------------------------------------------------------
# Signal: storage surprise vs a transparent point-in-time seasonal expectation
# --------------------------------------------------------------------------------------
def weekly_change(level: pd.Series) -> pd.Series:
    """Reported weekly change in working-gas stocks (Bcf): level(w) - level(w-1).

    Computed within a single vintage, so the NAIVE arm uses revised-minus-revised and the PIT
    arm uses first-release-minus-first-release. This is exactly the implied weekly net change
    the report publishes alongside the level.
    """
    return level.diff()


def seasonal_expectation(
    change: pd.Series, lookback_years: int = SEASONAL_LOOKBACK_YEARS
) -> pd.Series:
    """Trailing same-week-of-year average change: a transparent point-in-time expectation.

    For week ``w`` the expectation is the mean reported change over the same ISO week number in
    the previous ``lookback_years`` years, using ONLY weeks strictly before ``w``. No future
    information and no external consensus feed. Storage flows are strongly seasonal (injection
    in summer, withdrawal in winter), so the same-week historical average is a reasonable,
    fully reproducible expectation.
    """
    ch = change.dropna()
    woy = ch.index.isocalendar().week.to_numpy()
    years = ch.index.year.to_numpy()
    vals = ch.to_numpy(dtype=float)
    out = np.full(len(ch), np.nan)
    for i in range(len(ch)):
        wk, yr = woy[i], years[i]
        # same ISO week, strictly earlier years within the lookback window, strictly before i
        mask = (woy == wk) & (years < yr) & (years >= yr - lookback_years)
        mask[i:] = False  # belt-and-suspenders: never use anything at or after i
        prior = vals[mask]
        prior = prior[np.isfinite(prior)]
        if prior.size >= 2:
            out[i] = float(prior.mean())
    return pd.Series(out, index=ch.index, name="expected_change")


def rolling_zscore(x: pd.Series, lookback: int = ZSCORE_LOOKBACK_WEEKS) -> pd.Series:
    """Trailing z-score of ``x`` using a window that EXCLUDES the current observation.

    Mean and std are computed over the ``lookback`` weeks ending at w-1 (``shift(1)``), so the
    standardization at week w never sees week w. Strictly point-in-time.
    """
    mean = x.shift(1).rolling(lookback, min_periods=lookback // 2).mean()
    std = x.shift(1).rolling(lookback, min_periods=lookback // 2).std()
    return (x - mean) / std


def build_signal(level: pd.Series) -> pd.DataFrame:
    """From a storage-level vintage, build the surprise signal and the implied position.

    Returns a frame indexed by week-ending Friday with columns: change, expected_change,
    surprise, position. position = -zscore(surprise): a bigger-than-expected build (positive
    surprise) is bearish nat gas -> short UNG (negative position).
    """
    change = weekly_change(level)
    expected = seasonal_expectation(change)
    surprise = (change - expected).rename("surprise")
    position = (-rolling_zscore(surprise)).clip(-3.0, 3.0).rename("position")
    df = pd.DataFrame(
        {"change": change, "expected_change": expected, "surprise": surprise, "position": position}
    )
    df["release_date"] = df.index + pd.Timedelta(days=6)  # week-ending Fri + 6 = following Thu
    return df.dropna(subset=["position"])


# --------------------------------------------------------------------------------------
# Backtest assembly (no-look-ahead enforced by construction)
# --------------------------------------------------------------------------------------
@dataclass
class WeeklyBacktest:
    weekly_index: pd.DatetimeIndex
    positions: pd.Series
    fwd_returns: pd.Series
    strat_returns: pd.Series
    entry_by_week: pd.Series  # maps week-ending Friday -> chosen UNG entry trading day


def _first_trading_day_on_or_after(trading_days: pd.DatetimeIndex, date: pd.Timestamp) -> object:
    idx = trading_days.searchsorted(date, side="left")
    if idx >= len(trading_days):
        return None
    return trading_days[idx]


def assemble(panel: PricePanel, signal: pd.DataFrame) -> WeeklyBacktest:
    """Build the weekly surprise backtest. Entry = first UNG open on/after the Thursday release.

    Release timing is identical for NAIVE and PIT (they differ only in the storage vintage that
    fed ``signal``); the position is held one week, earning UNG open-to-open return over
    (entry, next entry]. A return at week w is earned only by a signal whose entry day is the
    start of week w, so decision information and the return it earns never overlap.
    """
    sig = signal.sort_index()
    trading_days = pd.DatetimeIndex(panel.prices.index)
    open_px = panel.prices["open"]

    entry_dates: list[object] = []
    positions: list[float] = []
    weeks: list[object] = []
    for week_ending, row in sig.iterrows():
        entry = _first_trading_day_on_or_after(trading_days, row["release_date"])
        if entry is None:
            continue
        entry_dates.append(entry)
        positions.append(float(row["position"]))
        weeks.append(week_ending)

    entry_by_week = pd.Series(
        pd.DatetimeIndex(entry_dates), index=pd.DatetimeIndex(weeks)
    ).sort_index()
    pos = pd.Series(positions, index=pd.DatetimeIndex(entry_dates))
    pos = pos[~pos.index.duplicated(keep="first")].sort_index()

    entry_open = open_px.reindex(pos.index)
    fwd = entry_open.shift(-1) / entry_open - 1.0
    strat = pos * fwd
    valid = strat.dropna().index
    return WeeklyBacktest(
        weekly_index=pd.DatetimeIndex(valid),
        positions=pos.reindex(valid),
        fwd_returns=fwd.reindex(valid),
        strat_returns=strat.reindex(valid),
        entry_by_week=entry_by_week,
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
    """Spearman rank IC between the signed continuous position and the next-week return."""
    df = pd.concat([positions.rename("p"), fwd.rename("f")], axis=1).dropna()
    if len(df) < 3:
        return float("nan")
    return float(df["p"].rank().corr(df["f"].rank()))


def summarize(bt: WeeklyBacktest, label: str) -> dict[str, object]:
    r = bt.strat_returns.dropna()
    n = len(r)
    if n < 3:
        return {"label": label, "n": float(n)}
    a = r.to_numpy(dtype=float)
    ann_ret = float(np.expm1(np.log1p(a).sum() * (WEEKS_PER_YEAR / n)))
    return {
        "label": label,
        "n": float(n),
        "ann_return": ann_ret,
        "sharpe": sharpe(r, periods_per_year=WEEKS_PER_YEAR),
        "ann_vol": float(a.std() * np.sqrt(WEEKS_PER_YEAR)),
        "hit_rate": float((a > 0).mean()),
        "ic": ic_vs_forward(bt.positions, bt.fwd_returns),
        "max_drawdown": max_drawdown(r),
    }


def _f(summary: dict[str, object], key: str) -> float:
    v = summary.get(key)
    if isinstance(v, (int, float)):
        return float(v)
    return float("nan")


def _slice(bt: WeeklyBacktest, mask: np.ndarray) -> WeeklyBacktest:
    idx = bt.weekly_index[mask]
    return WeeklyBacktest(
        weekly_index=idx,
        positions=bt.positions.reindex(idx),
        fwd_returns=bt.fwd_returns.reindex(idx),
        strat_returns=bt.strat_returns.reindex(idx),
        entry_by_week=bt.entry_by_week,
    )


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def run() -> dict[str, object]:
    panel = load_ung()
    first = load_first_release()
    revised = load_revised()

    # Diagnostic: how much do the two vintages actually disagree?
    common_levels = first.index.intersection(revised.index)
    level_diff = (revised.reindex(common_levels) - first.reindex(common_levels)).dropna()
    n_revised = int((level_diff.abs() > 1e-9).sum())

    naive = assemble(panel, build_signal(revised))  # revised-as-if-known: the leak
    pit = assemble(panel, build_signal(first))  # first-release-honest

    common = naive.weekly_index.intersection(pit.weekly_index)
    rn = naive.strat_returns.reindex(common)
    rp = pit.strat_returns.reindex(common)
    diff = (rn - rp).dropna()

    periods: dict[str, pd.Series] = {
        "full": pd.Series(True, index=common),
        "2015_2020": pd.Series(common < pd.Timestamp("2020-01-01"), index=common),
        "2020_2026": pd.Series(common >= pd.Timestamp("2020-01-01"), index=common),
    }

    out: dict[str, object] = {
        "n_weeks_first_release": int(len(first)),
        "n_weeks_revised": int(len(revised)),
        "n_weeks_actually_revised": n_revised,
        "max_abs_level_revision_bcf": float(level_diff.abs().max()),
        "mean_abs_level_revision_bcf": float(level_diff.abs().mean()),
        "first_release_first": str(first.index.min().date()),
        "first_release_last": str(first.index.max().date()),
        "ung_first": str(panel.prices.index.min().date()),
        "ung_last": str(panel.prices.index.max().date()),
        "n_trade_weeks_common": int(len(common)),
        "periods": {},
    }
    periods_out: dict[str, object] = {}
    for pname, pmask in periods.items():
        nsub = _slice(naive, naive.weekly_index.isin(common[pmask.to_numpy()]))
        psub = _slice(pit, pit.weekly_index.isin(common[pmask.to_numpy()]))
        d = diff.reindex(common[pmask.to_numpy()]).dropna()
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
            "diff_mean_weekly": mean_d,
            "diff_nw_tstat": t_d,
            "diff_nw_lag": lag,
            "pit_clears_null": bool(_f(sp, "sharpe") > 0.0),
        }
    out["periods"] = periods_out
    return out


def main() -> None:
    res = run()
    out_path = Path(__file__).resolve().parent / "results_leakage_tax_eia.json"
    out_path.write_text(json.dumps(res, indent=2, default=str))

    p = res["periods"]
    assert isinstance(p, dict)
    print("\nEIA natural-gas storage DATA-REVISION leakage-tax study")
    print(
        f"first-release weeks: {res['n_weeks_first_release']} "
        f"({res['first_release_first']} -> {res['first_release_last']}); "
        f"of these {res['n_weeks_actually_revised']} were later revised "
        f"(max |rev| {res['max_abs_level_revision_bcf']:.0f} Bcf, "
        f"mean {res['mean_abs_level_revision_bcf']:.2f} Bcf)"
    )
    print(
        f"UNG: {res['ung_first']} -> {res['ung_last']}; common trade weeks: {res['n_trade_weeks_common']}\n"
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
