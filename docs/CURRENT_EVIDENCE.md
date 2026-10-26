# Current research evidence — October 25, 2026

[Project](../README.md) · [Model card](MODEL_CARD_CURRENT.md) · [Machine-readable export](evidence/2026-10-25.json) · [Offline explorer](review/index.html)

This publication separates completed model experiments, current research serving and wagering readiness. The current numerical panels come from audited V117R1 scorecards; V118 adds serving and data evidence, not a new fitting result.

October 26 execution update: V119 passed 1,058 owner checks and its notebook gate, then failed at source admission before the experiment began. It completed zero real fits, admitted no new data and issued no new forecasts. Its qualification result is unavailable; every numerical panel below remains unchanged. See the [dated execution receipt](evidence/2026-10-26-execution.json) and [provenance case study](CASE_STUDY_PROVENANCE.md).

## Three campaigns, explicit comparison policies

Each cell is log loss / Brier; lower is better. References are selected independently for each metric. These panels are exposed and repeatedly examined, not untouched confirmation sets.

| Sport / campaign / policy | Games | MARKET | Matched control | Joint challenger | Best retained by metric |
|---|---:|---:|---:|---:|---:|
| NFL 2024–2025 fixed | 280 | 0.590011 / 0.201418 | 0.586801 / 0.200220 | 0.585244 / 0.199270 | **0.575083 / 0.194627** |
| NFL 2025–2026 fixed | 277 | 0.611923 / 0.213133 | 0.612458 / 0.213486 | 0.613622 / 0.213887 | **0.606098 / 0.210736** |
| NFL 2025–2026 annual | 277 | 0.611923 / 0.213133 | 0.615797 / 0.214913 | 0.619893 / 0.216829 | **0.606098 / 0.210736** |
| NFL 2026–2027 monitoring | 77 | 0.660022 / 0.233301 | 0.654355 / 0.230954 | 0.647299 / 0.227659 | **0.624093 / 0.217288** |
| FBS 2024–2025 fixed | 740 | 0.554096 / 0.188631 | 0.555546 / 0.189181 | 0.555214 / 0.189198 | **0.552031 / 0.187554** |
| FBS 2025–2026 fixed | 748 | 0.538547 / 0.181678 | 0.538485 / 0.181870 | 0.538406 / 0.181856 | **0.536814 / 0.181086** |
| FBS 2025–2026 annual | 748 | 0.538547 / 0.181678 | 0.538650 / 0.182114 | 0.538061 / 0.181917 | **0.535618 / 0.180522** |
| FBS 2026–2027 monitoring | 301 | 0.474843 / 0.156153 | 0.473781 / 0.156244 | 0.473819 / 0.155894 | **0.465519 / 0.152630** |

Fixed-origin heads train through 2023. The separate annual 2025 comparison generally trains through 2024; its strongest NFL retained reference is still the older fixed MARKET model. Current monitoring uses a distinct origin/update policy. FBS 2024 has different retained log-loss and Brier references. The 2026–27 cohort includes games only through October 15 Pacific, not the complete current season.

MARKET is archived bookmaker consensus after paired proportional de-vig with at least three common complete books. A median consensus is not an executable quote or necessarily a closing line. Learned MARKET-only models are explicitly distinguished from football-plus-MARKET systems.

## All four new frameworks

These are log losses on the same rows above. A framework label is an implementation choice, not proof of a useful football mechanism.

| Sport / campaign / policy | LightGBM | XGBoost | PyTorch | TensorFlow | Equal-weight primary | Best retained |
|---|---:|---:|---:|---:|---:|---:|
| NFL 2024–2025 fixed | 0.591500 | 0.589815 | 0.576723 | 0.589451 | 0.585244 | **0.575083** |
| NFL 2025–2026 fixed | 0.616364 | 0.613556 | 0.613085 | 0.617952 | 0.613622 | **0.606098** |
| NFL 2025–2026 annual | 0.615414 | 0.615307 | 0.628576 | 0.626578 | 0.619893 | **0.606098** |
| NFL 2026–2027 monitoring | 0.649243 | 0.653294 | 0.649979 | 0.644121 | 0.647299 | **0.624093** |
| FBS 2024–2025 fixed | 0.554504 | 0.555192 | 0.556135 | 0.560785 | 0.555214 | **0.552031** |
| FBS 2025–2026 fixed | 0.539858 | 0.538946 | 0.542453 | 0.537821 | 0.538406 | **0.536814** |
| FBS 2025–2026 annual | 0.538233 | 0.538233 | 0.541935 | 0.540059 | 0.538061 | **0.535618** |
| FBS 2026–2027 monitoring | 0.475002 | 0.472991 | 0.476573 | 0.475911 | 0.473819 | **0.465519** |

The JSON export also contains Brier, accuracy and AUC for every displayed framework. The new opportunity representation improves all four corresponding NFL controls in current monitoring, while remaining behind the strongest retained reference. FBS effects are smaller and inconsistent.

## Qualification and uncertainty

Both latest historical challenger qualification gates failed. That is a valid negative scientific result from a successful execution. It is not repaired by selecting a favorable current-season cell.

- NFL monitoring: 77 games, six weekly blocks. No weekly-block interval was issued because the study requires at least eight blocks.
- FBS monitoring: 301 games, eight weekly blocks. The new challenger's paired log-loss difference against MARKET is −0.001024; its 95% block-bootstrap interval is [−0.006468, +0.005928].
- Retained references are descriptive leaders from exposed comparisons. Repeated-selection multiplicity is not corrected by those intervals.
- The public snapshot does not establish long-run after-fee profitability or superiority to external commercial forecast services.

## Completed current serving

V118 passed 927 owner tests and issued 2,058 research probability rows across 39 unique games: 44 NFL rows for one game and 2,014 FBS rows for 38 games. Multiple model rows are not independent games. It made zero new real fits, zero paper actions, zero wagers and zero automatic promotions.

Its final source-read-to-issue interval was 6.282 seconds versus 245.440 seconds in an earlier execution. Different paths and workloads were involved, so this is an observational operational comparison. All named sportsbook quotes were still stale; faster processing did not make their source timestamps fresh.

## Data and operational readiness

| Layer | Verified inventory | Remaining boundary |
|---|---|---|
| NFL finals/PBP | 105 finals, 105 PBP games, 18,401 plays | Complete game-count coverage is not proof of every enrichment |
| NFL enrichment | 94 games, 16,070 exact play joins | 11 game gaps |
| FBS bulk drives | 566 finals and 566 covered games, 13,241 drives | Detailed summaries have separate admission checks |
| FBS detailed summaries | 549 games, 97,615 plays and 12,840 drives | 17 kickoff conflicts remain quarantined |
| FBS detailed boxes | 16,470 team-stat and 284,617 player-stat rows | Collected rows are not automatically admitted model features |
| Current prices | Zero fresh named quotes | Action gates remain closed |

Current pregame starter/participation, roster transitions, historical publication clocks and coherent contract-specific outcome distributions remain research dependencies. Public NGS summaries are not full tracking data. Newly collected observations cannot be inserted into historical folds under invented availability times.

## Provenance and reproducibility

The [aggregate export](evidence/2026-10-25.json) records the private owner-return digest and the scope of each public claim. It deliberately omits individual predictions and exact active recipes. The [public synthetic example](../examples/review_lab/README.md) independently demonstrates chronology, scoring and recovery behavior; its outputs are not these real football metrics.

The original [V065 publication](status/football_v065/README.md), [prepared V066 record](status/football_v066/README.md) and [historical model card](MODEL_CARD.md) remain preserved. Their older pending statuses describe those publications, not this current snapshot.
