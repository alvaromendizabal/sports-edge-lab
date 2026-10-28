# Model card — B003 basketball research

Publication date: October 27, 2026, Pacific time. [Project](../README.md) · [Study](BASKETBALL_FOUNDATION.md) · [Results](BASKETBALL_RESULTS.md) · [B003 aggregate](evidence/2026-10-27-basketball-b003.json) · [Preserved B002 aggregate](evidence/2026-10-27-basketball-b002.json)

## Intended use and current status

Separate NBA, NCAA men's and NCAA women's historical prediction research and prospective monitoring. B002 established the first functioning real modeling pipeline after the preserved B001 ingestion failure. B003 completed controlled opponent-adjustment experiments, broader cached MARKET comparisons and exact predecessor reuse. No qualified MARKET advantage, executable betting policy, profitable wagering record or continuous production service is established.

The public evidence contains aggregate scores, cohort digests and engineering contracts. Individual records, active feature transforms, fitted weights and private infrastructure paths remain excluded. The public example fits no model, and its invented probabilities are labeled separately from the actual owner aggregates.

## Targets and evaluated model families

| Family | Probability architecture | Predictor count | B003 evidence |
|---|---|---:|---|
| Historical prior | Historical outcome baseline | Baseline | Evaluated |
| Elo and Margin Elo | Chronological rating baselines | Baseline | Evaluated |
| Strength | Regularized logistic with chronological calibration | 15 | NBA full-cohort selection |
| Style | Regularized logistic with chronological calibration | 25 | Retained control |
| Combined | Regularized logistic with chronological calibration | 53 | Retained control; both T−24h college selections |
| LightGBM, XGBoost, CatBoost | Native boosted classifiers with chronological calibration | 53 | Retained T−60 controls |
| Strength plus opponent adjustment | Regularized logistic with chronological calibration | 25 | New controlled T−60 arm |
| Rich combined | Regularized logistic with chronological calibration | 63 | New T−60 arm; both college historical selections |
| Rich LightGBM | Native boosted classifier with chronological calibration | 63 | New controlled T−60 arm |
| Learned MARKET-only | Declared regularized MARKET classifier | 3 | Blocked by earlier training support |
| Integrated basketball plus MARKET | Declared regularized integrated classifier | 56 | Blocked by earlier training support |

The winner target is the completed game's home-win outcome. Separate shared Ridge regressors predict margin and total; home and away points are derived coherently. A classifier label does not name the point estimator. Impossible issued scores are rejected rather than clipped. Point estimates do not constitute calibrated intervals, a joint score distribution or cover/over probabilities.

The ten added predictors use historically available opponent state under the reconstruction policy. This is not a full dynamic Bayesian hierarchy. PyTorch, TensorFlow, learned player graphs and temporal player encoders did not train basketball models in B003. A discoverable library or graph-derived statistic is not evidence of a trained architecture.

## Chronology, selection and uncertainty

Training ends in 2024 for validation in 2025 and in 2025 for validation in 2026. Later chronological training partitions supply calibration; future validation outcomes never fit preprocessing or calibration. Historical results select probability and point recipes separately. Final selected recipes fit eligible history through 2026.

The season ending 2027 is excluded from feature choice, tuning, calibration, ensembling, ranking and champion promotion. Already released current outcomes may update pregame team histories under the frozen policy. Retrospective current-season monitoring remains distinct from genuinely preissued predictions.

All completed historical tracks use an explicit 24-hour reconstructed statistical-release assumption because original publication clocks are unavailable. A frozen 48-hour input-delay sensitivity is separate. T−60 and T−24h are separate experiments. All earlier B002 control probabilities, point estimates, outcomes and cutoffs are unchanged in the B003 comparison audit.

Both validation seasons are development-exposed after selection. Paired seven-calendar-day block intervals are descriptive; repeated-team and longer-range dependence may remain. No multiplicity adjustment, untouched validation or causal interpretation of feature gains is claimed.

## Results, weaknesses and MARKET qualification

Pooled T−60 selected log loss is 0.607468 for NBA strength, 0.525415 for men's rich logistic and 0.457143 for women's rich logistic. The college rich models improve both historical folds relative to the 53-predictor controls, but their pooled fixed-bin calibration errors increase. Women's 2025 correct-pick count decreases despite better proper scores. NBA's added features do not improve the previous probability selection.

The [generated results](BASKETBALL_RESULTS.md) retain each season, baseline, game count, proper score, accuracy, calibration error and separate point diagnostic. They also show all equivalent-game MARKET comparisons. Full-cohort scores cannot be compared with a market result from different games.

After cached recovery, T−60 MARKET validation counts are 9/16 NBA games, 0/1,143 men's games and 149/143 women's games in 2025/2026. Eligible earlier training counts remain 6/15, 0/0 and 0/149. Learned MARKET-only and integrated models do not pass the existing support requirements. The women's rich model loses to MARKET in 2025 and improves in 2026, with both paired intervals including zero. No league qualifies a MARKET advantage.

NBA's selected point model has total bias about +1.84 and +2.66 points in the two seasons. Better 2025 bias did not solve the 2026 weakness. Men’s selected rich point head underpredicts totals by about two points. These failures motivate a historical bias/uncertainty study; current-season outcomes cannot tune its correction.

## Data risks and unimplemented inputs

Historical NBA advanced-box features lose support because of inconsistent rebound definitions. College membership/opponent status remains a research proxy. Women's early box coverage is incomplete. Source denominators describe provider-covered eligible schedules, not certified complete league universes.

No verified player-level modeling joins or historically timed injury, projected-minute, roster continuity, coaching or replacement-value inputs are established in B003. Current-season roster change can therefore invalidate the apparent confidence of a stale team-history forecast. Unknown original publication clocks, revisions, league drift, missing data and dependent games remain additional risks.

## Immutable forecasts and operational scope

B003 preserves and checks all 110 B002-issued rows: all pending, no settled outcomes at the snapshot. It issues 110 later versions across the same 61 distinct upcoming games. All are early outlooks before declared locks, with no qualified current MARKET price. Earlier probabilities remain immutable. Every issue is rechecked after inference for source cutoff, model availability and pregame timing.

There are 60 new real estimator units, 156 imported predecessor units and 232 cumulative unique basketball units. The 216 current-release manifests do not imply 216 new fits. Exact input, label, feature-order, dependency and numerical-method compatibility plus byte hashes govern reuse. Failure and resource-stop paths preserve checkpoints and produce diagnostics.

Cumulative active work remains charged across releases; the returned floor is 3,571.02 seconds of the 4,500-second work ceiling. A continuously deployed service, service-level objective, automated order execution and realized P&L remain undemonstrated.

Kalshi, Polymarket US and international Polymarket have separate settlement and execution evidence requirements. No venue has admitted historical exchange observations or current executable quotes in B003. Displayed page prices are research observations, not fills. Basketball bankroll is unset and profit is null rather than zero realized profit.

## Next decision

[B004 subsequently executed and stopped at the public-request ceiling](BASKETBALL_B004_EXECUTION.md). Six new score-correction units completed, but no probability or point challenger passed promotion. The selected B003 probability recipes and separate point heads remain unchanged. The execution note reports rejected challengers and empirical intervals without presenting them as approved forecast uncertainty.
