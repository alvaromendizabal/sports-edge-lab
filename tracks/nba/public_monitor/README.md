# NBA public evidence monitor

**[Open the public NBA evidence dashboard](https://sports-edge-lab-nba.alv-mendizabal.chatgpt.site)** in your browser; no HTML download is required. The reviewed five-asset projection was deployed and public access verified November 3, 2026. It contains no live provider acquisition, inference or private forecast service.

An offline review of dated aggregate diagnostics and two reproducible, invented failure cases. The [evidence page source](../../../docs/nba/monitor.html) is generated from the reviewed [current publication capsule](evidence-v2.json). The [earlier capsule](evidence.json) remains unchanged. GitHub's source view is not a deployed application; a static-host export and its deployment receipt are separate from the source commit.

## Start in five minutes

From the repository root, using Python 3.11 or 3.12:

```bash
python -m tracks.nba.public_monitor
python -m unittest discover -s tracks/nba/public_monitor/tests -v
python -m tracks.nba.public_monitor.build --check
node --test docs/nba/monitor.test.cjs
```

Python uses only the standard library. Node.js is needed only for the optional interaction-logic tests. These four local commands need no model weights, external package installation, network requests, cloud credentials, licensed data, or real estimator fits.

The separate NBA hosted browser job follows the repository's established pinned Playwright setup. It renders desktop/mobile screenshots, exercises actual controls and keyboard navigation, checks no-JavaScript content and sampled text contrast, and blocks remote page requests. Browser/dependency installation is a CI setup operation, not a provider-data acquisition. Its artifact is a bounded review, not a complete external accessibility or cross-browser audit.

## What is measured

The dated public capsule retains the original B003 fixed-model diagnostic on three explicit cohorts: 1,164 games in each completed season and 94 current-season games. The current cohort is a **retrospective fixed causal reconstruction, not 94 genuinely issued forecasts**. Actual raw-source pre-tip possession closure is not established. Its log loss is 0.6472, not approximately 0.46. Historical seasons remain development-exposed.

Winner diagnostics use natural-log loss, binary Brier, accuracy at a home-probability threshold of 0.5, ROC AUC, and 10-bin ECE. Margin and total errors use points. Every row keeps its own exact denominator; a season filter does not change or refit a model. The public table is a representative control summary, not an all-model ranking. It does not assert that the control is the numerically best model on every objective.

The historical branch completed 366 estimator fits, after a prior completed study of 654. Its overall owner **failed** when a fresh result response omitted a previously possessed final. The next refresh reused all 366 fits, completed 758 software tests and performed **zero new estimator fits**, but also **failed**: a retained reconstruction differed after its source inputs refreshed. Neither overall owner is promoted to success. Original issued records and completed research remain preserved.

The active comparison policy is **DraftKings, Kalshi and Polymarket**. Polymarket US and international remain separate product scopes, not a pooled fourth provider. Historical evidence for older provider scopes is retained in the prior capsule. This public snapshot admits zero qualified current common-cohort comparisons; it does **not** establish zero raw provider coverage. Raw historical coverage is not evaluated in the public capsule. Both disagreement directions, market advantage and executable P&L remain unknown. The prospective rolling protocol remains inactive; synthetic code is not authorization or evidence of live rolling execution.

## What the example reproduces

All [fixtures](fixtures.json) use invented events in 2035. They are separate from the aggregate capsule.

1. A forecast must be issued before its declared cutoff, using a source version published and actually possessed before issuance. An early issue keeps an early-outlook label.
2. Original issue versions are immutable. Exact repeats are reuse, not additional forecasts. Multiple versions for one model/event require an explicit policy rather than an after-results choice.
3. A new source response cannot delete an earlier qualified final. Conflicting corrections stop for review instead of silently changing a score.
4. A rolling update can only see finals possessed strictly before the update starts. The original control stays unchanged. The toy example contains no trained private model and does not compare unmatched track counts as if they were a common experiment.
5. Model and provider comparisons must ask the same event/side/target/line/horizon/product/settlement question with valid quote-possession clocks. These identity and clock checks alone do not establish executable prices or legal access.
6. Missing price, fees, depth or settlement evidence produces **NO BET**, unknown EV and unknown P&L. Optional one-unit arithmetic uses only invented numbers and always allocates zero.
7. Completed work and overall owner success are different states. A failed publication preserves completed fit evidence but cannot become successful merely because its research branch finished. Reuse earns zero new credit.
8. A different input-source version may change a fixed model's reconstruction without changing its parameters. New snapshots append, while reusing an identity with changed values fails. Issued and reconstructed rows never acquire each other's evidence class. Same-input oracle checks retain their strict tolerance.

The interactive example shows why a refreshed response containing only a win would report 100% toy accuracy, while the admitted two-event union retains the loss and reports 50%. The rejected view is labeled explicitly; it is not a competing valid model result.

The source-version example shows an invented 70% original issue alongside a later 62% reconstruction. Switching views never changes the original. Time-only first/last issue policies cannot inspect outcomes; same-clock collisions require explicit resolution instead of a score-based tie-breaker.

## Static-host projection

### Historical recovery and local-view integrity

The [recovered-history contract](HISTORY_PANELS.md) adds a credential-free,
invented-only demonstration of latest-before-tip versus T60/T120 references,
historical versus prospective possession eligibility, full-inventory retention,
unknown settlement and exact-byte local-import checks. Its tests run under the
existing NBA CI matrix. Recovering a historical quote later is not a reason to
hide it; the source and acquisition clocks determine which claims it supports.
This addition does not change the dated public capsule or publish real prices.

The public exporter emits exactly five reviewed assets: the current dashboard, preserved October 29 page, local interaction script, sanitized capsule and hosting provenance. It rewrites repository navigation to an exact public commit. No private workspace, model or source response enters the bundle.

```bash
python -m tracks.nba.public_monitor.build_site --source-ref EXACT_PUBLIC_COMMIT_SHA --destination /tmp/new-empty-nba-static-export
```

The destination must be new or empty; no cleanup or overwrite is attempted. Export reports `EXPORTED_NOT_DEPLOYED`. Only a successful host deployment receipt establishes the live URL. The deployment has no live provider acquisition or inference service.

## Public/private boundary and ownership

This directory is NBA-owned. The patch does not change the NFL, FBS, NCAA, shared review architecture, root navigation, or shared protocols. The NBA-specific workflow runs the existing branch tests plus this module and its generated-page checks.

No raw source responses, individual actual forecasts, provider quotes, proprietary features, tuned model configuration, model weights, cloud object locations, private archive identities, execution handoffs, account information or credentials are included. The [publication boundary](../../../docs/PUBLICATION_BOUNDARY.md) continues to apply. Synthetic reproducibility is not full private-study reproduction.

## Limitations and next evidence

- The frozen diagnostic reconstruction is not a prospectively issued track record.
- Historical source possession and base out-of-fold provenance remain incomplete.
- A source refresh must be reconciled and admitted before publication of a newer snapshot.
- Current-season outcomes cannot choose new models or research directions.
- A rolling study needs a separately registered, approved, causally qualified policy and actual timestamped issues.
- Matched quotes, product rules, fees, liquidity and settlement are prerequisites for executable financial claims.
- UI tests cover interaction logic, HTML structure, labels and deterministic generation. The separate hosted browser job adds actual rendering and bounded accessibility checks; it is not a full external accessibility or cross-browser audit.
- This publication adds no real fits, new provider acquisitions, promotions or profits. A deployed static projection is a presentation deliverable, not a live model or acquisition service.

The dated [October 29 NBA review](../../../docs/nba/index.html), existing research history and negative findings remain intact.

## Calendar coverage and missing data

The [calendar inventory example](COVERAGE_INVENTORY.md) keeps every observed game while separately reporting requested-date completion, historical reference coverage and original possession. Its invented failure cases cover empty dates, source failures, reschedules, local-week boundaries and separate Polymarket products. Forecast availability never filters the acquisition inventory.

## Archive receipts and compatibility

The [offline receipt closure example](RECEIPT_CLOSURE.md) distinguishes logical
descriptor aliases from physical payload counts. Invented ZIP fixtures exercise
legacy reference normalization, exact manifest closure, content pins and explicit
regular-file types, including the manifest. A successful local byte check does
not establish a fresh provider read, completed computation or source-use grant.

## Bounded work and progress evidence

The [bounded acquisition and progress example](WORK_PROGRESS.md) separates verified
rows and covered games from attempts, empty responses and heartbeats. Its invented
fixtures demonstrate phase-local cooldowns, conditional ETA, finite priority
budgets and a preserved history backlog after model/report work.


## Stage completion and publication retries

The [checkpoint commit example](CHECKPOINT_COMMIT.md) keeps action success,
prepared output and committed completion separate. Invented failures show why a
retry must verify the retained result pin and full readback before publishing
COMPLETE, while an ambiguous action is never replayed automatically.

The [bounded checkpoint example](BOUNDED_CHECKPOINT.md) extends that distinction
to outputs that exceed a single envelope. Bounded content-addressed shards retain
the exact ordered record sequence, independently verified publication and strict
capacity limits. Partial uploads can reuse immutable returned output without
calling its producer; corrupt or incomplete closure never becomes completion.

