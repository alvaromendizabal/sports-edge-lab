# Frozen point-loss objective adapter (V062)

Public scientific method code, prepared for owner execution. V062 has not produced actual football results. The private orchestration and data are not published here.

This adapter changes only LightGBM `regression_l2` to `regression_l1` relative to the frozen V060 control, preserving version4.7.0, all five seeds6001, tree settings,200-round ceiling and two CPU threads. It targets conditional median margin/total, not expected scores, win probabilities or a joint scoring distribution. No fitting on evaluation rows, tuning, early stopping or provider calls occurs here.

The23 offline tests include exactly four tiny synthetic fits, independent control configuration verification, repeatability, serialization and rejection of malformed inputs/version drift. These tests establish implementation behavior, not actual football predictive quality or the private AWS workflow.

The private prepared experiment makes16 fits on frozen NFL16/FBS60 features and compares exact same-game accepted, matched-linear and matched-L2 forecasts. Development decisions are locked before already-exposed evaluation. Better exposed performance cannot rescue failed development, and no automatic promotion is allowed.

References: [LightGBM4.7.0 objectives](https://lightgbm.readthedocs.io/en/v4.7.0/Parameters.html), [Gneiting, Making and Evaluating Point Forecasts](https://arxiv.org/abs/0912.0902).


## Actual V062 outcome

The owner run completed all 16 planned real fits and 238 runtime tests. NFL totals passed development but failed exposed evaluation; no model was promoted. [Completed evidence](../../docs/status/football_v062/README.md) preserves scores, controls and limitations. The public synthetic tests demonstrate adapter behavior and do not reproduce private-data scores.
