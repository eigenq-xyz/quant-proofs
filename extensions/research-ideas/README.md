# research-ideas

Exploratory work that doesn't yet meet this repo's bar for a load-bearing result. Nothing here
is formally verified and nothing here is claimed as an edge; it's preserved because the code and
the question are worth more than deleting them, not because the finding is done.

Moved out of `research-pipeline/` on purpose: that package's contents all route through the
verified backtester or are otherwise disclosed and defensible. Mixing exploratory breadth work
into it made the pipeline's actual claims harder to see.

## What's here

- **[Leakage-tax map](LEAKAGE_MAP.md)** (`commodity-leakage-tax/`, `macro-leakage/`): does a
  data-revision look-ahead artifact explain apparent alpha in a CFTC positioning signal, an EIA
  gas-storage signal, or a nonfarm-payrolls signal? Early finding: whether it matters depends on
  the signal's functional form, not how heavily the series is revised. Not enough studies have
  run to generalize this past three series.
- **Cross-asset breadth** (`crossasset.py`, `run_cross_asset.py`, `compare_combine.py`): does a
  momentum signal built on AQR's free pre-built factor-return sleeves (TSMOM,
  Value-and-Momentum-Everywhere) generalize across equities, bonds, currencies, commodities? These
  consume return streams that never touch the verified event-driven backtester, so the output is
  breadth/generalization evidence, not a verified result. For the raw-price variant that does
  route through the verified backtester, see `research_pipeline.crossasset.run_cross_asset` in
  `research-pipeline/src/` (that one stayed in the pipeline package).

## What it doesn't claim

- No formal verification. Nothing here is proved in Lean.
- No claim of a tradable edge. These are ideas being tried, not results being reported.
- The AQR cross-asset breadth work specifically does not inherit the research-pipeline's
  no-look-ahead guarantee, because it never runs through the backtester the guarantee covers.

## Run

```bash
cd extensions/research-ideas
python3.12 commodity-leakage-tax/run_study.py
python3.12 commodity-leakage-tax/run_study_eia.py
source ~/.config/eigenq/fred.env && python3.12 macro-leakage/run_study_macro.py
python3.12 macro-leakage/run_study_threshold.py
python3.12 run_cross_asset.py --dataset tsmom
python3.12 run_cross_asset.py --dataset vme
python3.12 compare_combine.py --dataset tsmom
```

Each script's `_meta.reproduce` field in its output JSON is the authoritative command.

## Dependencies

Imports `research_pipeline` (from `research-pipeline/src/`) as an installed-package dependency,
not a relative import: this directory lives outside that package on purpose, so `sys.path` is
extended at the top of each script.

## License

Apache 2.0.
