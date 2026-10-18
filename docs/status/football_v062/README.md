# V062 — completed objective comparison and partial source repair

**Actual outcome, October 18, 2026:** 16 LightGBM L1 fits completed; **one of four development qualifications passed, zero exposed qualifications passed, and zero models were promoted**. Accepted NFL V047 and NCAAF V048R1 references remain unchanged. The valid execution brings the verified minimum to **386 real fits; 21 accepted / 12 failed / two stopped execution runs; 11 accepted / one failed modeling runs**.

The comparison changed only the objective from L2 to L1, holding V060 inputs, LightGBM 4.7.0, all seeds 6001 and other settings fixed. All 16 fits completed 200 rounds. Three exact cached references were reused without refitting. NFL uses 16 fields; FBS-versus-FBS uses 60, with declared historical opponent context. The candidate produces conditional medians, not expected scores, win probabilities or joint distributions.

## Point accuracy: MAE, lower is better

| Track | Task | Phase | Games | Accepted | Matched linear | L2 LightGBM | L1 LightGBM |
| --- | --- | --- | --- | --- | --- | --- | --- |
| NFL | margin | 2022–2023 development | 569 | 9.728097 | 9.728097 | 9.957677 | 9.824034 |
| NFL | margin | 2024–2025 exposed | 570 | 10.198375 | 10.198375 | 10.155027 | 10.118940 |
| NFL | margin | 2026 monitor | 80 | 9.898554 | 9.898554 | 9.958589 | 9.738635 |
| NFL | total | 2022–2023 development | 569 | 10.881346 | 10.881346 | 10.864426 | 10.715334 |
| NFL | total | 2024–2025 exposed | 570 | 10.332147 | 10.332147 | 10.416418 | 10.436805 |
| NFL | total | 2026 monitor | 80 | 11.980695 | 11.980695 | 12.389521 | 12.223035 |
| NCAAF | margin | 2022–2023 development | 1568 | 12.821899 | 12.829299 | 13.327795 | 13.227576 |
| NCAAF | margin | 2024–2025 exposed | 1606 | 12.819829 | 12.868194 | 13.193786 | 13.174680 |
| NCAAF | margin | 2026 monitor | 336 | 12.916027 | 12.924678 | 13.692153 | 13.747658 |
| NCAAF | total | 2022–2023 development | 1568 | 13.101301 | 13.113400 | 13.300096 | 13.294700 |
| NCAAF | total | 2024–2025 exposed | 1606 | 13.093919 | 13.094981 | 13.117648 | 13.057386 |
| NCAAF | total | 2026 monitor | 336 | 12.577538 | 12.610560 | 12.762425 | 12.705872 |

NFL totals are the positive development signal: accepted MAE **10.881346 → 10.715334**, a 1.53% reduction; paired difference **−0.166012 points**, 95% interval **[−0.335385, −0.000286]**. L1 also improves over matched L2 by 1.37%. The upper interval versus accepted is barely below zero, and all these periods have been examined before.

The result fails on exposed 2024–2025 games: **10.332147 → 10.436805**, a 1.01% worsening, interval **[−0.059323, +0.273938]**. NFL margin's exposed 0.78% improvement is below the 1% gate, and it failed development. FBS totals improve only 0.28% exposed; FBS margin worsens. No exposed movement rescues failed qualification. The NFL 2026 sample has six week blocks, so uncertainty is withheld. No untouched test, prospective success or market edge is claimed.

RMSE, bias, median signed/absolute errors, p90 absolute error, season and subgroup diagnostics, and residual interval coverage/width/scores all recompute. Brier/log loss need probabilities and CRPS needs a distribution; these are not new metrics for this point-only arm. [All aggregate metrics and gates](metrics.json).

## Source outcome

The finite 17-source queue captured **16 sources** and validated **13 current official HTML games**, producing **26 team rows / 262 regulation drives**. The audit recomputed 285 retained DOM-row hashes and counts, with 23 explicit bookkeeping/zero-play rows excluded. These are secondary drive representations, not complete PBP or tracking coverage.

Four selected drive gaps remain:

| Game | Actual outcome |
| --- | --- |
| LSU–Mississippi State | PDF downloaded and text extracted; exact identity parser rejected its quarter-score header. |
| Rutgers–Maryland | HTML downloaded; a drive clock/duration conflict remains quarantined. |
| Temple–UConn | PDF was not fetched after its host's robots request returned 403. |
| Boise State–San Diego State | PDF downloaded and text extracted; exact identity parser rejected its quarter-score header. |

There are **zero verified PDF-text-only identities**; downloaded PDF text is not validated coverage. Prior historical secondary validation stays **12/14**, while this current 15-game queue is **13/15**. Original ESPN source gaps remain source-specific.

The ledger records **33 public attempts**, 30 HTTP 200 responses, two robots 404 allowances and one robots 403 stop; **28,605,855 bytes**, zero inflight reservations. ESPN and the newly denied host remain stopped; CFBD, CBBD and odds usage was zero. No provider limit was bypassed.

The new current features have conservative availability between **October 18, 16:02 and 17:34 UTC**; none was eligible at the run's approximately 00:16 UTC completion. A later clock alone does not insert them into frozen models: source compatibility and the declared feature contract still apply. Publication time remains unknown. [Acquisition counts and limitations](acquisition_completion.json).

## Verification and next work

The independent audit passed **8,187 numerical/source checks**. Runtime records show **238/238 tests** and four separate synthetic smoke fits. ZIP CRC, exact extraction and all present hashes match; 98 compact omissions were not independently fetched from AWS. [Summary](summary.json) · [Integrity summary](integrity_summary.json).

V063 is an engineering continuation: cached parser repair, accepted-model serving parity, an immutable prospective shadow forecast/abstention ledger, and executed evidence. It plans **zero new research fits and zero provider calls**. No V063 result is claimed here. Source captures remain outside frozen benchmarks until eligibility and compatibility are established.

[Earlier preparation contract](preparation.json) and [preparation tests](public_checks.json) are preserved as dated pre-execution evidence. [Model card](../../MODEL_CARD.md) · [Data readiness](../../DATA_READINESS.md).
