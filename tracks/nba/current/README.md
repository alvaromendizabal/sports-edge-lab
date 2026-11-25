# NBA Spread & Totals — saved B119 evidence, B120 preparation

[Open the board source](../../../docs/nba/spread-totals/index.html) · [Public data](board.json) · [iPhone graphics](graphics/)

This is the selected-role analytical projection of the verified B119 partial return. B119 reported **2,140 unique durable-publication task failures and zero new model fits** (1,200 frontier tasks plus 940 legacy application tasks: 240 box, 160 original-model and 540 stack tasks; the three-branch summary is not an additional task count). Its partial return still preserves authenticated saved research and some current-population applications. **B120 remains preparation only at this publication cutoff; the owner launches its research run.** Publishing these files is not a model fit, a source refresh, a qualified contract application, or a production model deployment.

## Population and issue clocks

The official NBA census was observed on November 25, 2026 at **19:34:47 UTC**. The public board retains all **1,200 observed 2026–27 games**, including **261 completed** games. Future calendar completeness remains unproved where tournament/postseason scheduling has not been released. The board neither invents those games nor treats bookmaker overlap as the game manifest.

The November 23–29 Pacific week contains **48 games**: 10 Monday, 3 Tuesday, 9 Wednesday, none Thursday, 11 Friday, 5 Saturday, and 10 Sunday. At the saved census cutoff, 13 were completed and 35 were upcoming. The default board opens the upcoming portion and provides full-week, completed, future, and full-season filters.

At nominal T120, **47 of 48 week games** have all three selected point-role issues with saved pregame clocks. Miami at Cleveland on November 29 retains its winner and margin issues, but its total stays unavailable because the saved forecast's fixture time differs from the current observed schedule. This is explicit in the game details.

For November 25 onward week games, the displayed winner and margin issues were saved at **2026-11-25 19:40:27 UTC**. The total role retains its older **2026-11-19 22:10:55 UTC** issue. Nominal T60/T120 identifiers never replace these issue clocks. Historical reconstructions without a saved pregame issue are left unavailable in the public per-game display. The private owner return retains their separate scientific reporting.

## Selected roles and qualifications

Winner probabilities use the validation-selected **log-loss role**; point margins and totals use their respective **RMSE roles**, independently for each horizon. Those are declared display roles, not a new selection. The signed margin is away score minus home score. Winner and margin roles can disagree.

Primary selection is the equal average of the 2024–25 and 2025–26 annual validation metrics. The saved validation manifests contain 1,321 and 1,322 games, including postseason and Cup finals. The board provides all 26 saved objective/horizon selections and the original annual metric denominators. Current winner/margin reports cover 261 games; retained total and other reports may cover 210 of 261. A 210-game score is never relabeled as full current-season coverage.

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

Desktop browser rendering and a 375-pixel content-width mobile viewport were inspected. Search, horizon switching, full-season coverage, missing-role details, and card overflow were checked. Automated regression probes reject private recipe fields, post-tip issues, missing manifest games, and test metrics substituted for validation selection. Local checks and hosted CI are separate evidence.

**Publication state:** static public source snapshot; production website deployment unverified. The optional hosting registration did not complete. Public source publication does not imply website deployment or a provider refresh. Historical NBA pages remain dated archives; no other owner's files are changed.
