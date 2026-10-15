# NFL Edge Lab — Paid Data Acquisition Plan (2026-10-15)

**Current status:** No third-party paid subscriptions have been purchased, and no API key is installed by this project. We separately acquired/cataloged public sources; purchase and private credential entry require the account holder.

## Prioritized vendors

| Priority | Vendor | Verified price | Why | Key constraint |
| --- | --- | --- | --- | --- |
| 1 | [The Odds API](https://the-odds-api.com/) | 20K/$30, 100K/$59, 5M/$119 monthly | Multi-bookmaker historical NFL h2h/spread/total snapshots since June 2020; some player props history since May 2023 | Paid key; 10 credits per market/region/snapshot for featured historical feeds; plan first |
| 2 | [PFF PRO](https://www.pff.com/subscribe) | $199.99 per year listed | Premium player grades, charting and programmatic API access | Confirm historical NFL programmatic endpoints, data terms and usage allowance before purchase |
| 3 | [SportsDataIO Discovery Lab](https://sportsdata.io/developers) | Odds $99/month; Fantasy + Odds $149/month listed | Independent market and player-data cross-check | Next-day delayed research product; historical point-in-time correction trails generally unavailable outside odds movements |
| 4 | [SportsDataIO enterprise odds](https://sportsdata.io/live-odds-api) | Quote | Full pregame line movement, sportsbook-specific history, broad props | Verify archive coverage and license in writing; do not infer coverage from marketing text |

**Recommended first purchase:** The Odds API **5M plan ($119/month)** for a bounded one-month historical backfill; only purchase after confirming the NFL archives, specific bookmakers and permitted archival research rights. A 100K plan ($59/month) may suffice for sparse as-of snapshots; 5M leaves room for deeper intraweek time series and propensity/line movement research.

Official endpoint: `/v4/historical/sports/americanfootball_nfl/odds`, with `markets=h2h,spreads,totals`, `regions=us` and `date=...` (UTC). The billing formula for these core historical markets is `10 × markets × regions`, i.e. **30 credits per request** at 3 markets and one region. This is not the same as requesting every individual game's player props.

Reference prices and docs:
- https://the-odds-api.com/
- https://the-odds-api.com/liveapi/guides/v4/
- https://the-odds-api.com/historical-odds-data/
- https://www.pff.com/subscribe
- https://sportsdata.io/developers
- https://sportsdata.io/help/historical-data-integration-guide

## Point-in-time policy

For every quote persist `requested_snapshot_utc`, `returned_snapshot_utc`, `bookmaker_last_update`, `commence_time`, book and market key, full unmodified response, price and point. Do not treat the time a corrected game or player dataset was downloaded as the historical availability time.

Store secrets only in AWS Secrets Manager or environment variables loaded from a secure store. Raw licensed responses belong in the **private** bucket `s3://sagemaker-nfl-edge-lab-560403859723-us-west-2/paid/` under a segregated prefix. They must never be committed or publicly redistributed.

## Additional source workstreams

- Reconstruct NFL injury publication timestamps from official NFL injury/practice bulletins, and explicitly flag availability gaps by week.
- Join historic NOAA/NWS **forecasts issued before kickoff**, not realized game weather, for backtesting.
- Audit archived point-spread/moneyline reference lines back into historical seasons with source and time provenance.
- Archive pregame QB announcements and projected depth charts; separate observed after-game starter from forecast starter.
- Build planned line snapshots at T−72h, T−24h, T−6h and T−15m, and later additional movement series; confirm actual historical book availability.
- Include a player-prop-specific cost/coverage study before any bulk requests.

No profitability, availability, line completeness or exclusive-data access is claimed until supported by raw archive evidence.
