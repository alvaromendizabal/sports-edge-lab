# Which models would I use?

All 285 finals in 2024 and all 285 in 2025 are validation. Every one of the 148 completed 2026 games at the November 15 evening cutoff is test. One game was live and 123 had yet to start.

Keep MARKET as the operational incumbent. For a market-independent model fixed at the start of the season, use the league/home correction for winner probabilities, N113 team strength for expected margin, and the recent opponent ridge for total points. These are recommendations for owner review. Each objective has its own loss.

| Objective | Validation nominee | 2024 | 2025 | 2026 test |
| --- | --- | --- | --- | --- |
| Winner accuracy | League/home correction | 59.3% | 60.4% | 59.5% |
| Winner log loss | League/home correction | 0.6981 | 0.7236 | 0.7091 |
| Winner Brier | League/home correction | 0.4755 | 0.4926 | 0.4741 |
| Margin MAE | N113 team strength | 10.861 | 10.789 | 10.269 |
| Margin RMSE | Pooled opponent ridge | 14.061 | 13.796 | 12.986 |
| Margin CRPS | League/home correction | 7.850 | 7.771 | 7.333 |
| Total MAE | Recent opponent ridge | 10.100 | 10.789 | 10.998 |
| Total RMSE | Pooled opponent ridge | 13.155 | 13.541 | 13.761 |
| Total CRPS | League/home correction | 7.537 | 7.661 | 7.724 |

## How close are these decisions?

All ten validation comparisons between first and second place include zero in their paired 95% intervals. The N113 margin-MAE lead is 0.009 points, with a 95% interval for N113 minus the pooled ridge from -0.176 to +0.156. Historical evidence supports keeping several models active.

The 30% / 70% validation weights preserve the 15-to-35 ratio of the standing policy. 2026 has zero selection weight. The downloads also report an equal-year validation analysis and a descriptive 15% / 35% / 50% retrospective score. Equal weighting changes the margin-MAE nominee to the pooled ridge. The 2026 outcomes were already visible in earlier releases.

The seven principal fixed policies and five controls or ablations have 36 annual rows. One combined download holds 2,247 model, target, season and evidence records, including all 48 inherited registry recipes. Every target a model produces uses the full, same-ID schedule. Conditional postseason matchups are supplied to the fixed policies. The original and weekly-updating models have their separate, like-for-like evidence below.

# What each model knows

Exact ordered inputs, fitted weights, calibration banks and code are retained in the private return. These are the features that distinguish the models selected for owner review.

## League/home correction

Pooled opponent ridge predicts each team’s points. A two-coefficient correction adjusts league-wide scoring error and the signed home-field difference. The point model uses older data; the immediately preceding season supplies its residual distribution.

## N113 team strength

Five away-minus-home feature differences: recent scoring, recent points allowed, last-eight opponents’ mean net score, last-16 team net score, and capped rest. Native Week 1 coefficients and integer residual counts are used throughout each season.

## Recent opponent ridge

Fits team offense, opposing defense, league scoring level and home advantage. Prior scores have a 140-day half-life and ridge penalty 6. Its separately learned total distribution gives over, exact total and under probabilities.

## Pooled opponent ridge

Same design as the recent ridge, with a 330-day half-life and ridge penalty 12. Its full-season validation RMSE led for both margin and total points.

## N114 opponent total

Nine team/opponent and venue inputs cover last-eight scoring and allowance, elapsed rest, opponent-adjusted effects, and last-three versus previous-five form. Predicts team scores with a paired residual bank for totals.

## Team error correction

Adds team-specific offense and opposing defense error terms to the league correction. It got 94/148 test winners right. Its validation log loss of 0.7039 and 0.7451 kept it behind the league correction. Randomized team assignments provided a negative control.

The selected league model averaged 3.05% tie probability on 2026 games. There was one tie in 148 (0.68%). This calibration issue matters particularly for exact margins and integer pushes. The separate postseason sensitivity sets tie probability to zero for every policy in postseason games, then rescales home/away probabilities.

# The historical champion and the market

N025 predicts the away winner conditional on a decisive game. All three policies below use the same binary outcome and the same decisive games. Margin and total errors still include each tied game.

| Season | Policy | Winners | Log loss | Brier | Margin MAE | Total MAE |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | N025 retained | 193/285 | .6159 | .2129 | 10.06 | 9.83 |
|  | Weekly recent | 191/285 | .6236 | .2168 | 10.21 | 10.04 |
|  | Opening market | 205/285 | .5986 | .2049 | 9.75 | 9.77 |
| 2025 | N025 retained | 187/284 | .6259 | .2187 | 10.00 | 10.65 |
|  | Weekly recent | 180/284 | .6360 | .2231 | 10.17 | 10.61 |
|  | Opening market | 188/284 | .6114 | .2122 | 9.72 | 10.45 |
| 2026 | N025 retained | 95/147 | .6286 | .2197 | 9.83 | 11.04 |
|  | Weekly recent | 92/147 | .6310 | .2207 | 9.81 | 11.18 |
|  | Opening market | 99/147 | .6184 | .2137 | 9.57 | 10.57 |

The protected N025 winner and margin each combine seven component predictions. Its total combines six. Features include team scoring and allowance, strength, count models, opponent context and prior out-of-fold errors. Totals also include rest, pace and passing context. Of the 148 test games, 27 have pregame family evidence. For 121, the reconstruction uses a proxy for when an input became available. Both validation seasons also use proxy-clock replays.

The opening market is a dated reference with no sportsbook attribution. It has lower winner log loss, margin MAE and total MAE than N025 across these three years. The archived 0.45684 NFL log loss covers 15 issued cases. It cannot establish a season-wide winner.

A second protected model, N022, reproduced all nine original first-week fitted objects and 144 original Week 1 outputs. On the same decisive games, it got 166/285, 160/284 and 90/147 correct (log loss 0.6837, 0.7148, 0.6579). Only 633 of its 7,017 historical 2026 training rows have every input independently dated before that historical game. These scores have their own evidence label.

## Why the old answers disagreed

N120 intersected games with the required provider and multiple model targets. That left 34 games in 2024, 217 in 2025 and 53 in 2026. Such an intersection answers a particular market question. The N122 headline starts with the complete schedule, retains missing rows, and withholds a full-season rank from any incomplete model or target. N110, for example, covers the 2026 test, but only 193 of 285 games in its 2024 validation.

Every model’s original operating policy matters: a weekly model can learn from last week, a frozen model only from pre-season material. A price observed during the week often has information unavailable in September.

# How much market coverage do we have?

A row with an observed price has additional requirements before it can enter a model comparison: exact contract, orientation, time, settlement, and a model forecast available by the same decision point.

| Population | Games | DraftKings | Kalshi | Polymarket intl. |
| --- | --- | --- | --- | --- |
| 2024 finals | 285 | 285 | 0 | 211 |
| 2025 finals | 285 | 285 | 0 | 107 |
| 2026 finals | 148 | 148 | 140 | 148 |
| Pittsburgh at Cincinnati, live | 1 | 1 | 1 | 1 |
| Future, kickoff set | 99 | 93 | 1 | 28 |
| Future, kickoff TBD | 24 | 0 | 0 | 0 |

DraftKings feed coverage includes 13 recovered 2024 events and 2 recovered 2025 events. They match the actual provider event, teams, settlement and source clock after reconciling recorded kickoff times. The inherited lookup returned 272 and 283. Both Super Bowl source events are now authenticated, including original Seattle versus New England snapshots showing the scheduled kickoff exactly. These are games with at least one supported product. Indianapolis at Houston was the only unstarted game with any exact product at all three. No unstarted game had a verified identical spread or total across all three at the audited checkpoint. Future games remain visible pending a price, contract or kickoff.

## Source-clock matched comparisons

At two hours before kickoff with five-minute native quote freshness and cross-venue time tolerance, one spread and zero totals qualified across all three. Allowing asynchronous quotes up to six hours old produced 50 spreads and 57 totals across 88 games. All four participants in each comparison faced the identical event and payout.

| 2026 secondary Brier | League/home model | DraftKings | Kalshi | Polymarket |
| --- | --- | --- | --- | --- |
| 50 spreads | .2456 | .2535 | .2533 | .2527 |
| 57 totals | .2655 | .2498 | .2487 | .2491 |

All six paired model-minus-market intervals include zero. Transaction fee, executable depth and pregame archive custody remain separate from these probability scores. No profitability estimate follows from these rows.

## A full-season benchmark exists

Ten dated 2026 nflverse revisions, plus the preserved validation archives, give a two-sided weekly moneyline, spread and total for every one of the 718 completed games. The source names no sportsbook. In 2026 the no-vig market Briers were 0.21541 for winners (147 decisions, one tie returned), 0.25137 on spreads (145 decisions, three pushes), and 0.24922 on totals (148 decisions). The weekly market beat all nine applicable frozen policies on Brier in all nine year-by-target comparisons. All pushes remain in the ledger.

Paid provider calls for this run: zero. All-venue public coverage is distinct from the private tape and from the number of eligible matched contracts.

# Every official Circa week

Circa Million applies to the regular season. This objective has 18 eligible weeks in each validation season and 10 published weeks in the test, while the main NFL scoreboard also includes the playoffs.

All 46 sets of contest lines were recovered from official publications. Every side was checked against its opponent, opposite spread, contest number and schedule. Nine readable source worksheets also agree on all 276 independently checked sides. Each historic card ranks P(cover) + 0.5 P(push) before grading its five distinct games.

| Model | 2024 points | 2025 points | 2026 settled | Open |
| --- | --- | --- | --- | --- |
| Pooled opponent ridge | 41/90 | 44.5/90 | 26.5/49 | 1 |
| League/home correction | 41/90 | 44.5/90 | 27.5/49 | 1 |
| N113 team strength | 42/90 | 42.5/90 | 29/49 | 1 |
| Recent opponent ridge | 43.5/90 | 40.5/90 | 28.5/49 | 1 |
| Team error correction | 40.5/90 | 41/90 | 22.5/50 | 0 |
| Team scoring | 41/90 | 40/90 | 25.5/50 | 0 |

Pooled opponent ridge and the league/home correction tied in both validation seasons. Neither reached 45 points in either validation season. Both reconstructed Week 10 cards selected Tennessee, Arizona, Dallas, Pittsburgh and Atlanta. Four had lost, Pittsburgh was live. The older weekly recent-ridge worksheet took different sides and finished at 3/5. Neither worksheet represents a submitted entry.

694 official matchups, 322 five-pick cards and 9,716 team-side alternatives were reconstructed across seven policies. The dashboard shows cover/push/loss probabilities, grading, prior team ATS, and each family’s prior chosen-side ATS for that team. The 2024 and 2025 regular seasons each have 272 official game lines. Week 1 through Week 10 in 2026 have 150, including the live game and Monday night.

The sign convention always starts with away points minus home points. To grade the away side, add the published away handicap to that margin. A zero pays half a contest point. Whole-point lines can push; half-point lines cannot. Totals use a separately estimated distribution. Exact margin and at-least margin are different sums of the integer law.

# What ran and what can be verified

Pacific dates put N110–N115 on Saturday night, November 14. The Sunday, November 15 work runs from N116 through N122. All times below refer to that day in Los Angeles.

## N110–N115 · Saturday context

Recovered bookmaker and exact exchange contracts, tested winner combinations, drive/red-zone effects, team strength and separate team-scoring laws. On 73 games a drive/red-zone test increased margin error from 9.24 to 9.86.

## N116 and N117

N116 recorded 138 fits, 26 distribution issues and one personnel revision. N117 preserved 260 historical fits. The native resume stopped at freeze117.py line 275 because a live injuries asset no longer matched its pinned ID and SHA. The historical return survived.

## N118 and N119

N118 recovered native execution, recorded 127 historical fits and two native fits, and retained four new issues. N119 recorded 162 fits and 15 original issues. Authenticated earlier issues for Pittsburgh–Cincinnati and Chargers–Baltimore predate T-120.

## N120 and N121

N120 recorded 125 fits and exposed the source-overlap limitation. N121 built the full-season schedule, verified old champion recipes, recorded 174 earlier fit units and three new forward fits, and graded three afternoon finals. The N121 projections were publicly readable 21 minutes before Pittsburgh kicked off.

## N122

Twelve genuinely new correction fits succeeded. Twelve were reused on a warm run. Eighteen authentic first-week historical states and banks were reused and checked against 288 original Week 1 outputs. Six historical arms added 4,308 fully graded cases and the new corrections added 2,154. The three new families produced 369 future distributions across 99 timed and 24 time-TBD games. No new projection for the live Pittsburgh game was admitted.

## Execution and status

Scientific execution and independent replay ran in the recovery environment. The existing SageMaker Space was running; native N122 execution and its incremental cloud bill require the Space execution receipt. The tested single runner and immutable return, including the earlier evidence, are supplied through the private handoff. Production remains at the authenticated incumbent. No promotions or contest submissions.

Methods and sources: Circa Sports Million VI–VIII official weekly publications; nflverse/nfldata (Lee Sharpe and contributors, CC BY 4.0); Gneiting and Raftery, Strictly Proper Scoring Rules, 2007, DOI 10.1198/016214506000001437; Glickman and Stern, A State-Space Model for National Football League Scores, 1998, DOI 10.1080/01621459.1998.10474084.

# Forecasts issued before kickoff

The dashboard keeps the original release and its issuance or publication time. These timestamps matter when comparing a live game to a forecast that already existed.

## Pittsburgh at Cincinnati

N119’s native issue had Cincinnati at 51.07% to win and favored it by 1.61 points. N118’s separate total was 46.30. The later N121 recent model gave Cincinnati 53.21% with a projected total of 48.01. Signed-out site readback recorded those bytes at 4:58:58 p.m. Pacific, 21 minutes before the 5:20 p.m. kickoff. N122 suppressed every new Pittsburgh pregame projection because generation began after kickoff.

## Chargers at Baltimore

The older native N119 issue had Baltimore at 62.33% and favored by 3.33, with the separate N118 total at 40.43. The Sunday N121 update gave Baltimore 56.33%. The N122 league/home model gave Baltimore 56.84%, Los Angeles 39.81%, and a tie 3.35%, with expected Baltimore margin 4.49 and total 43.55. The model-as-of and actual public release are distinct timestamps.

## What injuries added

The practice model uses three features: the difference in offensive did-not-practice or listed players, the difference on defense, and within-position simultaneous absences. Among 11 final games with authentic Week 10 pregame issues, the practice version lowered margin MAE from 12.195 to 11.592 but raised RMSE from 15.124 to 15.531. On the latest three finals, its MAE rose from 11.250 to 11.492. A separate 173-case historical attenuation study had no qualified 2025 games. These experiments do not qualify as full-season champions.

## How much probability error matters for Circa

The league correction predicted 3.08% pushes on this season’s 61 whole-point Circa spreads. Six pushed (9.84%). The week-resampled 95% interval for forecast minus observed is -11.86 to -1.66 percentage points. On the older official whole-number lines, 5/124 pushed in 2024 and 4/86 in 2025. The simple expected-points ranking is exact for the stated law, but a miscalibrated push probability affects weekly pick ordering.

Every upcoming fixture has a conditional matchup projection. Across the 123 still to start, 112 have an intervening unfinished game for at least one team, and 24 lack a fixed kickoff. Those projections can change after new outcomes or time-qualified injury reports.

