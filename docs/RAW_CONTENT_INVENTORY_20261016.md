# Raw-content inventory v025

The collector measures current S3 object counts and stored bytes under the
canonical `tracks/` and `shared/raw/` prefixes. It does not read raw payloads,
request indexes, or receipts. All 15 embedded classifier and aggregation tests
run in AWS before the first listing request.

Explicitly counted content includes the six supported public-archive formats (Parquet, CSV, CSV.GZ, JSON, JSON.GZ, RDS),
content-addressed paid API responses, provider canaries, official NBA report
PDFs, American Conference report images, NWS point/forecast JSON, and original
NOAA GRIB fields. NOAA listing XML and GRIB indexes are source metadata and are
excluded. Return bundles, code, audit files, request indexes, discovery evidence,
and the duplicate legacy archive are also excluded.

Unknown raw formats are recorded separately with a small example list instead
of silently inflating the content total. Check that field before presenting a
new inventory as a full comparable census. NWS point metadata is included with
forecast responses and is explicitly labeled in the report.

The scan has a start/end observation window and per-prefix windows. Active
collectors can add objects while pagination proceeds, so the result is not a
transactionally frozen point-in-time snapshot. Counts are stored files, not
unique games, API captures, training rows, complete seasons, or approved model
features. Public source families and revisions can overlap. Content-addressed
paid responses deduplicate within their provider/sport namespace.

The run permits 1,000 listing pages and 240 application seconds, with a 300-second
SageMaker stop. It emits progress and cost estimates, a compact JSON report, and
one unique return ZIP. The receipt records whether listing completed. No source
API credits are used and no archive content is changed.

The first v023 scan completed but its conservative classifier omitted one existing 151,579-byte RDS standings fallback. The corrected v025 whitelist matches the downloader's six supported formats and excludes paid failure receipts explicitly. The original source, report and small family-listing evidence remain preserved. This was a counting-classification correction; no data was lost or reacquired.
