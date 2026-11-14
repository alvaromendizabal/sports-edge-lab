# NCAA V11.1 continuation status

## Latest observed R12 census

The observed-census panel now exposes the authenticated report snapshot from **2026-11-14 05:23:59 UTC**, separately from the earlier model-comparison payload. Its **24,522 inventory rows** comprise **2,502 canonical games**, **903 unresolved official records**, and **21,117 unresolved schedule records**. Unresolved records may overlap and must not be added to the unique game denominator. The complete official season universe remains unverified.

Canonical statuses are **1,482 final, 1,013 scheduled, 3 in progress, and 4 unqualified**. The source report called the scheduled-plus-in-progress total of **1,016** upcoming; the panel makes that meaning explicit. It contains **zero qualified saved forecasts**. Publication does not issue forecasts, refresh feeds, score models or create scientific fit credit.

The two downloadable JSON projections contain only league, public event ID, team names, event time/precision, status, inventory kind, missing-reason codes, and away/home final scores. They exclude source hashes, cloud locations, source versions/receipts, private clock details, model inputs, weights, raw quotes and unissued forecasts. The canonical table loads first; unresolved records are loaded only when selected. Filters, pagination and filtered JSON export preserve the report as-of time and incomplete-universe flag. The prior scientific payload remains byte-identical.

The [interactive V11 evidence page](v11.html) preserves the previously published
NCAA men's and women's comparisons. Its source analysis time remains
**2026-11-13 23:38:59 UTC**. A publication update is not a source refresh or a new
owner run.

## Latest actual execution: R12 resource-deferred

The authenticated R12 owner execution began **November 13, 2026 at 8:57 p.m.
Pacific** (November 14 at 04:57 UTC). It ended at 9:27 p.m. Pacific after
**1,837.837 seconds — 30 minutes 37.8 seconds** with
`RESOURCE_DEFERRED_PARTIAL_WORK_PRESERVED`. Source refresh completed, then
parent-stage resource admission stopped execution before fitting. Newly committed
target, scalar-calibration and empirical-residual fits were **zero**. Verified
fit reuse, scientific worker starts, new forecasts and promotions were also zero.
Uncommitted optimizer attempts are not inferred from missing artifacts.

### Admission defect and execution time

The final wait lasted **120.000 seconds across 115 observations**. The first
sample was stale. The remaining **114 observations** reported measured capacity
admitted with a one-CPU reservation and no draining, while the
additional-worker admission predicate remained false. The existing parent
already occupied the retained CPU. Its continuation was tested as an additional
worker instead of as continued work within its existing verified lease.

The final observation recorded **47.94 available CPU cores**, **91.02 GB available
memory**, and **538.67 GB free disk**. This was not evidence of exhausted host
resources. The repair must distinguish existing-parent continuation from new
worker admission while retaining genuine lease, affinity, active-work, memory,
IO, disk and cost guards.

The source-refresh stage took **1,361.410 seconds**, including **1,028.527 owner
CPU seconds**. A **1,095,672-row** display-history snapshot occupied a declared
single-worker serialization path for **259.720 seconds**. The report later
reused that snapshot, but that did not avoid the earlier serialization. Initial
current-coverage reporting took approximately another 116 seconds.

Peak granted CPU was **one**, against a configured ceiling of twelve. Peak
measured owner-tree CPU was **1.0007 cores**; average parent CPU was **0.73293
cores**. No 12-core training or new fitting throughput claim is supported.

### Preserved source and return work

The current receipt contains **2,502 canonical games**, including **1,482 final**
and **1,016 upcoming games**, with **zero saved forecasts**. All **3,429 weekly
display rows** lack win, margin and total predictions. Unresolved official and
schedule identities remain explicit; complete official coverage is not claimed.
Acquisition progress is not training or a completed current-model comparison.

R12 recovered **all 65 indexed R11 diagnostic bodies**, totaling **9,522,212
bytes**. The actual R12 ZIP is **83,145,771 bytes** and passed integrity checks
for **239 declared payloads**. Its **39,979-byte manifest** and ZIP were uploaded
and fully read back: **2 PUT and 2 GET calls**, with **83,185,750 bytes in each
direction**. Scientific completeness remains partial.

The main-store receipt, before final return publication, records 6,479 GET
attempts, 6,306 full-GET successes and 3,579,131,373 bytes read; 3,355 conditional
PUT creations and 3,575,321,395 bytes written; and 8,605 verified cache reads
totaling 10,282,383,511 bytes. These counters do not establish a complete priced
API-credit bill or the SDK's unobserved internal retries.

The observed whole-instance wall-cost estimate is **$1.311556** at **$2.57/hour**.
It is not an invoice or an exclusive NCAA allocation. Work after the summary and
additional service charges are excluded.

The previous R11 source-guard repair, diagnostic recovery and final return
persistence worked during R12. The requested scientific continuation still failed.

### Selected execution tally

| Scope | Actual owner runs | Completed with gaps | Failed | Resource deferred |
|---|---:|---:|---:|---:|
| Recent R9 / R10 / R11 / R12 | 4 | 1 | 2 | 1 |
| Nine preserved older runs | 9 | 0 | 6 | 3 |
| Earlier B033 / B036 returns | 2 | 1 | 1 | 0 |
| Combined selected evidence | 15 | 2 | 9 | 4 |

Thirteen selected runs were unsuccessful or deferred. These are not lifetime
counts. The recent completed run performed frozen saved-row scoring; the recent
four runs contain **zero new target fits**. Four older interrupted runs retained
useful partial science. B033 failed after committing 108 target fits; B036
completed with 65 newly committed target fits and 35 scalar-calibration fits.
Those historical fits receive no new-fit credit in this update. One reported
parser attempt and two transfer attempts are separate from owner executions.

### R13 is unreleased

R13 preparation is incomplete. The focused resource suite recorded **47 cases:
46 passed and 1 errored**, with correction pending. The workspace reset removed local preparation files before complete validation
and packaging. Recovery from authenticated prior artifacts is in progress. The acquisition
continuation adapter is **not implemented**. No ready R13 release, actual R13
owner execution, new fitted model or forecast is claimed.

### Historical R12 local validation evidence

These checks passed before the actual R12 failure. They did not establish that
the complete owner continuation would succeed. Separate suites may overlap and
are not summed. None supplies production fit, forecast or owner-execution credit.

| Local check | Observed result | Wall time |
|---|---|---:|
| Fresh startup prerequisites | 318/318 passed; zero failures, errors or skips | 48.2225 s |
| Warm receipt | 0 cases executed; 318 prior validation cases reused for identical code/environment | 0.651828 s |
| Native checkpoint bridge | 54/54 passed | 61.2418 s |
| Physical return transport | 16/16 passed | 37.6982 s |
| Original numerical and feature scopes | 19/19 matched | Source equality |
| Independent review binding | 15/15 source pins matched; no unresolved findings | Review evidence |

Real serialized archives of 536,870,911; 536,870,912; 536,870,913; and
2,150,629,376 bytes passed integrity and reassembly checks using 1, 1, 2 and
5 physical parts. The 512 MiB limit is per transferred part.

The first local transport attempt stopped at a real free-disk gate on the
temporary volume: 15 cases passed and one reported an error. The same executable
then passed all 16 on a local volume with sufficient storage. This validation
iteration is excluded from the 15 actual owner-run tally.

Authentic B033/B036 archive validation retained 108 and 85 candidate records,
respectively. It deserialized no models and received zero new or verified reused
fit credit. Actual current runtime, input and artifact readback gates remain
required during the next owner execution.

## Prior scientific work preserved

The prior completed R10 owner run completed saved-row scoring and a bounded
result refresh with explicit coverage gaps. It produced **zero new fitted
models, inference calls, issued forecasts or promotions**. The latest partition
set contains 867,979 scored model rows: 854,308 initial rows, replacing 47,620
earlier current-season rows with 61,291 refreshed rows. These are model rows,
not distinct games. Benchmark repetitions are excluded from this total.

The V11 page already contains 512 descriptive paired comparisons, 48 metric
leader rows for full available cohorts, 48 comparable early-week leader rows
and 336 model panels. The current matched research cohorts include 486 men's
games and 483 women's games. All results retain their evidence class and
explicit denominator; these incomplete, exposed cohorts cannot establish
prospective superiority.

The 50% / 35% / 15% current/prior/earlier season policy and alternative weight
policies are retained. No exact recovered candidate identity spans all three
seasons, so weighted ranks remain withheld. The recovered payload keeps its original 1,208 withheld uncertainty labels.
The separately dated historical supplement below supplies 336 exploratory
intervals while current and comparable early-week intervals remain withheld. All 1,344 source/model panels
have zero qualified market matches. Missing evidence is never zero error.

The current inventory reconciles 3,469 prior display rows to 3,425
source-specific event IDs and retains 6,894 observation versions. These IDs
are not asserted to be unique across providers. Six identity conflicts remain
quarantined. Future unissued numeric forecasts remain withheld.

## Preserved historical uncertainty supplement

The earlier local statistical replay of 12 authenticated historical partitions
reproduced all 336 exact cohort hashes and game counts. Paired point estimates
agree with the recovered public evidence to at most 8.9 × 10⁻¹⁶ absolute loss.
The study was registered at 2026-11-14 00:55:00 UTC and executed 149,999 paired
resamples of whole America/New_York calendar weeks, retaining unequal week
sizes and the recovered per-partition multiple-comparison family. No model was
fitted or used for new inference.

The 336 exploratory Bonferroni-adjusted percentile intervals contain 9 positive
loss improvements, 15 negative results and 312 intervals including zero. The
last count includes 28 self-baseline controls. All 40 negative-control checks
passed. These are metric comparisons, not 336 distinct models or wins.

| Competition / season | Positive | Negative | Includes zero | Interval rows |
|---|---:|---:|---:|---:|
| Men 2024–25 | 2 | 0 | 82 | 84 |
| Men 2025–26 | 1 | 1 | 82 | 84 |
| Women 2024–25 | 2 | 4 | 78 | 84 |
| Women 2025–26 | 4 | 10 | 70 | 84 |

The historical partitions contain 22–23 week clusters. These exploratory
conditional percentile intervals do not remove repeated-team dependence,
selection exposure, nonstationarity or source drift; they do not implement
bootstrap-t or guarantee exact finite-sample coverage. Two- or three-week
current-season intervals stay withheld because additional resamples do not
create independent weeks. There is no weighted champion, market-advantage
claim, prospective improvement claim, new issue or promotion.

The study records [Gneiting and Raftery’s scoring-rule paper](https://sites.stat.washington.edu/raftery/Research/PDF/Gneiting2007jasa.pdf)
and [Cameron, Gelbach and Miller’s clustered-bootstrap paper](https://www.nber.org/system/files/working_papers/t0344/t0344.pdf)
as method references. The latter is a caution about clustered inference, not a
claim that this percentile procedure reproduces their bootstrap-t method.

## Preserved scoring benchmark and pending continuation

The prior completed owner scored the same 854,308 records across 18 independent tasks
in each declared benchmark layout. The one-worker layout took 56.500 seconds;
the 12-worker layout took 6.652 seconds, an 8.493× wall speedup with 8.317
measured process CPU core equivalents. This measures saved-row scoring, not
fitting. Requests for 6×2 and 4×3 actually used 6×1 and 4×1; additional native
thread throughput has not been established.

V11.1 requires one complete immutable logical return and a 512 MiB limit per
physical transfer part, with numbered parts and integrity-checked reassembly
when needed. Aggregate transport size must not prevent otherwise admissible
science. Exact recipes, source rights, information clocks, actual resource
availability and independent promotion review remain required. R12 recovered
all 65 indexed R11 diagnostic bodies and verified its complete declared return,
while the scientific workflow remains partial. R13 is unreleased and requires
correction, complete validation and packaging. Recovery checkpoint references
are not model-fit counts.

## Publication scope

The embedded scientific payload is preserved byte for byte from the recovered
public V11 page. The added [operational status](v11_1_execution_status.json)
contains only aggregate execution facts and the incomplete R13 preparation status. The earlier
uncertainty supplement is reused unchanged; it is not counted as new work. Private
recipes, weights, owner packages, cloud paths, raw feeds and future unissued
candidate values are excluded. Older NCAA pages and other sports' evidence
remain unchanged. Source publication and hosted deployment are separate events.

Validation lives in `examples/ncaa_review/test_v11_public_evidence.py`. It checks
payload continuity, row-count conservation, no false fit credit, per-part
transport semantics, withheld unsupported claims, future issue qualifications
and the public boundary. The browser review separately checks the interactive
filters, paging, mobile layout and execution panel.
