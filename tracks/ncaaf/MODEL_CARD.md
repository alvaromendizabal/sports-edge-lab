# NCAA FBS model card · V026 completion and 2026 monitoring

**Evidence dated November 3, 2026. Historical recovery complete; no new live forecast, rolling fit or model promotion.**

[Season and market explorer](../../docs/fbs/index.html) · [Methodology](../../docs/fbs/SEASON_EXPLORER_2026-11-03.md) · [Preserved V024 card](MODEL_CARD_V024.md) · [Historical studies](../../docs/fbs/research.html)

## Intended use and publication scope

This report supports review of an NCAA FBS research system: winner probabilities, home-minus-away margins and combined points. The observed population includes FBS teams playing other FBS teams and non-FBS opponents. It is not a claim of independently proven official-season completeness or a trading service.

The owner explicitly authorized public schedule/result facts, rounded derived model outputs, provider reference values and source clocks. Complete private forecast archives, licensed response bodies, model weights, exact feature transforms and execution packages remain private. Rounded display values do not rescore headline metrics. The [publication boundary](../../docs/PUBLICATION_BOUNDARY.md) defines the narrow FBS scope.

## Actual completed work

V026 completed **100 new learned fits and reused 197 authenticated states**, producing 297 committed learned states in **70.212252817 seconds**. The inherited V025 attempt had stopped after 197 committed states and one failed forward attempt. Recovery preserves that failure and the original numerical stop signal; it does not count saved states as new fits.

The registered research reuses saved base predictions. Its chronological meta-policy selection uses only data through 2023. The 2024/2025 evaluations are exposed diagnostics; 2026 outcomes cannot select or tune a model. Annual fitted coefficients stay fixed while past completed-game feature state may expand. This is not a season-start feature freeze.

Actual V026 owner return: **128,049,129 bytes**, SHA-256 `fda3b6c068f9bf457add339027e1d9fdd53810a9fb56976e23ad4593abca7606`. Independent archive authentication checked physical bytes, all report pins, source/parent identity, the separate terminal record and a later external completion. Public release checks validate the sanitized export; the digest alone is not a substitute for those private records.

## Exposed historical results

| Season | Games | Winner log loss | Brier | Accuracy | Margin MAE / RMSE | Total MAE / RMSE |
|---|---:|---:|---:|---:|---:|---:|
| 2024 | 918 | 0.525230 | 0.178311 | 73.31% | 13.536 / 17.003 | 12.782 / 16.252 |
| 2025 | 934 | 0.493465 | 0.164686 | 74.95% | 12.806 / 16.239 | 12.693 / 15.727 |

These are the completed V026 registered selections. Winner log loss remains worse than V020 in both displayed seasons; V023 also has lower 2025 loss. Margin and total metrics move in different directions. The result does not establish universal improvement or authorize promotion. All earlier fixed selections remain in the season explorer; full V024 comparison panels remain in the historical page.

Repeated inspection makes 2024/2025 unsuitable as untouched confirmation. Pre-2024 selection scores are selected OOF evidence, not an independent confirmatory test. Descriptive intervals are not formal coverage guarantees.

## Current-season evidence

The authenticated inventory contains **888 observed games: 622 completed and 266 scheduled**. The original retrospective replay covers all 622 completed rows; 465 winner picks were correct and 157 incorrect. The separately preserved TF228 monitor has 301 games and approximately 0.465519 log loss. It must not replace or expand the broader cohort.

| Original replay metric | Exact 622-game cohort |
|---|---:|
| Winner log loss | 0.513328 |
| Brier | 0.173252 |
| Accuracy | 74.76% |
| ROC AUC | 0.769937 |
| Ten-bin ECE | 0.044593 |
| Margin MAE / RMSE | 14.600 / 18.185 |
| Total MAE / RMSE | 13.093 / 16.290 |

The preceding complete Pacific calendar week, October 26–November 1, contains 56 observed games and 46 correct original replay winners. The current November 2–8 calendar week contains 63 observed scheduled games at the source clock. The prior calendar week spans 169 hours because daylight saving time ends; native football phase/week identifiers remain separate.

No replay row is represented as an issued forecast. This snapshot has **zero admitted rolling forecasts and zero new genuine issues**. The raw-to-feature numerical reconstruction and causal input checks are incomplete. Market and schedule collection proceeds independently of those model admission requirements.

## Market comparison and abstention

On the archived exact 192-game DraftKings winner cohort, model log loss is **0.604359**, versus **0.553191** for DraftKings. Among 40 winner disagreements, the model was correct 18 times and DraftKings 22 times. On 199 point-market games, model/DraftKings margin MAE is **14.325 / 12.030**, and total MAE **14.637 / 13.329**. These are negative matched accuracy results for the model.

DraftKings, Kalshi, Polymarket US and Polymarket Global are distinct comparison products. The dashboard records observed coverage and retains each missing game. A last trade, candle close, book midpoint or no-vig sportsbook probability is labeled with its own meaning. A late retrieval can support a retrospective comparison, but cannot establish possession before a historical model issue. A captured snapshot can establish availability by a later cutoff even without an individual source quote time; that clock remains null and the capture basis is explicit. Future cutoff windows remain pending.

No executable edge, realized P&L, ROI, fill, fee or settlement result is established. Every paper decision is **NO BET**, with **$0 proposed stake**.

## Reproducibility and remaining limits

The public report and deterministic renderer reproduce the all-game display from the committed sanitized JSON. Generic timing and left-join contracts run without credentials. Adversarial tests reject duplicate identities, post-cutoff observations, late captures without source clocks, straddling candle buckets, changed replay results, private fields and silent inventory loss. Browser CI exercises mobile/desktop views, keyboard details, all four products, current/last-week windows, disagreement export and the complete no-script table.

This public execution does not retrain the private football models. Independent official-population closure, complete native provider price histories, real historical possession, the remaining feature-value producer and genuinely issued prospective evaluation are unresolved. These limitations affect scientific claims; they do not justify hiding available game or market observations.

### Current native point-reference qualification

Current spread/total displays use descriptive bid/ask-supported threshold bounds. Bands wholly above/below 50% supply lower/upper support; equality supplies neither. A wide band can have a 50% midpoint without locating the distribution, so its old nearest-half threshold remains only in expanded diagnostic details. Separate support clocks govern cutoff qualification. The dashboard preserves one-sided and uninformative states and invents no expected score or executable line. Historical price-only point cohorts remain unchanged and separately labeled.
