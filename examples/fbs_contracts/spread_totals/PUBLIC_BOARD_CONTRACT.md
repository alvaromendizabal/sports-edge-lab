# FBS Spread & Totals public presentation contract

The source is `fbs.spread-totals.public-board.v1`. The builder validates a qualified public export; it never fits, calibrates, creates contract probabilities, settles contracts, or fabricates a quote. All source evidence remains with the owner. Do not pass a private owner report directly to this renderer.

## Required structure

`owner` is `fbs`; `product` is `Spread & Totals`. The top-level objects are `release`, `clocks`, `selection`, `population`, `models`, and `publication`. The arrays are `games`, `contracts`, `missing_inputs`, `performance`, and `provenance`. `graphics` and `source_coverage` are optional. Unknown top-level fields are rejected.

`release` supplies `label`, `status`, `owner_execution_status`, `new_model_fits`, and `notice`. `clocks` supplies timezone-aware `generated_at`, `forecast_as_of`, nullable `market_as_of`, and `forecast_horizon`. `population.manifest_games` counts every retained game and `current_week_games` counts the Pacific-week view. The source export must not shrink that manifest for missing forecasts or contracts.

`selection` supplies `validation_seasons: [2024,2025]`, `test_season: 2026`, `primary_weights: [0.5,0.5]`, `test_used_for_selection: false`, `training_year_reweighting: false`, and the exact preregistered `primary_strike_rule`. The presentation does not choose a strike using outcomes.

`selection` describes the inherited forecasts actually displayed. A separately prepared campaign can appear in `release.next_research`, with status `PREPARED_AWAITING_OWNER_LAUNCH`, scope `["margin","total"]`, training seasons `[2024,2025]`, selection season `2026`, regime `2026_EXPOSED_VALIDATION`, and explicit prior exposure. The prepared status must retain `forecast_snapshot_replaced: false`, `new_fits_reported: 0`, and `new_calibrations_reported: 0`; it cannot relabel the displayed predictions or count unexecuted work. `prospective_test` describes the future launch-time boundary. Only public campaign summaries and runtime controls belong here, never private feature recipes or fitted states. A future executed export requires its own verified scientific authority and compatible presentation schema.

`release.next_research.weather_campaign` is optional preparation metadata. It records a finite positive `registered_base_fit_jobs`, status `REGISTERED_NOT_EXECUTED`, and zero `completed_base_fit_jobs`, `new_calibration_fits` and `forecast_rows_published`. Its public source, roof-state and finite-comparison qualifications must be nonempty. It cannot announce realized weather coverage or newly fitted forecasts before an executed scientific export is separately admitted. A venue's structural dome flag does not establish a retractable roof's position at a particular game.

`release.latest_owner_execution` can summarize a verified return with measured fit, calibration, scoring and rejected-callback counts kept separate. Its evidence fingerprint belongs in `provenance`. A partial failure stays partial even when earlier commits or scoring work were preserved.

`release.latest_owner_execution` may also describe an observed failed execution whose final return was not created, provided the status says so and saved-work claims have independent physical integrity evidence. `release.previous_verified_return` keeps the earlier verified return separate; its counters must never be rendered as the newer run’s work.

`release.recovery_audit` carries only aggregate counts and generic repair descriptions. Completed prediction partitions plus saved states still needing export must equal the saved base-fit count. Saved base fits plus conditionally remaining fits must equal qualified jobs; qualified plus source-blocked jobs must equal the registered budget. The condition must disclose exact identity matching and launch-time reconciliation. Native readiness requires verified executable and self-test evidence. Preparation cannot claim an executed owner run, changed scientific callbacks or newly selected champions. Private model identities, artifact locations and recipes remain excluded.

`models` maps public aliases such as `P06` to only `name`, `family`, `role`, `calibration_status` and `selection_objective`. Exact private feature transforms, parameters and model recipes are excluded.

## Game rows

Each row has `game_id`, `home`, `away`, nullable `kickoff_utc`, `status` (`scheduled`, `completed`, `postponed`, `canceled`, `unavailable`), `is_current_week`, optional observed `home_score` and `away_score`, and:

- `winner`: `home_probability`, `model`, `calibration_status`, optional `gap_reason`. Calibration is `fitted`, `fitted_component_blend`, `identity`, or `unknown`; only the first two receive a calibrated display label.
- `margin`: `home_minus_away`, `model`, optional `gap_reason`. The page derives the named point favorite from this explicitly signed value.
- `total`: `points`, `model`, optional `gap_reason`.
- `forecast_kind`, nullable `forecast_as_of`, nullable `nominal_cutoff_utc`, `forecast_horizon`, and `original_issued`.

Missing predictions are null with a reason. No zero placeholder or substitute champion is allowed.

## Exact binary contract rows

Each row has a public `contract_id`, `game_id`, `market` (`spread` or `total`), `source: Kalshi`, exact `proposition`, `strike`, `operator` (`>`, `>=`, `<`, `<=`), `basis` (`home_margin`, `away_margin`, `total`), `period`, `terms_summary`, optional exact public `source_url` and `terms_url`, `equality_settles`, `settlement_status`, public `model`, `forecast_as_of`, `observed_at`, and `forecast_horizon`.

When `probability_qualified` is true, `p_yes` and `p_no` must be finite complements in [0,1]. The row must affirm `integer_mass_preserved`, `orientation_checked`, and `monotonicity_checked`; `comparable_group` binds comparable strikes. `most_probable_side` is only `YES` or `NO`. Comparable upper-tail probabilities must decrease with increasing strike; lower-tail probabilities must increase. Equality follows the operator, without a half-point adjustment or half-credit.

When probability qualification is false, `p_yes`, `p_no`, and `most_probable_side` must be null and `gap_reason` is required. The proposition may still appear as an observed alternative.

An authenticated contract can separately carry `point_baseline_side`, `point_baseline_model`, `point_baseline_value` (oriented to its exact basis), and `point_baseline_comparison_checked: true`. The selected side must match the actual strict/inclusive comparison of that supplied point value with the strike. This is labeled a **point-estimate baseline**, never a binary probability, calibrated threshold model, or probability-ranked pick. Unqualified baselines are shown chronologically in a separate table and phone pages. No invented half-point adjustment is used.

`primary_for_game` is boolean; at most one contract per game and market may be primary. Alternatives stay attached. `settlement_status` is `pending`, `YES`, `NO`, `canceled`, `void`, `fair_price`, or `unavailable`; neither tie nor push is a trading side. Exceptional fair-price settlement is retained outside the binary ranking and requires its own status evidence.

`sides.YES` and `sides.NO` may contain `executable_price` in units of dollars per $1 payout, `executable_at_observation`, exact `observed_at`, `fee_per_contract`, `fees_qualified`, `expected_net_per_contract`, and `return_method`. Executability and a quote clock are mandatory when a price is shown. Net returns additionally require qualified probability, price, fees, and the supplied return convention. `best_return_side` stays null when unsupported. It is distinct from `most_probable_side`. A dated best ask can instead be shown as `observed_ask_price`, `observed_ask_at` and `observed_ask_status` (`CURRENT`, `STALE`, `CLOSED`, `UNQUALIFIED`). A stale or closed observation cannot populate the executable-price field or a price-based net-return ranking.

## Gaps, performance and publication

`missing_inputs` rows have `game_id`, `market` or `input`, `code`, and `detail`. Preserve canceled, void, pending and unavailable conditions here where relevant. `performance` rows have `scope`, `season`, `model`, `metric`, `value` or `display_value`, `scored_n`, `expected_n`, `qualification`, and optional `uncertainty`. Original cards, updated test diagnostics, all-game contract evaluation and ranked subsets remain separate scopes.

`source_coverage` contains sanitized current provider/bookmaker/season/target/horizon counts, observation clocks, full manifest denominators, weekly matches and gap counts. Every row retains `CURRENT_REFERENCE_ONLY_NO_SCORED_COMPARISON`; a current The Odds API reference cannot establish historical pregame possession, native exchange terms or a scored benchmark. Requested zero-coverage bookmakers remain visible. Raw provider responses and historical quote arrays are excluded.

`publication` supplies truthful `source_state`, `deployment_state`, `site_url`, `last_verified_site_version`, and optional short `graphics_status_label`. Source publication, Site deployment and scientific production promotion remain distinct. `provenance` contains only public evidence labels and SHA-256 fingerprints.

## Reproducible outputs

Run the phone renderer on the checked public dataset, optionally attach its index, then build the standalone HTML. Phone graphics are 1290 × 2796 pixels, with checked text bounds and paginated game/qualified ranking cards. They retain the release, clock, coverage and qualification. `graphics.science_sha256` binds the complete dataset excluding the graphic index itself. The pipeline uses Pillow and system DejaVu fonts; no network assets or model execution are involved.

```sh
python examples/fbs_contracts/spread_totals/render_phone_cards.py --data docs/fbs/spread-totals/board.json --output docs/fbs/spread-totals/graphics --attach-index
python examples/fbs_contracts/spread_totals/build_board.py --data docs/fbs/spread-totals/board.json
python examples/fbs_contracts/spread_totals/build_board.py --data docs/fbs/spread-totals/board.json --check
```

Do not label a generated preview as deployed before an actual native deployment receipt exists. The parent release owns final public export qualification and the exact source push/deployment sequence.
