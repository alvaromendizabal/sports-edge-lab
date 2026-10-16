# Start NFL/NCAAF modeling — October 16, 2026

We can start building the core football models now. The finite selected historical odds acquisition queue is finished, and current completed-game data is present. Continued collection is for newly published games and revisions; a sports season never becomes a permanently finished dataset.

## What is actually available

| Data | Verified state | Remaining limitation |
| --- | --- | --- |
| NFL 2026 play-by-play | 14,031 rows, 80 games; all completed schedule games represented through October 15 | Schema/sequence and feature construction checks remain; current files are revised archives |
| NCAAF recent FBS core | 22,151 plays, 2,888 drives; 124 completed games in Weeks 5–7 represented in plays, drives, team/player boxes and advanced rows | Representation does not prove every nested statistic or play is complete |
| Public NFL NGS | 27,613 player-week/season summary rows, 2016–2026; all 692 current rows have exact week/team/GSIS joins | Summaries, not trajectories or video; original publication time is unverified |
| NFL snaps and rosters | 7,445 of 7,463 current snap rows have verified GSIS identity and same-week/team membership | 18 unresolved/conflicting rows stay unjoined; they need not block a team-level baseline |
| College availability | 2,402 structurally valid archive rows, 2,306 exact player joins; 96 unmatched | Late archive observations cannot establish historical pregame knowledge; the Friday subset is an additional observation, not 19 new unique players |
| NFL availability | 374 rows captured at 23:23:06 UTC October 16, including 14 changes from the previous capture | Injury player IDs and original publication times still need verification |
| Historical game prices | V039: 4,696/4,696 selected missing NCAAF checkpoints acquired; selected NFL missing queue was already zero | V046 audited the newly acquired NCAAF block, not every older NFL/NCAAF cache |

Eight unchanged public assets were skipped after their release hashes matched the existing cache. V046 fetched two NFL public URLs (robots and injuries), with zero odds credits, CFBD calls or CBBD calls. ACB remains excluded and its canonical raw prefix is empty.

## The three gates before trusting a model

1. **Create consistent game tables.** Resolve provider event IDs to canonical NFL/CFBD games; verify teams, season type, actual kickoff, score/settlement and cancellations. V046's 3,885-event registry identifies 1,674 IDs with kickoff revisions and 20 with team-name/pair revisions. Those are review queues, not automatically different games. Exclude unresolved identities instead of guessing. Validate completed-game play order, duplicates and score/drive consistency.
2. **Construct features at a declared prediction time.** Use prior games only. Keep event time, source publication, retrieval, quote update and prediction time in separate fields. Join roster/availability versions valid for the target game and known at the chosen cutoff. Keep unverified publication times null. Do not backdate today's injury report to an earlier game. Do not use a game's final snaps, final box score or actual weather as its pregame features. Audit older cached NFL/NCAAF price blocks with the same checks before including them.
3. **Run chronological evaluations.** Freeze a dated dataset, train on earlier periods, tune on a later validation period and evaluate once on a still-later holdout. Compare simple team-strength/prior-game baselines with market baselines at the same time. Report log loss/Brier score and calibration for win probability, MAE for margin/total, and uncertainty by season/league. Record missing features and test richer features by ablation. There is no verified predictive edge yet.

Historical revised-source baselines can begin as explicitly retrospective research. They must not be described as strict point-in-time trading/betting backtests until information availability is established. In parallel, the current immutable vintages support a prospective evaluation beginning now. Full tracking access is not a prerequisite for these core models.

For the initial fresh-price benchmark, use a declared maximum snapshot lag of ten minutes and report excluded coverage. V046 identifies 17 responses outside that threshold. This is an experiment policy, not a claim about the provider's guaranteed interval. Passing the V046 timestamp/shape checks alone does not apply that freshness filter or settle kickoff revisions.

## Concrete first projects

| Project | First model and data | Advancement after baseline |
| --- | --- | --- |
| NFL availability-adjusted game forecasts | Team strength, opponent-adjusted prior-game play efficiency, rest, venue and quarterback/availability signals that pass identity/time gates; predict win probability, margin and total | Add lagged NGS, participation and FTN charting, then play-sequence representations; require improvement on untouched later games |
| NCAAF opponent-adjusted game forecasts | Team/opponent strength, prior-game play/drive efficiency, pace, roster continuity and verified quarterback availability; preserve FBS/FCS/season-type scope | Add player usage, transfers/recruiting, interaction and sequence features only after effective-date and completeness checks |

The next engineering deliverable is one canonical game table and one prediction-time feature table per football track, with a reproducible baseline experiment. The remaining 18 NFL and 96 college player joins can be addressed alongside this work. Do not spend more subscription credits to compensate for a join or timestamp problem.

## Downloads that continue

- Capture final pregame availability and roster/depth revisions when published. At 23:16 UTC, the Friday Washington–Purdue subset still had no final game-day status; 19 rows were valid and uniquely joined, while one missing-jersey row was quarantined.
- Capture the three Friday games after they finish and their play/box data is published. The last CFBD schedule observation was 22:46:51 UTC; it found no additional completed games. V046 reused that schedule and made no CFBD call.
- Recheck 2026 NFL PBP/NGS/snaps/rosters/depth/player release metadata and fetch only changed hashes. Existing current odds collection retains its bounds.
- Obtain a verified 2026 American Conference football availability source. The available 2025 football page must not be relabeled as current. The existing v022 one-off is an American basketball availability collector, not a promise of current football coverage.

The finite weekend follow-up continues at 17:15 Pacific October 16 through 06:15 Pacific October 19; this manual pass covered the original 16:15 observation. There are 41 remaining scheduled observation opportunities. No historical job was restarted.

## Tracking and aligned video

No new entitlement was found in the existing provider email threads during this pass. SkillCorner's automated reply says no B2C sales; an eligible organizational license is not established. Genius has no confirmed access grant. This remains a separate data-access workstream. Obtain a written offer specifying leagues/seasons, actual player/ball fields, delivery, aligned-video rights and permitted ML use before accepting a license or downloading restricted data. No new outreach, paid trial or subscription was started.

[Latest validation evidence](FOOTBALL_VALIDATION_V046.md) · [Weekend capture workflow](FOOTBALL_WEEKEND_REFRESH_20261016.md) · [Tracking access](TRACKING_AND_VIDEO_ACCESS_20261016.md)
