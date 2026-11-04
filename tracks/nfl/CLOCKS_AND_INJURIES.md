# Prediction time, market time and injury inputs

[NFL overview](README.md) · [Open the dashboard](review.html#latest-coverage) · [Forecast readiness](CURRENT_FORECAST_STATUS.md)

**T2 means two hours before kickoff. It is an evaluation cutoff, not a collection deadline.** Continue collecting newer odds and injury reports. Preserve the information used by each earlier forecast, and show later references with their actual clocks.

| View | What it means | What it does not mean |
|---|---|---|
| T1 | Latest genuine information available at or before one hour before kickoff | An observation must occur at that exact minute |
| T2 | Latest genuine information available at or before two hours before kickoff | Stop collecting or displaying information after that time |
| T24 | A 24-hour boundary used by some original forecast records | A new T24 market series is supplied by this guide |
| Latest before kickoff | Last authenticated historical quote strictly before kickoff | A later market price was known to an earlier model |
| Latest observed upcoming | Most recent supported captured reference for an unstarted game in this dated snapshot | A continuously live executable offer or the eventual closing quote |

For example, a model issued at 11 a.m. can be compared with a market observed at 12:55 p.m. before a 1 p.m. kickoff. That is a **later-information benchmark**, not a same-cutoff comparison. Both clocks stay visible. The original 11 a.m. forecast does not change.

Downloading history after a game is not itself leakage. A genuine historical quote with verified pregame timing can support a retrospective benchmark. A current postgame order book cannot replace missing pregame history, and a reconstructed forecast cannot be relabeled as an originally issued pick.

## Injury information must reach the model

Displaying an injury report beside a projection does not prove the model consumed it. A feature boundary timestamp also does not prove that every report available before that boundary was included.

The injury extension must retain report availability, actual acquisition and forecast issue times; identify missing coverage; and distinguish historical reconstruction from information actually consumed before a live issue. Missing reports are unknown, not healthy. Expected starters and injured-reserve context matter because a weekly practice report may not list every unavailable player.

The existing projection remains the original record. Any successor forecast needs a new model/input version and actual issue time. Its improvement must be measured against a matched baseline, including models that combine injury and market information where appropriately registered. More features or more training does not guarantee improvement.

**Current status:** this public snapshot has no authenticated trained injury-augmentation result or demonstrated injury-driven gain. Existing frozen monitoring, rolling reconstructions and genuine issues retain their separate roles. News context and local engineering tests do not count as new model performance.

## Reading incomplete coverage

Every scheduled game remains visible. Missing provider entries describe the authenticated capture available here, not proof that no market exists. Newer source recovery can add a dated reference without changing historical metrics or inventing prices. The active comparison providers are DraftKings, Kalshi and Polymarket.
