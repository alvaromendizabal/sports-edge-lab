# Sports Edge Lab · NFL

**Pregame forecasting, honest market comparisons, and recoverable ML systems.** Built by [Alvaro Mendizabal](https://github.com/alvaromendizabal) as one track in the existing [Sports Edge Lab](../../README.md) portfolio.

**Owner evidence dated October 29, 2026:** N006 completed all-game accounting and checkpoint verification. N007 subsequently stopped at coordinator admission before its worker. MARKET remains the accepted reference; no new predictive advantage or promotion is established. The separate N008 continuation is pending owner execution.

## Start here

| Inspect | What it demonstrates |
|---|---|
| [Interactive NFL evidence review](review.html) | All 28 source seasons; exact smaller model cohorts; target/protocol/family/stable-ID controls; explicit monitoring limits |
| [Model card and evaluation boundary](#model-card) | Conditional win vs point targets, matched MARKET references, historical exposure and unavailable uncertainty |
| [Coordinator incident and reconciliation method](#a-real-integration-failure) | A proved pre-worker failure, unknown existing state and a safe semantic admission gate |
| [Public source and negative tests](contracts.py) / [tests](test_contracts.py) | Outer-universe accounting, ties, postseason season labels, exact cohort identity and immutable reentry |
| [Executed public methods notebook](../../notebooks/engineering_review.ipynb) | Existing synthetic methods and separately labeled owner aggregates; no private NFL retraining claim |
| [System architecture](../../docs/SYSTEM_DESIGN.md) | Source, model and decision contracts across the existing project |

The interactive review is a self-contained offline HTML file. Download/open it locally; GitHub's file viewer shows source. No server, credentials, provider calls or external assets are required. Its [aggregate export](evidence.json) has no per-game forecasts, paid raw odds, private paths, weights or active tuning.

## What the owner evidence establishes

| Evidence | Verified state |
|---|---|
| Full game universe | **7,549 identities**, 28 source seasons from 1999 through the October 29, 2026 snapshot; no pre-1999 coverage claim |
| 2024 season | **285 accounted / 280 retained**; five regular-season games outside saved inputs |
| 2025 season | **285 accounted / 277 retained**; six regular and two Wild Card games outside saved inputs |
| 2023 original training | **285 accounted / 276 retained**; four regular and five postseason omissions |
| 2026 exposed monitoring | **107 scored / 77 retained**, plus 165 unplayed regular-season matchups; no invented future postseason IDs |
| Saved prediction audit | **316 tables / 948 recomputed metric scalars**, using authenticated saved files |
| N006 preservation | **237 parent checkpoints**, 1,948 scientific files preserved; 450 owner checks passed; no new scientific fits |
| N003 qualification | **0 of 522** recorded corrected comparisons pass; MARKET retained; zero actual orders |
| N007 outcome | Executable admitted, coordinator filename rejected before parsing; worker/tests/science/migration not reached |

Both 2024 and 2025 contain 272 regular-season games and 13 playoff games. All 22 omitted 2023–2025 training/evaluation games are absent from both saved MARKET/design input tables. This proves the saved-table gap; it does not establish that original provider quotes never existed. A complete accounting ledger can preserve those gaps without manufacturing predictions.

The 2025 tie is also absent from both input tables. The 2026 tie is present in both, including point targets, but excluded by the legacy non-tie cohort. Future margin/total eligibility must be qualified separately. Future games, canceled games, missing inputs and unsupported target semantics are distinct states.

## Run the public checks

From the repository root, using Python 3.11 or 3.12; no third-party Python packages:

```bash
python -m unittest discover -s tracks/nfl -p 'test_*.py' -v
python tracks/nfl/contracts.py --check-review
python tracks/nfl/contracts.py --demo --output /tmp/nfl-review-demo.json
python tracks/nfl/contracts.py --demo --output /tmp/nfl-review-demo.json
```

The first demo invocation writes one verified **invented** reconciliation artifact. Reentry checks its identity and modification time remains unchanged; the receipt reports zero new work. Corrupt prior evidence is rejected and preserved. This example performs no model fits or network calls. The existing [public fitting example](../../examples/review_lab/README.md) remains the broader credential-free ML entry point.

To regenerate the page from its committed data/template, run `python tracks/nfl/contracts.py --build-review`. `--check-review` validates the aggregate contract and exact deterministic page, without modifying files. Optional Chromium checks use the existing Playwright installation convention: `node tracks/nfl/browser_test.cjs`; `NFL_SCREENSHOTS` selects an output directory. Unit/visual preparation, hosted CI and live deployment are separate receipts.

## Model card

| Topic | Contract and limitation |
|---|---|
| Intended use | Retrospective NFL research review and engineering demonstration; no wagering recommendation |
| Win target | Home win conditional on a non-tied result; no tie encoded as a loss or fabricated half-win |
| Point targets | Home margin and game total; displayed saved files retain their original cohort, including its exclusions |
| Comparators | Raw archived sportsbook MARKET, retained original models (N002 IDs), registered N003 ensembles |
| Cohorts | Exact game-ID digests, season, target and annual/fixed/monitoring protocol must match; equal row counts alone are insufficient |
| Metrics | Log loss/Brier for win; MAE/RMSE for points. Negative differences mean smaller loss on that panel only |
| Exposure | 2024/2025 repeatedly inspected development; 2026 exposed monitoring with stable IDs, no outcome ranking or promotion |
| Uncertainty | Paired intervals, ECE and complete correction-family details are not in this compact export; unavailable values remain explicit |
| Qualification | Preserved 522-comparison N003 corrected family has zero passing entries; lower displayed loss alone does not qualify a model |
| Reproducibility | Public contracts and invented fixture fully runnable; owner aggregates inspectable; full private training requires authorized data and implementations |

Model IDs are opaque stable references across panels. Coarse family labels communicate model breadth without exposing active feature recipes. The view does not invent ablation results, fresh forecasts, calibration evidence or prospective performance. The registered N004 feature-family study is a separate pending owner stage and is not included in these N006 aggregates.

## A real integration failure

N007 passed executable integrity admission, then observed `workspace_layout_manifest.json`. Its organization code expected `workspace_layout.json` and rejected the name before parsing the contents. The resulting diagnostic ZIP proves that boundary; it does **not** prove an invalid schema, stale lock or incompatible project layout. No new scientific fits, source recovery, canonical migration or S3 publication followed. N006 remains the latest successful owner execution in this snapshot.

The public coordinator example tests semantic layout identity independent of filename/list order, preserves unknown fields and defers unknown schemas or unsafe lock declarations. A recognized parse still grants **no mutation**: the actual advertised lock must be acquired and the document identity rechecked. This educational example neither operates a real coordinator nor substitutes for the private runtime's process/filesystem protections.

This case illustrates a practical distinction: a portable artifact can pass its own integrity tests while failing an integration assumption at the owner boundary. Preserve the failure, capture the actual external contract, and repair that boundary without retraining accepted models.

## Provenance and public boundary

The [export](evidence.json) records SHA-256 identities for the independently audited N006 return, N007 failure return, recomputed metric aggregate and audit summary. The audit verified each actual saved prediction file and hashed its sorted string game IDs as compact UTF-8 JSON. It asserted complete cohort-hash and MARKET-metric equality across every table in a season/target/protocol panel. The export copies these observed hashes by the original panel key; no hash is inferred from a row count or label. The original 2026 protocol spelling remains in `source_policy` when the UI groups it as monitoring. The export exposes counts, coarse families and aggregate scores only. It cannot independently reproduce private model training or recover per-game outputs. See the existing [publication boundary](../../docs/PUBLICATION_BOUNDARY.md).

The source snapshot is dated. The dashboard does not assert current AWS storage, current live workloads, completed N008 work, a newly executed notebook or a live website deployment. The [change manifest](change_manifest.json) identifies this NFL-owned publication scope; actual PR/commit/check receipts determine its publication state.

## Review by role

- **ML Engineer:** inspect exact-cohort comparisons, target contracts, retained model identities and zero-work reentry.
- **AI Engineer:** inspect semantic admission, immutable artifacts, failure isolation and observable boundaries. This contribution makes no LLM/agent capability claim.
- **Data Scientist:** inspect the complete denominator, missingness distinctions, chronological exposure, unavailable uncertainty and negative qualification result.

<details>
<summary>Dated V061/V062 track history — preserved without relabeling</summary>

# Historical NFL entry — preserved October 17, 2026

**Historical verified state — V061, October 17, 2026:** NFL V047 remains accepted. All 24 situation-feature linear/XGBoost fits completed on 52 fields; none of six candidate/task combinations qualified. The [public feature method](../../modeling/football_v061/README.md) remains a no-fit construction demo, separate from actual performance. V062 is prepared, not executed: a fixed L1 margin/total comparison on the original 16 fields, with cached references and no win-model refit.

The current refresh downloaded six assets and verified four semantic changes. Revised PBP remains 14,031 rows / 80 games with no added game IDs. Audited history remains 498,285 rows across 2016–2026; the broader archive spans 1999–2026.

[Current model card](../../docs/MODEL_CARD.md) · [Data readiness](../../docs/DATA_READINESS.md) · [Feature strategy](../../docs/FEATURE_STRATEGY.md) · [V061 actual evidence](../../docs/status/football_v061/README.md) · [Prepared V062](../../docs/status/football_v062/README.md)

<details>
<summary>Original acquisition-stage research plan — retained as history</summary>

The original plan below records intended feature families and model directions. It does not describe the complete accepted implementation; current cards above supersede its phase and coverage statements.

Quarterback-adjusted team strength, EPA-based matchups, calibrated win probabilities, point margins and game totals.

This track lives in the shared [Sports Edge Lab](../../README.md) repository and `sports-edge-lab-dev` workspace. Its private archive prefix is `tracks/nfl/` in the central data lake.

## Model sequence

1. Regularized win-probability classifier.
2. Opponent-adjusted team and QB ratings.
3. Joint score and margin distributions.
4. Usage-conditioned player props after the game-level audit.

## Feature families

- Rolling EPA and success rates.
- Quarterback availability and prior performance.
- Opponent-adjusted offense and defense.
- Rest, travel and forecast weather.

## Source scope

- nflverse schedules, play-by-play, rosters and statistics.
- official injury reports and archived weather forecasts.
- The Odds API historical moneylines, spreads and totals.

These are acquisition and research targets, not assertions of complete coverage. The source/season audit determines which observations may enter each experiment.

## Temporal boundary

Realized starters, observed game weather and final statistics are labels or postgame records unless a separate pre-decision source establishes availability.

## Acceptance criteria

Apply the [shared research protocol](../../docs/RESEARCH_PROTOCOL.md). Establish sport-specific identity mappings and source coverage before feature development. A market backtest requires an actual bookmaker quote and a recorded availability time. Track quality with log loss, Brier score, calibration and distribution coverage, then separately assess simulated market returns, closing-line value and uncertainty.

**Current phase:** source acquisition and audit. No trained-model performance claim.

</details>

</details>
