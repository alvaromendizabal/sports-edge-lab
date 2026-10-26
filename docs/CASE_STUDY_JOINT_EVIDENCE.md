# Did the features work together?

[Project](../README.md) · [Current evidence](CURRENT_EVIDENCE.md) · [Runnable evaluator](../examples/review_lab/factorial.py) · [Tests](../examples/review_lab/tests/test_factorial.py)

The central research question is whether two feature families improve a complete forecasting system together. Testing each family alone cannot answer that. V119R1 evaluated four corresponding systems in LightGBM, XGBoost, PyTorch and TensorFlow while reusing frozen controls and comparing exact cohorts.

## The experiment

| Arm | Information added to compact football + MARKET | Purpose |
|---|---|---|
| C | Neither addition | Frozen common control |
| L | Learned football representations | Contribution of learned structure |
| U | Direct football measurements | Contribution of additional observations |
| UL | Both | Test the complete combined system |

The owner completed 96 new fits and reused 96 corresponding control cells. Every addition is evaluated jointly with the common system. The paired interaction contrast is Loss(UL) − Loss(U) − Loss(L) + Loss(C). For log loss, a negative contrast means combined improvement exceeds the sum of separate improvements on that loss scale. It is a predictive, scale-dependent comparison, not a causal treatment effect.

## The result and decision

Both historical qualification gates failed. All estimable primary ensemble interaction intervals crossed zero. Current NFL UL improved over raw MARKET but regressed against the learned-only model and the retained leader; current FBS UL regressed against both MARKET and its retained leader. The correct decision was to retain the stronger references and close this exact joint-feature hypothesis, preserving its negative evidence.

One subtle case matters: a negative interaction can coexist with a model that still loses to MARKET or to a better retained model. Complementarity, absolute predictive quality and executable value must be evaluated separately. Likewise, a high test count establishes software checks, not successful research.

## A diagnostic worth pursuing

A separate read-only audit found many neural UL corrections near their configured correction limit in current monitoring:

| Implementation | NFL | FBS |
|---|---:|---:|
| TensorFlow UL | 42 / 77 | 200 / 301 |
| PyTorch UL | 18 / 77 | 132 / 301 |
| LightGBM UL | 0 / 77 | 0 / 301 |
| XGBoost UL | 0 / 77 | 0 / 301 |

This is an observable symptom, not proof that the limit caused the regression. It motivates examining correction distributions, training/serving parity and concentration of loss before changing capacity or adding more features. Exact active limits, individual predictions and transformations remain private. Widening a bound after viewing outcomes would constitute a new exposed experiment, not a repair to the completed result.

## Reproduce the reasoning without private inputs

The public evaluator uses six prediction tables: base, A, B, AB, MARKET and retained. Its three fixtures are explicitly invented score scenarios: complementary, redundant and harmful. Probabilities are assigned relative to known invented outcomes to make the arithmetic transparent. They are not a realistic forecast simulation or evidence of skill.

```bash
python -m examples.review_lab.factorial
python -m unittest examples.review_lab.tests.test_factorial -v
```

The implementation aligns by exact event identity, rejects mismatched labels/blocks, computes proper scores and resamples complete weekly blocks for paired descriptive intervals. Unequal block sizes retain event weighting. Missing support returns an unavailable interval and cannot become a positive evidence decision. A dedicated test makes MARKET stronger while leaving the factorial interaction favorable; the evaluator correctly declines comparative success.

The generic example's support settings and fixtures are educational. It contains no private production promotion recipe, football feature transformations, fitted weights or individual forecasts. Its output always states that prospective qualification remains unestablished.

## What would change the conclusion

A materially different representation or missing source could justify a new preregistered hypothesis. Reweighting these exposed results until a combination looks favorable would not create confirmation. A prospective protocol also needs immutable forecasts, information-matched references, known outcome mapping and executable prices/costs before economic claims are tested.
