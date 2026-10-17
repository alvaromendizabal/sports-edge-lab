# V059 — FBS scope, cached regulation repair and dynamic joint-score states

This bounded addendum supersedes only V2's dated immediate V057 instructions. All master safeguards remain in force. The current scope is NFL and FBS football. New college model training and evaluation use **FBS-versus-FBS games only**. Existing FCS context stays archived; it is not reacquired or newly modeled.

## Verified predecessor

V058 completed all **36 fits**: 12 NFL histogram-boosting fits and 24 NFL/college MLP fits. Its 66 runtime tests passed; execution took 82.178 seconds. An independent audit recomputed 23,053 numerical checks. All nine candidate/task qualifications failed, with no model promotion. Cached accepted NFL V047 and college V048R1 predictions remain the references.

The verified minimum ledger is **17 accepted / 12 failed / two stopped executions**. The modeling subset is **seven accepted / one failed**, with **246 completed real fits**. A valid negative result counts as an accepted execution.

## Four workstreams

1. **Validate scope and cached inputs.** Verify exactly 16 assets totaling 10,668,204 bytes. Preserve frozen canonical identities and labels. Filter college training and evaluation using both season-specific FBS flags. The frozen table contains 7,895 completed FBS-versus-FBS games; the current canonical schedule contains 7,898. The three later finals are inventory updates only and remain excluded from the matched model comparison.
2. **Repair regulation-drive validation.** Recover eight selected FBS games from seven existing NCAA annual caches. Separate explicitly identified, noncontradictory overtime rows before applying the unchanged regulation-validation rules. Preserve all 33 excluded overtime rows and input hashes; produce 16 secondary team rows. The FBS gap count becomes **22 → 14 only after runtime verification**. The remaining cases are six absent alternate-source games, five unknown positive-play outcomes and three current finals. Six mixed FBS/FCS context gaps remain outside the new target scope. Repairs are separate from score-state model inputs and do not establish predictive improvement.
3. **Compare fixed joint-score models.** Fit static and dynamic Gaussian team-state models: two tracks × two arms × four chronological partitions = **16 joint-fit attempts**. Each fit emits home/away means, covariance, win probability conditional on an approximate non-tie event, margin and total. These are not 48 independent task fits. Both arms share priors, likelihood and forward-only released observations; the dynamic arm adds fixed team-state time evolution. No parameter sweep or baseline refit is permitted. All new college labels and state observations are FBS-versus-FBS; the cached accepted reference was trained on the previous mixed cohort, which must be disclosed. Compare identical target games against both accepted predictions and the static control. Fixed settings are heuristic; do not claim to reproduce a paper's estimated posterior.
4. **Return complete evidence.** Produce exact paired scorecards, proper scores, calibration, temporal uncertainty, Gaussian distribution diagnostics, readiness findings and an executed notebook/HTML report. Emit one unique compact return ZIP. There are no live forecasts, provider calls or automatic promotions.

## Information and evaluation contracts

NFL decision time is kickoff minus 24 hours; FBS decision time is kickoff minus one hour. Result availability at kickoff plus 24 hours is an explicit assumption. Source publication remains null when unknown. Require release strictly before decision, construct predictions before updates and never use backward smoothing.

Previously released evaluation outcomes may update both arms under the declared prequential protocol. **Static means zero process drift, not frozen observations.** All cohorts are already exposed, including 2026 monitoring. Nominal market horizons differ; the history actually used must precede the quote. No executable market advantage or ROI is claimed.

The primary win metric is log loss; point targets use MAE. Report Brier, AUC, calibration, accuracy, RMSE, bias, season errors and diagnostic slices as appropriate. Dynamic must improve primary loss by at least **1% against both accepted and static references** in pooled 2022–2023 development and exposed 2024–2025 evaluation. The paired blocked 95% loss-difference upper bound must be below zero. Neither development year may regress by more than 1%; win Brier must not regress, and point RMSE may regress by at most 1%. Exposed results cannot rescue failed development. Passing permits only a frozen prospective trial, not accepted-model replacement.

Gaussian CRPS, marginal NLL, 80%/95% coverage, width, interval score, joint-score NLL and negative-score mass evaluate the candidate's declared continuous distribution. Do not fabricate a full-distribution comparison for baselines that provide only point predictions. Proper Gaussian priors prevent an improper posterior, but offense/defense components are not causal and are not uniquely identified by the likelihood alone. Parameter uncertainty is conditional on fixed hyperparameters; future coverage is not guaranteed.

## Bounded owner execution

Real-data fits run in the existing AWS CPU app. Local preparation is limited to synthetic fits and cached-data/schema/repair inspection.

| Resource | Contract |
| --- | --- |
| Real fitting | Exactly 16 maximum joint-fit attempts; no baseline refits |
| Runtime smoke fitting | Four tiny synthetic fits |
| Parallelism | One process; two numerical threads |
| Memory / output | 12 GiB process-tree RSS; 2 GiB output ceiling |
| Inputs | 12 MB cap; 16 pinned assets totaling 10,668,204 bytes |
| Time | 60-minute work safety ceiling plus 90 seconds for final upload |
| Sports-provider use | Zero odds, CFBD, CBBD or other provider requests |

No job creation, IAM changes, subscriptions, licenses, outreach or new acquisition. ACB remains excluded. Use only the existing canonical AWS account, bucket and region.

Integrity, offline tests and notebook/Plotly checks precede credentials or network access. Preserve durable fit reservations, checkpoints, fingerprints, heartbeats, idempotent accepted re-entry, the overlap lock, classified failure ZIPs and nonzero failure exits. The compute estimate uses an assumed **$0.484/hour**, not a verified invoice; startup/idle, storage and S3 requests are separate. Stop the Studio app after retrieving the return when no further work is needed.

## Method basis

[Glickman and Stern (1998)](https://www.glicko.net/research/nfl.pdf) motivates evolving team strength and uncertainty. This joint offense/defense Gaussian filter is an adaptation, not the paper's score-difference/MCMC implementation. [Tabular tree/neural benchmarks](https://arxiv.org/abs/2207.08815) support testing inductive bias rather than assuming neural superiority. Project-specific negative evidence governs the next choice.
