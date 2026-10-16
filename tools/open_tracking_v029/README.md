# Historical out-of-scope acquisition — disabled project use

ACB is outside the five Sports Edge Lab tracks. Do not run this collector for further project downloads or use its data in project coverage/modeling. Source and receipts are retained to reproduce the earlier scope mistake.

# SkillCorner ACB open tracking pilot v029

This collector acquires the official SkillCorner open basketball sample into the Sports Edge Lab research namespace. It is **Spanish Liga ACB 2025–2026**, separate from the NFL/NBA/NCAAF/NCAAM/NCAAW production tracks.

The inspected `data/matches.json` lists ten games between **2025-10-11 19:00 UTC and 2026-05-29 18:30 UTC**. The pinned official repository documents 25-frame-per-second player and ball positions, game metadata, and provider-derived dynamic event annotations. No video files are included. Tracking contains both detected and extrapolated positions; provider error and detection indicators must be retained. Roughly half of frames can contain no player positions during dead time.

## Exact acquisition scope

- Repository: https://github.com/SkillCorner/opendata-basketball
- Pinned commit: `4bbed2e35e8fdd2cf083e8c8b280b3e5381a2c66`.
- **32 data files / 394,736,881 bytes:** ten original gzip-compressed tracking files, ten event JSONs, ten game/roster JSONs, `matches.json`, and `player_id_aliases.csv`.
- **28 evidence files / 101,954 bytes:** LICENSE, README and the complete observed documentation directory.
- Total planned upstream payload: **394,838,835 bytes**. Robots probes are additional small requests.
- Season aggregate CSVs are excluded. Their broader 293-game scope is not acquired by this pilot.

`source_manifest.json` retains the observed source paths, exact commit-pinned GitHub content URLs, Git blob identities, ten Git LFS SHA-256 identities and sizes, discovery time, license fingerprint, and league labels. A research range canary returned HTTP 206 for an observed tracking asset, with gzip magic and the expected total compressed length. This proves an endpoint works; it does not count as an AWS-acquired game.

## License and ownership

SkillCorner publishes the repository with its 2026 MIT license and a README expressly presenting the data as open data. We infer that the repository-wide license covers its included data; the standard license text itself says software and associated documentation rather than separately defining data. No separate restrictive dataset license was observed. The pinned license is preserved in the artifact, return ZIP, and source evidence. SkillCorner attribution is retained.

The trajectories are SkillCorner's collected data, and its event annotations are provider-derived. The user owns this independent acquisition/validation workflow, not authorship of the upstream observations. No entitlement to SkillCorner's commercial catalog or redistribution of paid data is inferred. No messages are sent by this collector.

## Execution contract

One self-contained PYZ; sixteen automatic tests run in AWS before acquisition. Local syntax compilation is not an AWS test-pass claim. Tests cover manifest and exact URL scope, immutable content identities, rejecting LFS pointers as tracking, gzip validation, source stop responses, streaming bounds, league identity, cache reuse, and exactly one uniquely named return ZIP per run.

Defaults: **1,200 application seconds, 1,500 AWS maximum seconds, 600,000,000 HTTP bytes, 100 HTTP requests, at most ten games.** Collection is sequential and streams each asset to disk. It validates exact source size and Git identity or LFS SHA-256, then reads tracking through gzip EOF to verify CRC and frame structure. It stops on the first failed source/schema/hash gate and records pending paths for a cache-preserving resume.

Both GitHub content hosts returned 404 for robots during research. Runtime checks them again; a 404/410 means no robots directives are available, while authentication denial, forbidden responses and rate limits stop the source. Redirects and unlisted URLs are rejected. Any published robots rules and crawl delay are honored.

Raw files are stored at `shared/raw/skillcorner-acb-research/objects/{sha256}` with `.jsonl.gz`, `.json` or `.csv` suffixes. `url-index/*.json` receipts are excluded from raw counts. Documentation and robots evidence use `shared/acquisition/open-tracking/evidence/objects/`; run reports, progress and the unique return ZIP use `shared/acquisition/open-tracking/{run_id}/`.

The progress report records download/reuse counts, raw bytes, completed tracking-game IDs, elapsed time and an interval compute estimate at the supplied hourly rate. Costs exclude provisioning intervals, S3 requests/storage and other services. Captured-at, provider processing timestamps and historical game dates remain separate. Every receipt has `point_in_time_approved=false`.

## What this enables

The sample can support independently implemented player/ball tracking ingestion, uncertainty-aware spatial features, event-to-frame alignment, possession modeling prototypes and cross-game validation. Ten ACB games cannot establish NBA or NCAA performance, league-wide coverage, broad generalization, or a commercial betting advantage. It also cannot reproduce the provider's complete season aggregates.

## Primary references

- Repository and dataset description: https://github.com/SkillCorner/opendata-basketball
- License: https://github.com/SkillCorner/opendata-basketball/blob/main/LICENSE
- Tracking schema: https://github.com/SkillCorner/opendata-basketball/blob/main/docs/data_dictionary/tracking_data.md
- Primer: https://github.com/SkillCorner/opendata-basketball/blob/main/docs/PRIMER.md
- Known issues: https://github.com/SkillCorner/opendata-basketball/blob/main/docs/KNOWN_ISSUES.md

## Verified AWS acquisition

Run `20261016T195258Z-d0e4041c3c` passed all 16 tests and completed the pinned
sample at **2026-10-16 19:54:51 UTC**. It stored **32 raw files / 394,736,881
bytes**, covering all ten selected games, with zero errors and zero pending
assets. The separate 28 evidence files bring HTTP source bodies to 394,838,835
bytes. No video or additional league coverage was acquired. The report retains
`point_in_time_approved=false`; publication-time validation remains separate.

