# Case study: a valid distribution that did not qualify

[Project](../README.md) · [Complete results](CURRENT_EVIDENCE.md) · [Public evaluator](../examples/review_lab/distribution.py)

V120 tested whether the integrated football representation could improve prediction by modeling both teams' final scores jointly. The experiment completed successfully, but neither sport passed its historical candidate or season-stability gate. The earlier binary leaders remain retained. This case study records how the project separates a new capability, numerical correctness and demonstrated predictive value.

## The problem

A probability of winning, an expected margin and an expected total do not specify a full score distribution. They cannot by themselves supply tie probabilities, interval coverage, coherent over/under probabilities or the expected payout of a contract with its own settlement rule. Independently trained outputs may also disagree.

The preceding C/L/U/UL experiment tested complementary feature groups in concert. Combining the groups did not qualify a new winner model. V120 kept that integrated bank and changed the forecast target and uncertainty representation, while retaining all earlier comparison cells. This was a distinct mechanism test, not a search over tiny blend weights.

## The hypothesis and controls

| Component | Role |
|---|---|
| D0 | Integrated features produce a normalized joint score law with shared uncertainty structure |
| D1 | The same representation also conditions uncertainty and dependence on the matchup |
| Learned MARKET law | A fitted market-based joint-target reference |
| MARKET raw | Archived paired moneyline consensus for the conditional binary task |
| Retained project leaders | Stronger binary comparators on identical games |
| Native implementations | PyTorch and TensorFlow; 24 new fits each, 48 total |

The new fits span six declared chronological origins and both sports. The comparison bank reuses 192 accepted cells, including LightGBM and XGBoost systems. Retrospective development, fixed, annual and current monitoring panels remain labeled as exposed; a new version does not create an untouched holdout.

## Correctness that had to hold before interpretation

The score law must normalize as discrete probability mass. Scores outside its declared support cannot silently acquire fabricated mass. Non-tie winner probabilities must be derived by conditioning the law; tie mass must remain available for the unconditional target. Mixtures must combine laws before conditioning. Losses must retain authoritative log probabilities when ordinary floating-point probabilities round to zero or one.

The public [finite-law evaluator](../examples/review_lab/distribution.py) demonstrates these mechanics with invented probabilities. It includes 22 adversarial tests for normalization, exact support, underflow, mixture identity, conditional targets, CRPS, immutable inputs and settlement rules. It contains no football training routine, active parameterization, private feature recipe or fitted asset.

One invented example deliberately gives two laws different tie probabilities. Averaging their conditional win probabilities gives a different answer from mixing their full laws and then conditioning. The discrepancy is arithmetic, not a football result. A separate toy contract demonstrates why conditional win probability and expected contract settlement are different quantities. Purchase cost and fees are deliberately excluded and labeled.

## What happened

All 48 fits and all 1,278 owner checks completed. Independent rescoring matched 16,710 binary scalar metrics, 1,792 distribution scalar metrics and 414 paired binary point contrasts exactly. Both sports passed the support-sensitivity guard, but failed candidate and season-stability qualification. The result is a valid negative experiment.

Current NFL D1 improves mean marginal CRPS slightly against the learned MARKET law, while its joint NLL is worse. Its conditional winner score also trails D0 and the retained leader. These are different properties, so reporting only the favorable marginal score would hide important evidence. Current FBS D0 slightly improves joint NLL against the learned MARKET law but has worse mean marginal CRPS; D1 does not improve the complete comparison.

The [full tables](CURRENT_EVIDENCE.md) show every requested campaign. Current monitoring still ends October 15 and has limited blocks. These outcomes support retaining the earlier leaders and diagnosing the joint objective before expanding its capacity. They do not establish a deployable betting edge.

## Engineering consequences

The reusable advance is the distribution contract: coherent outcomes, explicit ties, proper scores, uncapped log probabilities, separately identified cohorts and preserved current issuance. That contract remains useful even when the current parameterization is rejected.

The failure is visible in the same artifacts as the passing checks. An employer reviewing the work should be able to reproduce generic numerical behavior, follow each aggregate result to its dated export, and see why the candidate was not promoted. Reliable research includes refusing a more complicated model when the evidence does not support it.

## Research context and scope

[Gneiting and Raftery (2007), Strictly Proper Scoring Rules, Prediction, and Estimation](https://sites.stat.washington.edu/people/raftery/Research/PDF/Gneiting2007jasa.pdf) motivates evaluating probabilistic forecasts with proper scores. This project applies those established evaluation principles; it does not claim to reproduce a published football system or inherit its performance.

Private source data, transformations, fitted models and individual forecasts are withheld. The public evaluator is a generic educational implementation. Reproducing its tests does not reproduce the private football results.
