# Current market source recovery

[Dashboard](review.html#latest-coverage) · [Forecast status](CURRENT_FORECAST_STATUS.md) · [Public overlay](current_source_overlay.json) · [Validator](current_source_overlay.py)

Additional Week 9 references are recovered from authenticated partial N035 source checkpoints. This is **partial source recovery, not an authenticated completed owner research return**. It adds market observations without changing any existing forecast, fit, issue time, historical result or earlier public payload.

## Coverage for all 15 Week 9 games

| Provider | Winner direction | Home-margin reference | Total reference |
|---|---:|---:|---:|
| DraftKings | 14 / 15 | 14 / 15 | 14 / 15 |
| Kalshi | 14 / 15 | 14 / 15 | 10 / 15 |
| Polymarket | 11 / 15 | 11 / 15 | 11 / 15 |

The overlay contains all 135 game/provider/target states: 45 winner states and 90 point states. Every missing reference keeps its evidence-specific explanation. These counts describe available references, not qualified bets or complete provider histories.

## How to read the current view

Choose **Current week · Week 9**, then **Latest observed upcoming**. The display selects the latest usable current reference independently of outcomes. A missing or older new capture does not erase an existing usable reference. Recovered rows are labelled in the card; the details retain actual quote and acquisition clocks.

Kalshi's recovered current books have genuine observation timestamps but no provider quote timestamp. They therefore say **Observed … · provider quote time unavailable**. The observation time is not invented as a quote time. These rows are restricted to the latest-observed view; they do not fill T−1h, T−2h or latest-before-kickoff history.

Winner directions require both team books and consistent directions. The compact export retains rounded home-contract midpoint proxies, but the UI displays only the derived team direction. Binary payout and tie semantics prevent treating those proxies as calibrated, executable two-team win probabilities.

Margin and total references show a quoted payoff condition and, when supported, an observed contract probability. They are not provider mean scores, complete distributions, model cover probabilities, executable fills or fee-adjusted returns. A threshold with missing or ambiguous source support remains unavailable.

## Preserved evaluation and model boundaries

The five earlier public JSON payloads are unchanged. The 121 completed games, Monday's original Seattle forecast and loss, the accepted N033 research scorecard, and all historical disagreements retain their original values and clocks. The partial source overlay adds no new fits or accepted research stages and does not qualify the early forecasts as final-hour recommendations.

Current injury/QB information remains **not verified in the displayed forecasts**. The separate Ravens source update describes current team information; it is not a manual adjustment to the saved Jacksonville–Baltimore projection. Personal wager activity is not tracked by this dashboard.

Public validation checks complete state coverage, quote/observation distinctions, pregame acquisition, rounded public values and separation from paired metrics. Authentication of private checkpoint and raw-source custody is separate from these public presentation tests.
