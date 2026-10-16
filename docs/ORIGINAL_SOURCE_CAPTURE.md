# Original-source capture

The [ESPN collector](../tools/acquire_espn.py) directly captures scoreboard and game-summary responses for the NFL, NBA, NCAA football, NCAA men's basketball and NCAA women's basketball. College scope is FBS football and Division I basketball.

It discovers events by date range and recursively splits intervals when the response appears saturated or ignores the requested dates. Game summaries can include box scores, plays or drives where exposed by the source; absent sections are recorded instead of assumed. It does not claim every season or event is available.

## Operation

Default limits are 3,300 seconds, 6,000 new summaries, a global two requests per second and four summary workers. The runner checks published robots rules, observes access denials and rate limiting, and never bypasses a blocked endpoint. Date discovery and summary acquisition use separate portions of the bounded run.

Private raw records are stored in the central bucket at `tracks/{sport}/raw/espn/`, with run receipts under `shared/acquisition/espn/{run_id}/`. Completed historical captures are reused; recent or incomplete events receive separate vintages. One compact return ZIP is produced per execution.

## Availability and acceptance

A completed game summary retrieved today is a historical outcome source, not evidence of what was known before that game. The collector explicitly records `historical_available_at: null`. All pregame features need a separate availability audit and must use only prior games or a timestamped pregame source.

Six embedded offline checks cover URL construction, grouping, date splitting, date filtering and return behavior. A synthetic end-to-end capture/resume check was also performed before launch. Live source accessibility, observed coverage and AWS storage success are reported only from actual run receipts.
