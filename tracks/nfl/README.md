# Sports Edge Lab · NFL

**Latest review: November 5, 2026 — expanded injury study completed.** All 1,152 historical cells and 462 rolling jobs finished; 1,038 new fitted identities and three separately timestamped early forecast lanes are documented. [Read the N045 update](N045_RESEARCH_UPDATE.md). These results are not automatic promotion or a qualified betting recommendation.

[**Open the live NFL dashboard →**](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/) · [Latest research update](N045_RESEARCH_UPDATE.md) · [Model card](CURRENT_MODEL_CARD.md)

**Pregame forecasting, matched market evaluation and recoverable ML systems.** Built by [Alvaro Mendizabal](https://github.com/alvaromendizabal). Review the evidence in your browser; no setup or private credentials required.

## Latest verified work · November 5, 2026

- **Expanded injury study completed:** all 1,152 historical cells and 462 rolling jobs; 1,029 new native fits and nine new stacks. All eight native families were evaluated. [Read the actual study](N045_RESEARCH_UPDATE.md).
- **Current forecasts refreshed:** three retained forecast lanes issued 261 early target rows for 29 games. The current rolling lane used a roughly 53-second-old base snapshot and a 121-game training view. It remains raw research, separate from the new designation study.
- **Three-provider coverage:** all 15 Week 9 games have observed winner, margin and total references from DraftKings, Kalshi and Polymarket. Historical comparisons preserve exact event sets, original clocks and winning **and** losing disagreements.
- **Injury data expanded:** all 72 discovered official archive articles normalized, with 3,671 T1-qualified rows. Current reports cover 28/30 Week 9 teams; Buffalo and Minnesota remain unknown. Announced starter, backup quality, depth and reserve roles are not verified inputs.
- **Performance governs promotion:** the new selected annual winner reconstruction has 385/569 correct and 0.6252 log loss on 2024/25; 78/119 and 0.6633 on current monitoring. Better accuracy did not mean better probability loss. Retained leaders and adverse paired results stay visible; no automatic promotion or durable betting edge is claimed.

T2 means two hours before kickoff; T1 means one hour. These are comparison cutoffs, not collection barriers. Later pregame observations remain visible with their actual timestamps. Threshold contracts are conditions with probabilities, not provider score forecasts.

**Recovered source correction:** Chicago–Seattle already had genuine T1 pregame vectors and a causal label append. The retained updating view had not inherited them; published scores and the original Seattle loss remain unchanged. [Inspect the correction](N041_RESEARCH_UPDATE.md).

### Five-minute review

| Question | Open | What is inspectable |
|---|---|---|
| What did the model say about every game? | [Game/week explorer](review.html#latest-coverage) | All 272 scheduled games, 121 finals, every Week 9 game, distinct forecast streams |
| Does it outperform markets? | [Matched performance and disagreements](review.html#coverage-performance) | Common-event metrics, winning and losing disagreements, coverage limits |
| What changed scientifically? | [Completed injury study](N045_RESEARCH_UPDATE.md#performance-and-promotion) | New derived experiments, target-specific scores, uncertainty and retained negative findings |
| What injury inputs are actually used? | [Current injury inputs](N045_RESEARCH_UPDATE.md#current-forecasts-and-injuries) | Acquired versus eligible data, current role gaps, historical publication limits |
| Can I reproduce the engineering? | [Promotion demonstration](injury_promotion.py) · [Tests](test_injury_promotion.py) | Credential-free invented examples of chronology, paired cohorts and admission failures |

```bash
python tracks/nfl/injury_promotion.py --demo
python -m unittest discover -s tracks/nfl -p 'test_*.py'
python tracks/nfl/contracts.py --check-review
```

The public repository contains generic engineering, sanitized evidence and selected rounded issued cards. Proprietary transforms, production weights and licensed raw feeds remain private. [Read the publication boundary](../../docs/PUBLICATION_BOUNDARY.md).

The dated scorecards and prior research history below remain preserved. They are not silently replaced by a newer source capture.

## Current NFL evidence · November 3, 2026

The project combines chronological modeling research with an engineering system that preserves exactly what ran, what could be known before kickoff, and what a comparison can support. The strongest current finding is a **small descriptive improvement over Kalshi on the same resolved games**. It is not yet evidence of a durable betting edge.

### The season, on identical games

**Audited Kalshi winner cohort: 120 finals, 119 non-ties, registered T−2h primary reconstruction.** Both team contracts and T−1h history are also audited. The explorer keeps the later T−1h quote sensitivity separate; it does not relabel the model as a T−1h issue. Verified T−2h lineage includes the late-appended resolved event; retrospective reconstruction does not establish original issuance.

| Model / reference | Correct winners | Accuracy | Log loss ↓ | Brier ↓ | Disagreements: model correct / Kalshi correct |
|---|---:|---:|---:|---:|---:|
| Kalshi reference | 76 / 119 | 63.87% | 0.644377 | 0.224897 | — |
| Market-informed probability model | 77 / 119 | 64.71% | 0.629080 | 0.219521 | 5 / 4 |
| Accuracy-focused research model | 79 / 119 | 66.39% | 0.646823 | 0.227057 | 11 / 8 |

The probability model lowers log loss by **0.015297** (2.37% relative) and Brier by **0.005377** (2.39% relative) in this cohort. The accuracy-focused model adds **three correct picks**, a **2.52 percentage-point** difference. These are hindsight leaders from exposed current-season monitoring. **All paired week-bootstrap intervals cross zero.** Neither result qualifies a prospective strategy or demonstrates profit.

- [Resolved disagreement examples](current_disagreements.csv) show both model wins and losses, with rounded model confidence.
- [Interactive evidence](review.html#current-seasons) separates winner, margin and total results across 2024/2025/2026.
- [Provider coverage](review.html#current-providers) keeps DraftKings, Kalshi and Polymarket distinct.
- The full current source census, scored cohort and last-week coverage are documented in [the model card](CURRENT_MODEL_CARD.md). The 120-final Kalshi audit is not a claim to cover every latest source final.

A winner forecast and a spread bet are different targets. An independently placed live bet cannot be counted as an issued pregame model pick. The public export now includes rounded current research forecasts and actual clocks. Exact recipes, fitted weights, private locations and raw paid quote arrays remain private.

### Every week, every game, and an honest issue clock

[**Weekly forecast explorer →**](review.html#weekly-cards) shows all **14 Week 8 finals** and all **15 Week 9 scheduled games**, with winner probability, margin, total, result and forecast origin. [**Full-season inventory →**](review.html#season-inventory) retains all **272 schedule games**: 121 final and 151 upcoming at the November 3 source observation. Missing or incomparable forecasts remain explicit.

The prior accepted N033 run added **192 native forward fits** and issued early research predictions. The later authenticated N034 diagnostic run **reused those 192 fitted heads** and issued a distinct **27,405 early target rows across 29 games** at **22:58 UTC on November 3**, including multiple candidate arms. N034 failed overall; its completed evidence is retained without promoting the run to accepted research. Both issue sets had **zero final-hour-qualified cards**. The upcoming historically selected heads are not the hindsight leaders in the season table. Current early cards say **Early projection · betting assessment pending**. That describes research readiness, not whether anyone personally wagered. Current injury/QB availability is not verified in these forecasts. [Read the status definitions and separate Ravens update](CURRENT_FORECAST_STATUS.md).

### Five-minute employer review

| Review question | Start here | What you can verify |
|---|---|---|
| Can the modeling claims withstand scrutiny? | [Current model card](CURRENT_MODEL_CARD.md) | Cohorts, target-specific results, uncertainty, missing evidence |
| Is the pipeline engineered for real failures? | [Exact dependent replay](DEPENDENT_REPLAY.md) · [Packaged source](PACKAGED_SOURCE.md) | Authenticated inputs, isolated imports, deterministic recovery |
| Does the evaluation prevent leakage? | [Chronology](ROLLING_CHRONOLOGY.md) · [Methods](CURRENT_METHODOLOGY.md) | Availability cutoffs, frozen versus rolling policies, honest issue clocks |
| Can I run something without credentials? | [Paired evaluation](paired_evaluation.py) · [Contract source](contracts.py) | Recomputable invented examples and negative tests |
| Is the interface usable? | [Offline evidence explorer](review.html) · [Browser tests](browser_test.cjs) | Responsive filters, exact denominators, keyboard controls, no external requests |

From the repository root, using only Python's standard library:

```bash
python tracks/nfl/paired_evaluation.py --demo
python -m unittest discover -s tracks/nfl -p 'test_*.py'
python tracks/nfl/contracts.py --check-review
```

**Public reproducibility has a clear boundary:** invented fixtures reproduce evaluation and recovery behavior; authenticated private-run aggregates are inspectable; proprietary transforms, tuned recipes, trained weights and licensed raw feeds remain private. Rounded per-game research outputs are published under the scoped disclosure policy in the [methods](CURRENT_METHODOLOGY.md#public-reproduction-and-private-evidence). These public tests do not reproduce private training or substitute for owner acceptance.

[Open the hosted dashboard directly](https://sports-edge-lab-nfl.alv-mendizabal.chatgpt.site/). GitHub remains the canonical repository for source and public evidence. The self-contained [HTML download](review.html) works offline; this Markdown overview is the direct GitHub reading path.

<details>
<summary><strong>Preserved engineering and research history · dated snapshots</strong></summary>

## Preserved engineering and research history

The notes below retain their original snapshots. Older “latest” states, provider gaps and storage figures describe those dated records, not the current evidence above. The [historical explorer](review.html#legacy) preserves **316 saved panels, 948 metric scalars, 66 week slots and 330 provider states** without replacing their underlying data.

**Preserve exact inputs through numerical replay:** the [dependent-replay example](DEPENDENT_REPLAY.md)
shows why a permitted floating-point difference in a baseline can change a derived
feature. It checks independent fields exactly, verifies each derived formula and
returns the original authenticated bytes for exact training hashes. Invented
tests prove this boundary; actual owner acceptance remains a separate requirement.

**Test the executable's actual import context:** the [packaged-source example](PACKAGED_SOURCE.md)
reproduces a source-read failure that occurs inside a zipapp but not an extracted
tree. Its exact-source and physical-archive checks are exercised in a real `.pyz`
subprocess, including wrong-hash rejection. Invented fixtures establish
engineering behavior; they provide no model-fit or owner-acceptance credit.

## Exact spread/total probability scoring

The [discrete settlement-distribution example](SETTLEMENT_DISTRIBUTION.md)
maps a supplied game probability distribution to one exact spread or total,
retains push mass, and distinguishes proper three-state losses from conditional
non-push diagnostics. Its deterministic fixtures are invented engineering
examples, not private sports results or betting advice.

**Installed-file evidence, with an explicit trust boundary:** the [runtime manifest guide](RUNTIME_MANIFEST.md) and [stdlib example](runtime_manifest.py) verify a complete bounded package tree against pinned local installed metadata. The installed digest is required; an original source size is separate provenance. A declared installed size is optional but enforced when present, and the actual full length is always measured and retained. Altered metadata, missing/extra files and changes before phase entry are rejected. The example uses invented files and executes no package code. N018 previously passed scientific runtime admission and then failed its test gate. The newer N019 result below advances the numerical work while retaining separate report, native-acceptance and persistence gates.

**Complete model reporting, with explicit roles:** [the model-role guide](MODEL_ROLES.md) and [stdlib example](model_roles.py) now check an independently declared model inventory against reported rows. An omitted model differs from a reported model with an unknown score. Frozen, weekly-updated and unresolved models remain visible under their declared policies; exact prediction aliases do not become independent model evidence. The example uses invented values, performs no fitting or ranking, and establishes no new forecast edge.

**Different models for different targets:** [the target-replay guide](TARGET_REPLAY.md) and [stdlib example](target_replay.py) evaluate explicit winner, margin and total recipe declarations separately. Matched winner accuracy, log loss and Brier complement point-target MAE/RMSE. Full census rows, ties and missing weeks remain visible. Current-season selection is rejected; reconstructed rows never become historical issued picks. All demonstration values are invented.

**Consistent comparisons and visible disagreements:** [the uniform-comparison guide](UNIFORM_COMPARISON.md) and [stdlib example](uniform_comparison.py) pin exact event membership before comparing a model with a reference. Missing provider rows leave headline scores unavailable; separately labeled intersections cannot silently replace that cohort. The game ledger shows both model-only and reference-only correct picks. Margin/total point errors remain separate from line direction, pushes and missing distributions. The example uses invented values and claims no gambling profit.

**Learning from earlier errors under a separate policy:** [the rolling-chronology guide](ROLLING_CHRONOLOGY.md) and [stdlib example](rolling_chronology.py) distinguish frozen historical training from a separately registered rolling experiment. Strict weekly label cutoffs, matured forward out-of-fold residuals and actual issue clocks prevent current-week outcomes or reconstructed picks from becoming pregame evidence. All demonstration data are invented; the example performs no fitting, selection or promotion.

**Reuse with the intended source consumer:** [the source-isolation guide](ISOLATED_SOURCE.md) and [stdlib example](isolated_source.py) prevent an earlier stage's cached, same-named module from replacing the selected consumer. The helper verifies exact archive and module identities, loads captured source bytes, and restores original import state even after failure. Invented tests cover nesting and pathname replacement; this mechanism grants no new fit or forecast credit.

**Paper-return arithmetic, with explicit unknowns:** [the invented scenario guide](PAPER_SCENARIOS.md) and [standard-library example](paper_scenarios.py) explain prices, returned stake, profit, tie rules, quote clocks and a whole-week budget. Run `python tracks/nfl/paper_scenarios.py --demo` for all 16 win/loss dollar scenarios across four invented positions. Unknown prior commitments produce zero new proposed allocation; no provider calls or orders occur.

**Owner-state update, October 31, 2026 at 5:35 PM PDT:** authenticated N014 completed 102 fresh standard-library tests and its content-pinned market/comparison/paper-report stage, then failed installed-runtime admission before research. New or reused owner fits, new learned forecasts and genuine day-before forecast issues remain zero. N012, N013 and N014 each count once: the verified minimum is nine logical owner outcomes, comprising two scoped successes, six failures and one admission block; the separate checksum launch rejection remains separate. Verified persistence of failure evidence does not turn the run into a scientific success. The dated historical public review below is unchanged and does not publish current prices or private picks.

**Dated shared V011 storage snapshot: scoped cleanup completed October 30, 2026 at 7:21 PM PDT.** Its final snapshot reports **107.962 GiB available, 27.99% used**, after 30 authorized cold roots were removed recoverably and all six protected dependency roots remained. The **34.768 GiB shared free-space increase** is not assigned exclusively to NFL. These are uploaded dated observations, not current telemetry. Do not repeat that global cleanup or restore the old folder layout.

**Owner numerical milestone, November 1, 2026 at 3:08 PM PST:** the authenticated N019 return preserves **405 new real estimator fits and 81 target/arm/origin panels**, with zero Original/N003 refits. Its required 565-test gate passed; actual numerical source-consumer checks passed for their stated panel scope. Independent return auditing reopened every fit/output receipt and recomputed 756 metric scalars. An actual five-cell notebook contains two inline Plotly figures, but later full-runtime acceptance did not pass. A duplicate-identity report defect and a dependency-alias admission defect stopped final reporting and persistence. The exact later completion receipt was not found. **Numerical work completed; the overall owner attempt remains failed and full scientific acceptance is incomplete.** Preserve completed fits and repair the failed stages. MARKET remains retained; no new promotion or profitability claim follows from fit counts.

The historical N010 attempt failed before tests or new science; the dated N014 and N018 histories remain separate. Reuploading an identical return adds no attempt or fit credit. N006 remains the latest successful coverage-only run. N019 now supplies actual new numerical work after N003, although its later required acceptance gates failed. N011 was prepared but no owner execution is established. The dated public review of **316 historical model panels, 948 metrics, 66 week slots and 330 provider states** remains unchanged; it is not a current N019 scientific-results dashboard.

## Maintenance, preparation and scientific outcomes

Through N010, the historical NFL ledger contained six authenticated logical owner outcomes: N003 research success; N006 coverage-only success; N007 admission block; N008, N009 and N010 failures. This is **2 scoped successes, 3 failed, 1 blocked**, plus **one separately observed N005 checksum launch rejection**. Repeated snapshots/transcripts and the identical N010 upload are deduplicated. Shared V011 is a separate successful maintenance operation, with zero NFL scientific-success credit. N002's inherited 147-fit completion is separately supported; its final invocation receipt is unavailable here. Lifetime totals remain unknown.

N012 prepares a separately versioned chronological feature-family and interaction study, compact/expanded comparisons and market-free/market-aware controls. It must qualify the actual source views, reuse only compatible completed work, fit learned transforms within training folds and use historical nested validation. The current season remains excluded from estimator fitting and adaptive selection by default. Registered work, local tests, actual owner execution and scientific improvement are distinct states.

A large source catalog is insufficient evidence of working model inputs. V011 cataloged 55,076 member records; those are not 55,076 engineered feature columns. Consumer migration requires proof of compatible ordered schemas, keyed values, missingness, availability clocks and fold identity. The new **invented feature-parity example** in [contracts.py](contracts.py) demonstrates that boundary without publishing a private recipe or claiming migration of owner data.

The prior N011 local replay of authenticated historical tables preserved 316 panels, 5,688 model-week rows, 66 weeks and 330 provider states through simulated resource failure and packaging. It was preparation, not AWS execution. Its old cleanup proposal is superseded by the completed shared V011 operation. New runtime access must verify the exact returned source bytes without bulk restoration of deleted roots.

## A dated official schedule observation

At **October 31, 2026, 3:00:03 PM PDT**, two official NFL weekly pages yielded 28 Week 7/8 observations, zero conflicts and zero changes to known results or canonical identities. Week 7 had 14 completed games. Week 8 had 13 unstarted games; 11 were already beyond the day-before decision cutoff. Two still-open cutoffs do not establish qualified forecasts or executable prices. This is a separately dated public-source preparation observation, with no owner run or modification of frozen historical model cohorts.

The prior N010 schedule diagnostic records 108 scored 2026 games. The unchanged historical scientific/week export below retains its explicitly dated earlier 107-scored snapshot. These different vintages remain separate. Complete 2024/2025 inventories remain 285 each; the eight excluded 2025 cohort rows comprise seven absent-market rows and one tie. A tie is not proof that no provider market existed.

All five providers in the dated public aggregate snapshot below remain **NO VERIFIED QUOTE**. Actual issued last-week results, reconstructed paper economics and remaining budget remain unknown; **NO BET and zero new paper allocation**. Public schedule availability cannot establish an old issue ledger, a bettable quote or current account eligibility. This snapshot's local preparation status is recorded in [change_manifest.json](change_manifest.json); exact PR/merge/main receipts determine later publication. **AFTER is NOT VERIFIED; 9.9 remains a target.**

## Start here

| Inspect | What it demonstrates |
|---|---|
| [Interactive NFL evidence review](review.html) | All 28 source seasons; 66 NFL week slots; 330 provider/week states; exact smaller model cohorts and preserved model controls |
| [Target-specific monitoring replay](TARGET_REPLAY.md) / [tests](test_target_replay.py) | Fixed declared recipes, matched accuracy/probability/point errors, full weekly gaps and honest reconstruction clocks |
| [Uniform comparison and disagreement audit](UNIFORM_COMPARISON.md) / [tests](test_uniform_comparison.py) | Pinned event membership, compatible targets/lines/cutoffs, both directions of disagreement and explicit incomplete provider support |
| [Model card and evaluation boundary](#model-card) | Conditional win vs point targets, matched MARKET references, historical exposure and unavailable uncertainty |
| [Information-time contract](#a-source-boundary-is-not-model-completion) | The actual N009 boundary mismatch and an interactive, executable invented clock audit |
| [Storage recovery](#n009-recovery-followed-by-an-information-time-stop) | Verified allocation arithmetic, preserved results and a later scientific stop |
| [Coordinator incident and reconciliation method](#a-real-integration-failure) | A proved earlier failure and a semantic admission gate |
| [Public source and negative tests](contracts.py) / [tests](test_contracts.py) | Information clocks, retained-result identity, full denominators, exact cohorts and immutable reentry |
| [Installed-manifest contract](RUNTIME_MANIFEST.md) / [tests](test_runtime_manifest.py) | Whole-tree identity, original versus installed hashes, local-metadata trust and phase-entry rechecks using invented files |
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
| N008 outcome | Coordinator admitted; first worker disk guard failed before tests, full parent admission, coverage refresh or new science |
| N009 recovery | 15,383,494,656 allocated bytes reclaimed; 909 tests passed; 147 original + 90 N003 checkpoints admitted; no parent refits |
| N009 scientific boundary | Stricter source-clock guard failed; zero completed N004 job receipts or prediction tables, with fit-attempt counters unset |
| Three-season weekly review | **66 NFL season/week slots + 330 provider/week states**, locally recomputed from authenticated N006 evidence; no new fits, forecasts or provider calls |

Both 2024 and 2025 contain 272 regular-season games and 13 playoff games. All 22 omitted 2023–2025 training/evaluation games are absent from both saved MARKET/design input tables. This proves the saved-table gap; it does not establish that original provider quotes never existed. A complete accounting ledger can preserve those gaps without manufacturing predictions.

The 2025 tie is also absent from both input tables. The 2026 tie is present in both, including point targets, but excluded by the legacy non-tie cohort. Future margin/total eligibility must be qualified separately. Future games, canceled games, missing inputs and unsupported target semantics are distinct states.

## Every NFL week and five provider evidence states

The [weekly view](review.html#weekly) covers **2024, 2025 and 2026** with 18 regular-season weeks plus Wild Card, Divisional, Conference and Super Bowl rounds for each season. Use its season selector to inspect 22 rows or all 66; the provider selector exposes each named provider for the same slots. January postseason games remain in their football season. The existing target, protocol, metric, family and stable-model-ID controls are unchanged.

The underlying [aggregate JSON](evidence.json) carries all **330** provider/week combinations for DraftKings, Underdog, PrizePicks, Kalshi and Polymarket. Every provider state in that preserved snapshot is `NO_VERIFIED_QUOTE`. This means the admitted evidence does not establish that provider's qualified quotes, product contracts, issued picks and settlements. It is not proof those providers offered no markets. Generic archived MARKET stays a separate comparison reference; provider coverage, profit and ROI remain `null`, never zero.

The schedule was captured at **2026-10-29 19:38:19 UTC**. The weekly export is the preserved local N009 preparation reanalysis of N006's authenticated saved predictions. The subsequent N009 owner attempt did execute, but its failure fallback did not rescan model panels; that weaker diagnostic does not replace these accepted results or establish a refreshed schedule. Saved win/margin/total counts are availability unions across registered panels, not issued forecasts or pooled performance. The four 2026 postseason rows hold **13 expected games by format and zero captured matchups**; no game identity or result is invented. The 165 unplayed regular-season rows remain distinct from missing completed evaluations.

The public checks enforce slot closure, full-season denominators, tie eligibility, future-round semantics, unknown-value preservation and provider separation. They cannot recover private source records or establish historically issued forecasts.

## N009: recovery followed by an information-time stop

The authenticated N009 return contains 77 verified payloads and 14 verified output pins. The owner run passed lossless catalog recovery, **909 tests** (736 inherited + 173 N009), and admission of 147 original plus 90 N003 checkpoints. The worker then failed its source-boundary guard before the first new model job was scheduled. No completed N004 job receipts or prediction tables were present. Unset launched-fit counters remain unknown; test fixtures do not become real estimator fits.

| Dated owner storage evidence | Bytes | Meaning |
|---|---:|---|
| Original catalog allocated blocks | 17,911,427,072 | Retired only after verified preservation |
| Retained compressed archive allocation | 2,527,780,864 | Lossless archive with independent full-decode verification |
| Retained targeted view allocation | 151,552 | Bounded lookup representation |
| **Attributed allocated reduction** | **15,383,494,656** | **14.326996 GiB**, excluding directory/journal metadata and concurrent changes |
| Final shared filesystem available | 28,284,907,520 | 26.342373 GiB at 2026-10-30 01:53:36 UTC |
| Research reserve at that observation | 4,829,478,912 | 4.497803 GiB; no reserve shortfall |

Original and compressed **logical** sizes were 17,911,418,880 and 2,527,775,402 bytes. Logical compression reduction, allocated payload reduction and shared-volume free-space movement are separate quantities. The final shared filesystem was 82.43% used, with 55,244,189 inodes available. These are dated uploaded measurements, not current telemetry, a cost estimate, or proof that all new free space came from NFL cleanup. Per-execution newly allocated bytes and net NFL allocation change were not fully attributed and remain unknown.

All **1,948** files in the full worker preservation scope and **1,680** files in the narrower bridge scope retained content, size and modification time. The scopes overlap and must not be added. Original data, completed parent fits and scientific payloads were preserved. The public view operates on aggregate receipts and never performs owner cleanup.

N008's earlier storage failure remains recorded: 3.721 GiB available against a 4.498 GiB reserve on October 29 at 22:11:59 UTC. N009 crossed that boundary and failed later. The later science failure does not erase verified storage recovery or promote the attempt to scientific success. Its schedule-only diagnostic reported zero rescanned model panels, which means **not rescanned**, not lost. Public contract checks pin every accepted model row and the entire weekly/provider object to their previous canonical hashes.

## A source boundary is not model completion

The diagnosed N009 guard requires a source training-information boundary strictly earlier than the earlier of the recorded decision and **24 hours before kickoff**. The preserved source split records an admissible training cutoff. It does not record actual wall-clock fit completion. A bound one hour before kickoff does not establish the stronger day-before contract, even when the native out-of-sample prediction remains valid under its original protocol.

This is a mismatch between contracts. A permissive source bound alone is not proof of actual future-information use; it is also insufficient evidence for an earlier policy. Replacing strict comparison with equality, moving the saved timestamp backward, or calling a source bound an actual completion time would manufacture proof. Original frozen clocks and completed models remain unchanged.

The [interactive clock experiment](review.html#timing) and [standard-library audit](contracts.py) use **invented** instants to separate four questions: source training bound, actual latest input availability, actual latest label availability, and model completion. Six scenarios under two explicit decisions show insufficient metadata, strict equality, known late information, late fit completion and a complete illustrative admission. A decision 48 hours before kickoff remains the governing earlier policy. Naive/malformed clocks are rejected; missing clocks remain unverified; timezone-equivalent instants receive the same result.

A new eligible-subcohort study is a separate contract. It must retain every game in the accounting ledger with an exclusion reason, compare candidates and MARKET on identical eligible game IDs, preserve prior full-cohort metrics, and keep valid older outcome labels available for later causal history. This public patch does not claim that N010 completed science or that N011/N012 owner science has executed or improved performance. Full-season accounting does not imply that every model is eligible for all 285 games.

## Run the public checks

From the repository root, using Python 3.11 or 3.12; no third-party Python packages:

```bash
python -m unittest discover -s tracks/nfl -p 'test_*.py' -v
python tracks/nfl/contracts.py --check-review
python tracks/nfl/contracts.py --demo --output /tmp/nfl-review-demo.json
python tracks/nfl/contracts.py --demo --output /tmp/nfl-review-demo.json
```

The first demo invocation writes one verified **invented** reconciliation artifact with all 12 information-time scenarios and the invented feature-consumer parity receipt. Reentry checks its identity and modification time remains unchanged; the receipt reports zero new work. Corrupt prior evidence is rejected and preserved. If an earlier v1 or v2 demo exists at that output path, choose a fresh filename for this v3 example; it does not overwrite older artifacts. This example performs no model fits or network calls. The existing [public fitting example](../../examples/review_lab/README.md) remains the broader credential-free ML entry point.

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

Model IDs are opaque stable references across panels. Coarse family labels communicate model breadth without exposing active feature recipes. The view does not invent ablation results, fresh forecasts, calibration evidence or prospective performance. The N004 feature-family study reached its guard and failed during N009; no completed new model results are included. N010 executed and failed before science; N011 and N012 owner scientific execution are not established.

## A real integration failure

N007 passed executable integrity admission, then observed `workspace_layout_manifest.json`. Its organization code expected `workspace_layout.json` and rejected the name before parsing the contents. The resulting diagnostic ZIP proves that boundary; it does **not** prove an invalid schema, stale lock or incompatible project layout. No new scientific fits, source recovery, canonical migration or S3 publication followed. N006 remains the latest successful owner execution in this snapshot.

The public coordinator example tests semantic layout identity independent of filename/list order, preserves unknown fields and defers unknown schemas or unsafe lock declarations. A recognized parse still grants **no mutation**: the actual advertised lock must be acquired and the document identity rechecked. This educational example neither operates a real coordinator nor substitutes for the private runtime's process/filesystem protections.

This case illustrates a practical distinction: a portable artifact can pass its own integrity tests while failing an integration assumption at the owner boundary. Preserve the failure, capture the actual external contract, and repair that boundary without retraining accepted models.

## Provenance and public boundary

The [export](evidence.json) records SHA-256 identities for the independently audited N006 return, N007/N008 failure returns and the N009 recovery/failure return, original recomputed metric aggregate and audit summary, the two pinned weekly aggregate CSV sources, and N009 storage, test, preservation and failure receipts. Blank CSV cells are converted to JSON null without adding values. The audit verified each actual saved prediction file and hashed its sorted string game IDs as compact UTF-8 JSON. It asserted complete cohort-hash and MARKET-metric equality across every table in a season/target/protocol panel. The export copies these observed hashes by the original panel key; no hash is inferred from a row count or label. The original 2026 protocol spelling remains in `source_policy` when the UI groups it as monitoring. The export exposes counts, coarse families and aggregate scores only. It cannot independently reproduce private model training or recover per-game outputs. See the existing [publication boundary](../../docs/PUBLICATION_BOUNDARY.md).

The source snapshot is dated. The dated dashboard does not assert current AWS storage, live workloads, completed N010 science, accepted N011/N012 owner science, a newly executed owner N004 notebook or a live website deployment. The qualified N019 numerical milestone above is a separate dated update. N009's verified cleanup/tests are separated from its failed new-science stage. The [change manifest](change_manifest.json) identifies this NFL-owned publication scope; actual PR/commit/check receipts determine its publication state. The dated shared V011 return establishes scoped maintenance only; it does not revalidate every historical weight or feature consumer.

## Review by role

- **ML Engineer:** inspect exact-cohort comparisons, target contracts, separate information/fit clocks, retained model identities and zero-work reentry.
- **AI Engineer:** inspect semantic admission, immutable artifacts, failure isolation, capacity attribution and observable boundaries. This contribution makes no LLM/agent capability claim.
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

### Model roles and matched comparisons

The [model-role evidence example](MODEL_ROLES.md) distinguishes a saved candidate, a retrospective minimum, an unrun challenger, and an authenticated selected champion. Its invented data and executable tests require identical game identities and per-game market references; missing results remain unknown, and exposed 2026 monitoring cannot generate a ranking. This is a public engineering example with no new owner fits or claimed predictive improvement.



### Feature dependency admission

[Feature lineage](FEATURE_LINEAGE.md) checks the full dependency graph at the decision cutoff, including unknown upstream teacher training clocks. Valid count-based features remain usable when a separate derived family is blocked. The credential-free example and behavioral tests use invented metadata, not sports results.

</details>
