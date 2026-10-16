# Execution source versions

**Latest update, October 16 at 20:59 UTC:** ACB data and its collector have been deleted. V011 remains Stopping; v038 has not launched. [Current backlog, removal evidence and collection endpoint](DOWNLOAD_CLOSEOUT_20261016.md) supersede older status observations below.

A running AWS Processing job keeps the source uploaded at launch. Updating the repository does not hot-patch that running process. Preserve its exact source alongside the current implementation so receipts remain reproducible.

| Source | Version and use | Bytes | SHA-256 |
| --- | --- | ---: | --- |
| [Launched base collector](../tools/history/acquire_paid_data_v001_launched.py) | `sports-edge-lab-paid-v001`; launched by `sports-edge-lab-paid-backfill-20261016-v006` | 39,208 | `56de66fafdef8cabd609cfa8809ea42740ee1b7d46f301ebadc28f754ead49b7` |
| [Current base collector](../tools/acquire_paid_data.py) | `sports-edge-lab-paid-v002`; reusable engine and next-run shooting-query repair | 41,494 | `868c011d061b42cce68b863006b8902a4990dcb8294f50dcecf036f54e001a0c` |
| [Player-prop collector](../tools/acquire_player_props.py) | `sports-edge-lab-props-v001`; imports the v002 base collector above | 15,531 | `1da70fdf659621eaa1113b05183ad9255b5267d94381182f247c5a36543d3445` |

The v001 collector has already archived successful responses. Optional CBBD shooting endpoints initially omitted a required conference or team selector; those failed requests were recorded as nonblocking incidents and were not cached as successes. V002 derives valid selectors from the captured team-season statistics and reuses all successfully cached requests.

Player-prop acquisition uses existing archived event IDs and does not pay for a second event-discovery pass. Its additional credit ceiling is 500,000 across four supported leagues. The base collector's credit ceiling remains 1,000,000; the two executions have separate run IDs and usage ledgers.

The historical source file is preserved byte-for-byte for audit. Use current code for subsequent planned executions. A source version or passing offline test proves neither historical data completeness nor a live acquisition outcome; use the actual S3 run receipts for those conclusions.

## Public archive revision

The completed `sports-edge-lab-public-archive-20261016-v007` job launched the revision with five automatic tests. The current `tools/acquire_public_archives.py` adds a sixth mocked download/resume/hash-rejection test. That test-only update does not change the running job, and the current source must not be mislabeled as the byte-identical launched artifact. The exact launched revision is preserved at [`tools/history/acquire_public_archives_v007_launched.py`](../tools/history/acquire_public_archives_v007_launched.py): **20,087 bytes**, SHA-256 `6de859894c88a8458c10312f149282dd1501b5cb72a633167ca1a55be62b3b35`.

## Continuation artifacts

The v011 continuation imports the unchanged v002 base engine. Its source is [`tools/continue_acquisition.py`](../tools/continue_acquisition.py). The v012 original-context source is [`tools/acquire_original_enrichment.py`](../tools/acquire_original_enrichment.py). Each was packaged as one self-contained executable PYZ; artifact byte counts, SHA-256 digests and test counts are recorded in the [paid continuation build manifest](status/build_paid_continuation_20261016.json), [original-context manifest](status/build_original_context_20261016.json), and [incremental public manifest](status/build_public_delta_20261016.json).

The public delta uses the current six-test public archive source: SHA-256 `955a727b7074372f6b41e40f40fde42edce3d3ecfeea17d1e606794bc148d2c1`. It reuses existing immutable assets and preserves revised versions. Deployment receipts and budgets are in [the continuation record](CONTINUATION_20261016.md).


## Frontier-relevant acquisition continuation

The earlier collectors remain byte-identical. These separate sources add bounded, resumable workstreams and are gated by their own offline tests in AWS and CI. Actual launch and first runtime results are recorded in [the acquisition milestone](FRONTIER_ACQUISITION_20261016.md).

| Collector source | Bytes | SHA-256 |
| --- | ---: | --- |
| [Continued player props](../tools/continue_player_props.py) | 28,803 | `1c977b8fbaef3e16b5455d80188a7868d900d9724961341b3ad7b8d1a1cd8b09` |
| [NWS forecast continuation](../tools/acquire_weather_continuation.py) | 30,883 | `b7bb7d76c7a6941253d53c8d11f1b038c9531532ed346d2abacf9c65d6d95d3b` |
| [Official NBA availability](../tools/acquire_nba_availability.py) | 19,105 | `88013507c30b31b3c38d959f4d6999e379f000a2f31ce1efdcbe5af97a6f2ee0` |
| [Original NOAA HRRR fields](../tools/acquire_hrrr_original.py) | 42,742 | `f5fc39360dc9f09661eb1d73212c64613c564036cb8295970157578f9b1d4a79` |

The player-prop continuation imports the unchanged v002 paid engine. Availability also requires the published `tools/nba_report_seeds.json`, which the self-contained PYZ embeds. Artifact build manifests preserve the actual executable hashes and source inputs. NOAA initialization time and forecast-valid time are recorded separately from unknown historical release availability. No passing source test or successful HTTP response establishes feature eligibility.

NOAA v017 passed its 11 guards but failed before any source HTTP request because its historical CFBD cache descriptor used a current-data vintage. The [exact failed-launched source](../tools/history/acquire_hrrr_original_v017_launched.py) and [artifact manifest](status/build_noaa_hrrr_v017_20261016.json) remain preserved. V018 adds exact historical and current/reference cache-identity regression guards (13 tests total), after the existing 2024 receipt was verified read-only. It does not repeat the paid CFBD acquisition.

NOAA v018 obtained listing/index metadata but rejected forecast pairs with both total and hourly precipitation accumulations. It downloaded zero GRIB fields. Its [exact launched source](../tools/history/acquire_hrrr_original_v018_launched.py) and [build manifest](status/build_noaa_hrrr_v018_20261016.json) remain preserved. Current v019 keeps the accumulation intervals distinct and embeds the complete actual NOAA index fixture in its 15 guards; fixture tests require no external file. Source/run evidence must establish actual field acquisition separately.


## Season expansion, shooting continuation and content census

The v020 NOAA collector expands the existing forecast-field cache across the
eligible 2024 football season without changing URL/range/ETag identities. The
exact v019 pilot source is preserved at
[`tools/history/acquire_hrrr_original_v019_launched.py`](../tools/history/acquire_hrrr_original_v019_launched.py).

The v021 shooting collector bundles an isolated copy of the paid engine under
`tools/shooting_continuation_v021/src/`. Its engine change refunds a call
reservation when provider suspension cancels a queued request before HTTP send.
This keeps nonexistent requests out of usage counters. Existing collectors and
the shared engine remain unchanged. The build script preserves the executable
module layout; CI runs the bundled source's offline guards.

The v025 census reads S3 listing metadata only, separates actual content from
receipts and source indexes, and records an observation window while collectors
are active. Its count is not a unique-game or complete-season metric.

| Source | SHA-256 | Mandatory tests |
| --- | --- | ---: |
| [tools/acquire_hrrr_original.py](../tools/acquire_hrrr_original.py) | `2283df2797f85191362287b749b7c1f262810a118f0e3d712ad809d07b821d34` | 21 |
| [tools/shooting_continuation_v021/src/__main__.py](../tools/shooting_continuation_v021/src/__main__.py) | `abccf9cbbba35a1b78c09cc4d3eed9668e72f0db9fe3df3d02326fc60f263cd2` | 29 |
| [tools/shooting_continuation_v021/src/acquire_paid_data.py](../tools/shooting_continuation_v021/src/acquire_paid_data.py) | `6da4a715f239b60b00ef506857821751de8da63efc0332af5710316d3dcd326b` | Included in v021 |
| [tools/history/inventory_raw_content_v025_launched.py](../tools/history/inventory_raw_content_v025_launched.py) | `5c516796088b89454cc01e5ff5e8894051fca9b3af0ecd239889e32aa0f729bd` | 15 |

See [the expanded acquisition record](EXPANDED_DATA_COLLECTION_20261016.md) for runtime and schedule evidence. Source tests and successful storage do not approve data for model features.

The scheduled v022 American Conference collector source is [`tools/acquire_ncaa_availability.py`](../tools/acquire_ncaa_availability.py), SHA-256 `eb6932e44a70025d75fee1e204de16ee5c57d262e5e7a7e3b1720b7cb24f1916`. Its 23 mandatory tests enforce the observed UTC visit window, source permission, PNG validation, cache reuse and bounded return handling. The seed list is [`tools/ncaa_availability_seeds.json`](../tools/ncaa_availability_seeds.json). The scheduling receipt is separate from proof of a future acquisition.

The original v023 inventory source is preserved at [`tools/history/inventory_raw_content_v023_launched.py`](../tools/history/inventory_raw_content_v023_launched.py). Its completed scan conservatively omitted one existing RDS fallback; v025 matches all six supported public archive formats and explicitly excludes failure receipts. The separate listing evidence identifies the 151,579-byte standings file. No archive data was lost.

The v021 shooting execution was stopped when its initial 300 HTTP successes contained no shooting records; the final frozen audit counted 580 empty and zero nonempty responses. V024 preserves those valid-empty caches, prioritizes conference-filtered requests, and gates bulk work on positive cached 2026 and new 2024 Duke/ACC records. Its isolated engine adds a return-bundle hook for the stopped-run receipt audit. It never replaces the shared engine. The 34-test source and executable identities are recorded in [the v024 build manifest](status/build_shooting_continuation_v024_20261016.json).

- [tools/shooting_continuation_v024/src/__main__.py](../tools/shooting_continuation_v024/src/__main__.py): SHA-256 `240e7ed274bee968ae38c3650d9e7cb620d20c65532f88b1151060b7be46c5de`.
- [tools/shooting_continuation_v024/src/acquire_paid_data.py](../tools/shooting_continuation_v024/src/acquire_paid_data.py): SHA-256 `5b918e7f0a8af2d9fd5bd5db3d5935f0c102dd9ce699ad64ad3747b1cad7c009`.


## Current snapshots, original pages and tracking research

The v028 inventory classifier extends the existing measured content census to
explicit original NFL HTML and SkillCorner ACB research files. It keeps
trajectory JSONL, provider game/event JSON and identity CSV counts distinct.
The original v025 classifier remains preserved at
[`tools/history/inventory_raw_content_v025_launched.py`](../tools/history/inventory_raw_content_v025_launched.py).
The updated source SHA-256 is
`bf0bbac42357bb089464b1b91aef1fefcca11b95a022cb464e78aa0d744a4469`;
its 19 tests must pass before AWS lists archive metadata. The classifier does
not read payloads, infer event freshness, or claim NBA/NCAA tracking coverage.

[Freshness and access interpretation](DATA_FRESHNESS_AND_ACCESS_20261016.md)
separates acquisition time from source update, report/game time and permitted
tracking scope.

The current v026 snapshot collector keeps its engine isolated under
`tools/current_snapshot_v026/src/`; it does not replace historical collectors.
It distinguishes fresh retrieval times from event and quote-update timestamps,
uses a conditional S3 lease against overlap, and enforces per-run provider
budgets and a remaining-quota reserve. The v027 collector captures original
NFL HTML. The unrelated v029 collector and its ACB data were deleted at the user’s request.

| Exact source | SHA-256 | Mandatory AWS tests |
| --- | --- | ---: |
| [Current v026 entrypoint](../tools/current_snapshot_v026/src/__main__.py) | `e3ec320fa2c78609084695c5fce0678c4ac920b404b7a97ee0bca2d3b43284c5` | 30, including engine |
| [Current v026 engine](../tools/current_snapshot_v026/src/acquire_paid_data.py) | `2c2e51cc33133aa03c1f122b3b9968029cfe1e7a2584abd2a707713f20d6bb3b` | Included above |
| [Original NFL v027](../tools/history/acquire_nfl_current_v027_launched.py) | `93110c43e8222bd77b2fc92a2f0a3d9e8dc8f143d208efdf19c1dce6e079f29d` | 14 |

Build manifests retain executable hashes for retained sources. V030 reuses the exact v020 weather artifact
and existing source caches; it introduces no new collector source.

The first NFL run captured 30 roster pages because its profile-link parser
required a trailing slash. Two observed links in the archived directory omit
that slash. V031 accepts both observed forms, verifies the existing report and
30 stored roster bodies, and requests only the missing rosters. The
[exact v027 source](../tools/history/acquire_nfl_current_v027_launched.py)
remains preserved. V031 source SHA-256 is
`c92dc82354e7e4bc005585576c18d063fec41b68bbe0e673d0af703ff7c3936d`,
with 17 mandatory AWS tests. Its executable and diagnosis are recorded in
[the v031 manifest](status/build_nfl_current_v031_20261016.json) and
[archived-source diagnosis](status/nfl_current_v031_diagnosis_20261016.json).

V032 reuses the exact v024 shooting artifact (SHA-256
`261940c3acfaca4bdac975700e4cb29e37ee824fa101d7ce1bcbc671b5438e0e`)
under a new job identity with 500 statistics calls, 1,200 application seconds
and 1,500 AWS seconds. It preserves the v010 source descriptor and reuses the
958 verified successes from v024; no code rebuild or new engine version was
introduced. Its 34 AWS tests and first cache/new-capture counters are retained
in [the replay evidence](status/shooting32_tests_and_progress_20261016.json).


## Current football and scope correction, v034–v037

- v034: `sports_edge_lab_football_current_v034_20261016.pyz`, SHA-256 `ef6267e093a100d232d83dca6380109655c787cea3c64ebc213ee639cc34c736`, 35 mandatory pre-network tests. [Build manifest](status/build_v034_20261016.json).
- v035: `sports_edge_lab_nfl_recent_v035_20261016.pyz`, SHA-256 `875ceb6f3f45cd2171c44229abf1b9a5a56dc27b6aeaefa241124b70d5e03375`, 3 mandatory pre-network tests. [Build manifest](status/build_v035_20261016.json).
- v036: `sports_edge_lab_content_inventory_v036_20261016.pyz`, SHA-256 `faa2ab3d1bf38ab36bfc8134ce9984762c4e297757c0c1e1f6346bd4586b4af2`, 19 mandatory pre-network tests. [Build manifest](status/build_v036_20261016.json).
- v037: `sports_edge_lab_odds_only_v037_20261016.pyz`, SHA-256 `46318afcc310f5705267885fae59ce23f39fa924bd18fe5e21229ec3f219e9a9`, 37 mandatory pre-network tests. [Build manifest](status/build_v037_20261016.json).

V034 packages the unchanged v026 current engine and a public rendered Big Ten
seed. The seed remains in the private AWS artifact, with its SHA-256 in the
build manifest; raw player-status records are not published to Git. The source
modules and provenance are public. V035 downloads the observed current NFL
release asset and audits actual game dates. V036 excludes the entire ACB
prefix and recognizes rendered availability separately from original PDFs.
The earlier v028 inventory source is preserved byte-for-byte under
`tools/history/inventory_raw_content_v028_launched.py`.
V037 preserves the original v011 and v002 modules in an isolated package and
adds a rate-limited odds-only wrapper, predecessor terminal-state guard,
successful-index reuse and fail-closed quota checks. CBBD is not requested.
