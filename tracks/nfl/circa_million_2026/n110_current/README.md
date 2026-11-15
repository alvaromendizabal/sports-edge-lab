# N110 NFL model and market review

The 2026 regular-season snapshot contains 137 finals, 111 upcoming games with scheduled kickoffs, and 24 games awaiting a kickoff time. The dashboard’s **Games & venues** tab shows the forecast, quote timing, settlement terms, and coverage reason for each matchup. [Open the Circa Million Picks & Performance Dashboard](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n110/)

## Kalshi spread and total contracts

The N110 market-anchored model called the direction of 70 spread contracts correctly across 129 settled games. Kalshi called 59 correctly. In 2026 the fitted team adjustment to the margin was zero, so the model kept the opening spread as its margin forecast. The 70 correct calls reflect that market anchor and the model’s calibrated margin distribution. Kalshi had the lower Brier score and log loss on both spreads and totals. The paired directional tests are consistent with sampling variation.

| Exact settlement target | Directional games | Model correct | Kalshi correct | Paired p-value | Brier, model / Kalshi | Log loss, model / Kalshi |
|---|---:|---:|---:|---:|---:|---:|
| Named team wins by at least the quoted margin | 129 | 70 | 59 | 0.215 | 0.2523 / 0.2482 | 0.6980 / 0.6895 |
| Combined points reach the quoted total | 128 | 59 | 69 | 0.268 | 0.2570 / 0.2491 | 0.7073 / 0.6913 |

Brier score and log loss use all 129 settled contracts per target. One totals quote implied exactly 50% and supplied no directional pick. The two-sided exact McNemar tests use only games where one prediction was correct and the other was wrong. On spreads those counts were 38 for the model and 27 for Kalshi. On totals they were 28 and 38.

These are walk-forward historical reconstructions. The model’s reference time was two hours before kickoff. Ten games had a native price timestamp within five minutes of that reference. The other 119 used a later pregame price. The comparisons measure forecast performance. Executable depth and fees were unavailable.

## Provider coverage across the schedule

Each cell counts distinct games with at least one price or qualified comparison. A single price can establish game coverage while other products or times for that game are missing.

| Provider | Finals with a matched model comparison (137) | Timed upcoming with any price (111) | Timed upcoming with matched terms and model (111) | Kickoff TBD with price (24) |
|---|---:|---:|---:|---:|
| DraftKings | 137 | 107 | 107 | 0 |
| Kalshi | 129 | 26 | 13 | 0 |
| Polymarket international | 137 | 37 | 37 | 0 |

Across all 272 games, 155 had a price at all three venues and 142 had qualified terms at all three. The acquisition observed all three venues on 26 upcoming games. No fixture had evidence that all three quotes were in hand within the same five-minute window. Historical Kalshi quotes were missing for eight Chargers finals. Polymarket US had prices on 28 finals and zero qualified matches, so its figures are tracked separately.

## Drive features across 105 held-out games

At 7:25 p.m. Pacific on November 14, a walk-forward reconstruction extended the 2026 study from 73 to 105 held-out games across Weeks 3–10. The extension recovered 1,544 drive records from 74 games in 2025 that had been published before the 2026 season opener. All 137 completed 2026 games had eligible feature inputs. The 105-game score uses held-out forecasts only. The additional history changed 24 fitted fold weights.

| Margin forecast | Mean absolute error, points | Root mean squared error, points |
|---|---:|---:|
| Opening spread | 8.8571 | 11.5253 |
| Opening spread with a pooled defensive-stop adjustment | 8.9153 | 11.6606 |
| Opening spread with drive opportunity and red-zone finishing | 9.2812 | 11.9518 |

The drive opportunity and finishing model increased mean absolute error by 0.4241 points relative to the opening spread. Its paired gain was −0.4241 points, with a week-based 95% interval from −1.0290 to +0.1826. On the original 73 games, its MAE improved from 9.8608 to 9.6507 with the additional history. The opening spread scored 9.2397 on those same games.

The replay used records available before the relevant 2026 forecast origins. The earlier archive revisions arrived too late for the corresponding prior-season backtests. This study issued zero original forecasts and promoted zero models.

[Release scoreboards, model features, and fixture details](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n110/) · [Reviewed page source](./index.html.source)
