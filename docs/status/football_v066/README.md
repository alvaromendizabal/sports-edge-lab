# V066 — FBS source adjudication and an operational fallback

**Prepared and verified; owner execution has not occurred.** No V066 fit, forecast or model-quality result is counted complete. The package passed **582 offline tests** and a full mocked interruption/resume/reentry check: 47 immutable files preserved, zero refits, six executed notebook cells, and one unique ZIP per attempt. Accepted reentry reused its ZIP. [Preparation receipt](preparation.json).

V065 successfully acquired a current independent drive source, but 81 primary-reference games disagree and 66 lack accepted comparisons. The 49 missing strict-FBS comparisons are quarantined, not undownloaded. The current FBS60 model depends on that unresolved primary-drive contract. V066 tests whether a model using only existing team-score/schedule history can reduce this dependency without an unacceptable accuracy loss.

## Four workstreams

1. **Adjudicate cached drive clocks and periods.** Retain source values, counterexamples and quarantine. Arithmetic-derived candidates are diagnostic research evidence, not authoritative repairs or permission to insert data into model inputs.
2. **Reconstruct FBS16 features.** Verify exact historical feature parity and released-past ordering. Assess current readiness independently of the drive feed while preserving the separate canonical-schedule freshness requirement. Future targets are FBS versus FBS; previously declared opponent context stays explicit.
3. **Fit a fixed linear comparison on AWS.** Twelve fits maximum: win, margin and total at four chronological origins. Reuse strict-FBS60 control predictions rather than refitting them. No parameter search or additional model family.
4. **Report coverage and predictive risk.** Produce same-game primary/secondary metrics, season-week uncertainty, readiness, original-forecast accounting and an executed notebook/return. No new live forecasts or automatic promotion.

## Frozen comparison

Train through 2021 for 2022 development; through 2022 for 2023 development; through 2023 for exposed 2024–2025 evaluation; through 2025 for exposed 2026 monitoring. Scaling is trained inside each fold. The comparator is V060's strict-FBS-trained, unpromoted 60-feature linear control.

Operational noninferiority allows at most **1% primary-loss degradation** on both pooled development and exposed evaluation, including a paired blocked upper bound at most 1% with sufficient support. Secondary guards remain frozen in the final runtime contract. Lock the development decision first; exposed results cannot rescue failed development. A pass is an unpromoted candidate for a separately frozen prospective trial, not an accuracy breakthrough or betting approval.

## Bounds and evidence status

Seven exact owned inputs total 7,511,389 bytes. Maximum 12 real fit attempts; zero baseline refits, provider/public/CFBD/CBBD requests, odds credits or live forecasts. Two numerical threads, 12 GiB memory, 2 GiB output and a one-hour application safety ceiling. Model/data artifacts and their private pins are not redistributed here.

The current verified tally remains **24 accepted / 12 failed / two stopped executions and 386 real fits**. Preparation and synthetic fixtures do not change that tally. [Actual V065 result](../football_v065/README.md) · [Feature strategy](../../FEATURE_STRATEGY.md) · [Model card](../../MODEL_CARD.md).
