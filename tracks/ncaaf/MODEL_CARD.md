# NCAA FBS · V024 research model card

**Dated evidence: November 3, 2026. Status: historical research complete; no model promotion and no genuine live forecasts.**

[Interactive evidence](../../docs/fbs/index.html) · [Full-precision public aggregate](../../docs/fbs/V024_AGGREGATE_2026-11-03.json) · [Verification record](../../docs/fbs/V024_REVIEW_2026-11-03.md) · [Executed notebook](../../notebooks/fbs_branch_review.ipynb)

## Intended use

This card supports review of an NCAA FBS forecasting research pipeline, its historical model comparisons, and the engineering needed to preserve trustworthy results. The public repository supplies aggregate outcomes and generic reproducible contracts. It does not serve individual predictions, support automated wagers, or establish a profitable strategy.

The study models the home-team winner, home-minus-away final margin, and final combined points. It evaluates registered private model variants on a declared FBS-target population. FCS opponents can contribute context; “FBS-target” must not be read as a universal pure-FBS-versus-FBS population. The exact evaluated populations are committed separately for each season.

## Training, selection and evaluation

| Stage | Role | Evidence |
|---|---|---|
| 2021–2023 | Chronological recipe selection and interval calibration | 432 new inner-selection fits |
| 2024 | Exposed historical evaluation | 918 matched games, seven published fixed comparisons |
| 2025 | Exposed historical evaluation | 934 matched games, seven published fixed comparisons |
| Frozen model states | Research output retained for later admissible inference | Three fresh states |
| 2026 | Current source diagnostics; excluded from recipe selection | Zero rolling fits and zero genuine issued forecasts |

The owner run completed **723 fresh fits: 432 inner selection + 288 historical evaluation + 3 frozen states**. It reused zero fit commitments and recorded zero failed units. The historical evaluation work includes registered arms beyond the seven selected/fixed aggregate panels published here. Each fit is a separate estimator invocation, not an observation or an inference. Research elapsed time was **1,485.157569 seconds**. This is run-local work, not the all-project lifetime fit count. [Source: dated aggregate](../../docs/fbs/V024_AGGREGATE_2026-11-03.json).

The public names identify comparison panels. They do not reveal active feature definitions, fitted parameters, model checkpoints, blend construction, or selection formulas. The existing [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) applies. A complete private rerun requires the private source and model artifacts; the public example does not claim to perform it.

## Primary observed result

| Exposed season | Games | Previous study V023 log loss | Registered challenger V024 log loss | Change, challenger minus previous |
|---|---:|---:|---:|---:|
| 2024 | 918 | 0.5264508762 | 0.5320835801 | +0.0056327039 |
| 2025 | 934 | 0.4887974041 | 0.4980247955 | +0.0092273914 |

Lower log loss is better. V024 is worse on both panels. Its winner calibration error is lower, and individual point metrics move in both directions; these diagnostics do not establish an overall improvement. The study does **not** promote the challenger. All seven fixed panels and the winner, margin and total metrics remain available in the [explorer](../../docs/fbs/index.html). No matched current market benchmark belongs to this particular study, so it cannot establish an advantage over market prices.

The 2024 and 2025 seasons have been repeatedly examined. They are permanently exposed historical diagnostics, not untouched holdouts. Selecting a new recipe from these displayed results would introduce further selection bias. Differences in displayed scores are descriptive; no statistical significance or causal claim is attached to them.

## Metric definitions and comparison integrity

Winner metrics are natural-log binary log loss, Brier score, accuracy at a 0.5 threshold, correct count, ten-bin expected calibration error, and Matthews correlation coefficient. Margin and total metrics are mean absolute error, root mean squared error, and signed bias (prediction minus observed points). Lower error is better; higher accuracy and correlation are better; bias is judged by proximity to zero.

Independent local verification of the private owner evidence established identical event identities, ordered teams, and labels across all seven panels for each season. All 21 per-game prediction columns agreed with the paired export, and **all 12 displayed aggregate metrics matched independent recomputation within 10⁻¹²**. The [aggregate JSON](../../docs/fbs/V024_AGGREGATE_2026-11-03.json) records season commitments and verification scope. Hash commitments identify the checked populations; they do not make the private records publicly reproducible or prove timing on their own.

The generic [public scorer](../../examples/fbs_contracts/matched_cohort.py) demonstrates exact identity/label/kickoff checks on two invented events. It rejects equal-size mismatched cohorts instead of taking an intersection. It checks declared issue times but does not authenticate real historical possession. Its scoring logic is distinct from a native private feature producer. Its tests establish software behavior, not sports prediction quality.

## Interval diagnostics

The nominal interval level is 90%. Calibration uses pre-2024 outcomes. In 2024, both margin and total intervals covered 819 of 918 games (89.22%). In 2025, margin covered 849 of 934 (90.90%) and total covered 845 of 934 (90.47%). Mean width was 55.99 margin points and 52.41 total points. [Source: interval aggregate](../../docs/fbs/V024_AGGREGATE_2026-11-03.json).

These are descriptive diagnostics. Reusing selection data, dependent outcomes, population shifts and repeated examination prevent a formal distribution-free coverage guarantee. Coverage near a nominal level is insufficient to authorize current inference or a bet.

## Current-use limitations and abstention

The required current raw feature values do not yet have a verified executable reconstruction path. Matching metadata, ancestor hashes and observation clocks does not prove that submitted numeric values were produced by the required transformation. The current issue path therefore remains blocked. This run completed zero rolling refits and zero genuine forecasts. There is no public live betting or serving interface.

Observed source availability is also bounded. At the run’s acquisition clock, the strict next seven days contained 63 games, while an extended schedule contained 68. The 2,168 quote rows comprise 2,039 game-market rows and 129 player-prop rows. Of the game-market rows, 2,006 map and 33 are quarantined; 62 of 63 observed events have unique mappings. Zero rows were certified as actual 60- or 120-minute historical captures. These counts establish acquisition scope, not a qualified market comparison or permission to buy data. [Correction details](../../docs/fbs/V024_REVIEW_2026-11-03.md#source-scope-corrections).

## Reproducibility and rights

Three levels are explicit:

1. **Public aggregate validation:** check schema, metric/count consistency, fit accounting, cohort commitments, publication fields and generated-page freshness.
2. **Public invented execution:** run exact-cohort scoring, chronology guards, three small synthetic fits and unchanged reentry that adds zero fits. Run the notebook in a real kernel and inspect persisted HTML outputs.
3. **Private research verification:** verify the authenticated return, independent completion and the individual source/prediction records. The public repository reports the verification outcome and byte commitments; it does not distribute those records.

Run instructions and exact tests are in the [FBS example](../../examples/fbs_contracts/README.md). The notebook and browser checks execute in FBS-specific CI. No new software or data license is granted by this card. Original-source terms and the [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) remain applicable. Earlier evidence is retained in the [FBS history](../../docs/fbs/README.md); different cohorts must not be pooled as if they were one experiment.
