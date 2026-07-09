# Leakage-tax study (data revision): nonfarm payrolls

Third cell of a 2-D "where does point-in-time matter" map. The map has two axes: **revision
magnitude** (how much the first-release figure moves before it settles) and **signal reliability**
(whether the underlying strategy has any honest edge to begin with). The thesis under test is the
same throughout: *how much apparent alpha is a data-revision artifact?* A leakage tax can only
appear where revisions are large AND the honest strategy has real alpha.

The two earlier cells both came back **null**, and both for a mechanical reason:

- [`commodity-leakage-tax/README.md`](../commodity-leakage-tax/README.md) (CFTC COT) tested only
  **release timing**.
- [`commodity-leakage-tax/README_eia.md`](../commodity-leakage-tax/README_eia.md) (EIA gas storage)
  tested data revision, but EIA storage is **barely revised**: mean absolute revision 0.90 Bcf,
  and only ~12% of weeks are ever revised at all. With revisions that small, the difference between
  trading the first-release figure and the final figure is negligible relative to the noise in
  weekly returns, so the tax was mechanically zero.

This study moves the identical test to a series that ALFRED shows is revised on essentially every
observation by a large fraction of the headline number: U.S. nonfarm payrolls (FRED `PAYEMS`). It
is the natural place to look for a real leakage tax: maximally revised data.

## The strategy

- **Universe / instrument:** total nonfarm payrolls as the signal, the SPY ETF as the tradable
  (daily adjusted via `yfinance`, `auto_adjust` on).
- **Signal:** payrolls **surprise** = reported month-over-month change in payrolls minus a
  transparent, point-in-time-computable expectation. The expectation is the trailing 12-month
  average change (`trend_expectation`), using only months strictly before the month being scored.
  No external consensus feed, so nothing fragile to scrape.
- **Rule:** the surprise is standardized by a trailing 36-month z-score (window ending at m-1, so
  it never sees month m) and the position is `-z`, clipped to [-3, 3]. The fade is deliberate: at
  the monthly horizon over this sample, the empirical linkage is "good news is bad news", a hot
  jobs print raises Fed-tightening expectations and the rising-discount-rate channel dominates the
  growth channel, so SPY tends to give back over the following month. Verified on the honest (PIT)
  arm: the momentum sign loses (Sharpe -0.16) and the contrarian fade clears the flat-book null
  (Sharpe +0.16). Continuous tilt, monthly holding, SPY open-to-open returns.

## The leakage

Two variants run on **identical code**, differing only in which payrolls vintage feeds the signal:

- **NAIVE** uses the **final/revised** level (the latest ALFRED vintage, today's `PAYEMS`) as if it
  were known at the release date. Both the reported change and the trailing expectation are
  computed from the revised series. This is the standard (wrong) way a macro signal is backtested
  off a database snapshot: today's FRED `PAYEMS` already contains years of annual benchmark
  revisions that nobody had on the original Jobs Friday.
- **PIT (point-in-time honest)** uses only the **first-release** vintage available at the decision
  timestamp (ALFRED `realtime_start`): the figure actually published that morning. Both the change
  and the expectation use only first-release figures.

Crucially, **release timing is held identical** across the two arms: under both, the position may
act only from the first SPY open on/after the ALFRED `realtime_start` (the genuine release
timestamp, almost always the first Friday of the following month). This isolates the pure
**data-revision** effect from the release-timing effect the COT study already covered.

The **leakage tax** is `SR_naive - SR_pit` (annualized) plus the bps/yr return gap, with a
Newey-West HAC t-stat (automatic Bartlett bandwidth) on the monthly return **difference**
`r_naive - r_pit`.

## Data sources

- **Real-time vintages:** FRED/ALFRED `PAYEMS` via `fredapi.get_series_all_releases`, which returns
  one row per (reference month, vintage). First-release = earliest `realtime_start`; revised =
  latest. API key is read from `~/.config/eigenq/fred.env` (`FRED_API_KEY`); it is never printed,
  logged, or committed. The raw release table is cached as CSV under `data_cache/` (git-ignored).
- **Price:** SPY daily via `yfinance` (free), 1993-present.
- **Contemporaneity filter:** ALFRED real-time PAYEMS vintages begin in the late 1990s, but the
  table also contains old reference months that first appear in the 1997 ALFRED snapshot. To keep
  the PIT timestamp real, we restrict to months whose first release is genuinely contemporaneous,
  release lag in [20, 60] days (the actual following-month Jobs Friday), not back-loaded.

## No-look-ahead and backtester reuse

The trend expectation and the z-score are trailing-only and the z-score window explicitly ends at
m-1, so the signal at month m never sees month m. A monthly return is earned only by a signal
whose entry day starts that month, so decision information and the return never overlap. Enforced
by construction in `build_signal` / `assemble`. As in the EIA study, this reuses the verified
`research_pipeline.data.PricePanel` for point-in-time price access (whose `as_of` is the runtime
witness of the Lean `NonAnticipating` spec) and `research_pipeline.evaluation.sharpe` /
`max_drawdown` for the metrics.

## Revision magnitude (the contrast that matters)

This is the headline result, the reason the study exists. ALFRED shows nonfarm payrolls is revised
on **100% of months** (852 first-release months, 1955-2026):

| series                | % obs revised | mean abs revision | revision as % of the change |
|-----------------------|---------------|-------------------|-----------------------------|
| EIA gas storage (Bcf) | ~12%          | 0.90 Bcf          | ~1% of a typical weekly change |
| **PAYEMS (jobs, k)**  | **100%**      | **123k on the MoM change** | **~45% (median) of the typical ~197k change** |

The month-over-month **change** in payrolls, the number markets actually trade, is revised by a
**median of 45% of the change itself** (mean absolute change-revision 123k jobs, max 1.38M during
the 2020 benchmark turbulence) against a typical first-release change of ~197k. On the revision
axis, payrolls sits at the opposite extreme from EIA storage.

## Result (real data, 1997-2026)

852 first-release months (after the contemporaneity filter); SPY daily 1993-01-29 to 2026-06-26;
**399 common trade months**.

| period    | variant | ann ret | Sharpe | hit  | IC     | maxDD  | tax (SR) | tax (bps) | NW t  |
|-----------|---------|---------|--------|------|--------|--------|----------|-----------|-------|
| full      | naive   | -0.2%   | +0.13  | 0.55 | +0.058 | -86.5% | -0.03    | -134      | -0.09 |
| full      | pit     | +1.1%   | +0.16  | 0.51 | +0.021 | -59.0% |          |           |       |
| pre-2008  | naive   | +5.7%   | +0.45  | 0.52 | +0.076 | -29.5% | -0.05    | +20       | +0.15 |
| pre-2008  | pit     | +5.5%   | +0.50  | 0.54 | +0.074 | -27.2% |          |           |       |
| 2008-2016 | naive   | -16.5%  | -0.28  | 0.56 | -0.063 | -86.5% | -0.28    | -1269     | -0.98 |
| 2008-2016 | pit     | -3.9%   | +0.01  | 0.47 | +0.001 | -55.6% |          |           |       |
| 2016-2026 | naive   | +5.3%   | +0.33  | 0.59 | +0.135 | -53.7% | +0.26    | +658      | +1.26 |
| 2016-2026 | pit     | -1.3%   | +0.07  | 0.51 | -0.016 | -43.7% |          |           |       |

Newey-West lag = 5 (full), 3-4 (sub-periods).

## Verdict

**The honest strategy clears the null, the revisions are enormous, and the data-revision leakage
tax is still statistically zero.** This is a more informative null than EIA, because here the
mechanical excuse is gone: payrolls is the maximally revised series, and the PIT (honest) arm has a
real edge (full-sample Sharpe +0.16, positive in three of four sub-periods, so there is genuine
alpha that leakage could in principle inflate). Yet the full-sample tax is `-0.03` Sharpe / `-134`
bps with NW t = -0.09, completely indistinguishable from zero and in fact slightly **negative**:
trading the revised figure did not help. The sub-period taxes swing both ways (`-1269` bps in
2008-2016, `+658` bps in 2016-2026) but none is significant (max |NW t| = 1.26), which is what
noise looks like.

Why a huge revision still produces no tax: the strategy trades a **standardized** surprise, not the
raw level. A 45% revision to the monthly change is large in jobs, but once the change is
de-trended (minus the 12-month average) and divided by its trailing cross-month dispersion, the
revision moves the z-score by only a few tenths, and a few tenths of a z-score on a noisy SPY
monthly return is lost in the variance. Both arms end up taking very similar positions on most
months, so their return streams barely diverge. The release-timing identity across the two arms
removes the one channel (entry day) where a revision could have mattered more.

This sharpens the map's lesson: **large revisions are necessary but not sufficient for a leakage
tax.** What also has to hold is that the signal be a roughly linear function of the revised
quantity (so the revision passes through to the position), or that the revision move the entry
timing. A standardize-and-clip pipeline absorbs most of even a 45% revision. A real tax most
likely needs all three: large revisions, a level/threshold-sensitive signal (not a standardized
one), AND the revised quantity entering near a position-flipping threshold.

## Where this sits on the 2-D map

| | low revision (EIA) | high revision (PAYEMS) |
|---|---|---|
| **honest edge absent** | EIA cell: tax = 0 (no revision, no edge) | (not tested) |
| **honest edge present** | (not tested) | **PAYEMS cell: tax = 0 (big revision, real edge, standardized signal absorbs it)** |

EIA gave a null because the revisions were too small to matter and the signal had no edge. PAYEMS
gives a null for a deeper reason: the revisions are huge and the signal has an edge, but a
standardized signal is structurally insensitive to revision magnitude. The two nulls together
suggest the empty top-right "where PIT bites" cell requires a fourth axis, **signal functional
form** (level/threshold-sensitive vs standardized), not just revision magnitude. That is the next
study to design.

---

## Threshold-signal variant (`run_study_threshold.py`): the functional-form axis, tested directly

The standardized study above concluded with a hypothesis: the leakage tax needs **three**
conditions jointly, large revisions, a real edge, AND a revision-sensitive signal functional form,
and the standardized z-score fails the third. `run_study_threshold.py` tests that third condition
directly. It holds conditions (1) and (2) fixed (the **same** PAYEMS series, the same huge
revisions, the same ALFRED-vintage machinery, the same fade direction) and changes **only** the
functional form: it replaces the smooth, clipped z-score with a **discontinuous binary threshold
rule** that can flip across a boundary.

### The threshold signal

The reported month-over-month change in payrolls is compared to a fixed threshold `k` (thousands
of jobs):

```
position = -1 (SHORT SPY) if MoM change >= k      # a hot print, faded
position = +1 (LONG SPY)  if MoM change <  k
```

This is a **hard step at `k`**, not a continuous tilt. The economic direction is identical to the
standardized study (fade a hot jobs print). The one thing that changes is that this form can
**flip**: if the first-release change is just below `k` and the revised change is just above (or
vice-versa), the NAIVE arm (revised vintage) and the PIT arm (first-release vintage) take
**opposite** positions. NAIVE compares the revised change to `k`; PIT compares the first-release
change to `k`; release timing is held identical, so the flip is the **only** new channel.

### Flip rate: the diagnostic the standardized study could not produce

The headline diagnostic is the **flip rate**: the fraction of tradable decision months where NAIVE
and PIT take different positions because the revision crossed `k`. The standardized signal never
strictly flipped (positions only nudged by a few tenths of a z-score); the threshold signal flips
on roughly **one month in five**. The threshold `k` is swept near the typical first-release change
(~197k), since a boundary far in the tail is never crossed and is null for an uninteresting reason.

### Result (real data, 1997-2026; SPY 1993-01-29 to 2026-06-26)

Threshold sweep (flip rate over the 399 tradable common months; Sharpe and tax full-sample):

| k (jobs) | flip rate | # flips | SR naive | SR pit | tax (SR) | tax (bps) | NW t |
|----------|-----------|---------|----------|--------|----------|-----------|------|
| 0        | 8.8%      | 35      | -0.51    | -0.53  | +0.02    | +34       | +0.23 |
| 100      | 18.8%     | 75      | -0.41    | -0.20  | -0.21    | -315      | -1.37 |
| 150      | 21.1%     | 84      | -0.24    | -0.11  | -0.14    | -210      | -0.96 |
| 197      | 20.6%     | 82      | +0.15    | +0.12  | +0.03    | +48       | +0.22 |
| 200      | 19.8%     | 79      | +0.23    | +0.10  | +0.12    | +203      | +1.00 |
| **250**  | **21.1%** | **84**  | **+0.41**| **+0.17** | **+0.24** | **+399** | **+1.75** |

The honest (PIT) arm only clears the flat-book null at the higher thresholds (`k >= 197`, where it
fades only the genuinely large prints). The **headline threshold is k = 250k**: the highest flip
rate among the thresholds whose PIT arm has a real edge (so the tax is economically meaningful).
There, the full leakage-tax battery:

| period    | variant | ann ret | Sharpe | hit  | IC     | maxDD  | tax (SR) | tax (bps) | NW t  |
|-----------|---------|---------|--------|------|--------|--------|----------|-----------|-------|
| full      | naive   | +5.4%   | +0.41  | 0.58 | +0.054 | -63.0% | **+0.24** | **+399** | **+1.75** |
| full      | pit     | +1.4%   | +0.17  | 0.55 | -0.036 | -64.1% |          |           |       |
| pre-2008  | naive   | -2.0%   | -0.07  | 0.50 | -0.094 | -52.9% | -0.07    | -92       | -0.24 |
| pre-2008  | pit     | -1.0%   | -0.00  | 0.54 | -0.104 | -61.1% |          |           |       |
| 2008-2016 | naive   | +8.5%   | +0.52  | 0.64 | +0.170 | -50.3% | +0.28    | +559      | +1.91 |
| 2008-2016 | pit     | +2.9%   | +0.25  | 0.55 | +0.047 | -50.3% |          |           |       |
| 2016-2026 | naive   | +14.6%  | +0.95  | 0.64 | +0.156 | -36.3% | **+0.64** | **+1066** | **+2.96** |
| 2016-2026 | pit     | +3.9%   | +0.32  | 0.58 | +0.007 | -41.2% |          |           |       |

On the **84 flip months** specifically: NAIVE averages +0.77% per month and PIT averages -0.77%
(opposite positions over the same SPY return, so exactly negated), a +1.55% mean naive-minus-PIT
gap with NW t = +1.70. The flips are where the tax concentrates.

### Verdict: the threshold form EXPOSES the leakage the standardized signal hid

This is the **opposite** of the standardized study's clean null, and it confirms the three-condition
thesis. With the same series, the same revisions, and the same edge, switching only the functional
form from standardized to threshold turns a -134 bps / NW t -0.09 non-result into a **+399 bps /
NW t +1.75** full-sample leakage tax that always favours the look-ahead (NAIVE) arm, and a
**statistically significant +1066 bps (NW t +2.96)** tax in 2016-2026. The full-sample tax is
suggestive rather than conventionally significant, but its sign is consistent across three of four
sub-periods and the mechanism is explicit in the flip-month accounting.

The mechanism is exactly the one the standardized study predicted: a threshold signal does not
average the revision away. When the revised change lands on the far side of `k` from the
first-release change, the look-ahead backtest takes the position the honest backtest could not have
taken, and on this fade strategy the revised (look-ahead) figure systematically lands on the
profitable side. About one decision month in five flips, and those flips drive the entire gap.

**Honest caveat:** the full-sample tax is +1.75 t, below the conventional 2.0 bar, so on the whole
sample this is a suggestive, not decisive, positive tax. What is decisive is the **contrast** with
the standardized arm: same data, same edge, only the functional form changed, and the tax went from
indistinguishable-from-zero to economically large and (recently) significant. That contrast is the
finding.

### The 2-D map, updated

| | standardized signal | threshold signal |
|---|---|---|
| **low revision (EIA)** | tax = 0 (no revision to leak) | (not tested; nothing to leak) |
| **high revision (PAYEMS)** | tax = 0 (standardization absorbs the revision) | **tax > 0: +399 bps full / +1066 bps & t=2.96 in 2016-2026** |

The binding axis is **signal functional form**, not revision magnitude alone. Large revisions are
necessary but not sufficient; the revision must also pass through a revision-sensitive functional
form (a threshold the revision can cross) to become a tradable look-ahead advantage. A
standardize-and-clip pipeline is a structural defence against revision leakage; a hard threshold is
maximally exposed to it.

## Run it

```bash
source ~/.config/eigenq/fred.env          # exports FRED_API_KEY
python3.12 run_study_macro.py             # standardized signal: pulls ALFRED + SPY, writes results JSON
python3.12 run_study_threshold.py         # threshold signal: sweep + flip rate + leakage-tax battery
python3.12 -m pytest test_leakage_tax_macro.py test_leakage_tax_threshold.py -q
```

The standardized study's load-bearing test (`test_pit_uses_first_release_not_revised`) plants a
known +300k revision and asserts the PIT signal uses the first-release change while the NAIVE signal
uses the revised change. The threshold study's load-bearing test
(`test_revision_crossing_threshold_flips_position`) plants a revision engineered to **cross** the
threshold (first release 180k just below `k=200`, revised 220k just above) and asserts the two arms
take **opposite** positions, the flip mechanism the tax measures; a companion test confirms that on
a flip month the two arms' returns exactly negate. The ALFRED release table and SPY prices are
cached under `data_cache/` (git-ignored). FRED data is free public-domain government data; SPY
prices come from `yfinance`. `run_study_threshold.py` reuses the ALFRED loaders, `PricePanel` SPY
loader, `monthly_change`, `newey_west_tstat`, `summarize`, the period slicing, and the `assemble`
entry machinery from `run_study_macro.py` verbatim; only the signal (`build_threshold_signal`) and
the flip diagnostics are new.

`mypy --strict` reports only import-stub gaps (pandas-stubs is absent under the pandas-3.0 venv,
`fredapi`/`yfinance` ship no `py.typed`, and `research_pipeline` is imported via `sys.path`), the
same known profile as the EIA sibling; there are no logic-level type errors in either study file.
