# Basketball: why covered and uncovered gains differ

The larger NCAA men improvement outside the saved sportsbook panel is partly a calendar-composition and support problem. Matching baseline probability alone leaves almost the entire difference. Adding month and game type greatly reduces it, while discarding 29.09% of uncovered games. This is descriptive evidence about the comparison population, not a causal explanation or a qualified MARKET edge.

This review recomputes saved 2025–2026 predictions. It performs zero real fits, model inferences, source requests or new forecasts. B005 actually completed evidence recovery with zero fits; B003 remains the latest fully completed real modeling release, and B004 remains a stopped execution. The cumulative real-unit count stays 238.

## First correct the season comparison

Covered means a valid saved T60 sportsbook benchmark; uncovered does not mean no real-world market. All 1,143 covered NCAA men games are from 2026. The earlier pooled uncovered gain mixed 2025 and 2026, so it cannot identify a coverage effect. The college controls are exact B002 combined models. NBA compares the rejected rich candidate with its selected strength model; no champion changes.

| League | Season | Saved MARKET | Games | Control log loss | Rich log loss | Rich − control |
|---|---|---|---:|---:|---:|---:|
| NBA | 2025 | Uncovered | 1,239 | 0.612608757 | 0.614320226 | +0.001711470 |
| NBA | 2025 | Covered | 9 | 0.603386008 | 0.598678597 | -0.004707410 |
| NBA | 2026 | Uncovered | 1,233 | 0.601841739 | 0.601299031 | -0.000542709 |
| NBA | 2026 | Covered | 16 | 0.645275550 | 0.654399998 | +0.009124447 |
| NCAA men | 2025 | Uncovered | 5,758 | 0.530652365 | 0.524171133 | -0.006481232 |
| NCAA men | 2026 | Uncovered | 4,606 | 0.522552995 | 0.514027624 | -0.008525371 |
| NCAA men | 2026 | Covered | 1,143 | 0.577580458 | 0.577570458 | -0.000010000 |
| NCAA women | 2025 | Uncovered | 5,131 | 0.463780170 | 0.456514714 | -0.007265456 |
| NCAA women | 2025 | Covered | 149 | 0.433657861 | 0.430101008 | -0.003556853 |
| NCAA women | 2026 | Uncovered | 5,478 | 0.466506477 | 0.457584957 | -0.008921520 |
| NCAA women | 2026 | Covered | 143 | 0.497643383 | 0.490908635 | -0.006734748 |

Negative deltas favor the rich candidate over its league control. In NCAA men 2026, the covered-minus-uncovered improvement gap is +0.008515371, with a shared seven-day calendar-block interval [0.002993166, 0.014439907]. There is no covered men 2025 control. NBA has only 9 and 16 covered games; its small panel does not support a confident coverage explanation.

## Competitiveness alone does not explain the gap

Covered games have lower mean baseline favorite confidence (0.7172 versus 0.7326), but their central 0.4–0.6 home-win probability share is slightly lower: 253/1,143 (22.13%) versus 1,060/4,606 (23.01%). Calling the covered panel simply “more competitive” depends on the chosen definition. Reweighting uncovered games to the covered probability-quintile distribution retains every game and leaves a +0.008104461 gap. Probability deciles give +0.008414666.

The calendar mix is much more different: January–February supplies 1,002/1,143 (87.66%) of covered games versus 1,894/4,606 (41.12%) of uncovered games. November has 1 covered and 1,241 uncovered games. Month-only matching leaves +0.001553897, but retains only 72.77% of uncovered games. Month is both a context proxy and a coverage-support constraint; it does not isolate a causal mechanism.

## Report adjustment together with support loss

Each row below uses a fixed descriptive grouping and requires at least five observed games in each cohort per stratum, or twenty for the named sensitivity. Uncovered stratum means are reweighted to the retained covered distribution. Different rows can describe different retained populations. All fifteen declared sensitivities are shown; none selects a model. This independent forensic analysis uses minimum five plus minimum-twenty sensitivities. The offline B006 owner-analysis default uses minimum twenty with its own declared confidence strata and is a separate specification, not an exact numeric replay of the forensic table.

| Grouping | Covered retained | Uncovered retained | Uncovered ESS | Within-stratum gap | Descriptive 95% interval |
|---|---:|---:|---:|---:|---|
| `probability_quintile` | 100.00% | 100.00% | 4,472.6 | +0.008104461 | [+0.003198279, +0.013848060] |
| `probability_decile` | 100.00% | 100.00% | 4,329.7 | +0.008414666 | [+0.003522621, +0.014367593] |
| `favorite_confidence` | 100.00% | 100.00% | 4,329.7 | +0.008414666 | [+0.003522621, +0.014367593] |
| `month` | 99.91% | 72.77% | 2,363.4 | +0.001553897 | [-0.001923927, +0.004647551] |
| `game_type` | 100.00% | 100.00% | 4,522.9 | +0.008542960 | [+0.003233058, +0.014720643] |
| `neutral` | 100.00% | 100.00% | 4,140.6 | +0.008768922 | [+0.003333937, +0.014991952] |
| `probability_month_game_type` | 99.48% | 70.91% | 2,289.0 | +0.001829468 | [-0.002102329, +0.004976417] |
| `confidence_favorite_month_game_type` | 96.59% | 55.73% | 2,164.7 | +0.003012435 | [-0.000515032, +0.006018381] |
| `probability_month_game_type_neutral` | 98.78% | 67.98% | 2,234.4 | +0.001997879 | [-0.001378546, +0.005187397] |
| `probability_decile_month_game_type` | 96.59% | 55.73% | 2,164.7 | +0.003012435 | [-0.000515032, +0.006018381] |
| `month_min20` | 99.91% | 72.77% | 2,363.4 | +0.001553897 | [-0.001923927, +0.004647551] |
| `probability_month_game_type_min20` | 92.91% | 46.55% | 2,037.6 | +0.002292906 | [-0.002474356, +0.006576272] |
| `confidence_favorite_month_game_type_min20` | 85.30% | 40.08% | 1,803.0 | +0.001946332 | [-0.002709885, +0.006224796] |
| `probability_month_game_type_neutral_min20` | 89.76% | 41.95% | 1,907.2 | +0.002409896 | [-0.002199093, +0.006859897] |
| `probability_decile_month_game_type_min20` | 85.30% | 40.08% | 1,803.0 | +0.001946332 | [-0.002709885, +0.006224796] |

For probability quintile × month × game type, 1,137 covered and 3,266 uncovered games remain (99.48% and 70.91%). The within-stratum gap is +0.001829468 with interval [−0.002102329, +0.004976417] and uncovered effective sample size 2,289.0. The full raw gap decomposes into +0.003423843 from support exclusion, +0.003262061 from composition within retained support, and +0.001829468 within strata. It would be misleading to attribute the entire reduction to competitiveness or say the cohorts are now equivalent. The decomposition also depends on the reference distribution: a symmetric decomposition on the same support gives −0.000291602 within strata and +0.005383131 composition. No reference choice is a unique causal explanation.

The raw interval resamples shared seven-day calendar blocks. The adjusted intervals use positive exponential multipliers on shared seven-day blocks with supported strata frozen before resampling. They are exploratory sensitivity intervals, unadjusted for multiple comparisons, from development-exposed seasons. They are not independent validation or causal confidence intervals.

## What the prediction changes show

On covered men games, rich combined corrects 22 baseline mistakes but loses 23 baseline correct picks; on uncovered games it corrects 131 and loses 113. Rich probability updates move toward the realized winner on 45.49% versus 55.67% of games. These are outcome-conditioned diagnostics, not available pregame signals.

The covered rich model moves closer to sportsbook probabilities: mean absolute disagreement is 0.04258 versus 0.05253 for combined. Its signed probability-error correlation with MARKET is 0.99317 (shared subtraction of the same outcome mechanically raises residual correlations), and its mean log loss remains 0.010443758 worse than MARKET. Similar probabilities and highly correlated errors do not establish incremental information. No learned MARKET-only or integrated model is qualified; the 300-base/80-calibration requirements and stability gates remain intact.

## Limits and the next controlled investigation

- Baseline probabilities are a proxy for strength and competitiveness, not an independent team rating.
- Exact retained event joins support calendar month, native game type and neutral venue indicators. No team or event identifiers are public.
- Provider conference tags are not independently verified historical conference membership and are omitted from the public matching analysis.
- Feature-availability time is league-state recency under reconstructed 24-hour research timing, not per-team or per-feature freshness and not an independently verified original publication clock.
- Frozen feature matrices were not exported; per-game feature missingness, box completeness and support cannot be directly attributed from these saved predictions.
- Common-support reweighting is descriptive, changes the retained population and is not a causal effect of sportsbook coverage.
- All intervals are exploratory, unadjusted for multiple comparisons and use development-exposed historical seasons.
- Residual correlations do not establish a trainable MARKET residual model, a new qualified blend, an executable wager or profit.

Future work is registered for explicit budget approval: obtain sufficiently early MARKET training support; qualify original timing and genuinely new pregame information; then compare frozen residual or integrated candidates on exact historical cohorts and untouched future monitoring. More similar blends are not treated as new information. Current 2027 outcomes remain monitoring-only and cannot select features, hyperparameters, calibration, ensembles or champions.

B005 preserved all 330 forecast versions across 18 files and 61 games, with no new forecast or order. Its recovered scorecards are reused evidence, not additional fits. The measured active floor is 4,250.265382922 seconds. The still-open finalization reservation extends to 4,430.265382922 seconds; that reservation is not measured spent time. Against the 4,500-second work ceiling, conservative availability is 69.734617078 seconds until a later authenticated closed receipt replaces the reservation. Public-source requests are 48/48. No extra training, source access or spending allowance is active. Offline B006 audit/code preparation stays within inherited authority.

The project rating stays 8.5/10: the recovery and cohort diagnosis improve auditability, not independent MARKET advantage or trading evidence.

## Reproduce the public aggregate checks

The [sanitized aggregate evidence](evidence/2026-10-28-basketball-market-coverage.json) includes all fifteen sensitivities and supported-stratum sums. The [executed notebook](../notebooks/basketball_market_coverage.ipynb) retains two interactive Plotly figures, exact tables and a later completion cell. The validator recomputes pooled/year arithmetic, support counts, weights, decomposition and effective sample size. Bootstrap intervals are retained owner-data analysis outputs; public aggregates cannot independently regenerate their block resamples.

```bash
python -m examples.basketball_contracts.evidence_market_coverage --check
python -m unittest discover -s examples/basketball_contracts/tests -v
python -m examples.basketball_contracts.execute_coverage_notebook --output /tmp/basketball-market-coverage.ipynb
```

See the preserved [B004 execution outcome](BASKETBALL_B004_EXECUTION.md), [historical leaderboards](BASKETBALL_RESULTS.md) and [model card](BASKETBALL_MODEL_CARD.md). No private event-level predictions, feature matrices, source identifiers, production weights or trading configuration are published.
