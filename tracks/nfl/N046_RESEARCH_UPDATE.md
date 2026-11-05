# NFL research update · N046 owner run

**Later source update, November 5 at 23:28 UTC:** a separately verified official NFL capture now contains **340 listed rows across all 30 Week 9 team tables**, including Buffalo 18 and Minnesota 9. It is later than the N046 issues and **was not an input to those forecasts**. The earlier 295-row/29-team owner snapshot remains unchanged. [Inspect the new source census](injury_source_update_n047.json). This is source coverage, not proof of complete roster health or new model performance.

The fourth, designation-based forecast lane now exists as actual timestamped research output. The run issued **348 target rows for 29 games across four lanes**, fitted **three new native models plus nine stacks**, reported **4,384 restored fitted identities**, and did not refit protected originals. The run reported no first error. Whole-pipeline research acceptance remains false; there are no final-hour-qualified wagering cards.

[Open the dashboard](review.html#latest-coverage) · [Inspect every model’s evidence](review.html#model-evidence-registry) · [Current model card](CURRENT_MODEL_CARD.md)

## What the four lanes mean

| Lane | Actual issue, UTC · November 5 | Current-season training games | Calibration | Evidence status |
|---|---|---:|---|---|
| Retained calibrated heads | 22:23:55 | 120 | Existing calibration | Early issued research; older base snapshot |
| Injury-contribution shadow | 22:24:36 | 120 | Raw | Early issued research; older base snapshot |
| Current rolling | 22:25:44 | 121 | Raw | Early issued research; refreshed base snapshot |
| New designation rolling | 22:28:10 | 121 | Raw | Early issued research; three newly fitted heads |

Each lane contains winner, margin and total outputs for the same 29 games. All outcomes are blank at issue. These streams have **zero scored outcomes in this snapshot**; no historical reconstruction score is assigned to their prospective performance. Selected cards are rounded public outputs, not a way to reproduce proprietary models. [Inspect their exact public clocks](current_issues_n046.json).

The designation lane’s base features were about 50 seconds old at issue. Its selected winner, margin and total models contain 308, 386 and 467 fields. The broader design can contain up to 497 fields; this does not mean every selected head uses all 497.

## Injuries: acquired, admitted and still unknown

Current formal reports contain **295 listed rows for 29 of 30 Week 9 team slots**. Minnesota is now present; Buffalo remains unknown. Unknown report coverage is never coded as healthy.

The additional **32-field designation block has a different coverage boundary**: listed-status evidence supports both teams in JAX–BAL, with seven rows and latest publication November 4 at 22:05:46 UTC. The other 28 forecast games are unknown for that block. Their separate pre-existing injury fields are not erased. Announced starting quarterback, replacement quality, full depth and reserve roles are still unverified features.

The new designation issue projected JAX **68.9%**, JAX by **6.1**, and a **45.7** total. It is raw early research, not proof that an injury adjustment improved accuracy and not a final-hour wager recommendation.

## Performance and promotion

The selected designation recipes retain their separately evaluated N045 reconstruction record. Recipe selection used eligible pre-2024 evidence. The 2024–25 seasons are development-exposed retrospective evaluation; 2026 rankings are descriptive monitoring.

| Selected annual reconstruction | 2024–25 | Current evaluated cohort |
|---|---:|---:|
| Winner accuracy | 385 / 569 · 67.66% | 78 / 119 · 65.55% |
| Winner log loss / Brier | 0.625236 / 0.217420 | 0.663311 / 0.235871 |
| Margin MAE | 10.004398 · 570 games | 10.066063 · 120 games |
| Total MAE | 10.298938 · 570 games | 11.394803 · 120 games |

These are **annual reconstruction metrics, not the results of the new 22:28 forward model body**. Weekly and event origins remain separate in the interactive study table. [Exact origin/season metrics](designation_metrics_n045.json).

On the exact 119-game non-tie T1 Kalshi cohort, the selected annual reconstruction has 78 correct against Kalshi’s 76, but its log loss is worse: **0.663311 versus 0.644579**. Brier is also worse: **0.235871 versus 0.225107**. All nine paired whole-week intervals across annual/event/weekly accuracy, log loss and Brier cross zero. This does not establish a durable or prospective advantage.

The retained probability leaders remain separate: N026 event mean log loss 0.617703 on 2024–25, and N022 feedback log loss 0.629080 / Brier 0.219521 with 77/119 correct on current descriptive monitoring. There is no supported full-cohort NFL log loss near 0.45 or 0.46.

Adverse findings are preserved: the selected designation annual head worsened current log loss and margin MAE against its exact same-root injury control. More data or more features does not guarantee better predictions. The public model registry makes verified, pending and unavailable evidence explicit for every selectable forecast version.

## Providers and prediction cutoffs

- **Week 9:** all 15 games have current observed winner, margin and total references from each of DraftKings, Kalshi and Polymarket. DraftKings includes one documented schedule-recovery event; 13 of 14 Week 10 events also have current DraftKings references.
- **Completed current-season games:** all 121 have latest genuinely recorded pregame Kalshi and Polymarket winner/margin/total references. These retrospectively acquired references are not proof of original possession or executable fills.
- **Historical gaps:** latest-pregame DraftKings references are not included in this public historical export. Older-season exchange gaps and smaller timed matched-evaluation cohorts remain explicit.

T2 means two hours before kickoff; T1 means one hour. They fix an evaluation boundary, not a collection ban. A later genuine pregame reference can be displayed in the latest-before-kickoff lane without rewriting earlier model inputs or timed scores. Provider quote time remains unknown wherever only observation time is supported. Exchange thresholds are conditions, not expected score margins or totals.

## Winner, points and spread-cover readiness

Winner probabilities, point margin and point total are issued. **A calibrated probability of beating an exact spread is not yet verified for these streams.** A projected margin above a line is insufficient to establish expected value. Fees, payout conventions, settlement and an appropriate uncertainty model are required. No personal bets or actual profit are inferred from research output.

The next separately registered spread-cover work is not completed research in this return. Public demonstrations and local tests cannot substitute for owner model acceptance.

## Operations and reproducibility

The run took **2,635.184 seconds (43 minutes 55 seconds)** through verified publication. It reused compatible work and observed shared-instance resource limits; no globally-fastest claim is supported. A later implementation may improve compatible reuse, but an unrun optimization cannot be credited as measured speedup.

Public artifacts contain sanitized derived evidence, exact clock distinctions, generic contracts and deterministic rendering. Production transforms, raw licensed sources and model bodies remain private. All older public evidence stays unchanged. Run the credential-free checks from the NFL README.
