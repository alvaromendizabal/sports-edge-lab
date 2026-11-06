# NCAA evidence review

[Project](../../README.md) · [Men's track](../../tracks/ncaam/README.md) · [Women's track](../../tracks/ncaaw/README.md) · [Publication boundary](../../docs/PUBLICATION_BOUNDARY.md)

This example makes the **evaluation contract** executable without credentials, data subscriptions or a machine-learning environment. It also generates the college basketball review pages from committed, sanitized aggregate evidence. The invented demonstration and the real historical aggregates remain separate: the example does not reproduce the private models or claim a betting record.

## Current review — November 6, 2026 UTC · B042 returned; B043 prepared

B042 completed **9 of 15 scientific stages** before the injury base-verification
stage failed. It committed **102 new target estimators, 46 scalar calibrations
and 24 empirical residual fits** across the two leagues in **92.61 minutes**.
It reused 108 historical target fits and 12 native target fits plus six native
scalar calibrations; those are separate from new work. The fixture gate passed
1,029 cases with one optional integration skip and no errors.

Current source acquisition, original-model inference, chronological monitoring
and native replay completed. The injury verifier used a floating-point reduction
that differed in its last bits from the historical producer. B043 prepares a
repair that reproduces the producer exactly and retains the equality check.
The injury study committed no challenger fits. Final issue reconciliation and
scorecards were among the five later stages that did not start.

Independent recovery authenticated **339 existing B042 issue rows across five
games**: 132 rows / two men's games and 207 rows / three women's games. Recovery
preserved their original bytes and issue clocks and created **zero new issues
or model fits**. These target/stream rows repeat games; they are not 339 distinct
games or settled wagers. The original frozen reconstruction covers 1,312 games /
3,936 target rows and receives zero original as-issued credit. The current
monitor and native replay contain 71,260 and 10,689 target rows respectively.
**New B042 paired scores and a new model winner remain unavailable.** Earlier
historical selections and the preserved current comparison keep their exact
values and cohorts.

### Updated capture, with explicit denominators

Source acquisition completed **November 6, 00:25:57 UTC** (November 5, 4:25 p.m.
Pacific). The retained display inventory contains **711,001 observations**:
561,323 Kalshi, 149,412 Polymarket international and 266 DraftKings. The increase
of 153,264 over B040 is a retained-observation increase, not newly requested
quotes, independent games or executable liquidity. Polymarket US remains
separately unacquired. The latest source quote and acquisition clocks remain
separate; publishing this review refreshes neither.

The visible inventory has **2,818 source/candidate records and 755 reported
finals**, while the ESPN source separately contains **1,792 game versions and
491 finals**. The official inventory has 1,797 accepted contest records, 775
exact matches, 1,022 unmatched official candidates, 44 conflicts and four rejected
records/date failures. These populations can overlap or duplicate one another;
complete physical-game coverage remains unverified. CBBD remains paused after
HTTP 429. Retained provider refusals and uncertain transport results are not
cleared by a new release. The Odds API found no configured runtime credential
and made zero new calls or credit charges.

### Injury evidence and prepared market-path research

There are **1,320 injury observations**, 643 men and 677 women: 1,306 bound and
14 unresolved. Seventy-four have a supported source-availability upper bound
(12 exact publication clocks and 62 date bounds). The other 1,246 lack one:
1,244 recovered image observations and two current PDF observations. **All
1,320 historical snapshot versions remain unverified.** More observations do
not establish complete injury coverage or a measured injury effect.

B043 prepares a separate market-path extraction, path-clock validation and
chronological paired study. Actual in-game observations and timestamp-supported
game-state windows are required. The B042 retained observation count does not
establish that support: its history collection ended at tip. No successor
owner execution, new B043 issue, injury improvement or market-path gain is
claimed. Original, rolling and issued tracks keep their separate semantics.

The actual nested B042 return SHA-256 is
`1550fbe4c1a1bd459e7117121444928c3be002c02fbb5fd37c7c79fc7362d618`.
The [men's aggregate evidence](../../tracks/ncaam/evidence.json) and
[women's aggregate evidence](../../tracks/ncaaw/evidence.json) provide stage
counts, source freshness, missing results and the preserved prior history.

### Preserved B041 and B040 evidence

B041 stopped during predecessor setup before any of its 15 scientific stages.
Its 982 passing fixtures and one optional skip produced no source requests,
imports, fits or forecasts. The independent-source progress repair preserves
the backward-counter guard. B040's dated inventory remains in history with
557,737 observations, 2,816 source/candidate records and 738 reported finals.
The new capture does not revise those earlier snapshots.

## Run the example

Python 3.11 or newer; standard library only:

```sh
python examples/ncaa_review/contracts.py --demo
python examples/ncaa_review/admission.py
python examples/ncaa_review/progress.py
python -m unittest discover -s examples/ncaa_review -p 'test_*.py' -v
python examples/ncaa_review/build_dashboard.py --check
```

The demo creates deterministic invented history, fits a three-intercept baseline at a chronological origin, and scores completed invented events separately by league, target and provider. Its result includes missing comparisons and both winning and losing directional disagreements. A pure payoff function demonstrates how explicit executable prices and fees affect an invented one-unit decision. It has no placement API and emits **zero orders**. Fixture fee values are not estimates of any provider's real fees.

The browser check exercises generated pages in real Chromium at desktop and mobile widths, every objective/window selector, all clock scenarios and keyboard navigation. It rejects JavaScript errors, unexpected external requests and page overflow. CI uses its separately pinned Playwright installation:

```sh
PLAYWRIGHT_MODULE_DIR=/path/to/playwright \
  node examples/ncaa_review/test_dashboard_browser.cjs
```

## What the real historical evidence says

The latest accepted historical population covers 2024–25 and 2025–26: **11,507 men's games** and **10,901 women's games**. These are represented games in an exact shared prediction cohort, not a claim of all official games. The models were selected after those seasons had been evaluated. The resulting scores are **development-exposed retrospective evidence**, not an untouched final test or prospectively issued performance.

| Objective | Men's pooled selection | Women's pooled selection |
|---|---:|---:|
| Minimum natural log loss | 0.523274 | 0.454618 |
| Minimum Brier score | 0.177371 | 0.151127 |
| Maximum winner accuracy | 72.35% | 77.01% |
| Minimum margin MAE, points | 9.075180 | 9.686569 |
| Minimum margin RMSE, points | 11.551616 | 12.273463 |
| Minimum total MAE, points | 13.336419 | 12.643371 |
| Minimum total RMSE, points | 16.941556 | 16.011293 |

Each row may select a different model. The women's log-loss and Brier selections are almost numerically identical but remain distinct. Public IDs identify the reported selections without disclosing exact private recipes. When the page switches seasons it keeps the same pooled-selected model; it does not select a different seasonal winner. The sanitized source tables are [men's evidence](../../tracks/ncaam/evidence.json) and [women's evidence](../../tracks/ncaaw/evidence.json).

Historical feature availability uses a declared 24-hour release assumption, which is weaker than independently proven historical publication. The one-hour evaluation horizon does not erase that limitation. Newly obtained information must never be moved backward to an earlier prediction cutoff.

### Probability and point error use different measurements

Winner comparisons use natural-log loss with the same clipping constant (`1e-15`), Brier score on the unmodified probability, and accuracy awarding half credit at probability `0.5`. Ties make no directional pick. Calibration bias is mean predicted probability minus observed frequency. The ten-bin reliability plot exposes bin support; ECE is the support-weighted absolute bin error, and ROC AUC uses average ranks for ties. ECE can hide differences within bins, while AUC does not measure probability calibration.

Margin means home points minus away points. Totals include both teams and overtime. MAE measures average absolute error; RMSE penalizes large misses more strongly; signed bias is predicted minus actual points. A margin-direction tie receives half credit. Total-point forecasts alone cannot establish over/under accuracy: the line, push rule and decision are required. A point forecast does not provide a calibrated spread-cover probability.

### The uncertainty is descriptive

The probability and accuracy selections are compared on exactly matching events, ordered teams, prediction clocks and outcomes. The report resamples whole local-calendar weeks **within each season**, with replacement, 2,000 times using a fixed seed. It sums game losses in each resample and divides by that resample's game count. It does not give each week equal weight regardless of its number of games.

| Probability selection minus accuracy selection | Men | Women |
|---|---:|---:|
| Log-loss difference | −0.005184 | −0.002887 |
| Descriptive 95% interval | [−0.006486, −0.003840] | [−0.005578, −0.000172] |
| Accuracy difference, percentage points | −0.0695 | −0.3257 |
| Descriptive 95% interval, percentage points | [−0.4308, +0.2912] | [−0.7948, +0.0640] |

The probability selections have lower historical proper-score losses. Both accuracy-difference intervals cross zero. These are selection-exposed intervals with no adjustment for the model search; they do not establish future superiority. Resampling weeks also does not eliminate dependence that persists across weeks or seasons. The private per-game inputs are not published, so the public aggregate tables allow inspection of these conclusions, not an independent reconstruction of the bootstrap.

## Preserved B037 market inventory and separate update clocks

The preserved B037 owner attempt failed during source consolidation and committed zero new model fits. Its preserved market array received a complete physical byte/hash readback: **477,340 observations**, consisting of **429,428 Kalshi**, **47,880 Polymarket international**, and **32 DraftKings** records. These are observed source rows, not unique games or qualified comparison pairs. B038's bounded preflight correctly deferred while B037 still owned the canonical lock; it did not run a new research workflow. B036's completed retrospective results above remain preserved. No new model-performance claim follows from recovery or public publication.

The private viewer now distinguishes the **captured observation inventory** declared in the report from the **observation rows loaded in this tab**. A compact report can carry all game rows and their selected quote references while the full timeline remains in bounded private objects. An empty inline array therefore displays its declared archive count and its missing local rows explicitly. The same distinction applies to unclassified source points. It never turns absent data into a zero-coverage claim.

A separate panel shows the season label/end year, report generation time, report observation time, data acquisition completion, last successful refresh, last attempted refresh and its status. Missing timestamps say unavailable. The 2027 season end year never becomes a 2027 update timestamp. Quote and forecast issue clocks remain attached to each record.

“Latest supported pre-tip” means the observation's supported source time precedes the exact start. It may have been recovered after the game. Where exact game, source quote and acquisition clocks are all supplied, the viewer separately shows whether capture occurred before tip; otherwise capture-before-tip remains unverified. T−120 and T−60 references disclose whether actual capture preceded that reference. These display diagnostics cannot change a model value, qualified pair, original issue, selection or ROI.

The optional **local bounded-file inspector** accepts one index part up to 16 MiB and one data chunk up to 32 MiB. It verifies physical bytes and SHA-256 against the imported manifest/index, checks order and record-count closure for the selected index part, and displays one validated data chunk at a time. Imported values use text-only DOM construction. A wrong hash, wrong count, missing part or malformed file preserves the last valid view. The page explicitly states that unselected chunks, metadata objects and the full logical archive were not verified in the browser. It never requests a cloud URL, uploads a file, persists data or grants model eligibility. The entire archive is not assembled in browser memory.

An optional **next-week** selector becomes usable when the report supplies exact next-week event membership. Existing report and metric week cohorts keep their established Eastern calendar definition; the expanded acquisition plan's Pacific current/next-week schedule scope is separately disclosed. The viewer does not recompute either membership from dates.

The additional browser checks use invented sparse inventories, deliberately different season/update clocks, a retrospectively recovered source quote, an on-time capture, exact bounded index/data hashes, corrupt data, an unknown index, unclassified observations and clear/reset behavior at desktop and mobile widths. Runtime fixture passes and viewer checks remain separate from owner science, new provider capture, complete coverage and profit.

## Preserved B036 evidence and private report viewer

The last completed workflow evidence, B036, completed all 12 stages with explicit coverage gaps: 65 new native reconstruction target fits, 35 scalar calibrations and 108 verified/reused historical targets. These counts are distinct. Its 536 passing fixtures and one optional skip are software evidence; its 8,100 native target prediction rows are retrospective reconstructions, not original or prospective issues. Current original-runtime and selected-monitor gates remained unresolved.

The public pages now expose fresh sanitized aggregate counts and a [browser-only private report viewer](../../docs/ncaa/private-report/index.html). Its source is [private_report.html.tmpl](private_report.html.tmpl). Users choose their private `sports-edge-lab.private.game-report.v1` JSON; the page uses `FileReader` and text-only DOM construction. It has no upload, network, analytics or browser-persistence path. Its content security policy rejects connection requests. No private sample data is embedded or committed.

The captured-price selector provides four separate references: **price supported by T−120**, **price supported by T−60**, **latest supported pre-tip**, and **latest observed**. Each value keeps its source quote, acquisition, support-end and history-resolution clocks. A later recovery can be visible without becoming an earlier model input. The latest observed value may be after tip or settlement; the latest supported pre-tip value is not a claim of a universal closing price or executable liquidity. The recorded strict T−60 model comparison uses the separately exported `provider_target_prediction` and status for each selected forecast stream. Changing a captured-price reference never changes that pair, a forecast, a selection or return. Identical captured observations can be displayed once across streams, while differing supplied source versions remain visible. Missing horizon values do not fall back to a later quote or a different stream's qualified pair.

An optional unclassified-source section retains native values and clocks separately when source semantics may include settlement, including ambiguous zero-resolution points. These records have their own supplied count and bounded 25-row paging, and cannot fill a captured pre-tip price, forecast, paired comparison or ROI. Older files without this inventory say **not supplied**, rather than asserting that no such observations exist.

An optional report-only horizon section shows the supplied T−120, T−60 and latest pre-tip paired populations, with the model and provider metrics side by side. Each population retains its explicit league, season, target, stream, evidence mode and membership digest. The later quote is compared with the fixed earlier model; this is neither a new fit nor evidence of execution or profit. Older reports without this section show **not evaluated**, with no invented zero or inferred result. These viewer capabilities do not establish completion of a newer owner run or replace the last authenticated B036 evidence above.

The optional three-provider comparison section gives **Kalshi, Polymarket and DraftKings equal visibility**. Season and weekly selectors expose each provider's paired population and the supplied common-game population separately. Model and provider log loss, Brier, accuracy, calibration, AUC and supported point-error metrics retain their original definitions, paired N and membership digest. The viewer does not pool recipes, overlapping weeks, leagues, streams or evidence modes, or compute missing metrics. A common-game comparison requires source metadata naming exactly the active three providers; legacy all-six-provider records remain in separate lineage. Unverified or incomplete common populations cannot establish a three-way ranking.

Each population keeps both supplied directional-disagreement counts: model right/provider wrong and provider right/model wrong. The exact supplied disagreement inventory has bounded paging and retains predictions, correctness, probability difference, cutoff, quote and acquisition clocks. It is a separate source table: selecting common metrics does not invent common membership for its records. Missing tables say **not supplied**; present empty tables say **supplied empty**. No rows under a filter means none in that supplied inventory, without asserting complete game or quote coverage. Unlabeled Polymarket products stay unverified, international and US are not combined, binary thresholds remain distinct from point forecasts, and paired scores do not establish ROI. Original raw CSV fields and source byte/hash pins remain available in details.

The viewer groups source records within each explicit league. It preserves missing-model games under every forecast-stream selection, uses exact exported window memberships, shows reconstructed and original-as-issued roles separately, and exposes all clocks and flags in details. A separate market tab retains unbound observations. It does not reinterpret binary threshold prices as point totals, infer quote availability, or manufacture a wager. The file-size limit is 64 MiB; schema and row inventories are validated before replacing an existing report. Invalid input leaves the existing report intact, and imported strings cannot create HTML elements.

Browser checks use invented records to exercise file import, pagination, exact windows, missing-stream retention, malicious-looking text, unresolved identities, invalid-file handling and clearing. Those tests do not publish or claim to validate private science. All inherited aggregate models and failure history remain unchanged.

## Preserved B033 current-season status and provider scope

The following paragraphs describe the earlier B033 snapshot. They remain historical evidence; the earlier B036 completed workflow remains preserved.

The latest B033 owner return completed parent restoration, historical feature construction and its registered study: **108 newly committed target-estimator fits across both leagues, 54 per league**. It then failed when current-source refresh selected a shared summary belonging to another project. Admission took **69.1 minutes**; scientific wall time was **21.6 minutes**, including **19.7 minutes** for the study. The **371 passing fixture tests** took 10.1 seconds and remain separate from model fits. The attempt produced no fresh current-game or provider corpus, current issues or orders. A full independent readback verified the returned bytes. The historical headline selections above are preserved; this partial run does not establish a new current-season performance record.

The earlier B032 attempt stopped at parent-data restoration with zero completed science. Its original failure, 250 passing fixtures and later durability verification remain in the JSON history. Neither an overall failed status nor a later readback erases valid committed work or manufactures additional scientific credit.

The retained current inventory is dated **November 2, 2026, 4:48 p.m. Pacific**: 437 men’s candidate records with 13 observed finals, and 419 women’s candidate records with 51 observed finals. The public pages show those counts and their age. They are not a reconciled official season denominator. The refresh failed before resolving missing phase, opponent-division, exact-time and potential duplicate cases.

The active comparison scope is **Kalshi, Polymarket and DraftKings**. Missing current-season paired coverage, log loss and ROI remain `null`/unavailable. Neither a high winner accuracy nor a low historical log loss demonstrates an executable economic edge. The public example compares model and reference on the exact same provider-specific population, preserving target, horizon, ordered teams, settlement, quote availability and outcome-release clocks. It deliberately refuses to merge evaluation tracks or substitute one provider's population for another's.

Quote display has its own evidence contract. A missing model forecast must not hide an otherwise bound observation. Latest captured pre-tip, latest observed, and eligible-at-forecast-cutoff prices remain separate, with actual acquisition clocks. A quote recovered later cannot create an earlier issue or prove executable profit. Polymarket international and US are separate products; US coverage remains unacquired and unverified. The current attempt did not refresh either product.

Frozen-original evaluation, rolling reconstruction, and genuinely issued prospective forecasts remain separate. A reconstruction can use an auditable historical information set; it cannot claim an earlier issuance time. A real prospective issue must be created with the model and features already available, within the declared one-to-two-hour horizon. Retraining on more released data can help or harm; it must earn its result in a separately reported chronological evaluation.

## A concrete boundary failure and its regression test

The failed owner code entered a streaming-body context manager and then called a wrapper-specific iterator on the returned object. That context manager returned the raw HTTP reader. The earlier test double inherited a stream whose context manager returned itself, so it did not represent the production interface boundary.

`verified_read` demonstrates a portable correction: retain the actual wrapper, call its ordinary bounded `read`, verify the complete byte count and SHA-256, and close that wrapper in `finally`. A regression double deliberately returns a *different* object from `__enter__`; the test proves that readback no longer depends on the context return value. Separate negative tests reject truncated, oversized and corrupt content and verify closure after failure. This public test exercises the failure class; it is not evidence that the replacement owner workload has already run successfully.

## Resource admission with a bounded diagnostic

[admission.py](admission.py) demonstrates a resource policy with **invented counters, process identities, memory sizes and worker demands**. It does not inspect this computer, modify a production lock or start an owner workload. The demonstration is a policy contract with injected sampler, lock and clock adapters; its successful admission is software evidence, not a completed scientific stage.

CPU headroom comes from the change in an aggregate busy-CPU counter divided by the sampling interval and subtracted from the capacity of that same scope. Available memory is a separate measured input. After explicit reserves, the policy selects the largest whole worker count allowed by both resources and the requested worker limit. An unrelated process existing is not a veto. Missing aggregate measurements remain unavailable and cause a measured deferral, not an assumed idle machine.

The process-tree diagnostic follows children and grandchildren using stable process identities that include start tokens. It does not confuse a reused PID with the original process. Aggregate counters include child work even when a child has exited between snapshots. The tree's CPU total is **not subtracted a second time**, and summed resident memory is not subtracted from available memory. Partial or invalid optional process detail stays explicit without overriding valid aggregate measurements.

The injected lock adapter represents the **existing canonical project lock**. Acquisition must be nonblocking, and release must accept only the caller's own acquired token. Resource waiting does not hold that lock. Once admitted, the context holds it until the protected work exits, including an exception. A busy project lock still prevents a second owner from starting. The policy has no operation for removing a lock, changing its identity, terminating another workload or substituting a second lock.

Waiting has an explicit positive budget measured by a monotonic clock. Each sampler call receives the remaining budget; each pause is clipped to it. The deadline is checked again after sampling and acquisition, so a result arriving at or after the deadline cannot authorize a start. Exhaustion yields one diagnostic containing sampled capacity, attempted worker counts, deferral reasons and elapsed waiting time. A token acquired too late is released before that diagnostic is yielded. Broken or nonadvancing clocks produce a diagnostic instead of an endless polling loop.

Actual adapters must honor their timeouts, sample the same resource scope as the workload, and account for applicable CPU affinity/quotas and memory limits. This loop cannot interrupt arbitrary blocking adapter code. Resource readings are a snapshot, not a reservation against future activity; production demand and reserves need workload measurements and ongoing supervision. The toy sizes and budgets in this example are not production recommendations.

Admission changes **when computation may start**, not which information a forecast may use. Original forecasts remain frozen; rolling models still need eligible training labels and inputs at each historical origin. The example makes no new source, fit, forecast, coverage or profit claim and changes none of the committed historical evidence or generated dashboards.

## Progress counts and empirical time estimates

[progress.py](progress.py) is an independently written, dependency-free contract using invented units and clocks. The dashboard embeds the exact JSON generated by its eight deterministic scenarios, so the interaction does not maintain a second estimation implementation. It is a demonstration, not a live connection to the owner workload.

A progress observation separates **newly committed**, **reused** and **failed-attempt** counters. Completed units are newly committed plus reused units. Failed attempts do not increase completion. A known total permits a fraction and a remaining count; an unknown pagination denominator remains unknown. Finishing all units still requires explicit phase finalization before a phase is declared complete.

An estimate requires two positive completion intervals from the current worker configuration. It uses up to six recent intervals, including idle time between commits. Restored units reduce remaining work without entering the measured new-work rate. A worker-count change resets the pace window. An extended gap since a new commit invalidates the estimate; a late restored checkpoint cannot revive stale throughput. Failed or cancelled phases keep their progress and return an unavailable ETA.

The displayed range multiplies remaining units by the fastest and slowest observed per-unit paces. It is **not a confidence interval or a completion guarantee**. Heterogeneous tasks, future contention, source pagination and later stages can change the duration. Phase elapsed time and total wall time are independent; the example does not use time spent in admission as a fit-rate measurement. It offers no host sampler, scheduler, resource reservation or process-control API.

Meaningful tests reject mixed phases, backward counters, zero or backward clock intervals, over-completion, nonfinite readings and unjustified completion status. Other tests verify restored-work accounting, idle-time inclusion, worker changes, stale estimates and finalization. The real browser check exercises all eight scenarios at desktop and mobile widths alongside the actual aggregate execution and coverage panels.

### Independent inputs keep independent progress

`QueueIdentity` combines the operation with the exact input content digest.
`estimate_queues` keeps each queue's observations, denominator and ETA history
separate even when operation names repeat. The invented source A completes 3/3;
source B independently reaches 1/5. Their counts are not a model-fit total.
Duplicate identities, mismatched operation names and a backward counter within
either queue remain errors. This example does not access production sources or
change the existing completion/ETA rules.

## Review map

| File | What can be inspected |
|---|---|
| [contracts.py](contracts.py) | Information clocks, exact identity pairing, separate metrics, invented baseline, explicit-fee payoff and stream verification |
| [test_contracts.py](test_contracts.py) | Future-outcome poisoning, equal-boundary exclusion, reordered identities, missing coverage, mixed-track rejection, stream-interface failures |
| [admission.py](admission.py) and [test_admission.py](test_admission.py) | Aggregate resource headroom, child accounting, canonical lock ownership, bounded waits, late-result rejection and explicit diagnostics using invented fixtures |
| [progress.py](progress.py) and [test_progress.py](test_progress.py) | Committed-versus-reused counters, known and unknown totals, phase clocks, empirical pace windows, worker changes and explicit unavailable estimates |
| [test_evidence.py](test_evidence.py) | Cohort closure, metric aggregation, calibration support, fixed selections, missing-value preservation and deterministic page generation |
| [build_dashboard.py](build_dashboard.py) | Deterministic, dependency-free rendering from aggregate JSON |
| [test_dashboard_browser.cjs](test_dashboard_browser.cjs) | Real desktop/mobile browser events, accessibility hooks, keyboard controls and offline rendering |

The accepted historical and failed current owner-return digests are included in the public evidence JSON. Raw provider records, private object locations, complete prediction archives, execution handoffs, exact active features and model parameters remain outside this publication. Nothing here changes the repository's existing rights or publication policy.

## Portable validation and honest outcomes

Run `python examples/ncaa_review/preflight.py` for four invented scenarios. A missing optional runtime function is an observation; a required operation still remains blocked. Check completion, successful execution, failures, unexpected errors and skips have separate counts. A skipped integration never becomes a passing test or a model fit. Duplicate check identities and unobserved capabilities fail before any check is invoked. Exception classes are retained without disclosing messages or private tracebacks.

The preserved B035 owner evidence records its actual preflight failure and zero scientific stages; the earlier B036 workflow completion is shown separately. B033's earlier valid historical study remains separately visible. Neither the invented checks nor a later preserved diagnostic establish fresh game coverage or scientific success.



## B039 evidence and bounded private-report recovery

The authenticated B039 NCAA owner completed ten stages and real model work, then failed while publishing dense weekly HTML. Its committed CSVs and model artifacts remain preserved. The updated track pages show the actual 156 target / 48 scalar / 60 empirical fits, separate reuses, measured resources, partial inventory and remaining coverage gaps. Historical selected panels are unchanged.

The browser-only private viewer accepts both the earlier flat format and a normalized format with shared, disjoint contexts. It resolves fields lazily, preserves zero and false, rejects invalid references or overlapping fields, and keeps declared total versus loaded part counts separate. A bounded index can load one local part only after its exact byte count and SHA-256 match. This generic transport contract does not supply private forecasts or reinterpret financial outcomes. Public tests use invented rows only.

Latest observed, latest supported pre-tip, latest actually captured before tip, and supported T−120/T−60 choices retain separate clocks. The public page uploads nothing, makes no provider calls, and grants no earlier forecast or betting eligibility. Unresolved official source records remain inspectable without inventing teams or start times.

## B040 current acquisition and checkpoint recovery

The later B040 owner completed six of 13 workflow stages, retained 557,737 market
observations, reused 108 historical target results and reconstructed or previewed
1,323 source games with the frozen original engine. It failed during checkpoint
address resolution before any new fits. These are observed source records, not a
reconciled official game denominator. Earlier valid B039 results remain visible
as separate historical work; publication does not make the next owner run complete.

## Injury reporting and information time

The [availability-time example](injury_time.py) uses invented records to separate
what can be displayed from what was available at a forecast's information boundary.
A report recovered later can support a labeled retrospective study while keeping
its actual acquisition time. Missing injury coverage never means a healthy roster.
Two-hour, one-hour and latest-pregame forecasts are distinct versions; a later report
cannot rewrite an earlier issue. These rules do not prevent display, retrospective
research or publication of generic engineering.

A useful injury study compares learned challengers and matching no-injury controls
on identical chronological populations, reports uncertainty and failed experiments,
and preserves the originals. Current-season outcomes do not choose a promoted model.
The B041 owner never reached the injury study; no performance gain is claimed here.


### All supplied availability observations

The private report viewer includes a separate, paged availability table for every
supplied named-player observation, including unresolved identities and unknown
publication clocks. League, status, source-clock and player/team/source filters
operate on these source records independently of model and market filters. Exact
repeated copies are grouped, while conflicting versions remain visible and cannot
inherit an eligibility label from a shared observation ID. A separate paged panel
retains source coverage gaps. Missing reports never establish healthy rosters.

The game-specific pregame views still use only their supplied eligibility audits.
An explicit latest-field map can select an appended display version while preserving
every earlier cell. An explicitly missing or malformed latest value is shown as
unavailable; it does not silently revert to an older view. Source rows do not enter
forecast inputs or change earlier issues, selection or ROI. Source links accept
plain public HTTP(S) URLs only; credentials, signed links and private cloud object
links are not rendered. All report rendering remains in the browser tab with no
network or persistence path. Browser fixtures use invented records only.
