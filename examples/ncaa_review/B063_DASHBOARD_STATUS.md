# B063 NCAA dashboard recovery edition

The NCAA entry dashboard now exposes the newest preserved public B060/B061 science from the B062 reports, instead of opening only on the older B058 preparation view. The earlier dashboard remains intact in a clearly dated expandable archive.

## What this publication preserves

- All 3,457 saved source records, including unresolved and unmatched identities.
- All 814 completed-game frozen-model replay triplets.
- All 96 selected original target outputs for 32 game identities, retaining original predictions and source/training/issue clocks.
- Exactly 30 original game identities bound to later observed outcomes. The other two retain six unscored original outputs without borrowing changed tip times.
- Historical 2024–25/2025–26 metric leaders and the separate 2026–27 reconstructed and originally issued scorecards.
- Six preserved historical selection roles; missing additional metric roles and rolling-champion rows remain explicit.
- The earlier 265-game Polymarket International comparison and honest DraftKings/Kalshi missing-evidence states.

The game table provides league, season, population, evidence-mode and team/event filters, bounded pagination, record-level clock inspection and a filtered CSV. All 1,139 unissued future previews retain blank public values. Upcoming records are future relative to the saved source cutoff; this is not a live schedule.

## Evidence and execution status

Scientific evidence remains as of **2026-11-11T06:29:49.601626+00:00**. The census is as of **2026-11-11T06:02:54.852518+00:00**. This publication does not complete the live B062 audit, execute B063, fit a new model, issue a new forecast, promote a model or establish a measured twelve-worker speedup. B063 engineering recovery remains in progress, with owner-runtime evidence pending.

The .40 reference is preserved: men 0.394806627 log loss over 415 replay games and women 0.318015308 over 399. These exposed reconstructions cannot be pooled with originally issued predictions or compared to another model's unmatched complete-season sample as proof of improvement.

## Provenance and public scope

The four input files are pinned by Git blob identity at source commit 268d9db3752a93ed089821350c664ce3b9293653:

1. B062_STATUS.json
2. B062_REPORT_DATA.json
3. data/ncaa_observed_games_b060.json
4. data/ncaa_preserved_selected_issues_scored_b061.json

The b063_dashboard.py renderer verifies every original source byte identity and every exposed game/output/clock against those files before rendering. B063_PUBLIC_DATA.json is an explicitly selected public projection, not a replacement for complete private provenance or owner returns. It contains only the permitted selected outputs and previously public facts/aggregates. Complete candidate grids, model bodies, private active recipes, raw feeds, credentials and private storage locations are excluded.

## Validation and publication receipt

Data and JavaScript checks cover source-population closure, exact issue-time binding, missing future values, historical-filter behavior, CSV injection and HTML escaping. Python validation rejects changed forecasts, issue clocks or invented execution credit. The existing browser suite now exercises the B063 controls and retains the previous dashboard assertions.

Local and hosted test results are reported separately in the pull request. Source publication does not imply a website deployment or provider refresh. No deployment receipt is created by this document.
