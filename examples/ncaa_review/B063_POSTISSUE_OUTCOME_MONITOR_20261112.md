# NCAA B063 — November 12 original-issue postgame monitoring

**Research only; eight selected games.** This report joins 46 already-issued B062 target/component rows to later official school finals. It preserves original prediction bytes and clocks. No model was fitted, blended, selected on these outcomes or promoted. The failed B063 startup and the prepared B063R1 repair are documented separately in [the recovery status](B063R1_DASHBOARD_STATUS.md).

## Source and calculation correction

[Draft PR #243](https://github.com/alvaromendizabal/sports-edge-lab/pull/243), reviewed at `94528c4d8e826e98718a1e1fb4e30f56148f2558`, first identified these eight official-source finals. Its rounded-public-prediction metric headlines are superseded here by a fresh local calculation from all 46 authenticated immutable records at original full precision. The final-source observations were independently reconfirmed on November 12. No exact earlier result-availability time or raw HTTP body hash is invented.

The public evidence is [B063R1_POSTISSUE_MONITORING.json](B063R1_POSTISSUE_MONITORING.json), SHA-256 `918e8951f0972429c6a226d8347d53f07c746fb7c3beae0b904a5fbdaa2ddd58`. Its aggregate metrics use full-precision originals; per-game probabilities are rounded to six decimals and point predictions to three for display. It preserves separate model aliases, exact cohort identities, original issue clocks, later outcome observation time and each result source. Complete underlying model/source closure is not newly certified by this bounded issue-record audit.

All original issue and server timestamps remain before the saved cutoff and scheduled tip. The original records retain `actual=null` and their candidate status. The final-score observations live in a separate layer observed at **2026-11-12 17:40:34.920809 UTC**. They are not backdated into training features or source availability.

## Official finals

| League | Home vs away | Final | Primary source |
|---|---|---|---|
| Men | Grand Canyon Lopes vs Cal Poly Mustangs | 99–71 | [Official final](https://gculopes.com/sports/mens-basketball/stats/2026-27/cal-poly/boxscore/21315) |
| Men | UC Santa Barbara Gauchos vs Nevada Wolf Pack | 76–63 | [Official final](https://ucsbgauchos.com/boxscore.aspx?id=12822&path=mbball) |
| Men | Colorado State Rams vs Portland State Vikings | 87–71 | [Official final](https://csurams.com/news/2026/11/11/mens-basketball-rams-depth-wins-over-portland-state) |
| Men | Nebraska Cornhuskers vs Lindenwood Lions | 94–60 | [Official final](https://huskers.com/news/2026/11/11/hot-shooting-huskers-roll-past-lindenwood) |
| Men | Boise State Broncos vs Oakland Golden Grizzlies | 111–79 | [Official final](https://broncosports.com/sports/mens-basketball/stats/2026-27/oakland/boxscore/23269) |
| Men | UCLA Bruins vs Arkansas-Pine Bluff Golden Lions | 106–37 | [Official final](https://uclabruins.com/news/2026/11/11/ucla-mens-basketball-cruises-past-arkansas-pine-bluff) |
| Women | Cal Poly Mustangs vs Seattle U Redhawks | 57–55 | [Official final](https://gopoly.com/news/2026/11/11/womens-basketball-mustangs-hold-off-redhawks-57-55-remain-unbeaten-at-home) |
| Women | Fresno State Bulldogs vs New Mexico Lobos | 74–56 | [Official final](https://gobulldogs.com/news/2026/11/11/womens-basketball-four-bulldogs-reach-double-figures-in-home-win-against-lobos) |

## Separate model and target scorecards

| League | Family / role | Target | Games | Accuracy | Log loss | Brier | MAE | RMSE |
|---|---|---|---:|---:|---:|---:|---:|---:|
| Men | histogram gradient boosting (component) | margin | 6 | — | — | — | 14.918040 | 17.558847 |
| Men | ridge regression (component) | margin | 6 | — | — | — | 14.686754 | 16.198923 |
| Men | histogram gradient boosting (component) | total | 6 | — | — | — | 11.571614 | 13.912049 |
| Men | ridge regression (component) | total | 6 | — | — | — | 10.990082 | 13.747747 |
| Men | histogram gradient boosting (component) | win | 6 | 0.833333 | 0.196472 | 0.053781 | — | — |
| Men | logistic regression (component) | win | 6 | 0.833333 | 0.215949 | 0.059738 | — | — |
| Women | ridge regression (frozen role) | margin | 2 | — | — | — | 10.003060 | 10.848679 |
| Women | PyTorch (frozen role) | margin | 2 | — | — | — | 11.459265 | 11.895966 |
| Women | PyTorch (frozen role) | total | 2 | — | — | — | 8.075096 | 8.853158 |
| Women | TensorFlow (frozen role) | win | 2 | 1.000000 | 0.338844 | 0.085660 | — | — |
| Women | PyTorch (frozen role) | win | 2 | 1.000000 | 0.391444 | 0.106596 | — | — |

Each row is a distinct original model/target group. Components do not become a retrospectively blended champion. The six men's games and two women's games all ended in home wins; the small one-week cohort does not support current-season model selection, provider outperformance or independent prospective confirmation.

The full-precision correction is material to the evidence contract even where rounding changes a number only slightly. Men's ridge and histogram-gradient margin MAEs are **14.686754** and **14.918040**, replacing the earlier rounded-input values 14.686833 and 14.917833. Women's margin MAEs are **10.003060** and **11.459265**, replacing 10.003000 and 11.459500. New metrics must never be calculated from the display projection when the original records are available.

## Preserved scope and remaining evidence

The existing 96 earlier original rows, 46 later selected candidate/component rows, two unresolved tipoff conflicts, historical B003 scores, frozen historical-role tables, prior negative results and provider coverage states remain unchanged. A separate recovery adds 90 selected preserved-role originals from the same B062 source, bringing the public selected archive to 232 rows; it does not turn private candidate grids into public outputs.

No new timestamp-matched DraftKings, Kalshi or Polymarket observations were acquired for this eight-game monitor. No complete current-season denominator, selection-adjusted uncertainty interval, model promotion, new owner fit or new original issue follows from it. The next owner must still establish genuine parallel execution, memory-safe research, exact checkpoint reuse and qualified current-season forecasting.
