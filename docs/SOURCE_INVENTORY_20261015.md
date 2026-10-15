# NFL Edge Lab — Verified Release Source Inventory

Generated from the [nflverse/nflverse-data releases API](https://api.github.com/repos/nflverse/nflverse-data/releases), audited 2026-10-15. The table reports **release asset inventory**, NOT files downloaded or coverage verified in local storage. We never assume data exists for every year in a span; inspect each asset name and source license before use.

| Release tag | All asset formats | Parquet assets | Aggregate Parquet MB | Parquet season labels | Examples |
|---|---:|---:|---:|---|---|
| [trades](https://github.com/nflverse/nflverse-data/releases/tag/trades) | 7 | 1 | 0.1 | global/varied | `trades.parquet` |
| [teams](https://github.com/nflverse/nflverse-data/releases/tag/teams) | 7 | 1 | 0 | global/varied | `teams_colors_logos.parquet` |
| [schedules](https://github.com/nflverse/nflverse-data/releases/tag/schedules) | 6 | 1 | 0.5 | global/varied | `games.parquet` |
| [stats_team](https://github.com/nflverse/nflverse-data/releases/tag/stats_team) | 554 | 111 | 8.5 | 1999–2026 | `stats_team_week_2003.parquet`, `stats_team_week_2004.parquet` |
| [stats_player](https://github.com/nflverse/nflverse-data/releases/tag/stats_player) | 554 | 111 | 38.1 | 1999–2026 | `stats_player_week_2003.parquet`, `stats_player_week_2004.parquet` |
| [ftn_charting](https://github.com/nflverse/nflverse-data/releases/tag/ftn_charting) | 21 | 5 | 2.4 | 2022–2026 | `ftn_charting_2023.parquet`, `ftn_charting_2022.parquet` |
| [espn_data](https://github.com/nflverse/nflverse-data/releases/tag/espn_data) | 12 | 2 | 0.4 | global/varied | `qbr_season_level.parquet`, `qbr_week_level.parquet` |
| [weekly_rosters](https://github.com/nflverse/nflverse-data/releases/tag/weekly_rosters) | 104 | 25 | 14.4 | 2002–2026 | `roster_weekly_2002.parquet`, `roster_weekly_2003.parquet` |
| [players](https://github.com/nflverse/nflverse-data/releases/tag/players) | 7 | 1 | 3.4 | global/varied | `players.parquet` |
| [pbp_participation](https://github.com/nflverse/nflverse-data/releases/tag/pbp_participation) | 46 | 11 | 37.4 | 2016–2025 | `pbp_participation_2016.parquet`, `pbp_participation_2017.parquet` |
| [officials](https://github.com/nflverse/nflverse-data/releases/tag/officials) | 7 | 1 | 0.2 | global/varied | `officials.parquet` |
| [misc](https://github.com/nflverse/nflverse-data/releases/tag/misc) | 17 | 1 | 1 | global/varied | `pfr_rosters.parquet` |
| [draft_picks](https://github.com/nflverse/nflverse-data/releases/tag/draft_picks) | 7 | 1 | 0.7 | global/varied | `draft_picks.parquet` |
| [contracts](https://github.com/nflverse/nflverse-data/releases/tag/contracts) | 7 | 1 | 11.1 | global/varied | `historical_contracts.parquet` |
| [snap_counts](https://github.com/nflverse/nflverse-data/releases/tag/snap_counts) | 77 | 15 | 3 | 2012–2026 | `snap_counts_2012.parquet`, `snap_counts_2013.parquet` |
| [rosters](https://github.com/nflverse/nflverse-data/releases/tag/rosters) | 434 | 107 | 17.1 | 1920–2026 | `roster_1981.parquet`, `roster_1982.parquet` |
| [player_stats](https://github.com/nflverse/nflverse-data/releases/tag/player_stats) | 1822 | 365 | 63.9 | 1999–2024 | `player_stats_kicking_2017.parquet`, `player_stats_2021.parquet` |
| [pfr_advstats](https://github.com/nflverse/nflverse-data/releases/tag/pfr_advstats) | 209 | 40 | 2.9 | 2018–2026 | `advstats_week_def_2021.parquet`, `advstats_week_pass_2021.parquet` |
| [pbp](https://github.com/nflverse/nflverse-data/releases/tag/pbp) | 164 | 28 | 494 | 1999–2026 | `play_by_play_2013.parquet`, `play_by_play_2014.parquet` |
| [nextgen_stats](https://github.com/nflverse/nflverse-data/releases/tag/nextgen_stats) | 95 | 3 | 2.3 | global/varied | `ngs_passing.parquet`, `ngs_rushing.parquet` |
| [injuries](https://github.com/nflverse/nflverse-data/releases/tag/injuries) | 77 | 18 | 2 | 2009–2026 | `injuries_2009.parquet`, `injuries_2010.parquet` |
| [depth_charts](https://github.com/nflverse/nflverse-data/releases/tag/depth_charts) | 109 | 26 | 16.2 | 2001–2026 | `depth_charts_2002.parquet`, `depth_charts_2003.parquet` |
| [combine](https://github.com/nflverse/nflverse-data/releases/tag/combine) | 7 | 1 | 0.4 | global/varied | `combine.parquet` |

## Recommended acquisition method

1. Query the release API for each tag, record the API ETag / `updated_at` / immutable asset ID, and select actual published `.parquet` files rather than assuming filename templates. If a release contains many files, paginate `releases/{id}/assets?per_page=100&page=N` until exhausted.
2. Acquire all available target-season Parquet assets (1999–2026 where offered) plus static players, teams, schedules, draft, contracts, combine, and official mapping files.
3. Archive with original source URL and SHA-256 alongside schema/row counts and extraction UTC timestamp in encrypted private S3. GitHub gets only code and provenance, **never paid licensed datasets**.
4. Distinguish a data *observation timestamp* from a *source update timestamp*. Historical injuries, depth charts, and next-gen stats may not preserve the exact snapshot that existed before every game.
5. For historical odds use a separate paid-feed connector. Closing odds from a retrospective dataset are not evidence that a given price was available 72 hours before kickoff.

## Known caveats

- nflverse's 2025 injury releases have documented availability issues; do not silently fill missing historical weeks with postgame revisions.
- Next Gen Stats includes aggregated statistics, not unrestricted proprietary full player-tracking coordinates.
- This audit inventories upstream assets; it does not verify permissions to redistribute. Follow upstream attribution and terms.
