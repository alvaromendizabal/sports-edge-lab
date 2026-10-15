# NFL Edge Lab — Data Catalog and Temporal Safety

## Source families

| Family | Acquired from | Temporal limitation |
| --- | --- | --- |
| Schedule, historical odds reference, game results | nflverse/nfldata `games.csv` and separate initial/closing lines | Results and observed postgame fields are embedded; archived line is not a timestamped book quote |
| Play-by-play and weekly stats | nflverse public release assets, 1999 onward | Contains game outcomes; only lagged, as-of features permitted |
| Player/roster/participation | nflverse rosters, stats_player, player_stats, snap_counts, depth_charts, pbp_participation | Roster updates and participation recorded retrospectively, so publication-time audit required |
| Advanced analytics | nflverse nextgen_stats, pfr_advstats, ftn_charting, ESPN QBR | Availability windows differ; do not assume full proprietary tracking access |
| Injury reports | nflverse releases and planned official NFL injury bulletin acquisition | Known gaps for recent seasons; as-of publication timestamp may be absent |
| Travel/venue | nfldata airports and stadium metadata | Confirm venue, kickoff timezone and actual travel conditions |
| Weather forecasts | Planned Iowa Environmental Mesonet archived NWS forecast products | Must use forecasts **issued before** decision time, never realized game weather |
| Timestamped NFL betting odds | Planned The Odds API paid historical endpoints | Preserve snapshots, bookmaker update timestamp, market keys and quote price |
| Premium player grades | Planned PFF Pro API purchase/coverage audit | Subscription/API rights and historical fields must be verified |

## Non-negotiable feature policy

**Eligible pregame features**: game identifiers, prior completed game/team/player statistics, known roster/eligibility/practice statuses published as of decision time, archived odds quotes known as of decision time, and weather forecasts issued before decision time.

**Prohibited postgame features for future game predictions**: final score, result, true winning team, realized cover, total points, actual snaps, actual weather, confirmed starters learned after kickoff, postgame injury information, and predictions/ratings trained on future games.

Never derive a quote's as-of time from the time the CSV was downloaded.

## Storage

- Private raw archive: `s3://sagemaker-nfl-edge-lab-560403859723-us-west-2/raw/`
- Private licensed odds: `s3://sagemaker-nfl-edge-lab-560403859723-us-west-2/paid/`
- Source checksums and metadata: public `catalog/public_asset_manifest_20261015.json`
- Local SageMaker copy: `/home/sagemaker-user/nfl-edge-lab-data/`
- Public repository: code, tests, source inventory, model cards, metrics; **no third-party raw files**

License and attribution review is required before commercial or public redistribution.
