# NBA Spread & Totals — B120 R2 prepared and verified, saved B119 outlooks

[Open the published board](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site) · [Versioned source](../../../docs/nba/spread-totals/index.html) · [Public data](board.json) · [iPhone graphics](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site/graphics/index.html)

The latest observed **B120 R1 owner run ended in a resumable partial report on November 26, 2026 at 21:42:11 UTC** after 53 minutes 21 seconds. It **recovered all 2,140 saved publication tasks**: 1,200 frontier, 240 box, 160 original-model, and 540 stack tasks. This recovery reused saved outputs with **zero inference calls and zero new prediction ledgers**. The run then stopped during continuation because an authenticated saved frontier-input reference was missing. It reported **zero new estimator, residual-distribution, calibration, or meta-model fits and zero provider requests**. The terminal exit code remains unverified. Checkpoints were preserved. **B120 R2 preparation is now verified; the main replacement owner run has not been observed.**

The 2,140 publication failures originally recorded by B119 remain dated history, not a new R1 failure count. Their successful recovery does not establish completed current-season research. This board keeps the same selected-role projection, game identities and tip times, research metrics, missingness, and forecast source/issue clocks from the verified B119 partial evidence. It includes the new operational status, **no new R1 forecast values**, and no production model deployment. Publishing these files does not refresh sources or qualify market contracts.


## B120 R2 preparation — November 26, 5:27 PM Pacific

All six final preparation scopes passed, along with the final 1,264-test engineering check. The exact launch preparation rehearsal completed at **2026-11-27 01:27:42 UTC**, exited 0 after **80.61 seconds**, made **zero new fits**, and left control pointers unchanged. This is **PREPARED_VERIFIED**; the main owner research run has not been observed.

Across preparation attempts, **23 estimators, 23 calibrators, and 23 residual distributions** were newly committed with diagnostic origins, using **101.45 component CPU seconds**. These are separately counted diagnostics, with zero test-game predictions and no champion selection; sustained scientific owner occupancy remains unqualified. The canonical owner-entry qualification reused all 2,140 saved publication tasks with zero new fits. No new game forecast values, annual metrics, source clocks, or model promotion are published by this preparation update.

## Latest weekly calendar — November 26, 3:43 PM Pacific

A separate bounded official NBA check covered every date from November 23 through November 29: **48 games, now 22 final and 26 scheduled**. Daily counts are **10, 3, 9, 0, 11, 5, 10**. All 48 game IDs, teams, and tip times match the saved board. Nine November 25 games gained final status and scores. Per-game calendar observations retain their actual retrieval clocks and links to the official NBA date schedules.

This update made seven official requests and **no model fits or inference calls**. It did not advance the saved forecast issue times, update market quotes, regenerate predictions, or recalculate model metrics. The original season census remains **261 completed / 1,200 declared at November 25, 11:34 AM Pacific**. Calendar observations are a separate weekly layer; they do not claim a fresh full-season census. The missing Miami at Cleveland total remains unavailable.

## Population and issue clocks

The official NBA census was observed on November 25, 2026 at **19:34:47 UTC**. The public board retains all **1,200 observed 2026–27 games**, including **261 completed** games. Future calendar completeness remains unproved where tournament/postseason scheduling has not been released. The board neither invents those games nor treats bookmaker overlap as the game manifest.

The November 23–29 Pacific week contains **48 games**: 10 Monday, 3 Tuesday, 9 Wednesday, none Thursday, 11 Friday, 5 Saturday, and 10 Sunday. At the saved census cutoff, 13 were completed and 35 were upcoming. The separate November 26 calendar check now has 22 final and 26 scheduled; the default board opens those 26 scheduled week games. Full-week and full-season filters retain every observed game, and status labels show the applicable observation clock.

At nominal T120, **47 of 48 week games** have all three selected point-role issues with saved pregame clocks. Miami at Cleveland on November 29 retains its winner and margin issues, but its total stays unavailable because the saved forecast's fixture time differs from the current observed schedule. This is explicit in the game details.

For November 25 onward week games, the displayed winner and margin issues were saved at **2026-11-25 19:40:27 UTC**. The total role retains its older **2026-11-19 22:10:55 UTC** issue. Nominal T60/T120 identifiers never replace these issue clocks. Historical reconstructions without a saved pregame issue are left unavailable in the public per-game display. The private owner return retains their separate scientific reporting.

## Selected roles and qualifications

Winner probabilities use the validation-selected **log-loss role**; point margins and totals use their respective **RMSE roles**, independently for each horizon. Those are declared display roles, not a new selection. The signed margin is away score minus home score. Winner and margin roles can disagree.

Primary selection is the equal average of the 2024–25 and 2025–26 annual validation metrics. The saved validation manifests contain 1,321 and 1,322 games, including postseason and Cup finals. The board provides all 26 saved objective/horizon selections and the original annual metric denominators. Current winner/margin reports score 261 games; retained total and other reports may score 210 games. Comparable population membership is unproven: the 210-game cohort is not established as a subset of the 261-game census. These counts do not establish a coverage fraction or a missing-game count, and metrics from the two populations are not directly comparable.

Historical point-in-time and full-season champion qualification remain incomplete. Calibration qualification is incomplete. Previously inspected 2026–27 results remain exposed report-only evidence and do not select these roles. No production champion promotion is claimed.

## Market evidence

DraftKings, Kalshi, Polymarket International, and Polymarket US are separate products. The current-season public coverage receipt has 4,383 source × market × horizon/status rows per product, with 102, 98, 102, and 34 qualified comparison rows respectively. These qualified rows are archive-replay observations. They are not distinct-game counts or executable orders.

The B119 return has **zero verified exact-contract rows** and **2,400 remaining contract rows**. Accordingly, the board does not manufacture Kalshi YES/NO sides, strikes, prices, fee-adjusted returns, or a ranking. A later bounded source diagnostic does not change these B119 qualification counts. Normal binary Kalshi settlement uses exact wording and the YES/NO complement; void/pending/canceled cases remain separate. Sportsbook rules stay separate.

## Public boundary and validation

The public projection contains selected rounded role outputs, public schedule/results, real issue/source clocks, coarse model-family labels, metric-role aliases, aggregate metrics, and explicit missingness. It contains no private recipe identifiers, feature transforms, model state, raw licensed feeds, cloud paths, credentials, or owner execution packages.

Rebuild and check from the repository root:

```sh
python -m examples.nba_branch.build_spread_totals
python -m examples.nba_branch.build_spread_totals --check
python -m unittest examples.nba_branch.test_spread_totals_public -v
python -m examples.nba_branch.build_review --check
```

The graphics generator requires Pillow and DejaVu fonts. It produces 12 PNGs at 1080 × 1920: one overview plus 11 date pages covering all 48 week games exactly once. Its manifest records each image's hash and game membership.

Earlier board rendering was inspected on desktop and a 375-pixel content-width mobile viewport. The current preparation status update has separate validation from the earlier owner result; local generation and boundary checks are recorded with its pull request. Search, horizon switching, full-season coverage, missing-role details, and card overflow were checked. Automated regression probes reject private recipe fields, post-tip issues, missing manifest games, and test metrics substituted for validation selection. Local checks and hosted CI are separate evidence.

**Publication state:** public snapshot published at [https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site), with the [twelve phone graphics](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site/graphics/index.html). Initial hosting verification is **2026-11-27 01:38:44.742760 UTC** (November 26, 5:38 PM Pacific), site version 1. Later publication metadata updates do not change that first verification time. Deployment did not refresh providers, issue forecasts, select or promote models, or launch the owner campaign. Historical NBA pages remain dated archives; no other owner's files are changed.


### Descriptive saved-week check

The saved winner picks were correct in 9 of the 22 completed games (40.9%). This is a descriptive check of the rounded T−120 view against the latest final scores, separate from the saved annual research metrics. It does not establish an original issued record or qualified calibration. Actual issue clocks remain unchanged on each game card; this check did not choose or update a model.

The observation covers the 22 finals in the November 23–29 week, checked November 26 at 3:43 PM Pacific. It does not grade the 26 scheduled games, change any of the 48 saved game forecasts, or establish market prices or prospective returns. Nominal T60/T120 views retain their distinct actual issue clocks.
