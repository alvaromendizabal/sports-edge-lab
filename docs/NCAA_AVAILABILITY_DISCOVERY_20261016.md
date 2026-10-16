# NCAA basketball availability acquisition

Verified October 16, 2026. This source is a sparse American Conference sample, not national NCAA coverage.

## Ready acquisition

The v022 collector contains eight observed, published American Conference daily report pages: six men's and two women's pages, January–March 2026. It requests only the exact report image `src` links present on these pages. It does not enumerate dates or construct image filenames. The official pages publish their PNG reports through `/common/controls/image_handler.aspx`; direct `/images/` paths are rejected by the collector.

The original women's March 14 image canary returned HTTP 200, `image/png`, 915,856 bytes, SHA-256 `7b11425980711279cf4a57e17d57605d94e2c42c80a0eaea68e0c6077dc04018`. This was source research in the development environment, not an AWS acquisition result, and must not be added to AWS inventory totals.

The source robots file permits the requested report-page and image-handler paths, specifies a five-second crawl delay, and requests `Visit-time: 0100-0645`. We honor that optional historical directive. Its original specification defines the clock as UT/GMT. The collector enforces 01:00 inclusive to 06:45 exclusive UTC before any source HTTP, including robots retrieval; it refreshes robots within that interval and checks again after pacing. Outside the interval it writes a deferred report and unique return ZIP without source HTTP or an idle wait.

Planned one-time start: **October 17, 2026, 01:05 UTC / October 16, 2026, 6:05 p.m. Pacific**. The schedule's actual creation and AWS execution status must be verified separately; this document does not assert either happened.

The artifact has 23 automatic tests, including source allowlists, direct-image rejection, robots rules, request limits, PNG chunk/CRC validation, capture/cache reuse, one return ZIP per run, visit-window boundaries, multiple windows, malformed windows, and a delay crossing the closing boundary. Tests execute in AWS before acquisition; local syntax compilation alone is not a test-pass claim.

Bounds: 600 application seconds, 900 AWS seconds, 200 HTTP calls, 100,000,000 HTTP bytes; one CPU processing instance. No paid provider requests. Runtime stops the source on 401/403/429 and never follows redirects or substitutes a different host.

## Stored evidence and limits

- Raw original images: `tracks/ncaam/raw/american-availability/objects/{sha256}.png.gz` and the corresponding `ncaaw` prefix.
- URL receipts: each track's `raw/american-availability/url-index/`; exclude them from raw-content counts.
- HTML and robots evidence: `shared/acquisition/ncaa-availability/evidence/objects/{sha256}.txt.gz`; exclude from report-image totals.
- Run progress, report, and exactly one unique return ZIP: `shared/acquisition/ncaa-availability/{run_id}/`.

Hash validation is required before reusing a cached image. Every original image retains its source page, source-page hash, capture time, upstream headers, and track. Retrieval today does not establish historical publication time. OCR, report-vintage verification, timezone resolution, player/game identity joins and prediction-cutoff checks remain required; `point_in_time_approved` is false throughout.

## Gaps explicitly retained

The NCAA announced its national 2026 men's and women's tournament reporting pilot. Its actual public `PAReports` hub presents a robot-verification page in observed access. The collector does not circumvent that challenge, contact HD Intelligence, or infer an entitlement.

Conference USA publishes official men's and women's tournament hubs with nine report links each. Its robots file disallows `/documents/`. These 18 observed links remain a blocked discovery inventory; the collector does not substitute public S3 copies to avoid that rule. This is independent conference coverage and does not replace the national NCAA tournament pilot.

The American Conference sample is neither a complete conference season nor a full availability history. It supplies original documents for a later extraction and timestamp-validation stage. No injury reason or medical diagnosis is inferred from an availability label.

## Primary references

- NCAA national pilot announcement: https://www.ncaa.org/news/media-center-ncaa-announces-implementation-of-player-availability-reporting-for-2026-di-mens-and-womens-basketball-championships/
- NCAA reporting process: https://www.ncaa.org/news/media-center-ncaa-releases-penalty-and-process-details-for-march-madness-player-availability-reports/
- NCAA public hub (observed robot-verification wall): https://www.ncaa.com/PAReports
- American women's March 14 report page: https://theamerican.org/sports/2026/3/14/wbb_pa_031426.aspx
- American men's March 1 report page: https://theamerican.org/sports/2026/3/1/mbb_pa_030126.aspx
- American robots: https://theamerican.org/robots.txt
- Conference USA men's report hub: https://conferenceusa.com/sports/2025/12/16/MBB_1216251132.aspx
- Conference USA women's report hub: https://conferenceusa.com/sports/2026/1/2/WBBAR.aspx
- Conference USA robots: https://conferenceusa.com/robots.txt
- Original Visit-time proposal and UTC convention: https://www.conman.org/people/spc/robots2.html
