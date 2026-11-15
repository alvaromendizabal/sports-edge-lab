import copy
import gzip
import hashlib
import json
import unittest
from pathlib import Path
import build_season_comparison as b

class SeasonComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selected, _ = b.read_json(b.ROOT / 'latest_research_outputs.json.gz')
        cls.review, _ = b.read_json(b.ROOT / 'latest_model_review.json')
        cls.acceptance, _ = b.read_json(b.ROOT / 'latest_v9_acceptance.json.gz')
        cls.leaders, _ = b.read_json(b.ROOT / 'current_saved_cohort_leaders.json')
        cls.projected = b.project(cls.selected, cls.review, cls.acceptance, cls.leaders)

    def test_complete_observed_schedule_without_claiming_unobserved_slots(self):
        self.assertEqual({r['game_id'] for r in self.projected['games']}, set(self.selected['games']))
        self.assertEqual(len(self.projected['games']), self.acceptance['coverage']['observed_games'])
        self.assertEqual(self.projected['coverage']['unobserved_regular_slots'], self.acceptance['coverage']['unobserved_regular_slots'])
        self.assertFalse(self.projected['coverage']['full_season_completion_claim'])

    def test_market_gaps_never_become_zero_prices_or_quote_clocks(self):
        for row in self.projected['games']:
            self.assertEqual(set(row['markets']), set(b.PROVIDERS))
            for market in row['markets'].values():
                self.assertIsNone(market['value'])
                self.assertIsNone(market['provider_quote_at_utc'])
                self.assertIsNone(market['observed_at_utc'])
                self.assertEqual(market['status'], 'ROW_LEVEL_OBSERVATION_NOT_EXPORTED')
        self.assertFalse(self.projected['market_coverage_complete'])

    def test_aggregate_comparisons_copied_without_rescoring_or_inflation(self):
        self.assertEqual(self.projected['matched_comparisons'], self.review['venue_comparisons'])
        self.assertEqual(self.projected['provider_coverage'], self.review['venue_coverage'])
        for effect in self.projected['publication_effects'].values(): self.assertEqual(effect, 0)

    def test_original_issue_value_and_clock_preserved(self):
        index = {r['game_id']: r for r in self.projected['games']}
        checked = 0
        for row in self.selected['role_views']:
            source = self.selected['issues'].get(row.get('current_issue_ref'))
            if not source: continue
            public = index[row['game_id']]['forecasts'][row['champion_role']]
            for key in ['prediction','issued_at_utc','source_asof_utc','issue_horizon_class','actual_lead_minutes']:
                self.assertEqual(public[key], source.get(key))
            checked += 1
        self.assertGreater(checked, 0)

    def test_older_champion_issue_cannot_fill_missing_current_role(self):
        selected = copy.deepcopy(self.selected)
        view = next(v for v in selected['role_views'] if v.get('current_issue_ref'))
        view['at_issue_ref'] = view['current_issue_ref'];view['current_issue_ref'] = None
        selected['role_views'] = [view]
        projected = b.project(selected,self.review,self.acceptance,self.leaders)
        game = next(g for g in projected['games'] if g['game_id']==view['game_id'])
        self.assertNotIn(view['champion_role'], game['forecasts'])

    def test_wrong_game_issue_rejected(self):
        selected = copy.deepcopy(self.selected)
        view = next(v for v in selected['role_views'] if v.get('current_issue_ref'))
        selected['issues'][view['current_issue_ref']]['game_id'] = 'invented-mismatch'
        with self.assertRaisesRegex(ValueError,'Issue/game mismatch'):
            b.project(selected,self.review,self.acceptance,self.leaders)

    def test_no_original_issue_credit_for_later_reconstruction(self):
        selected = copy.deepcopy(self.selected)
        view = next(v for v in selected['role_views'] if v.get('current_issue_ref'))
        selected['issues'][view['current_issue_ref']]['original_pregame_issue'] = False
        with self.assertRaisesRegex(ValueError,'original pregame'):
            b.project(selected,self.review,self.acceptance,self.leaders)

    def test_owner_summary_drops_private_paths_and_identifiers(self):
        private = {'release':'B086','status':'PARTIAL','private_path':'s3://secret/key',
                   'account':'123456789012','recipe':'private_recipe','credentials':'bad',
                   'new_estimator_method_returns':0}
        out = b.project(self.selected,self.review,self.acceptance,self.leaders,private)
        self.assertEqual(set(out['owner_execution']), {'release','status','new_estimator_method_returns'})

    def test_champion_historical_metrics_preserved_no_automatic_promotion(self):
        self.assertEqual(self.projected['champions'], self.selected['champions'])
        self.assertEqual(self.projected['saved_current_cohort_leaders'], self.leaders['rows'])
        for champion in self.projected['champions'].values():
            self.assertFalse(champion['automatic_production_promotion'])

    def test_public_page_remains_basketball_specific(self):
        raw, html = b.build()
        forbidden = 'ci' + 'rca'
        self.assertNotIn(forbidden, raw.decode().lower())
        self.assertNotIn(forbidden, html.decode().lower())

    def test_projection_does_not_modify_original_evidence(self):
        before = json.dumps([self.selected,self.review,self.acceptance,self.leaders],sort_keys=True)
        b.project(self.selected,self.review,self.acceptance,self.leaders)
        self.assertEqual(before,json.dumps([self.selected,self.review,self.acceptance,self.leaders],sort_keys=True))

    def test_generated_data_and_page_match_authoritative_inputs(self):
        raw, html = b.build()
        self.assertEqual(gzip.decompress((b.ROOT/'season_comparison.json.gz').read_bytes()),raw)
        self.assertEqual((b.ROOT/'season_comparison.html').read_bytes(),html)

    def test_actual_current_projection_preserves_separate_source_clocks(self):
        raw, _ = b.build();value=json.loads(raw)
        self.assertIn('market_comparison_evidence_as_of_utc',value)
        self.assertIn('game_inventory_evidence_as_of_utc',value)
        self.assertEqual(value['publication_effects']['new_forecasts'],0)
        for row in value['games']:
            for forecast in row['forecasts'].values():
                self.assertIsNotNone(forecast['issued_at_utc'])
                self.assertIsNotNone(forecast['source_asof_utc'])

    def test_active_public_data_excludes_exact_recipes_and_private_paths(self):
        raw, _=b.build();text=raw.decode()
        for key in ['"recipe_id"','"cohort_id"','"role_id"','/home/sagemaker-user','s3://','"recovered_native_constructor"','"base_names"']:
            self.assertNotIn(key,text)

    def test_current_inventory_keeps_every_final_and_separates_secondary_observations(self):
        raw,_=b.build();data=json.loads(raw)
        self.assertEqual(len(data['games']),1274)
        finals=[r for r in data['games'] if r['status']=='FINAL']
        self.assertEqual(len(finals),250)
        self.assertEqual(sum(r['phase']=='regular' for r in finals),183)
        self.assertTrue(all(isinstance(r['actual']['home_points'],(int,float)) for r in finals))
        self.assertEqual(data['coverage']['secondary_observations'],3)
        self.assertEqual(data['coverage']['unobserved_regular_slots'],24)

    def test_reference_coverage_never_exports_price_or_invents_quote_clock(self):
        raw,_=b.build();data=json.loads(raw)
        rows=[r for g in data['games'] for r in g['markets'].values() if r['status']=='PREGAME_WINNER_REFERENCE_RETAINED_PRICE_NOT_PUBLIC']
        self.assertEqual(len(rows),68)
        self.assertTrue(all(r['value'] is None and r['provider_quote_at_utc'] is None for r in rows))
        self.assertTrue(all(not r['matched_to_selected_model_cutoff'] for r in rows))
        self.assertEqual(data['publication_effects']['new_scoring'],0)

    def test_reference_rejects_wrong_game_future_observation_and_unqualified_price(self):
        raw,_=b.build();data=json.loads(raw)
        reference=next(r for g in data['games'] for r in g['markets'].values() if r.get('target')=='winner')
        for patch,reason in [({'home_team':'wrong'},'identity'),({'observed_at_utc':'2099-01-01T00:00:00Z'},'pregame'),({'value':0.5},'price')]:
            r=copy.deepcopy(reference);r.update(patch)
            with self.assertRaisesRegex(ValueError,reason):b.apply_reference_coverage(copy.deepcopy(data),{'rows':[r]})

    def test_current_science_keeps_different_cohorts_and_no_promotion(self):
        raw,_=b.build();data=json.loads(raw)['current_science_scores']
        pair=data['current_winner_matched_comparison']
        self.assertEqual(pair['matched_games'],128)
        self.assertFalse(pair['provider_baseline_comparison'])
        self.assertFalse(pair['promotion_allowed'])
        for row in data['new_frontier_current_ablations']:
            self.assertEqual(row['baseline_metrics']['games'],139)
            self.assertFalse(row['promotion_allowed'])

    def test_row_bound_inventory_reconciles_without_treating_unbound_as_absent(self):
        raw,_=b.build();data=json.loads(raw)
        counts={p:sum(g['markets'][p]['bound_observations'] for g in data['games']) for p in b.PROVIDERS}
        self.assertEqual(counts,{'DRAFTKINGS':0,'KALSHI':20918,'POLYMARKET_US':560,'POLYMARKET_INTERNATIONAL':0})
        self.assertEqual(data['provider_game_coverage']['summary']['KALSHI']['bound_games'],80)
        self.assertEqual(data['provider_game_coverage']['summary']['POLYMARKET_US']['bound_games'],73)
        self.assertEqual(data['provider_game_coverage']['summary']['POLYMARKET_INTERNATIONAL']['unbound_observations'],7308)
        self.assertTrue(all(g['markets']['POLYMARKET_INTERNATIONAL']['status']=='NO_CANONICAL_BINDING_IN_AUDITED_SNAPSHOT' for g in data['games']))

    def test_source_readiness_keeps_forecast_issuance_separate(self):
        raw,_=b.build();data=json.loads(raw)
        progress=data['current_science_scores']['future_source_progress']
        self.assertEqual(progress['source_qualified_future_targets'],32)
        self.assertEqual(progress['new_eligible_future_vectors'],64)
        self.assertEqual(progress['existing_feature_count'],63)
        self.assertFalse(progress['new_feature_recipe'])
        self.assertEqual(progress['new_model_fits'],0)
        self.assertEqual(progress['new_forecasts'],0)
        self.assertFalse(progress['full_season_source_or_market_coverage_claimed'])
        self.assertTrue(progress['prior_forecast_and_provider_clocks_unchanged'])
        if not data['current_science_scores'].get('future_forecast_issuance'):
            scheduled=[g for g in data['games'] if g['status']=='SCHEDULED']
            self.assertEqual(len(scheduled),1012)
            self.assertEqual(sum(bool(g['forecasts']) for g in scheduled),980)
            self.assertEqual(sum(not g['forecasts'] for g in scheduled),32)
        self.assertEqual(data['publication_effects']['new_forecasts'],0)

    def test_complete_work_reuse_does_not_claim_new_fits_or_speedup(self):
        raw,_=b.build();data=json.loads(raw)
        reuse=data['current_science_scores']['warm_cache_progress']
        self.assertEqual(reuse['verified_models_reused'],120)
        self.assertEqual(reuse['verified_prediction_rows_reused'],66432)
        self.assertEqual(reuse['new_estimator_fits'],0)
        self.assertEqual(reuse['new_prediction_rows'],0)
        self.assertEqual(reuse['stat_only_unproven_bytes_accepted'],0)
        self.assertFalse(reuse['same_work_speedup_claimed'])
        self.assertFalse(reuse['full_capacity_acceptance_claimed'])
        self.assertFalse(reuse['verifier_event_counts_are_disjoint_unique_files'])

    def test_R3_original_issues_close_only_the_known_scheduled_gap(self):
        raw,_=b.build();data=json.loads(raw)
        issue=data['current_science_scores']['future_forecast_issuance']
        self.assertEqual(issue['new_original_issue_rows'],448)
        self.assertEqual(issue['new_distinct_games'],32)
        self.assertEqual(issue['current_role_views'],704)
        self.assertEqual(issue['new_model_or_calibration_fits'],0)
        self.assertEqual(issue['new_calendar_requests'],0)
        self.assertEqual(issue['source_cache_reuses'],3)
        self.assertFalse(issue['provider_market_coverage_refreshed'])
        scheduled=[g for g in data['games'] if g['status']=='SCHEDULED' and g['phase']=='regular']
        self.assertEqual(len(scheduled),1012)
        self.assertTrue(all(g['forecasts'] for g in scheduled))
        new_games=[g for g in scheduled if any(f['issued_at_utc']>=issue['issue_clocks_utc']['first'] for f in g['forecasts'].values())]
        self.assertEqual(len(new_games),32)
        self.assertEqual(sum(len(g['forecasts']) for g in new_games),704)
        for g in new_games:
            self.assertEqual(len(g['forecasts']),22)
            for f in g['forecasts'].values():
                self.assertEqual(f['issue_horizon_class'],'EARLY_OUTLOOK')
                self.assertEqual(f['source_asof_utc'],issue['feature_asof_utc'])
                self.assertLess(f['issued_at_utc'],f['scheduled_start_at_issue_utc'])
        self.assertEqual(data['coverage']['unobserved_regular_slots'],24)
        self.assertFalse(data['market_coverage_complete'])
        self.assertEqual(data['owner_execution']['release'],'B087-R3')
        self.assertTrue(data['owner_execution']['return_verified'])
        self.assertEqual(data['owner_execution']['return_parts'],8)
        self.assertEqual(data['owner_execution']['exit_code'],2)

if __name__ == '__main__': unittest.main()
