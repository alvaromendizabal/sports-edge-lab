# NFL model selection and the full-season test

November 15, 2026 at 4:51 PM Pacific. Validation uses every final from the 2024 and 2025 NFL seasons. The test covers every 2026 final through this cutoff.

| Season | Role | Games in the evaluation | Winner scoring |
| --- | --- | --- | --- |
| 2024 | Validation | 285 · 272 regular-season and 13 postseason | 285 decisive, 0 ties |
| 2025 | Validation | 285 · 272 regular-season and 13 postseason | 284 decisive, 1 tie |
| 2026 | Test | 148 completed NFL games | 147 decisive, 1 tie |

## The decision I would make

Keep MARKET as the operational incumbent. For a model chosen on validation with no in-season updates, use the pooled opponent-adjusted ridge for winner probability and expected margin, and the recent ridge for total points. For a model that updates weekly as teams play, use the recent ridge for all three objectives. These are research nominations for owner review. The available full-season evidence leaves the fixed-line ATS and Circa champion open.

For winner probability the pooled fixed model led on both validation log loss and Brier. For margin its average validation lead over the recent fixed model was just 0.0023 points. The recent model led on fixed-model total MAE by 0.0045 points over the team-score baseline. All eight first-versus-second paired weekly 95% intervals include zero. The pooled-versus-recent margin MAE difference has a 95% interval from −0.092 to +0.085 points.

## Why the answer changed from N120

N120 required complete observations for four objectives and the same market on the same games. The common set fell to 34 games in 2024, 217 in 2025 and 53 in 2026. Those results describe the overlap of those sources. N121 starts with the season schedule. Missing forecasts keep a model out of that full-season ranking, and missing prices stay visible in the market panels.

The two validation seasons receive 30% and 70%, preserving the relative 15-to-35 weights. The 2026 test contributes zero to model selection. The 15%/35%/50% results are a labeled performance summary. Prior releases had already looked at 2026 outcomes, which limits independence even for a reconstruction with fully time-valid inputs.

## What the afternoon changed

Official final scores admitted in this update: LA 34–6 ARI, SEA 21–13 LV, SF 46–40 DAL. Each score was applied to the same registered game IDs throughout. The 145-game predecessor and all existing weights and issues remain separately verifiable.

# Frozen at Week 1 in each season

All three policies use their own Week 1 team weights and probability calibration for the entire season, including the postseason. The eventual matchup is given. These forecasts are historical reconstructions. Each row includes every final in its season.

| Model | Year | Correct | Log loss | Brier | Margin MAE / RMSE | Total MAE / RMSE |
| --- | --- | --- | --- | --- | --- | --- |
| Team scoring | 2024 | 165/285 | 0.7079 | 0.4833 | 10.91 / 14.16 | 10.05 / 13.18 |
| Team scoring | 2025 | 155/285 | 0.7232 | 0.4919 | 10.80 / 13.83 | 10.82 / 13.58 |
| Team scoring | 2026 | 88/148 | 0.7227 | 0.4863 | 10.38 / 13.13 | 11.10 / 13.90 |
| Recent ridge | 2024 | 171/285 | 0.7076 | 0.4820 | 10.89 / 14.12 | 10.10 / 13.21 |
| Recent ridge | 2025 | 165/285 | 0.7254 | 0.4931 | 10.79 / 13.81 | 10.79 / 13.53 |
| Recent ridge | 2026 | 89/148 | 0.7105 | 0.4757 | 10.15 / 12.90 | 11.00 / 13.78 |
| Pooled ridge | 2024 | 173/285 | 0.6985 | 0.4747 | 10.81 / 14.06 | 10.08 / 13.15 |
| Pooled ridge | 2025 | 170/285 | 0.7247 | 0.4931 | 10.82 / 13.80 | 10.84 / 13.54 |
| Pooled ridge | 2026 | 88/148 | 0.7127 | 0.4772 | 10.25 / 12.99 | 11.01 / 13.76 |

Winner is a three-outcome prediction: away, tie or home. The table counts a tie as a real outcome. Multiclass Brier is the sum across those three outcomes. Margin means away score minus home score. MAE gives the typical absolute miss in points; RMSE gives more weight to large misses. Lower is better for every loss and error column.

## What each model knows

Team scoring uses exponentially weighted points scored and allowed, a 220-day half-life, home-field adjustment and six prior games of shrinkage. The recent ridge models each team’s attack against its opponent’s defense, plus league scoring and home field, using a 140-day half-life and penalty 6. The pooled model uses the same design, a 330-day half-life and penalty 12. None of the three requires a betting price.

Each model builds separate integer-margin and total distributions from earlier forecast errors. The distributions account for ties and pushes; total points uses its own forecast and residuals. The signed margin grid supports exact winning margins, at-least thresholds and buckets. These marginal models do not supply joint-score probabilities.

Across nine verified fit/calibration objects, both historical validation seasons have an independently reconstructed fixed-policy score. The September 2026 fit reproduces all the archived 145-game fixed-test metrics within 0.0000000001. Every family sees the same game IDs. The downloadable season-lock CSV also includes CRPS for margin and total.

# Weekly models and the historical champion

The weekly policy can learn from earlier completed weeks. The original N025 winner predicts the away team conditional on a decisive outcome, so all three forecasts below use the same binary winner settlement.

| Year | Model | Correct | Log loss | Brier | Margin MAE | Total MAE |
| --- | --- | --- | --- | --- | --- | --- |
| 2024 | N025 retained | 193/285 | 0.6159 | 0.2129 | 10.06 | 9.83 |
| 2024 | N121 recent | 191/285 | 0.6236 | 0.2168 | 10.21 | 10.04 |
| 2024 | Opening market | 205/285 | 0.5986 | 0.2049 | 9.75 | 9.77 |
| 2025 | N025 retained | 187/284 | 0.6259 | 0.2187 | 10.00 | 10.65 |
| 2025 | N121 recent | 180/284 | 0.6360 | 0.2231 | 10.17 | 10.61 |
| 2025 | Opening market | 188/284 | 0.6114 | 0.2122 | 9.72 | 10.45 |
| 2026 | N025 retained | 95/147 | 0.6286 | 0.2197 | 9.83 | 11.04 |
| 2026 | N121 recent | 92/147 | 0.6310 | 0.2207 | 9.81 | 11.18 |
| 2026 | Opening market | 99/147 | 0.6184 | 0.2137 | 9.57 | 10.57 |

The opening market is a dated sportsbook-unassigned reference. Its game-level baseline is qualified across all three seasons. In N110, the market/team-shrink and opening-reference forecast families have strong complete 2026 results but cover only 193 of 285 validation games in 2024. The missing 92 keep those fitted families out of selection.

## How much weight to put on N025

The protected N025 winner and margin recipes blend seven forecasts from recent scoring, team-strength, count models and prior out-of-fold error. The totals model uses six count/context predictions, including ridge and boosted-tree corrections. Historical designs include 35 scoring, 129 strength, 72 and 201 count-related inputs; totals add error, rest, opponent, pace and passing context.

N025 has a reconstructed score on every game. Of the 148 test games, 27 have pregame family evidence and 121 use archival replays with publication-time proxies. Original N025 issues, protected N024-equivalent parent issues and N108 strict total-refit issues retain their version identities. Both historical validation seasons use proxy-clock replays. The archived 0.45684 NFL winner log loss came from 15 issues; the archive supplies no full-season 0.40 result.

Paired 2024/25 validation differences for N025 versus recent ridge are −0.0094 winner log loss (weekly 95% interval −0.0202 to +0.0018) and −0.1643 margin MAE (−0.3123 to −0.0216). The second comparison favors N025, subject to those source-clock limits.

# DraftKings, Kalshi and Polymarket

Coverage is incomplete. A published price, an exact game/side/contract match, a quote eligible at one cutoff and a settled model comparison are four separate facts. The dashboard lets you inspect them per game.

| Population | Games | DraftKings | Kalshi | Polymarket intl. |
| --- | --- | --- | --- | --- |
| 2024 finals | 285 | 272 | 0 | 211 |
| 2025 finals | 285 | 283 | 0 | 107 |
| 2026 finals | 148 | 148 | 140 | 148 |
| Upcoming with kickoff | 100 | 94 | 2 | 29 |
| Upcoming time TBD | 24 | 0 | 0 | 0 |

Counts require at least one exact product in the archived inventory. They do not promise all markets at every checkpoint. The eight 2026 Kalshi history gaps are Chargers games. For the 100 timed future fixtures, 96/15/31 listings were observed, 94/2/29 qualified, and only Pittsburgh at Cincinnati and Indianapolis at Houston had a product at all three. Only the Pittsburgh–Cincinnati spread had the same verified payout on closely timed quotes at all three. The international and US Polymarket archives are distinct. No US matches were established here.

## How many season-wide prices are really comparable?

At the two-hour checkpoint, requiring the same NFL game, same integer payout, comparable native quote time within five minutes across all three venues and genuine source clocks leaves one matched spread (Kansas City at Las Vegas, Week 4) and zero totals. Even allowing six-hour-old quotes while keeping five-minute cross-venue alignment did not expand that set. It was a historical observation. A season-wide three-venue trading advantage cannot be established on this evidence.

## Same two-hour decision time, different quote ages

| Settled contract | Games | N121 recent | DraftKings | Kalshi | Polymarket |
| --- | --- | --- | --- | --- | --- |
| Spread | 50 | 0.26099 | 0.25345 | 0.25332 | 0.25274 |
| Total | 57 | 0.27043 | 0.24981 | 0.24866 | 0.24906 |

Each row compares Brier on the same payout contracts and games for all four forecasts. There were 107 game-contract observations on 88 distinct games. Quotes could be up to six hours old at the two-hour cutoff. Median native quote ages were 53.4 minutes for DraftKings, 4.6 for Kalshi and 0.7 for Polymarket. All three markets beat the recent ridge on both panels.

# Afternoon results and upcoming forecasts

Future forecasts have no final score. Every model projection carries its model version and as-of time. Quotes, matchups and team availability can change before kickoff.

## The separately captured afternoon contracts

The two graded afternoon games with identical spread and total thresholds across all three venues supplied 4 game-contract observations. Model and venue average Brier on those same observations: DraftKings 0.24742, Kalshi 0.25265, N116 0.24788, Polymarket 0.24773. This narrow contract-specific comparison does not supply a season-wide edge.

The season-wide provider-specific panels compare one model with one venue on the same game, contract and allowed clock. At the held T−120 checkpoints, the recent model had higher Brier than DraftKings on winners, Kalshi on named spreads and international Polymarket on winners. A favorable exception was the Polymarket away-by-7-to-12 bucket. This is a distinct outcome with its own event rate and denominator.

## Week 10 Circa worksheet

The Week 10 replay picked Carolina, Minnesota, Arizona, New England and Buffalo. Carolina, Minnesota and Buffalo covered; Arizona and New England lost. Result: 3.0/5.0 against 2.927 expected points. The worksheet was retrieved after the contest deadline. It is a retrospective card with zero entries. All alternatives remain in the return.

Upcoming pages mark unconfirmed kickoffs and unresolved earlier team games.

## How the next forecasts were obtained

New forward weights incorporate the afternoon finals. The earlier weights and calibration remain available for grading. Each new projection has its own signed-margin and total distribution.

| Upcoming game | Away win | Tie | Home win | Away margin | Total points |
| --- | --- | --- | --- | --- | --- |
| PIT at CIN | 43.2% | 3.6% | 53.2% | -1.84 | 48.01 |
| LAC at BAL | 40.2% | 3.5% | 56.3% | -2.71 | 43.36 |

Shown here are the recent rolling model’s new projections on the two remaining Week 10 fixtures. The Sunday-night update was computed inside the two-hour betting benchmark. The earlier, time-qualified forecast remains available separately. Each of the 24 fixtures with an unconfirmed kickoff also has a conditional matchup projection.

## What can be called a champion

Five families qualify across both validation years: the three N121 scoring models, N113 team-strength margin (scoring, defense, opponent strength and rest), and N114 opponent-adjusted total. Eighteen families have full 2026 results on at least one objective: 15 winner, 14 margin and 11 total.

# What ran and what remains

Run history uses Pacific dates. Runs that began before midnight are identified separately from work done on Sunday, November 15.

| When and release | Verified work |
| --- | --- |
| Nov 14 · N110–N115 | N110 matched exact Kalshi spreads and totals on 129/137 early finals. N111–N115 tested winner blends, key margins, red-zone/drive and team-strength features, plus separate market-independent score and total distributions. A drive-feature test raised margin MAE from 9.24 to 9.86 on 73 games. |
| Nov 15 · N116 | 138 fits, 26 distribution issues and one personnel revision. Opening-line margin mixtures and total dispersion were separate registered studies. |
| N117 | 260 historical fits completed in replay. The native attempt later stopped at freeze117.py line 275 when the live injury asset failed the combined SHA and asset-ID check, before native training. |
| N118 and N119 | N118 graded two pregame Munich issues, added margin shrinkage and rest-based totals, and refit two strict scoring recipes on 7,155 outcomes. N119 tested recent forecast errors and practice effects, recorded 162 new fits and three first-issued margin forecasts. |
| N120 and N121 | N120 recovered comparable market-matched subsets. N121 rebuilt full-season eligibility, preserved 48 candidates, produced 174 prior fit units and recovered N025. The current update settles the afternoon and adds paired uncertainty and fixed-season scores. |

## Execution, handoff and open work

This update fitted 3 forward models on 3,176 settled games. Three local workers produced 372 projections for 124 remaining matchups. There were 0 failed fits and zero paid provider calls. The new fit outputs are prospective; they cannot enter or improve the validation or test records. Public forecasts include their as-of time and cutoff eligibility.

The scientific results were verified in the recovery workspace. Direct native execution of this N121 update on the SageMaker Space remains unverified. Private delivery receipts identify the verified files, execution scope and owner command.

The new runner reproduced the old B082 failure and then scored the NFL models with the same 383,217,225-byte support fixture. It also passed actual 512 MiB boundary, multi-GiB reassembly and missing/corrupt part tests. N119 measured a 5.24× speedup with 12 native workers. Native 12-core timing and incremental cloud cost for this N121 update remain unmeasured. No model was promoted, no contest entry was submitted and no market order was placed.

Primary scoring reference: Gneiting and Raftery, Strictly Proper Scoring Rules, Prediction, and Estimation (2007). Schedule and historical score source: nflverse/nfldata. Final scores are confirmed using the team and league results named in the settlement receipts.

