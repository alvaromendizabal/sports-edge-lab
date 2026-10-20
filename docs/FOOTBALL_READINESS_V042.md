# Football readiness v042 — verified October 16, 2026

V042 completed all five selected stages, with zero failed stages. AWS reports `Completed`, processing start `2026-10-16T22:46:11.415Z` and end `2026-10-16T22:47:18.089Z`. Application outcome is `completed_with_gaps`; completion does not approve a model training set. All 59 tests passed locally and again on AWS before runtime credentials/network.

| Result | Verified scope |
| --- | --- |
| Public NGS player joins | 692/692 current 2026 regular-season rows: 163 passing, 369 receiving, 160 rushing. All join exactly by week, team and GSIS ID after verified source team aliases. |
| NFL snaps | Initial 6,075/7,463 same-week/team PFR joins; 1,388 unresolved. V045 separately tests a fresh published player crosswalk. |
| College availability joins | Initial 2,306/2,403 rows match exact normalized team/name/jersey with a unique CFBD player ID. V045 adds structural quarantine; use its valid outputs. |
| Current NFL games | 80 completed games and 80 games in cached PBP, 14,031 rows, zero missing completed game IDs. Source release hash unchanged. |
| Current NCAAF games | Fresh 888-row FBS schedule; zero newly completed games since the previous capture. Previously saved 124-game Weeks 5–7 play/drive/box coverage retained. |
| NFL official availability | Fresh Week 6 injury report: 374 extracted rows, zero rejected rows; observed 22:47:04 UTC. Original publication time unavailable. |

The run made one CFBD subscription-quota request, one public NFL schedule request and two NFL robots/injury requests. No odds credits and no CBBD requests were used. Existing cached NGS/PBP/rosters/snaps and college rosters were reused. No subscription, role, bucket or license changed.

Information-time fields use actual input retrieval times conservatively. Identity evidence acquired later cannot be backdated to an older source observation. Availability rows store kickoff and distinguish observation before versus after kickoff; original publication timestamps stay null where unverified. Missing status is not interpreted as available. Historical point-in-time approval and model-ready flags remain false. Historical odds bookmaker timestamps, kickoff revisions, unresolved identities and source completeness still need an explicit modeling audit.

Raw and derived inputs are private in the canonical S3 bucket. The one unique return ZIP is `shared/acquisition/football-readiness/20261016T224648Z-7ab37da393/sports_edge_lab_football_readiness_return_20261016T224648Z-7ab37da393.zip` (8,646 bytes, SHA-256 `0eddb370ad28669375b2e2f0676085fb7a5de43ddb305e4b7ce23a79999c5178`). Its CRC, report and selected-stage counts were verified. [Receipts, tests, source and terminal metadata](status/football_readiness_v042/) preserve the exact result.

## Existing schedule guard v043

The old six-hour current collector still included CBBD calls despite the provider pause. V043 disables CBBD both in its work planner and its direct capture path. All 32 mocked tests passed before upload. The existing schedule `sports-edge-lab-current-6h-20261017-v026` was updated and read back at 22:48:33 UTC to point to the tested v043 artifact. All prior budgets, lease behavior, six-hour cadence and November 16 end date remain unchanged; no IAM permissions were added. This patch did not launch a new ProcessingJob.

[V043 source and reproduction](../tools/current_snapshot_v043/) and [schedule evidence](../tools/current_snapshot_v043/README.md). [Weekend continuation playbook](FOOTBALL_WEEKEND_REFRESH_20261016.md).
