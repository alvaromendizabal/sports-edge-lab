# NCAA B063 — November 12 original-candidate postgame monitoring addendum

**Research-only.** This document does not declare a new B063 owner execution, promotion, forecast issue, or complete current-season evaluation. It extends the already merged [terminal-evidence dashboard](B063_TERMINAL_DASHBOARD_STATUS.md), retaining all original forecasts and clocks.

## Newly matched games and source provenance

The B062 terminal return exposed **46 saved target/component prediction rows on eight games** (six men's and two women's); the public issue projection was later preserved in [PR #241](https://github.com/alvaromendizabal/sports-edge-lab/pull/241) and exact Git blob `34064825039486fc0786ddcf79ed1aef6139d3bd`. Its source cutoff is 2026-11-11 22:28:04 UTC. All 46 source-record issue and server timestamps are before their original 2026-11-12 02:00/02:30 UTC scheduled tips; all carry the retained `VERIFIED_ORIGINAL_CANDIDATE_ISSUE_BEFORE_CUTOFF` status. Their separate `original_issuance_status` is `CANDIDATE_PENDING_SERVER_COMMIT`; do not upgrade this to independently reauthenticated model/source closure.

After the original issue, official school final reports became available for eight games:

| League | Home vs away | Final | Source |
|---|---|---|---|
| Men | Grand Canyon vs Cal Poly | 99–71 | [GCU box score](https://gculopes.com/sports/mens-basketball/stats/2026-27/cal-poly/boxscore/21315) |
| Men | UC Santa Barbara vs Nevada | 76–63 | [UCSB box score](https://ucsbgauchos.com/boxscore.aspx?id=12822&path=mbball) |
| Men | Colorado State vs Portland State | 87–71 | [CSU recap](https://csurams.com/news/2026/11/11/mens-basketball-rams-depth-wins-over-portland-state) |
| Men | Nebraska vs Lindenwood | 94–60 | [Nebraska recap](https://huskers.com/news/2026/11/11/hot-shooting-huskers-roll-past-lindenwood) |
| Men | Boise State vs Oakland | 111–79 | [Boise box score](https://broncosports.com/sports/mens-basketball/stats/2026-27/oakland/boxscore/23269) |
| Men | UCLA vs Arkansas-Pine Bluff | 106–37 | [UCLA recap](https://uclabruins.com/news/2026/11/11/ucla-mens-basketball-cruises-past-arkansas-pine-bluff) |
| Women | Cal Poly vs Seattle U | 57–55 | [Cal Poly box score](https://gopoly.com/sports/womens-basketball/stats/2026-27/seattle/boxscore/9822) |
| Women | Fresno State vs New Mexico | 74–56 | [Fresno box score](https://gobulldogs.com/sports/womens-basketball/stats/2026-27/new-mexico/boxscore/19281) |

## Results and limitations

Two **distinct original components** per winner target scored five correct picks of six men's games each, with log losses **0.196472 and 0.215949** (Brier **0.053781 and 0.059738**). The two women's winner components scored two of two each, log losses **0.338844 and 0.391444**. The two men's margin components registered MAE **14.686833 and 14.917833**; in these six selected games every observed home margin exceeded both predictions. Women's margin MAEs were **10.003000 and 11.459500** on two games. These are **component-score results, not a combined champion**, and all eight games were home wins in one calendar week.

All new outcome-based comparisons are **post-issue, development-exposed monitoring**. No independent future confirmation, week-cluster uncertainty interval, model promotion, new owner training/fit, new official-results owner-ledger write, or market skill claim is established. This does not supersede the earlier 96 original target rows (32 games), two unresolved tipoff conflicts, 420 men's/403 women's retrospective B003 scores, historical champion research, or any prior unsuccessful trial.

The highest-value next work is exact private B063 owner-source/return recovery, B062 physical-fit accounting closure, then V5 champion-only current-origin refits and next-game issuance once host resources and immutable source clocks permit. No new canonical SageMaker executable is supplied by this report.
