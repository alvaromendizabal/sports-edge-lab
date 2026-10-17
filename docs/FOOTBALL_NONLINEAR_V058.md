# V058 — controlled nonlinear and neural football benchmark

This run-specific addendum advances the immediate V057 milestone in the embedded master prompt. Its 36-fit / 10 MB limits replace V057's 24-fit / 250 MB limits for this handoff only. Preservation, owner-executed AWS work, finite queues, no provider requests and honest evaluation requirements remain. No prior job is relaunched.

## Verified starting state

V057 completed 24/24 fits on October 17, 2026 at 21:35:36 UTC in 87.089 seconds, with estimated compute of $0.011709 at an assumed $0.484/hour. All three tasks failed qualification. Exposed total MAE improved 1.2345% versus accepted V047 but only 0.1300% beyond the continuity control, with confidence intervals crossing zero. No baseline was replaced.

The validated tally is 16 accepted / 12 failed / 2 stopped executions; the modeling subset is 6 accepted / 1 failed, with 210 completed real fits. Synthetic preparation is excluded.

PBP was not restricted to this season: 498,285 NFL records were audited for 2016–2026, while annual NFL raw files exist back to 1999. Stored college ESPN annual files for 2004–2026 contain 3,233,114 records by Parquet metadata. Sources overlap and include administrative rows. They are not independent labeled games or a complete validated feature table. Accepted modeling still uses 2016–2026. Frozen college features cover 9,086 completed games; the newer canonical inventory of 9,089 includes three later finals.

Earlier V047/V048R1 runs completed 24 confirmed histogram-gradient-boosting fits; they did not replace the accepted linear models. Identical college 60-feature boosting is not repeated here. The first fixed neural benchmark is the substantive new capability.

## Four workstreams

1. **Audit:** reuse 17 exact pinned feature/prediction objects, totaling 6,681,024 bytes. Validate schema, latest-used information times and all 24 cached baseline partitions. No PBP reaggregation, source acquisition or baseline retraining.
2. **Development:** NFL HGB/MLP on 36 unchanged V057 QB features; NCAAF MLP on 60 unchanged V048R1 features. Three targets and 2022/2023 forward folds.
3. **Evaluation:** exposed 2024–2025 and monitoring 2026 scorecards, matched references and market cohorts, probability/point/interval metrics and paired season-week uncertainty.
4. **Return:** model cards, readiness, frozen future-evaluation eligibility, an executed notebook/standalone HTML, hashed checkpoints and one unique compact return ZIP.

## Fixed models and controls

NFL HGB: 100 iterations, 15 leaves, depth 5, minimum leaf size 30, learning rate 0.05, L2 = 5 and 63 bins.

NFL/NCAAF MLP: input → 32 tanh → 16 tanh → one output; Adam learning rate 0.001, alpha 0.01, batch size 64, seed 5801 and exactly 200 training epochs. Input scaling and regression-target scaling are fitted on training rows only. No random validation holdout, early stopping, sweep, feature reselection or evaluation-driven reseeding. Numerical threads = 2.

The MLP has 1,729 NFL / 2,497 college parameters. It is a small tabular neural baseline, not a transformer, play-sequence model, causal QB model or licensed tracking model. One seed is exploratory. Training progress emits every 20 epochs plus start/end.

The 36 real fits are NFL 2 families × 3 targets × 4 partitions plus college 1 family × 3 targets × 4 partitions. Runtime also performs exactly four tiny synthetic smoke fits, including the full 200-epoch regression path. NFL compares against accepted V047 and cached same-feature V057 QB linear predictions. College accepted V048R1 is also its same-feature control. These controls separate nonlinear capacity from a feature change.

## Information and evaluation contract

Training ends 2021 → 2022, 2022 → 2023, 2023 → 2024–2025 and 2025 → 2026. Preprocessing uses only training rows. NFL nominal decision is 24 hours before kickoff; college is one hour. Used historical release times must strictly precede the decision. Original publication remains null. The 24-hour label-release assumption does not prove historical source availability.

All exposed cohorts have been viewed before. No fresh untouched test, automatic promotion or profitable strategy is claimed. A candidate must improve primary loss by at least 1% over both accepted and same-feature linear references on pooled development and exposed evaluation, have negative paired 95% upper bounds, no development-year regression above 1%, no win Brier regression and point RMSE regression at most 1%. Development is locked before exposed evaluation. Passing only nominates a frozen prospective test. Nine task/family hypotheses are exploratory; bootstrap intervals do not correct repeated model selection.

Markets: NFL quotes are later than the 24-hour cutoff; college matched quotes precede the nominal one-hour cutoff. Actual consumed college history precedes all matched quotes by at least 83.93 hours on these pins. Verify that relation, preserve quote counts, and do not claim a controlled matched-horizon market edge or executable ROI.

Win scores: log loss, Brier, AUC, accuracy, reliability/ECE and probability bias. Point scores: MAE, RMSE, median/90th-percentile absolute error and signed bias. Empirical 80%/90% intervals report coverage, width and interval score, calibrated using earlier forward-development residuals. Fewer than eight season-week blocks means unavailable bootstrap bounds. No coverage guarantee is claimed.

## Remaining data work and limits

This benchmark does not fill 28 college drive gaps, nine availability identity rows, three new finals' features, historical announcement timestamps, upcoming-starter confirmation or tracking/video entitlement. Cached PBP and drive-derived representations do not contain every potentially useful player/team signal. ACB is excluded and CBBD remains stopped. Zero odds credits, CFBD/CBBD requests, purchases, outreach, IAM changes or new jobs/schedules. Current collectors are not duplicated.

## Execution contract

The owner executes in the existing sports-edge-lab-dev CPU environment, canonical us-west-2 account and existing private bucket. Full offline tests, source integrity and notebook gates precede AWS credentials and project-data reads. Checkpoints preserve successful fits; every attempted fit counts. Missing or ambiguous durable budget evidence fails closed. Accepted re-entry returns the same ZIP, with no new fit or tally increment.

Expected duration is 3–10 minutes, about $0.03–$0.08 at an assumed $0.484/hour; actual billing rate is unverified. Safety limits: 60-minute application ceiling plus 90 seconds for final upload, 12 GiB process-tree RSS, 2 GiB run disk and 10 MB input. The estimate excludes idle/startup, storage and S3. Process exit does not stop Studio billing. Successful execution is not improved prediction.

## Primary method references

- https://arxiv.org/abs/2207.08815
- https://arxiv.org/abs/2106.11959
- https://scikit-learn.org/1.7/modules/generated/sklearn.neural_network.MLPClassifier.html
- https://scikit-learn.org/1.7/modules/generated/sklearn.ensemble.HistGradientBoostingClassifier.html
