"""Point-in-time "leakage tax" study: CFTC COT crude-oil positioning.

Measures how much apparent alpha in a commodity systematic strategy is an artifact of
look-ahead in the *data* (not the code). The signal is a contrarian fade of Managed Money
net-long positioning in WTI crude (CFTC Disaggregated COT); the tradable instrument is the
USO ETF. Two variants are run on identical code:

NAIVE  -- treats the Commitments-of-Traders snapshot as tradeable at/after the report's
          as-of Tuesday close. This is the standard (and wrong) way these signals are
          backtested, because it assumes you knew Tuesday's positioning on Tuesday.

PIT    -- point-in-time honest. The snapshot is *released* the following Friday 3:30pm ET,
          so the signal may not enter a position before the FOLLOWING Monday's open.
          We enforce release_date = as_of_tuesday + 3 days (Friday), and the position is
          only allowed to act from the next trading day at or after the following Monday.

The "leakage tax" is SR_naive - SR_pit (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat on the weekly return DIFFERENCE r_naive - r_pit.

Design notes on backtester reuse
--------------------------------
The verified no-look-ahead engine ``research_pipeline.backtest.run_backtest`` is a
cross-sectional, daily-rebalanced, IC-scored panel engine (weights = signal_to_weights on a
cross-section of assets, daily forward returns). This study is a single-asset, weekly-held,
directional timing strategy, which that engine does not model. We therefore run a clean
standalone weekly backtest here, but we REUSE the verified primitives:
  - ``research_pipeline.data.PricePanel`` for point-in-time price access (its ``as_of`` is the
    runtime witness of the Lean ``NonAnticipating`` spec),
  - ``research_pipeline.evaluation.sharpe`` and ``max_drawdown`` for the metrics.
The no-look-ahead guarantee here is enforced by construction in ``build_weekly_panel`` /
``assemble`` (a weekly return at week w earns only on the signal known strictly before w).
"""

from __future__ import annotations

import io
import json
import ssl
import sys
import urllib.request
import zipfile
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

WTI_MARKET_CODE = "067651"  # NYMEX Light Sweet Crude Oil (WTI-PHYSICAL), CFTC Disaggregated
CFTC_URL = "https://www.cftc.gov/files/dea/history/fut_disagg_txt_{year}.zip"
CFTC_FIRST_YEAR = (
    2010  # Disaggregated COT report begins 2010 (introduced after 2008); 2006-2009 return 404
)
LOOKBACK_WEEKS = 52  # 52-week percentile window for the positioning extreme
WEEKS_PER_YEAR = 52
CACHE = Path(__file__).resolve().parent / "data_cache"


# --------------------------------------------------------------------------------------
# Data acquisition
# --------------------------------------------------------------------------------------
def _http_get(url: str) -> bytes:
    """Fetch ``url`` with a verified TLS context.

    Prefers ``requests`` (bundles certifi); falls back to ``urllib`` with certifi's CA bundle.
    The uv-managed CPython here ships no system CA file, so a bare ``urllib.urlopen`` fails
    TLS verification against www.cftc.gov.
    """
    try:
        import requests

        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        return resp.content
    except ImportError:
        pass
    try:
        import certifi

        ctx = ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, timeout=120, context=ctx) as resp:  # noqa: S310
        return bytes(resp.read())


def _download_cftc_year(year: int) -> pd.DataFrame:
    """Download one year of the CFTC Disaggregated Futures-Only history, WTI rows only."""
    CACHE.mkdir(exist_ok=True)
    cache_file = CACHE / f"cftc_wti_{year}.csv"
    if cache_file.exists():
        return pd.read_csv(cache_file, parse_dates=["as_of"])

    url = CFTC_URL.format(year=year)
    raw = _http_get(url)
    with zipfile.ZipFile(io.BytesIO(raw)) as zf:
        name = zf.namelist()[0]
        with zf.open(name) as fh:
            # As_of_Date_In_Form_YYMMDD is the only report-date column whose name and YYMMDD
            # format are stable across all years (older files rename Report_Date_as_*).
            df = pd.read_csv(
                fh,
                usecols=[
                    "As_of_Date_In_Form_YYMMDD",
                    "CFTC_Contract_Market_Code",
                    "M_Money_Positions_Long_All",
                    "M_Money_Positions_Short_All",
                ],
                dtype={
                    "CFTC_Contract_Market_Code": str,
                    "As_of_Date_In_Form_YYMMDD": str,
                },
            )
    df.columns = [c.strip() for c in df.columns]
    df = df[df["CFTC_Contract_Market_Code"].str.strip() == WTI_MARKET_CODE].copy()
    out = pd.DataFrame(
        {
            "as_of": pd.to_datetime(df["As_of_Date_In_Form_YYMMDD"].str.strip(), format="%y%m%d"),
            "mm_long": pd.to_numeric(df["M_Money_Positions_Long_All"], errors="coerce"),
            "mm_short": pd.to_numeric(df["M_Money_Positions_Short_All"], errors="coerce"),
        }
    ).dropna()
    out = out.sort_values("as_of").reset_index(drop=True)
    out.to_csv(cache_file, index=False)
    return out


def load_cot(last_year: int) -> pd.DataFrame:
    """Concatenated WTI Managed-Money COT, one row per weekly report, sorted by as_of date.

    Columns: as_of (Tuesday snapshot date), mm_long, mm_short, mm_net, release_date.
    ``release_date`` = as_of + 3 days (the Friday 3:30pm ET public release).
    """
    frames = [_download_cftc_year(y) for y in range(CFTC_FIRST_YEAR, last_year + 1)]
    cot = pd.concat(frames, ignore_index=True).drop_duplicates("as_of").sort_values("as_of")
    cot = cot.reset_index(drop=True)
    cot["mm_net"] = cot["mm_long"] - cot["mm_short"]
    # The snapshot is public only the following Friday 3:30pm ET. Tuesday + 3 days = Friday.
    cot["release_date"] = cot["as_of"] + pd.Timedelta(days=3)
    return cot


def load_uso(start: str = "2006-01-01") -> PricePanel:
    """USO daily adjusted prices wrapped in the verified ``PricePanel`` (auto_adjust handles
    the Apr-2020 1:8 reverse split)."""
    import yfinance as yf

    raw = yf.download("USO", start=start, auto_adjust=True, progress=False)
    if raw is None or raw.empty:
        raise RuntimeError("yfinance returned no USO data")
    if isinstance(raw.columns, pd.MultiIndex):
        close = raw["Close"]["USO"]
        open_ = raw["Open"]["USO"]
    else:
        close = raw["Close"]
        open_ = raw["Open"]
    prices = pd.DataFrame({"close": close.astype(float), "open": open_.astype(float)})
    prices = prices.dropna()
    prices.index = pd.DatetimeIndex(prices.index).normalize()
    return PricePanel(prices)


# --------------------------------------------------------------------------------------
# Signal
# --------------------------------------------------------------------------------------
def positioning_percentile(mm_net: pd.Series, lookback: int = LOOKBACK_WEEKS) -> pd.Series:
    """Trailing ``lookback``-week percentile rank of net Managed-Money positioning in [0, 1].

    Uses only weeks <= the current week (``min_periods`` guards the warm-up); strictly a
    function of past+current observations, never future ones.
    """
    return mm_net.rolling(lookback, min_periods=lookback).apply(
        lambda w: float((w <= w.iloc[-1]).mean()), raw=False
    )


def contrarian_position(pctile: pd.Series) -> pd.Series:
    """Contrarian fade: short when the crowd is extremely long, long when extremely short.

    Maps the [0, 1] percentile to a position in [-1, +1] via ``-(2*pctile - 1)`` so a
    crowded-long extreme (pctile -> 1) gives a -1 (short) position. This is a continuous
    contrarian tilt, not a threshold rule, so the result does not hinge on a magic cutoff.
    """
    return -(2.0 * pctile - 1.0)


# --------------------------------------------------------------------------------------
# Backtest assembly (no-look-ahead enforced by construction)
# --------------------------------------------------------------------------------------
@dataclass
class WeeklyBacktest:
    weekly_index: pd.DatetimeIndex  # the Monday (or first trading day) of each trade week
    positions: pd.Series  # position held over the week, indexed at week open
    fwd_returns: pd.Series  # USO return realised over that week (open-to-open, next week)
    strat_returns: pd.Series  # positions * fwd_returns
    # entry date chosen for each COT report's as_of date, BEFORE dropping returnless weeks.
    # Maps as_of (Tuesday snapshot date) -> the trading day the position is allowed to enter.
    entry_by_as_of: pd.Series


def _first_trading_day_on_or_after(trading_days: pd.DatetimeIndex, date: pd.Timestamp) -> object:
    idx = trading_days.searchsorted(date, side="left")
    if idx >= len(trading_days):
        return None
    return trading_days[idx]


def assemble(panel: PricePanel, cot: pd.DataFrame, *, pit: bool) -> WeeklyBacktest:
    """Build the weekly contrarian backtest under the NAIVE or PIT timing convention.

    For each weekly COT report we compute the positioning signal from data available up to and
    including that report (``positioning_percentile`` is trailing-only). The position implied by
    that signal is allowed to act:
      - NAIVE: from the first trading day on/after the as-of Tuesday (assumes Tuesday knowledge),
      - PIT  : from the first trading day on/after the FOLLOWING Monday (release_date + weekend),
               i.e. strictly after the Friday 3:30pm ET public release.
    The position is held one week and earns the USO open-to-open return over (entry, next entry].
    A return at week w is earned only by a signal whose entry day is <= the start of week w, so
    decision information and the return it earns never overlap.
    """
    cot = cot.copy().sort_values("as_of").reset_index(drop=True)
    cot["pctile"] = positioning_percentile(cot["mm_net"])
    cot["position"] = contrarian_position(cot["pctile"])
    cot = cot.dropna(subset=["position"])

    trading_days = pd.DatetimeIndex(panel.prices.index)
    open_px = panel.prices["open"]

    entry_dates: list[object] = []
    positions: list[float] = []
    as_of_dates: list[object] = []
    for _, row in cot.iterrows():
        if pit:
            # Released Friday 3:30pm; first actionable open is the following Monday. For a
            # Tuesday as-of, release_date = +3 (Friday) and +3 more days lands on the Monday.
            target = row["release_date"] + pd.Timedelta(days=3)
        else:
            target = row["as_of"]
        entry = _first_trading_day_on_or_after(trading_days, target)
        if entry is None:
            continue
        entry_dates.append(entry)
        positions.append(float(row["position"]))
        as_of_dates.append(row["as_of"])

    entry_by_as_of = pd.Series(
        pd.DatetimeIndex(entry_dates), index=pd.DatetimeIndex(as_of_dates)
    ).sort_index()
    pos = pd.Series(positions, index=pd.DatetimeIndex(entry_dates))
    pos = pos[~pos.index.duplicated(keep="first")].sort_index()

    # Weekly forward return = USO open at next entry / open at this entry - 1.
    entry_open = open_px.reindex(pos.index)
    fwd = entry_open.shift(-1) / entry_open - 1.0
    strat = pos * fwd
    valid = strat.dropna().index
    return WeeklyBacktest(
        weekly_index=pd.DatetimeIndex(valid),
        positions=pos.reindex(valid),
        fwd_returns=fwd.reindex(valid),
        strat_returns=strat.reindex(valid),
        entry_by_as_of=entry_by_as_of,
    )


# --------------------------------------------------------------------------------------
# Statistics
# --------------------------------------------------------------------------------------
def newey_west_tstat(x: np.ndarray) -> tuple[float, float, int]:
    """HAC (Newey-West) t-stat for the mean of ``x`` with automatic bandwidth.

    Bandwidth L = floor(4 * (T/100)^(2/9)) (the standard Newey-West rule of thumb used by
    common software defaults). Returns (mean, t_stat, lag L).
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
        w = 1.0 - k / (lag + 1.0)  # Bartlett kernel
        cov = float(e[k:] @ e[:-k]) / t
        lrv += 2.0 * w * cov
    if lrv <= 0:
        return mean, float("nan"), lag
    se = np.sqrt(lrv / t)
    return mean, mean / se, lag


def ic_vs_forward(positions: pd.Series, fwd: pd.Series) -> float:
    """Spearman rank IC between the (signed, continuous) position and the next-week return."""
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
    """Pull a numeric field out of a summary dict as a float (NaN if absent/non-numeric)."""
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
        entry_by_as_of=bt.entry_by_as_of,
    )


# --------------------------------------------------------------------------------------
# Orchestration
# --------------------------------------------------------------------------------------
def run(last_year: int = 2025) -> dict[str, object]:
    panel = load_uso()
    cot = load_cot(last_year)
    naive = assemble(panel, cot, pit=False)
    pit = assemble(panel, cot, pit=True)

    # Align the two return streams on common trade weeks for the difference test.
    common = naive.weekly_index.intersection(pit.weekly_index)
    rn = naive.strat_returns.reindex(common)
    rp = pit.strat_returns.reindex(common)
    diff = (rn - rp).dropna()

    periods: dict[str, pd.Series] = {
        "full": pd.Series(True, index=common),
        "pre2020": pd.Series(common < pd.Timestamp("2020-01-01"), index=common),
        "2020_2025": pd.Series(common >= pd.Timestamp("2020-01-01"), index=common),
    }

    out: dict[str, object] = {
        "n_cot_reports": int(len(cot)),
        "cot_first": str(cot["as_of"].min().date()),
        "cot_last": str(cot["as_of"].max().date()),
        "uso_first": str(panel.prices.index.min().date()),
        "uso_last": str(panel.prices.index.max().date()),
        "periods": {},
    }
    periods_out: dict[str, object] = {}
    for pname, pmask in periods.items():
        nsub = _slice(naive, naive.weekly_index.isin(common[pmask.to_numpy()]))
        psub = _slice(pit, pit.weekly_index.isin(common[pmask.to_numpy()]))
        # Null: flat (zero) strategy -> Sharpe 0, by definition; we report the PIT vs null gap.
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
    out_path = Path(__file__).resolve().parent / "results_leakage_tax.json"
    out_path.write_text(json.dumps(res, indent=2, default=str))

    p = res["periods"]
    assert isinstance(p, dict)
    print("\nCFTC WTI Managed-Money COT leakage-tax study")
    print(f"COT reports: {res['n_cot_reports']} ({res['cot_first']} -> {res['cot_last']})")
    print(f"USO: {res['uso_first']} -> {res['uso_last']}\n")
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
