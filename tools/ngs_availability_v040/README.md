# Public NGS and availability v040

Offline tests: `python tools/ngs_availability_v040/src/__main__.py --self-test` (29 tests, no AWS credentials/source HTTP).

The launched immutable zipapp contains `__main__.py`, `nfl_current.py`, `sources.json` and private `availability_seeds.json`. The source tree here deliberately excludes rendered player-status data. Each seed needs conference, source_url, observed_at, capture_method, source_publication_time and extracted_markdown. The frozen input manifest and exact deployed artifact hash are in docs/status/ngs_availability_v040_*. Do not execute the source directly for acquisition or rebuild with invented/current inputs while claiming the deployed hash. Retrieve the preserved artifact from the canonical private S3 code prefix to reproduce this exact run. Tests mock the seed input and do not need private raw data.

No secrets or paid provider API calls. NGS release integrity, source pacing, denial stops, immutable hash cache, nullable statuses, strict headers, coverage counts and one unique return bundle are enforced. ACC missing headers intentionally yield raw_only, not guessed columns. See docs/NGS_AVAILABILITY_V040.md for actual terminal outcome and remaining gaps.
