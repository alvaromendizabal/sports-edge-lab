# FBS V091 launch failure and V092 preparation review

[Open the standalone report](index.html) · [Public aggregate evidence](data/status.json) · [Preserved V089 comparison source review](https://github.com/alvaromendizabal/sports-edge-lab/pull/386)

This small report separates the new V091 launch failure, the last verified V090 owner return, the retained V089 scientific results, and V092 preparation. It contains no duplicate candidate roster or game array. Those remain in their dated comparison report. The page runs offline from one HTML file and makes no runtime HTTP requests.

## Verified V091 startup failures

The owner reported one V091 command that passed its checksum check and returned immediately to the shell without visible output. The pasted transcript did not capture an exit code. The exact packaged entry function was reproduced locally with isolated temporary paths and nonroot identity; source integrity and the supervisor validators were unchanged, and child launching was forbidden. It returned 2 with empty stdout/stderr, zero child-launch calls and a saved `SUPERVISOR_RUN_ID_INVALID` receipt. No AWS calls or research fits occurred in that diagnostic.

The cause was release identity drift: V091 generated its own invocation suffix, but two inherited supervisor validators still accepted only V090. The parent caught the startup error, saved a failure record, and printed nothing. Earlier archive integrity checks and nonresearch self-tests did not cover the normal supervised launch. Their passing results do not establish a usable owner launch.

Live inspection subsequently found two distinct owner startup-failure receipts, at November 17, 6:19:09 p.m. and 6:20:36 p.m. Pacific. Both record the same identity error, no research child and no pointer advancement. One pasted launch report therefore corresponds to an audit with two verified V091 failed attempts and one defect. Together with V090, the explicitly scoped tally is three failed attempts and zero successful attempts. No all-time total or operator exit code is invented. V092 preparation centralizes release identity and adds a packaged supervised-startup check. The frozen replacement is 48,552,301 bytes. Five exact-package regression tests pass; its packaged self-test verifies 2,821 active members and three isolated supervised children with observed exits 0, 2 and 130. Separately, 88 compact-return/checkpoint checks pass. The final canonical was placed and checksum-verified in the existing owner environment at November 17, 6:42 p.m. Pacific. Its native packaged self-test passed the same three isolated child-exit cases and left the actual-return pointer unchanged. The metadata review ZIP is measured separately in the private delivery handoff, outside this public snapshot. V091's launch failure does not advance the verified-return pointer or alter V089 scientific results.

## Last verified owner return

The V090 owner attempt failed before registered model work. The authenticated failure is `KeyError: checked_at_utc`: a price-cache fallback expected that timestamp field, while the shipped cache used `checked_at` with `cache_age_seconds`. Its saved counters record zero base fits, calibrators, forecasts and scored rows; the fit-count completeness flag remains false after the early failure. The attempt has one operational failure and zero delivery failures. Its integrity-verified return contains 18,480,886,907 bytes in 35 ordered parts. Return finalization took 1,537.183 seconds and is separate from the 0.943 seconds measured before finalization.

The full-host end-to-end cost estimate is USD 1.1208455 through its saved measurement, not a cloud invoice. Time after that measurement is outside the estimate. A delivered failure archive does not become a successful scientific execution.

## Retained scientific comparison

The previous V089 tranche completed 90 model jobs, with 90 base fits and 90 calibrators. Its joint comparison retained 397 policy/target identities on the same 919 / 934 / 752 completed-game populations. Those are the observed 2024 / 2025 validation and previously exposed 2026 test populations. Independent official schedule completeness remains unproved, and exact historical champion certification is separate.

The latest attempt's zero reuse counter does not mean earlier scientific evidence was deleted. Previous durable artifacts and their verification history remain the basis of continuation. No metric is recalculated or selected by this public page.

## Prepared delivery and worker evidence

The registered next campaign remains the finite T120 pregame tranche and contains 936 model jobs and 84 fixed equal-weight blend policies. The display distinguishes its 624 validation and 312 frozen-test jobs, its 12-worker target and 24-worker ceiling, and its still-pending measured optimizer throughput. Native threads, memory, physical storage and the USD 200 compute guard constrain admission. An unlimited wall setting does not waive the cost guard.

The return audit found 134,098 of 134,110 payloads already present in V089, carrying 29,410,254,353 decoded bytes. Separately, 7,439,043,130 decoded bytes were duplicated within the same return. These quantities overlap and must not be added together. A metadata-catalog encoding of the exact existing set measured 12,276,949 gzip bytes in an engineering projection; that is not an executed owner return or a forecast of future output size.

The compact design references authenticated retained artifacts instead of repeatedly including them in every report. A small report is not an independent copy of all research data. Its durable dependencies must remain accessible and pass verification before reuse. Scientific work has no aggregate size cap; the existing 512 MiB limit applies to each transport part.

A changed completed-game population remains an explicit blocker until a safe frozen-inference extension covers all retained contenders. The replacement resumes the same registered campaign; the existing campaign does not add that extension or establish full V13 completion.

The earlier V091 executable measured 48,384,220 bytes and its separate prepared review ZIP measured 64,270 bytes. Those historical archive-integrity and self-test records remain visible with an explicit qualification: they missed the normal supervised-launch defect. They are not V092 acceptance evidence. The V092 canonical executable has been prepared and verified. This public snapshot reports its exact measured size. The metadata review ZIP measurement belongs to the separate private delivery handoff and is deliberately outside this snapshot. The native placement receipt is pinned as aggregate verification evidence; private host addresses and paths remain excluded. Preparation adds zero owner research executions, scientific fits or source retrievals. The actual return pointer advances only after integrity checks and preserves partial versus complete scientific status.

## Publication and reproduction

This is a draft source review. Website deployment, model promotion and original forecast issuance remain separate. The public export excludes private cloud locations, continuation bodies, owner executables, raw licensed arrays, exact active recipes, weights and unissued numerical forecasts. It does not modify another sport's report or the older FBS draft PR.

The deterministic generator validates the public aggregate fields, contradictory success/science claims, unknown/private fields, transport arithmetic, dependency verification, cost guards and prior test exposure. The browser check verifies both source and standalone variants on desktop/mobile, decimal/binary size controls, exact keyboard-triggered downloads, malformed-evidence rejection and zero external requests.

- `python examples/fbs_contracts/v091/build_review.py --check`
- `python tests/test_fbs_v091_public.py`
- `node tests/fbs_v091_browser.test.cjs`

Passing public engineering checks do not establish scientific acceptance or 24-core utilization for a future owner run.

