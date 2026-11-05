# November 5 injury-source refresh

[Open the dashboard](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/) · [Earlier issue](EXPERIMENTAL_INJURY_ISSUES.md) · [Derived cards](injury_refresh_n039.json)

Choose **Inspect the latest issued Week 9 cards** or **Latest injury refresh · Nov 5 UTC**. This separate series contains 29 actual early issues: 15 Week 9 games and 14 Week 10 games. Its 87 winner/margin/total rows are not 87 games or bets. The earlier issue, original forecast streams and historical scorecards remain unchanged.

## What changed

The continuation reused the same three fitted target heads and their frozen calibration. It performed zero new fits. New eligible injury observations now contribute to the point targets for 11 Week 9 games, compared with one in the earlier issue. The other four current-week games and all 14 Week 10 games still have no admitted current report rows.

| Jacksonville at Baltimore | Earlier November 4 issue | November 5 refresh |
|---|---:|---:|
| Jacksonville win probability | 64.2% | 64.2% |
| Projected Jacksonville margin | 4.5 points | 5.2 points |
| Projected combined points | 46.9 | 46.6 |
| Listed BAL / JAX feature-report rows | 9 / 5 | 18 / 10 |

All three selected target heads are ExtraTrees models. The winner target uses **249 base features without direct injury fields**; margin uses 324 features and total uses 417, including injury features and unknown-report flags. A changed point forecast does not prove an improvement until the games resolve and a valid evaluation is available. The displayed mean margin is not a cover probability at a market spread.

## What remains incomplete

Listed reports do not establish a complete roster-health census. Announced starters, quarterback depth and injured-reserve roles remain unverified model inputs. A separately linked official news report must not be mistaken for a feature incorporated by the model. Zero report rows mean missing information, not healthy players.

The base-feature snapshot remains November 4, 01:52 UTC, over 22 hours older than the new issue. Current injury observations update their own feature block; they do not refresh all other inputs. The reconstructed training cohort remains 120 current-season finals and lacks the feature-eligible Monday Chicago–Seattle row. The separate original Monday T1 forecast and its loss remain visible.

## Clocks and reuse

| Evidence | UTC timestamp |
|---|---|
| Base features | November 4, 01:52:35.279297 |
| Latest reused selected fit completed | November 4, 06:10:07.371551 |
| New admitted report observation | November 5, 00:07:24.723567 |
| Injury feature cutoff | November 5, 00:10:00.073931 |
| Actual new issue | November 5, 00:10:20.334054 |

All 29 games were unstarted and more than two hours from kickoff at issue. These are early research outputs, with zero final-hour-qualified cards and no qualified wagering recommendation. The overall owner research-acceptance flag remains false. Neither data collection nor website publication promotes that status.

The public validator checks event identities, reused-fit counts, unchanged winner outputs, separate clocks, target-specific feature roles, report gaps and rounding. Private model bodies, recipes, raw reports and complete candidate grids are not published. Public tests validate the reporting boundary; they do not replace the independent owner-return and selected-model verification.

## Current market observations

The separate source refresh provides November 5 Kalshi and Polymarket winner, margin and total references for all 15 Week 9 games. DraftKings has 14 fresh games and one retained November 4 LV–SF reference, visibly labelled with its original clocks. Another 13 of 14 Week 10 games have fresh DraftKings references. A retained observation is not relabelled fresh, and an absent newer reference does not erase an older usable one.

For captured point contracts, the outcome-independent display selects the latest complete two-sided book per contract and then the probability midpoint closest to 50%. This is not a claim of an official main line, expected score or guaranteed execution. Some provider observations follow the new model issue; they remain supplemental comparisons and are not presented as the information the model used.
