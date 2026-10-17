# V059 — FBS repair and dynamic team-state handoff

**Prepared and locally tested; no V059 real-data model fit has run.** The owner executes the private PYZ on the existing AWS app. No new jobs or provider calls are launched by this handoff.

The next package repairs eight cached FBS regulation games, preserves 33 excluded overtime rows, and restricts new college training/evaluation to FBS-versus-FBS. It then compares static and dynamic Gaussian joint-score states against matched accepted forecasts. Sixteen joint fits each emit win, margin and total outputs; they are not 48 separate fits.

The frozen model cohort has 7,895 completed FBS games. The current canonical schedule has 7,898; three later finals remain separate from matched historical evaluation. Accepted college predictions were historically trained on the earlier mixed FBS/opponent cohort; their FBS-only scores are not an FBS-only retrain.

[Milestone and current prompt addendum](MILESTONE.md) · [Handoff receipt](handoff.json) · [Local data preparation](local_data_preparation.json) · [Acceptance checks](acceptance.json) · [State mathematics](state_math_review.json) · [Market timing exclusions](market_timing_review.json) · [Public scientific core](../../../modeling/football_v059/README.md)

Local fixtures and mocked AWS checks do not establish private runtime execution. Native Gaussian uncertainty is conditional on fixed heuristic settings, permits negative scores, and is evaluated rather than assumed calibrated. No production promotion or economic edge is established.
