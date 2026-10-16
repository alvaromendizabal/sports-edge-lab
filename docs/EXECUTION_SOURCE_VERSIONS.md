# Execution source versions

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
