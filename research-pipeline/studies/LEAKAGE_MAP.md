# Where does point-in-time discipline actually matter? A leakage-tax map

One question runs through these studies: **how much of a backtest's apparent alpha is an
artifact of look-ahead in the data rather than in the code?** A strategy can be perfectly
non-anticipating in its logic (the property the pipeline proves formally) and still be
contaminated if the *values* it reads were not knowable at decision time, either because the
figure had not been released yet (release-timing look-ahead) or because the figure was later
revised (revision look-ahead).

Rather than assert that this contamination is large, these studies measure it on real data
across several series and report an honest map of where it bites and where it does not. The
leakage tax is defined as the metric gap between a NAIVE backtest (reads the figure as if it
were knowable immediately) and a point-in-time honest backtest (reads only what was actually
released and unrevised at decision time), with a Newey-West HAC t-stat on the per-period return
difference. Every cell runs on identical code with only the data-timing rule changed.

## The cells

| Study | Series | Leakage channel | Revision size | Signal form | Leakage tax | NW t | Verdict |
|-------|--------|-----------------|---------------|-------------|-------------|------|---------|
| `commodity-leakage-tax` (COT) | CFTC managed-money crude positioning | Release timing (3.5-day lag) | n/a | Standardized percentile, continuous | +151 bps/yr | +0.22 | Null |
| `commodity-leakage-tax` (EIA) | EIA natural-gas storage | Revision | Tiny (0.90 Bcf mean, 12% of weeks revised) | Standardized surprise | -10 bps/yr | +0.15 | Null |
| `macro-leakage` (standardized) | Nonfarm payrolls (`PAYEMS`) | Revision | Large (revised in 99.9% of months, mean change-revision ~45% of the median monthly change) | Standardized, clipped surprise | -134 bps/yr | -0.09 | Null |
| `macro-leakage` (threshold) | Nonfarm payrolls (`PAYEMS`) | Revision | Large (same series) | Hard threshold (fade hot print at k=250k) | +399 bps/yr full | +1.75 | Exposed but modest |

## What the map says

The first three cells all come back null, and the third is the decisive one. Nonfarm payrolls
is about the most heavily revised major macro series there is: it is revised in essentially
every month, and the typical revision is close to half the size of the monthly change the signal
keys on. If revision size alone drove a leakage tax, this is exactly where it should appear. It
does not. A standardized, clipped payrolls-surprise signal shows no tax (and the point-in-time
arm is, if anything, slightly stronger). The reason is mechanical: z-scoring and clipping map a
revised level and its final level onto nearly the same standardized position, so the trade does
not change.

The binding axis is therefore **not revision magnitude but signal functional form.** Swapping the
identical payrolls data onto a hard threshold signal (go short if the reported print is above a
cutoff, long otherwise) does expose a tax: the decision flips between the naive and point-in-time
arms in 21% of months, and on full sample the gap favors the naive (revised-data) arm by about
399 bps/yr. So the mechanism is real and reproducible.

The honest caveat is that even the exposed case is modest and not robust on full sample. The
cutoff k=250k was selected from a small sweep for its high flip rate; the full-sample t-stat is
1.75, below the conventional 2.0; the effect is negative in the pre-2008 subperiod and is
significant only in the recent 2016-2026 window (t=2.96). The defensible claim is qualitative,
not a measured alpha: **a standardized-and-clipped signal is structurally immune to revision
look-ahead, a level or threshold signal on the same data is exposed, and point-in-time discipline
is cheap insurance whose payoff depends on the signal's functional form, not on how heavily the
series is revised.**

A second, orthogonal point the map keeps separate: revision frequency tells you about the leakage
axis, not about whether a knowable value is *reliable*. A barely-revised series can be barely
revised because it is a near-census (EIA storage, trustworthy) or because nobody bothers to
correct it (untrustworthy). Reliability is read off the measurement mechanism, not off revision
stability. Point-in-time discipline addresses the leakage axis regardless; filtering or robust
estimation addresses the reliability axis.

## Reproducing

Each cell has its own README with the data sources, the exact signal and timing rules, and the
no-look-ahead argument. The runners reuse the pipeline's verified primitives (`PricePanel` for
point-in-time price access, the Newey-West HAC estimator, the evaluation metrics). Raw data is
fetched at runtime into per-study `data_cache/` directories that are git-ignored and never
committed; only the small summary `results_*.json` files and the source are tracked.

- `commodity-leakage-tax/README.md` (CFTC COT, release timing) and `README_eia.md` (EIA, revision)
- `macro-leakage/README.md` (payrolls, revision; standardized and threshold variants)
