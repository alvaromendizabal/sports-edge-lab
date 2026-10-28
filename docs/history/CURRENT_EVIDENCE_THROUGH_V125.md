# Current evidence — completed V125, October 27, 2026

[Overview](../../README.md) · [Exact-panel explorer](../current/index.html) · [Aggregate export](../evidence/2026-10-27-v125.json) · [Historical-selection boundary](../HISTORICAL_SELECTION_BOUNDARY.md)

The latest completed owner return reports SUCCESS, 20 new expert fits from 20 attempts and 2,523 passed owner checks. It reuses 456 native comparison cells and 6 fusion fits. Both NFL and FBS historical qualification gates failed; economic readiness is false, automatic promotions are zero and actual wagers are zero.

The public export contains 9,756 aggregate scorecards across 57 exact league/protocol/origin/target panels, 180 paired expert comparisons and 1,586 venue diagnostics. Repeated model rows are not additional independent games. Correct/incorrect counts, win metrics, point errors and distribution metrics remain task-specific; missing values are not filled with estimates.

The V4 contract makes 2026–2027 monitoring only. Current-season outcomes cannot choose or rank champions, feature sets, ensemble weights, calibrators or staking rules. The current explorer uses stable model order and no winner emphasis for those panels. Historical minimums are descriptive comparisons on matched games, not significance or promotion claims.

Kalshi archive intersections cover 77 NFL and 177 FBS games; Polymarket US covers 59 and 272; both-venue intersections are 59 and 174. These are 2026 monitoring cohorts. NFL contract-midpoint comparisons are conditional-non-tie proxies. Historical net profit is unavailable because adequate execution-quality evidence has not been established.

The following dated sections preserve earlier evidence and terminology. Earlier retained-reference descriptions are historical descriptive comparisons, not permission to select a champion from 2026 outcomes. The latest selection boundary takes precedence.

---

# Current evidence — completed V120

Publication date: October 26, 2026. [Project](../../README.md) · [Model card](../MODEL_CARD_CURRENT.md) · [Evidence explorer](../review/index.html)

V120 completed 48 new fits and a 240-cell comparison, including 192 retained cells. All 1,278 owner checks passed. Both historical candidate gates and both season-stability guards failed. The project retains its earlier winner-probability leaders; no model was promoted and no wager was placed.

The result adds a material forecasting capability: a coherent joint final-score distribution from the complete integrated feature bank. It does not establish that this capability is more predictive. The [case study](../CASE_STUDY_SCORE_DISTRIBUTIONS.md) connects the hypothesis, mathematical checks, complete results and negative decision.

## Compare the same target on the same games

The tables cover all three campaigns with a separate annual-origin policy in 2025–26. Lower is better; only the lowest displayed numeric cells are emphasized. The full [aggregate export](../evidence/2026-10-26-v120.json) and interactive explorer also include C, L, U, UL, all four retained frameworks, and every new PyTorch/TensorFlow D0/D1 implementation.

### Conditional non-tie win log loss

| Sport / campaign / policy | Games | MARKET raw | Retained leader | D0 ensemble | D1 ensemble | Learned MARKET law |
|---|---:|---:|---:|---:|---:|---:|
| NFL · 2024–2025 fixed | 280 | 0.590011 | **0.575083** | 0.672637 | 0.696305 | 0.593662 |
| NFL · 2025–2026 fixed | 277 | 0.611923 | **0.606098** | 0.745526 | 0.795849 | 0.609305 |
| NFL · 2025–2026 annual | 277 | 0.611923 | **0.606098** | 0.669268 | 0.675059 | 0.609473 |
| NFL · 2026–2027 monitoring | 77 | 0.660022 | **0.624093** | 0.643245 | 0.651836 | 0.657343 |
| FBS · 2024–2025 fixed | 740 | 0.554096 | **0.552031** | 0.574150 | 0.576601 | 0.554367 |
| FBS · 2025–2026 fixed | 748 | 0.538547 | **0.536814** | 0.556603 | 0.564830 | 0.538820 |
| FBS · 2025–2026 annual | 748 | 0.538547 | **0.535618** | 0.543917 | 0.544839 | 0.538898 |
| FBS · 2026–2027 monitoring | 301 | 0.474843 | **0.465519** | 0.474858 | 0.481886 | 0.476054 |

### Conditional non-tie win Brier score

| Sport / campaign / policy | Games | MARKET raw | Retained leader | D0 ensemble | D1 ensemble | Learned MARKET law |
|---|---:|---:|---:|---:|---:|---:|
| NFL · 2024–2025 fixed | 280 | 0.201418 | **0.194627** | 0.232444 | 0.242641 | 0.203119 |
| NFL · 2025–2026 fixed | 277 | 0.213133 | **0.210736** | 0.262443 | 0.269809 | 0.211857 |
| NFL · 2025–2026 annual | 277 | 0.213133 | **0.210736** | 0.232906 | 0.234504 | 0.211891 |
| NFL · 2026–2027 monitoring | 77 | 0.233301 | **0.217288** | 0.224035 | 0.228954 | 0.232354 |
| FBS · 2024–2025 fixed | 740 | 0.188631 | **0.187554** | 0.196291 | 0.196938 | 0.188926 |
| FBS · 2025–2026 fixed | 748 | 0.181678 | **0.181086** | 0.190197 | 0.193336 | 0.181975 |
| FBS · 2025–2026 annual | 748 | 0.181678 | **0.180522** | 0.184415 | 0.183908 | 0.181997 |
| FBS · 2026–2027 monitoring | 301 | 0.156153 | **0.152630** | 0.157144 | 0.159199 | 0.156926 |

Retained leaders are metric-specific. The annual NFL reference is an older fixed-origin model, explicitly retained as a stronger comparator. Selection occurred on exposed outcomes. These are project leaders on matched evidence, not a global ranking of proprietary forecasting systems. Monitoring includes games through October 15, not every completed 2026 game.

## A score distribution requires separate metrics

The learned MARKET law is a fitted distribution based on market score-location information. It is not raw MARKET moneyline consensus. Raw MARKET therefore has no invented joint-NLL or CRPS entry. Joint cohorts include ties; binary winner cohorts do not. NFL monitoring contains 78 joint outcomes and 77 non-tied outcomes.

### Joint negative log likelihood

| Sport / campaign / policy | Games incl. ties | Learned MARKET law | D0 ensemble | D1 ensemble |
|---|---:|---:|---:|---:|
| NFL · 2024–2025 fixed | 280 | **6.978033** | 7.260847 | 7.921615 |
| NFL · 2025–2026 fixed | 277 | **6.841500** | 7.144575 | 7.975015 |
| NFL · 2025–2026 annual | 277 | **6.810331** | 6.922013 | 7.062596 |
| NFL · 2026–2027 monitoring | 78 | **6.865024** | 6.958831 | 6.905238 |
| FBS · 2024–2025 fixed | 740 | **7.161243** | 7.206173 | 7.246193 |
| FBS · 2025–2026 fixed | 748 | **6.991377** | 7.039126 | 7.068239 |
| FBS · 2025–2026 annual | 748 | **6.994126** | 7.010242 | 7.010674 |
| FBS · 2026–2027 monitoring | 301 | 6.953087 | **6.951816** | 6.970415 |

### Mean marginal CRPS

| Sport / campaign / policy | Games incl. ties | Learned MARKET law | D0 ensemble | D1 ensemble |
|---|---:|---:|---:|---:|
| NFL · 2024–2025 fixed | 280 | **5.033389** | 5.629853 | 5.815351 |
| NFL · 2025–2026 fixed | 277 | **5.074783** | 5.700910 | 5.898776 |
| NFL · 2025–2026 annual | 277 | **5.073894** | 5.305080 | 5.289688 |
| NFL · 2026–2027 monitoring | 78 | 5.115817 | 5.318479 | **5.104259** |
| FBS · 2024–2025 fixed | 740 | **6.277458** | 6.442285 | 6.425862 |
| FBS · 2025–2026 fixed | 748 | **6.098414** | 6.264792 | 6.252351 |
| FBS · 2025–2026 annual | 748 | **6.097916** | 6.159811 | 6.143058 |
| FBS · 2026–2027 monitoring | 301 | **6.048390** | 6.065723 | 6.090322 |

These tables compare the ensembles and their fitted MARKET reference. All seven native/ensemble score laws, interval coverage and interval scores are in the export. Joint NLL evaluates probability mass on both final scores. Marginal CRPS evaluates the individual score marginals; it does not by itself assess their dependence. A coherent probability law can still be poorly calibrated or overconfident.

## More recent settlements, kept separate

The October 24–25 games add frozen pregame forecast evidence beyond the fixed October 15 monitoring cutoff. The archive contains 6,755 forecast rows but only 56 unique settled games: 12 NFL and 44 FBS. Repeated versions and repeated issuances are not new outcomes. The audit selects the earliest issue for each exact model/game identity and compares it with MARKET from the same issue.

| Exact model family / version | Games | Model log loss | Same-issue MARKET log loss | Model / MARKET correct |
|---|---:|---:|---:|---:|
| FBS · retained fixed TensorFlow base | 3 | **0.453486** | 0.465058 | 3 / 3 |
| FBS · upcoming feedback ensemble | 44 | 0.627104 | **0.625157** | 32 / 29 |
| FBS · upcoming TensorFlow base | 44 | **0.603075** | 0.625157 | 32 / 29 |
| NFL · retained weekly PyTorch feedback | 12 | **0.669402** | 0.695898 | 8 / 8 |
| NFL · upcoming feedback ensemble | 12 | **0.702977** | 0.704220 | 7 / 8 |
| NFL · upcoming PyTorch feedback | 12 | 0.723284 | **0.704220** | 8 / 8 |

These are separate matched comparisons, not one common-cohort leaderboard. The FBS fixed champion has only three eligible forecasts; its upcoming relative uses different fitted weights and covers 44. The exact NFL retained champion and upcoming relative are likewise distinct. There are only one or two UTC-week blocks per row, so no block interval is available. The family comparison is retrospective reporting of pregame forecasts, not a newly frozen model-selection test.

The new V120 score laws have no settled forecasts in this return. The [recent-settlement export](../evidence/2026-10-26-recent-settlements.json) supplies issue-horizon ranges and aggregate provenance without individual forecasts. These gains do not establish executed fills, profit or a prospectively selected betting strategy.

## What the systems contain

| System | Information and representation | Current status |
|---|---|---|
| MARKET raw | Complete-book paired moneyline consensus, with bookmaker margin removed | Benchmark, not an executable quote |
| Learned MARKET | Book quotes, book identity, missingness and archived price paths | Separate project-trained references |
| C | Team history, offense/defense, opponent adjustment, matchups, feedback, dynamic form and quality | Retained compact control |
| L | C plus learned opportunity, matchup, drift, uncertainty and support representations | Retained learned-feature arm |
| U | C plus direct charting-quality and possession-response information | Retained direct-feature arm |
| UL | The full C + direct + learned bank | All four frameworks evaluated together; historical gates failed |
| D0 | Full integrated bank producing joint score outcomes with a shared uncertainty structure | New PyTorch/TensorFlow models, 24 fits per framework across D0/D1 |
| D1 | Same integrated bank with matchup-dependent uncertainty and dependence | Both historical candidate and season-stability guards failed |
| Learned MARKET law | Fitted score distribution using market score-location information | Joint-target baseline, distinct from raw MARKET |

Bookmakers' internal feature sets are unknown. Rank-one depth charts are not confirmed starters. The current active bank is not a complete player/injury/roster/transfer/weather system. Data that exist in a cache are not automatically historically admissible features.

## Data and serving outcomes

| Layer | Verified V120 state | Boundary or remaining gap |
|---|---|---|
| NFL play by play | 106/106 completed games | Enrichment remains 94/106 games |
| FBS detailed summaries | 566/566 games; 100,687 plays | Two native drives quarantined; historical observation clocks remain distinct |
| Price admission | 69/77 incoming events admitted | Seven identity rejections; one insufficient-common-books rejection |
| Immutable research output | 4,749 forecast rows across 69 priced games | Multiple rows per game are not independent observations |
| Wager admission | Zero paper actions, zero actual wagers | Stale source quotes remain a separate gate |

The prior snapshot had 52/71 admitted events; its denominator differs from the new 69/77 snapshot. Seventeen event-scoped identity repairs were implemented without changing the original forecast history. The incoming provider set also changed, so this is not an unchanged-cohort coverage comparison.

The source inventory extends beyond the fixed monitoring cohort. Extending a metric requires eligible frozen forecasts and matching labels, not merely newer final scores. Historical source observations can postdate the games they describe; unknown publication remains unknown and release assumptions remain disclosed.

## Audit and execution

The return passed CRC verification, 572 member pins, 1,050 source-member pins and all 48 fit-checkpoint pins. Independent rescoring reproduced 3,342 binary scorecards, 112 distribution scorecards and 414 paired point contrasts, with zero maximum absolute discrepancy in the checked scalar outputs. The owner notebook executed in a separate kernel and saved/reopened its rich outputs.

The worker took 857.01 seconds; supervised execution took 892.22 seconds, with 2.05 GiB peak process-tree RSS. Active worker compute is estimated at $0.120 using the inherited $0.484/hour reference. That rate is an assumption, and the estimate excludes idle/startup time, storage and transfers.

These are execution and research checks, not a prospective profitability certificate. NFL monitoring has only six weekly blocks; FBS has eight. Repeated model selection is not corrected by a paired bootstrap.

## Preserved evidence

- [V120 completed execution](../evidence/2026-10-26-v120-execution.json)
- [V119R1 integrated feature experiment](../evidence/2026-10-26.json) and [joint-feature case study](../CASE_STUDY_JOINT_EVIDENCE.md)
- [V119R1 execution](../evidence/2026-10-26-v119r1-execution.json)
- [V119 source-state failure](../evidence/2026-10-26-execution.json)
- [Earlier dated comparison](../evidence/2026-10-25.json)

Public artifacts expose evaluation mechanics and sanitized aggregates. The private data, exact active transformations, fitted assets, per-game forecasts and execution configuration remain outside the public repository. Read the [publication boundary](../PUBLICATION_BOUNDARY.md).
