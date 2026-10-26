# A technical review of Sports Edge Lab

[Project](../README.md) · [Current evidence](CURRENT_EVIDENCE.md) · [Model card](MODEL_CARD_CURRENT.md)

The strongest way to evaluate this project is to follow one result from its assumptions to its implementation and failure cases.

## Five minutes

1. Read the matched current-season table and its qualification limits in the [current evidence](CURRENT_EVIDENCE.md).
2. Inspect the [system design](SYSTEM_DESIGN.md): data validity, model validity and decision validity are separate contracts.
3. Run the [public example](../examples/review_lab/README.md). It fits two small synthetic models, evaluates a held-out chronological cohort, writes a verified artifact, and refuses invalid reuse.
4. Open the [executed notebook](../notebooks/engineering_review.ipynb) and [evidence explorer](review/index.html). The page is an offline file, not a hosted deployment.
5. Inspect the [publication boundary](PUBLICATION_BOUNDARY.md) before interpreting reproducibility claims.

For an integration-failure example, follow the [provenance case study](CASE_STUDY_PROVENANCE.md) and its executable synthetic notebook section. It shows how individual checks passed while a missing relationship between two verified parents still stopped the owner run before fitting.

## For an ML engineering review

Follow `validate_rows`, `fit_synthetic`, `predict_synthetic`, `score_matched` and `write_run` in the [small public core](../examples/review_lab/core.py). The [tests](../examples/review_lab/tests/test_core.py) deliberately exercise future information, duplicate identities, equal-size but different cohorts, unavailable models, corrupt artifacts and zero-fit reentry.

Then inspect the broader, preserved [published source inventory](PROJECT_SCOPE.md), including native fitting and interruption/recovery implementations. The compact example is an entry point, not a claim that the full private system consists of a small logistic model.

## For a data-science review

Ask whether each comparison uses the same events, targets and decision horizon; whether the reference was selected after outcomes; whether uncertainty supports the conclusion; and whether the strongest retained model actually improved. The latest combined representation failed both historical qualification gates. Read the [joint-evidence case study](CASE_STUDY_JOINT_EVIDENCE.md) and run the factorial evaluator to inspect how predictive complementarity is separated from superiority over MARKET and retained references.

## For a systems review

Examine how raw source revisions, canonical identity, information clocks, model provenance, immutable issue time, price freshness and settlement rules constrain a decision. V120 produced current research forecasts while admitting zero actions. This is an observable boundary, not a claim of profitable deployment.

## Questions this project cannot answer from public assets alone

Exact retraining of the private football models requires licensed/raw source snapshots, active feature transformations and fitted assets that are intentionally withheld. No external commercial forecasting ranking, prospective profitable wagering record or independent real-data reproduction is claimed.

## Inspect the newest capability

Read [the score-distribution case study](CASE_STUDY_SCORE_DISTRIBUTIONS.md), then compare its conditional-win and joint-target tables in the [current evidence](CURRENT_EVIDENCE.md). The generic [distribution evaluator](../examples/review_lab/distribution.py) demonstrates normalization, exact support, log-space stability, ties, mixtures and contract settlement using invented inputs. Its tests are independent of the private football data and model recipes.
