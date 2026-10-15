# NFL Edge Lab — Paid & Additional Source Acquisition Plan (2026-10-15)

**Status:** public NFL asset acquisition complete (815/815 pinned assets; 722,613,027 bytes in private project S3). **No paid subscriptions purchased; no paid API key obtained.**

## Primary paid provider — The Odds API

- Vendor: https://the-odds-api.com/
- Official v4 historical documentation: https://the-odds-api.com/liveapi/guides/v4/
- Prices: https://the-odds-api.com/#get-access; 5,000,000-credit plan advertised $119/month and 100,000-credit plan $59/month (verify at checkout).
- Data: archived NFL pregame bookmaker offers (moneyline, spread, total) from June 2020; additional player prop and alternate markets may be available from May 2023. Snapshots were 10-minute cadence originally and 5-minute from September 2022.
- Historical featured endpoint: `GET https://api.the-odds-api.com/v4/historical/sports/americanfootball_nfl/odds?regions=us&markets=h2h,spreads,totals&date=<UTC>&apiKey=<SECRET>`
- The API returns the historical snapshot at or before requested date. Store **actual** snapshot timestamp and each bookmaker/market last-update timestamp, never just the requested date.
- A three-market, one-region historical snapshot costs **30 credits** (10 per region per market). The reported headers `x-requests-remaining`, `x-requests-used`, `x-requests-last` provide the authoritative usage ledger.
- Use the featured historical endpoint rather than event-level endpoint for standard moneyline/spreads/totals. Event-level snapshots for player prop markets require historical event IDs, discoverable from the historical events endpoint.
- Data rights: retain in *private* S3 for research/ML; no GitHub upload or raw licensed-data redistribution. Reconfirm your specific plan terms before publishing aggregate derivatives or a public dashboard.

### Backfill strategy

1. First trial a few known NFL game timestamps in 2024 and 2025, before making a full paid backfill.
2. Read pregame kickoff UTC from verified schedule tables. Build T−72h, T−24h, T−6h, and T−15m target snapshots, plus opening and near-close snapshots if reliably captured.
3. Deduplicate target timestamps across simultaneous games: a single featured-market snapshot includes **multiple games**, so do not bill one request per game needlessly.
4. Only request one US region initially. Later add a second region or specific US bookmakers if coverage analysis justifies the increase.
5. Archive exact raw response bytes and response headers to versioned S3 keys (UTC, market, region, response hash), plus a manifest mapping original request to returned snapshot, vendor coverage, source availability and spend.
6. Use bounded monthly credit cap, per-run request cap, exponential backoff for 429s, 5xx retries, and receipts. Stop before the cap; track exact credits from response headers, not just estimates.
7. Validate game ID/team mapping, offered American/decimal odds, market pricing and line directions, bookmaker update times, duplicate rows, vig, and whether a quote could have been available at the hypothesized pregame decision timestamp.

**Illustrative credit budgets (not vendor quotes):**
- At three markets in one region, 30 credits per successful historical snapshot.
- 1,000 distinct timestamps = ~30,000 credits.
- 3,000 distinct timestamps = ~90,000 credits.
- 10,000 distinct timestamps = ~300,000 credits.
- Prop requests are event-scoped and scale with the number of games and player markets; account for them separately. Empty/failed responses can alter actual billing.

**Plan decision:** the $59/100K plan may cover a carefully deduplicated featured-market pilot. For **full historical depth plus multi-bookmaker and player props**, prefer the $119/5M plan as long as current terms and quotas are reconfirmed; one month of focused backfill, then evaluate whether to downgrade or cancel. Buying more credits does not create earlier-than-offered source history.

**Secret provisioning:** Do not paste a key into chat, notebooks, Github, scripts, or terminal history. Use AWS Systems Manager Parameter Store SecureString or AWS Secrets Manager, scope the execution role narrowly, and pass credentials at execution time. Never print API keys or signed request URLs in logs.

## Additional provider evaluation

| Priority | Source | Data to verify | Access, caveats |
|---|---|---|---|
| High | SportsDataIO NFL Betting Feeds | Historical pregame line movement, player props, sportsbook mapping, historical availability | Commercial tiers and licensing vary; request a coverage/sample extract first. https://sportsdata.io/developers/api-documentation/nfl |
| High | SportsDataIO NFL player/depth/injury feeds | Original timestamped injuries, starters, depth charts, playtime/snap reports | Verify point-in-time coverage and whether historical revisions are preserved. https://sportsdata.io/ |
| Medium | PFF / Sports Info Solutions / FTN premium | Player grades, pressure, scheme and matchup charting | Commercial quote required; confirm historical seasons and model-training rights before procurement |
| Medium | Sportradar NFL feeds | Plays, rosters, injuries, event statistics and richer football reference data | Commercial; validate endpoints/history and licensing. https://developer.sportradar.com/football/reference/nfl-overview |
| Free | NOAA NCEI / Iowa State Mesonet | Stadium weather observations, archived issued forecast products | Reconstruct weather that was *forecast* pregame, not observed postgame. https://www.ncei.noaa.gov/ , https://mesonet.agron.iastate.edu/ |
| Free/limited | NFL official injury & practice reports | Timestamped practice participation, game status | Audit archival completeness and respect site rate limits/robots; do not backfill missing historical timestamps with retrospective values |
| Free | NFLverse/nfldata | Play-by-play, team/player, Next Gen aggregated, FTN samples, archived game lines | 815 assets archived already; still needs schema/date/availability audits |

## S3 storage plan

- `raw/nflverse/`, `raw/nfldata/`: completed original source archive.
- `raw/paid/the_odds_api/`: original immutable API responses, private.
- `raw/paid/sportsdataio/`: only if purchased and licensed.
- `raw/weather/noaa/`, `raw/weather/forecasts/`: source captures with issuance timestamps.
- `curated/market_quotes/`: normalized price/time/availability ledger; enforce game start > market observed time.
- `curated/pregame_features/`: strictly as-of feature matrices, independently versioned.
- `manifests/`, `reports/`: receipts, sizes, hashes, schema stats, credit usage, missingness, coverage gates.

## Mandatory gates

- **Rights:** verify training, caching, redistribution and employer-demo permissions.
- **Temporal integrity:** pregame existence, actual update timestamp, player news timing, bookmaker market freshness.
- **Coverage:** source × season × week × bookmaker × market × lag window.
- **Quality:** sample game/line manually compared to canonical games; no duplicate/quasi-postgame labels.
- **Economics:** actual credits and AWS costs tagged to project; no auto-renew commitments assumed.
- **Data lineage:** each upstream asset/version and transformed table reproducible and auditable from its own source snapshots.

The project is designed for research and paper backtests. No profitability is asserted without strict chronological, out-of-sample evaluation.
