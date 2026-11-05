# Injury inputs, trained models and promotion

[Open the dashboard](review.html#injury-model-readiness) · [Current issue clocks](INJURY_REFRESH_N040.md) · [Retained model card](CURRENT_MODEL_CARD.md)

Injury data has been trained and tested. The completed N037 study contains **2,304 historical native cells**, across eight estimator families, eight rooted feature blocks, three targets, six evaluation seasons, and paired matched-base/injury representations. Selected rolling fits, stacks, calibration and forward heads are separately counted. This is a declared experiment, not a claim to exhaust all possible feature combinations.

## What the selected issue actually uses

| Target | Selected model family | Feature count | Direct injury fields | Current status |
|---|---|---:|---|---|
| Winner | ExtraTrees | 249 | No: the selected matched base remains in use | Early research issue; not a newly promoted champion |
| Home margin | ExtraTrees | 324 | Yes, including unknown-report flags | Early research issue; source coverage remains partial |
| Total points | ExtraTrees | 417 | Yes, including unknown-report flags | Early research issue; source coverage remains partial |

The research tested injury variants for winner prediction, too. Selecting a baseline for the winner target does not mean that injury variants were never tested. The published issue must identify the model actually selected; it cannot imply a QB injury was included in that winner probability.

A weekly report and a verified starter are different inputs. Listed participation or game-status rows do not establish the full roster, expected starting quarterback, backup quality, injured-reserve status or replacement value. A player missing from the report is **unknown**, not healthy. Current official news is useful context, but displaying a link does not establish model ingestion.

## The historical coverage limit

A completed model grid is not proof of complete injury inputs. The retained study admitted qualified report information for 284 of 285 games in 2024, **zero of 285 games in 2025**, and **zero of 120 games in the retained 2026 cohort**. Those later-season injury inputs remain explicitly unknown. Their model metrics cannot establish the benefit of rich injury information in those seasons.

Of the 75 declared injury channels, 51 concern report status; 24 starter, depth and usage channels remain dormant because historical source availability and identity have not been established. No exact private feature transforms are disclosed here. The completed study does not imply that every legacy model version has been retrained with the missing source blocks.

Current reports improve new issues prospectively; they cannot be inserted into past games as if they were observed then. Historical repair and compatible model evaluation must be completed before making broader injury-gain or promotion claims.

## Retained selected-model evaluation

These results were computed in N037 and reused by N040. They are not the realized performance of the new early issue cards. The winner target is the selected matched base; only point targets use direct injury fields. See [the exact sanitized metrics](injury_selected_metrics_n037.json), including AUC, calibration, RMSE, bias and interval coverage.

| Season | Winner log loss / correct | Margin MAE (games) | Total MAE (games) |
|---|---|---|---|
| 2024 | 0.622382 / 192 of 285 | 10.0238 (285) | 9.9432 (285) |
| 2025 | 0.636437 / 188 of 284 | 10.0546 (285) | 10.6424 (285) |
| 2026 | 0.661069 / 74 of 119 | 9.9509 (120) | 11.4768 (120) |

The winner uses frozen pre-2024 calibration. On the current cohort, calibration changes log loss from 0.653945 to 0.661069 and accuracy from 76 to 74 correct. This negative finding remains visible; recalibrating on these outcomes to improve the displayed score would contaminate evaluation. Earlier fitted identities and historical metrics remain unchanged.

The 2024/2025 evaluations are development-exposed and 2026 is descriptive monitoring. The source has 121 finals, but this historical model cohort lacks the genuine feature vector for Chicago–Seattle. Its separately issued original forecast loss remains visible elsewhere in the dashboard. No row is silently invented to fill that gap.

## Promotion is a separate decision

1. **Source eligibility:** establish event/player identity and genuine publication or first-observation time before the registered cutoff. Keep acquisition time separate. Quarantine unresolved names and historical timing gaps.
2. **Matched experiments:** compare injury candidates with their exact baseline on common events, target definitions and available information. Retain negative findings and uncertainty.
3. **Recipe selection:** choose transforms, hyperparameters, blends, calibration and acceptance thresholds from eligible pre-2024 out-of-fold evidence. The 2024/2025 seasons remain development-exposed retrospective evaluation; 2026 rankings remain descriptive monitoring.
4. **New fit and issue:** fit an approved recipe on eligible earlier outcomes, bind the model and input identities, and record the actual issue time before kickoff. A new source capture is not a new trained model.
5. **Readiness and monitoring:** check current source coverage, model qualification, uncertainty and target-specific operational guards. Preserve original frozen monitoring and separate rolling/issued performance. No new champion or wagering recommendation is implied by these early cards.

More report rows can improve coverage without improving predictions. A model may remain overconfident, miss replacement-player quality, or use stale non-injury features. A scientifically useful negative result stays in the record. Repeatedly choosing whichever model won the current season would contaminate that monitoring period.

The current pipeline has no completed full-pipeline promotion acceptance and no final-hour-qualified card. The next source/model extension must be executed and audited before its work or gains can be claimed. The public repository provides generic contracts, selected rounded issued cards and sanitized evidence; private source arrays, weights and active transforms remain private.
