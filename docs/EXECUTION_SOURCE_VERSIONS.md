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

The running `sports-edge-lab-public-archive-20261016-v007` job launched the revision with five automatic tests. The current `tools/acquire_public_archives.py` adds a sixth mocked download/resume/hash-rejection test. That test-only update does not change the running job, and the current source must not be mislabeled as the byte-identical launched artifact. The exact launched revision is preserved at [`tools/history/acquire_public_archives_v007_launched.py`](../tools/history/acquire_public_archives_v007_launched.py): **20,087 bytes**, SHA-256 `6de859894c88a8458c10312f149282dd1501b5cb72a633167ca1a55be62b3b35`.
