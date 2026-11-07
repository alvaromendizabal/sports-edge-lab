# Sports Edge Lab NFL — complete season research

The active [complete-season dashboard](season_review_n053r1.html) starts from the authenticated **272-game 2026 schedule: 122 completed games and 150 future games**. It includes Chicago–Seattle and Jacksonville–Baltimore, the actual earlier issues for those games, all retained model versions, and equal event coverage for DraftKings, Kalshi and Polymarket.

The actual scientific parent remains **N052**. **N053R1 is prepared, not owner-executed.** The earlier prepared N053 handoff and all original scientific evidence remain preserved. This reporting revision creates zero native fits, zero owner issues and zero source acquisitions.

## Read the evidence

- [Complete 2026 season dashboard](season_review_n053r1.html): every game, selectable model version, explicit provider horizon, actual clocks, specific absence reasons and downloads.
- [Complete season public data](current_season_n053r1.json.gz): all 272 schedule records, full model/game/target cells, full provider/game/target/horizon cells, source-path support and denominator bridges. The compact source decompresses losslessly; the dashboard exports complete ordinary JSON and CSV.
- [Cohort and capability explanation](SEASON_REVIEW_N053R1.md): why the complete season differs from the frozen scientific cohorts.
- [Coverage, chronology and publication contracts](test_season_review_n053r1.py).

## Denominators have explicit roles

| Evidence role | Count | Explanation |
|---|---:|---|
| Complete 2026 schedule | 272 | All 32 teams and every retained scheduled game |
| Completed games at the N052 snapshot | 122 | Includes CHI/SEA, JAX/BAL and one tie |
| Future games at the same snapshot | 150 | A future game remains visible without an invented result or forecast |
| Frozen historical point benchmark | 120 | Excludes CHI/SEA and JAX/BAL; their actual issue evidence is separate |
| Frozen historical winner benchmark | 119 | Excludes the tie from the 120-game point cohort |
| Retained Polymarket T1/T2 reference support | 92 | Includes the tie; this is an older fixed-horizon cohort |
| Retained Polymarket decisive comparisons | 91 | Removes the tie from those 92 supported games |
| Completed minute-path registration | 121 | Excludes JAX/BAL; Kalshi 121 and Polymarket 113 supported paths |

The 29 older Polymarket source gaps have been recovered under exact pinned scope. A separate restored view now covers all 122 completed games, with T1 comparisons on the 119-game native cohort and a matched 119-game three-provider T2 cohort. Its older 92-source / 91-decisive record and 113-game minute paths remain unchanged.

The dashboard presents each provider on the same **122-game completed denominator** and shows its available observations, numeric values and eligible scored records separately. Later source restoration keeps its actual collection time. Direction-only records do not become numeric probabilities.

## Scientific findings remain intact

N052 completed 150 support-versus-content correction states, 41,503 report rows, 165 season metrics, 255 paired comparisons and three nested checks. Selection used 2022–2023; no designation-content variant was chosen. The N051 144-cell / 864-comparison negative result and prior 288-cell injury-only negative result remain unchanged. Neither study was refitted.

Annual, weekly and event reconstructions are historical analyses with their registered earlier-data boundaries. A later reconstruction is not evidence of a real historical issue. Genuine issue timestamps, current feature assembly and reused fit components remain separate fields.

## Active capabilities and frontier

The current view exposes versioned historical models, current original / shadow / fresh / designation issues, injury timing and missingness, three-provider references, source identity gaps and 1 / 3 / 5 / 10-minute path diagnostics. Research preparation is shown separately from completed evidence. Candidate quarterback, rushing, personnel, matchup and market-context features require explicit source-time admission and preregistered validation; listing a candidate does not claim an implemented or successful model.

## Reproduce the active presentation

```bash
python tracks/nfl/build_season_review_n053r1.py --check
python -m unittest discover -s tracks/nfl -p 'test_season_review_n053r1.py'
```

The full NFL suite and browser workflow also validate the unchanged historical views. Release requires exact PR-head checks, a permitted merge, final-main checks and publication provenance. No other sport or shared CI gate is changed by this NFL revision.

## Dated archives

The [N052 audit / N053 preparation view](review_n053.html), [earlier N051 audit](review_n052.html) and [complete historical review](review.html) retain their dated scientific objects and wording. Their cohort counts and preparation labels describe those snapshots; they are not the current season inventory. The active presentation is the complete-season page linked above.
