# NBA public evidence monitor

An offline review of dated aggregate diagnostics and a reproducible, invented failure case. Open the [evidence page](../../../docs/nba/monitor.html) locally after cloning; the HTML is generated from the reviewed [aggregate capsule](evidence.json). GitHub's source view is not a deployed application.

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

The latest historical branch completed 366 estimator fits, after a prior completed study of 654. The latest overall owner nevertheless **failed** when a fresh result response omitted a previously possessed final. That source frame is not admitted. Completed branch evidence is preserved without claiming overall success or repeating fits.

Qualified current provider common cohorts are absent in this snapshot. Therefore disagreement accuracy, market advantage and executable P&L are not estimable. Unknown profit is not zero profit. The prospective rolling protocol remains inactive; synthetic code is not authorization or evidence of live rolling execution.

## What the example reproduces

All [fixtures](fixtures.json) use invented events in 2035. They are separate from the aggregate capsule.

1. A forecast must be issued before its declared cutoff, using a source version published and actually possessed before issuance. An early issue keeps an early-outlook label.
2. Original issue versions are immutable. Exact repeats are reuse, not additional forecasts. Multiple versions for one model/event require an explicit policy rather than an after-results choice.
3. A new source response cannot delete an earlier qualified final. Conflicting corrections stop for review instead of silently changing a score.
4. A rolling update can only see finals possessed strictly before the update starts. The original control stays unchanged. The toy example contains no trained private model and does not compare unmatched track counts as if they were a common experiment.
5. Model and provider comparisons must ask the same event/side/target/line/horizon/product/settlement question with valid quote-possession clocks. These identity and clock checks alone do not establish executable prices or legal access.
6. Missing price, fees, depth or settlement evidence produces **NO BET**, unknown EV and unknown P&L. Optional one-unit arithmetic uses only invented numbers and always allocates zero.
7. Completed work and overall owner success are different states. A failed publication preserves completed fit evidence but cannot become successful merely because its research branch finished. Reuse earns zero new credit.

The interactive example shows why a refreshed response containing only a win would report 100% toy accuracy, while the admitted two-event union retains the loss and reports 50%. The rejected view is labeled explicitly; it is not a competing valid model result.

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
- This publication adds no real fits, new provider acquisitions, promotions, profits or deployment claims.

The dated [October 29 NBA review](../../../docs/nba/index.html), existing research history and negative findings remain intact.
