# Current market source recovery

[Dashboard](review.html#latest-coverage) · [Forecast status](CURRENT_FORECAST_STATUS.md) · [Public overlay](current_source_overlay.json) · [Validator](current_source_overlay.py)

Additional Week 9 references combine preserved N035 source checkpoints with the authenticated **N036 source-only return**. The latter reached its registered public-request budget and is not completed owner research acceptance. It adds market observations without changing any historical result or earlier public payload. A separate primary-issue addendum displays later genuinely issued early forecasts with their own clocks; acquisition alone never updates a forecast.

## Coverage for all 15 Week 9 games

| Provider | Winner direction | Home-margin reference | Total reference |
|---|---:|---:|---:|
| DraftKings | 15 / 15 | 15 / 15 | 15 / 15 |
| Kalshi | 15 / 15 | 15 / 15 | 15 / 15 |
| Polymarket | 13 / 15 | 13 / 15 | 13 / 15 |

The original overlay contains all 135 game/provider/target states: 45 winner states and 90 point states. The separate schedule-revision addendum replaces three previously unavailable display states for one exact event. A separate immutable [N036 addendum](source_recovery_n036.json) adds 13 more reference cells captured through November 4, 04:25:40 UTC. Polymarket TB–CHI and BUF–MIN remain unavailable; the source budget stopped during the first of these events. Every remaining missing reference keeps its evidence-specific explanation. These counts describe available references, not qualified bets or complete provider histories.

## How to read the current view

Choose **Current week · Week 9**, then **Latest observed upcoming**. The display selects the latest usable current reference independently of outcomes. A missing or older new capture does not erase an existing usable reference. Recovered rows are labelled in the card; the details retain actual quote and acquisition clocks.

Kalshi's recovered current books have genuine observation timestamps but no provider quote timestamp. They therefore say **Observed … · provider quote time unavailable**. The observation time is not invented as a quote time. These rows are restricted to the latest-observed view; they do not fill T−1h, T−2h or latest-before-kickoff history.

Winner directions require both team books and consistent directions. The compact export retains rounded home-contract midpoint proxies, but the UI displays only the derived team direction. Binary payout and tie semantics prevent treating those proxies as calibrated, executable two-team win probabilities.

Margin and total references show a quoted payoff condition and, when supported, an observed contract probability. They are not provider mean scores, complete distributions, model cover probabilities, executable fills or fee-adjusted returns. A threshold with missing or ambiguous source support remains unavailable.

## Preserved evaluation and model boundaries

All eight earlier public JSON payloads are unchanged. The 121 completed games, Monday's original Seattle forecast and loss, the accepted N033 research scorecard, and all historical disagreements retain their original values and clocks. The partial source overlay adds no new fits or accepted research stages and does not qualify the early forecasts as final-hour recommendations.

Current injury/QB information remains **not verified in the displayed forecasts**. The separate Ravens source update describes current team information; it is not a manual adjustment to the saved Jacksonville–Baltimore projection. Personal wager activity is not tracked by this dashboard.

Public validation checks complete state coverage, quote/observation distinctions, pregame acquisition, rounded public values and separation from paired metrics. Authentication of private checkpoint and raw-source custody is separate from these public presentation tests.

## Schedule revision reference

The separate [LV–SF addendum](reschedule_reference.json) recovers one DraftKings winner, home-margin and total reference from an already authenticated capture. Its six source outcomes were independently replayed against their physical source and receipt hashes. The source event and ordered teams are the same; the provider retained the original **November 8, 21:05 UTC** kickoff, while the official current schedule says **21:25 UTC**.

The quote was updated **November 4 at 01:51:50 UTC** and captured **01:52:38 UTC**. The exact schedule mapping was verified separately at **03:33:20 UTC**. This recovery made **zero new provider requests**. The revision's first publication time is unknown, and the addendum is confined to latest-observed upcoming references; it cannot enter one-hour/two-hour historical comparisons or alter original forecasts.

For San Francisco at home, the displayed **home margin > 10** condition corresponds to the **SF −10 sportsbook handicap**, not SF +10. A final margin of exactly 10 may push under the sportsbook's integer-line rules. The **52.5 total** is a quoted threshold, not a provider mean-score forecast. Neither threshold is a model cover probability or a guaranteed fill.

The original source overlay remains unchanged. [The public contract](reschedule_reference.py) validates the exact event, separate clocks, immutable prior payload and resulting 15/15 DraftKings display coverage. It rejects invented quote times, other-event substitutions and historical-metric reentry. Source replay is a separate private custody audit; these presentation tests do not establish completed owner research acceptance.

## Source replay and public validation

The N036 source-only return is bound by physical SHA-256 `8c95d4eefa2563165add5c318a7977f32b197126e7d1d9f62e7b40d665e3a537`. Its seven new normalized objects, 16 selected raw books and nine rule/metadata objects passed independent full-body SHA/size verification. Selected references were replayed against their event, team/token, quote clock, rule predicate and source prices; no raw feed or order book is redistributed here. The [public validator](source_recovery.py) separately checks the sanitized display, exact coverage, immutable earlier data and non-promotion into historical metrics. These are distinct verification scopes.

This update added zero model fits and zero new forecast issues. The acquisition run made no paid Odds API calls. It does not establish all-provider freshness, an injury-aware trained model or a betting edge.
