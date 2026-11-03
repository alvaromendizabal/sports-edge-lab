# NFL evaluation and retraining policy

[Current results](README.md) · [Offline evidence explorer](review.html) · [Current model card](CURRENT_MODEL_CARD.md)

A credible scorecard starts with the event set, target and information cutoff. The public examples reproduce those checks with invented data. They do not recreate the private feature pipeline or obtain paid data.

## Three questions, three records

| Record | What it measures | What it does not establish |
|---|---|---|
| Protected original monitoring | Performance of an unchanged historical model on later games | The benefit of retraining |
| Registered expanding reconstruction | Performance when eligible earlier outcomes update parameters under a predeclared recipe | That a forecast was issued at the time |
| Genuinely issued prediction | A timestamped forecast produced before its cutoff, with the model available then | Profit without execution, price and settlement evidence |

The original monitoring record remains intact. A separately registered weekly or event expanding policy may use earlier current-season labels only when their actual availability precedes the prediction cutoff. It cannot use current-season outcomes to choose a better recipe after the fact. More data may help or hurt; the comparison must measure the result.

## Time is a data contract

Source publication or historical availability, label availability, model completion and forecast issue time are different facts. The primary current winner reference uses the registered T−2h reconstruction and T−2h Kalshi quotes. The late-appended resolved event passed exact T−2h input/quote/model-availability checks; its post-result reconstruction is not original issuance. T−1h quotes are a separately labeled later-reference sensitivity, not a reissued model forecast. Original T−24h evaluations remain separate. A modern acquisition time does not by itself prove a historical quote was available; genuine historical arrays and their clock evidence are required.

For a rolling fit, only outcomes available strictly before its registered cutoff enter training. An outcome from the game being predicted never enters its purported out-of-sample forecast. A retrospective reconstruction is labeled as such, even if its inputs were historically admissible. An expired pregame probability is not a live wagering forecast.

The [rolling chronology demonstration](rolling_chronology.py) rejects late labels and confused issue clocks. The [information-time controls](review.html#timing) make those checks interactive using invented times.

## Selection, uncertainty and monitoring

Recipes, tuning, calibration and ensemble weights must be selected on eligible **pre-2024 out-of-fold evidence**. The 2024 and 2025 seasons have been repeatedly inspected during development and are reported as development-exposed retrospective evaluations. The 2026 results are descriptive monitoring, with no claim of an untouched model-selection holdout.

A retrospectively best accuracy model may differ from the best log-loss, margin or total model. The public scorecard labels this distinction and retains the pre-2024 selected model as a separate reference. A hindsight leader is not an ex-ante profitable strategy.

Paired uncertainty uses the same games for model and reference, resampling entire weeks to preserve within-week dependence. Point estimates and intervals should be read together. The current historical Kalshi comparisons have intervals crossing zero; the result does not establish a durable edge.

## Uniform metric definitions

| Target | Required evaluation | Comparison boundary |
|---|---|---|
| Winner probability | Log loss, Brier, accuracy and calibration | Same resolved games, same horizon, same tie policy |
| Home points margin | MAE, RMSE, signed bias; interval coverage/width when intervals exist | Same home-minus-away score definition and events |
| Game total | MAE, RMSE, signed bias; interval coverage/width when intervals exist | Same sum-of-scores definition and events |
| Exact spread/total contract | Line-specific settlement distribution including pushes; proper scoring when qualified | A point forecast alone is insufficient |
| Hypothetical economics | Declared price, fees, settlement, stake and predeclared selection | Separate from originally issued picks and realized profit |

Unavailable metrics remain unavailable. The complete 120-final Kalshi winner audit includes one tied game; the 119-non-tie headline uses the declared zero-tie probability proxy. Half-tie settlement and fixed tie-rate sensitivities remain separate analyses. Player props are never converted to game-winner probabilities. Historical point-contract coverage is incomplete and cannot support an all-season Kalshi margin/total claim.

## Learning from earlier mistakes

Error and disagreement features are valid only when they use genuinely earlier issued or forward out-of-fold predictions plus outcomes already available. Residual histories, calibration summaries and disagreement interactions must be recomputed inside chronological training folds. In-sample residuals and future outcomes would contaminate the feature.

The registered design covers eight native estimator families, eight rooted feature blocks, 224 fixed pairwise blends, family/all-family means and causal out-of-fold stacking. This is the declared search space, not every imaginable subset. Earlier negative findings are retained; later feature interactions require a new registered test. Planned arms, newly fitted arms, restored fits and blocked arms are reported separately.

## Public reproduction and private evidence

The public code exposes evaluation contracts, recovery behavior, disclosure checks and invented demonstrations. Sanitized result aggregates and resolved examples can be inspected. Exact production features, fitted weights, tuning rules, active forecasts, licensed raw feeds, credentials and private cloud locations remain private.

From the repository root:

```bash
python tracks/nfl/paired_evaluation.py --demo
python -m unittest discover -s tracks/nfl -p 'test_*.py'
python tracks/nfl/contracts.py --check-review
```

These commands require only Python's standard library. A separate Chromium check exercises actual page interactions at desktop and mobile widths. Passing public tests is engineering evidence; it is not acceptance of a private owner run.
