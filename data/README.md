# WRDS OptionMetrics + FRED data

Encrypted (git-crypt) market data for backtesting.

## Files

| File | Contents | Encrypted |
| --- | --- | --- |
| `optionmetrics_secid_ticker_cusip.csv` | secid ↔ ticker mapping | no |
| `optionmetrics_asset_prices.csv` | underlying daily closes | no |
| `optionmetrics_tickers_options_data.csv` | option chains (best_bid/offer, IV) | no |
| `portfolio_atm_options.parquet` | engine-ready ATM ±3% subset | no |
| `fred_treasury.enc` | FRED short-rate series | yes |
| `wrds_sp500.enc`, `wrds_spx_options.enc`, `wrds_vix.enc` | extended WRDS pulls | yes |

## Provenance

- Source: WRDS OptionMetrics IvyDB US, FRED
- Tickers: SPY, QQQ, AAPL, MSFT, JPM
- Date range: 2019-01-01 to 2024-12-31
- License: Academic use only

## Setup

See [docs/wrds_data_download.md](../docs/wrds_data_download.md) for the WRDS download procedure.
Encrypted files require git-crypt; request the decryption key from the maintainer via secure channel.
