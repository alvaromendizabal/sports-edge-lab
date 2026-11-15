# N121 NFL model and market evaluation

[Download the interactive dashboard](https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/main/tracks/nfl/circa_million_2026/n121_current/index.html) and open the saved HTML in a browser. It contains all 842 fixtures and works offline. The [published N120 archive](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/circa/n120/) records the earlier fixed-subset study.

- [Seven-page champion and market debrief](N121_NFL_Champion_and_Market_Debrief.pdf) with the model features, annual results, validation decision, market controls, current venue gaps, contest review and execution limits.
- [All 994 final score and coverage rows](N121_Full_Season_Leaderboard.csv) for 48 registered recipes, including 18 with a complete 2026 test objective.
- [All 411 commercial venue panels](N121_Market_Panels.json) and [unsettled fixture comparisons](N121_Forward_Venue_Comparisons.json).
- [Season scores and available-case study diagnostics](N121_Season_Scores.csv) for all registered recipes.
- [Additional complete seasonal results](N121_Additional_Complete_Scores.csv) for seven further 145-game test models and 11 full-season incumbent metrics. The freeze on model choice predates these results.
- [Full historical study summaries for 21 recipes](N121_Original_Study_Season_Scores.csv). This later archival recovery contains all 63 native seasonal rows. For the N025 paper models, the full 2024 and 2025 totals and margins have 285 games per year. Winner scoring has 285 and 284 decisive fixtures. Earlier 2026 archive rows have 120 finals and 119 decisive games. Historical source-clock and study-population labels remain attached.

N121 uses 285 validation games in 2024, 285 in 2025 and 145 completed games in the 2026 test. The 2026 season also has three games in progress, 100 scheduled future kickoffs and 24 games awaiting a kickoff assignment at the recorded cutoff. The dashboard uses 411 matched venue panels, including 210 panels comparing all three N121 families in the 2026 test. N121 forecasts for future fixtures were computed on the tool host and remained unissued at this freeze.

## Post-freeze N025 paper champion

[Read the N025 original paper-champion reconciliation](N121_N025_Original_Champion.md) for all 145 completed 2026 games, with decisive-winner metrics on 144. The outcome ledger already had these 145 finals at 21:29:38 UTC on November 15. The N121 test froze the identical 145 game IDs at 22:06:43 UTC. The one tie is excluded from both decisive-winner scores. The forecast source clocks include retrospective proxies. These figures are diagnostic and excluded from the frozen N121 rankings. [Season metrics CSV](N121_N025_Original_Champion.csv) · [Source reconciliation JSON](N121_N025_Original_Champion.json).

## Portable evidence recovery

[Download the verified release runner](https://raw.githubusercontent.com/alvaromendizabal/sports-edge-lab/685e55419d426e8c252cd6706916e3216b82ad21/tracks/nfl/circa_million_2026/n121_current/evidence-recovery.pyz) or build the same bytes from [the Python source](runner_source/). The release SHA-256 is `72d84f2a5c8579f402417c5f6bc9f6791719f72eade0c20b8db7a5f63923cf5f`. The release workflow rebuilds the archive, runs the offline self-test and publishes the verified runner as a downloadable Actions artifact.

```sh
python -I runner_source/build.py evidence-recovery.pyz
python -I -u evidence-recovery.pyz --self-test
```
