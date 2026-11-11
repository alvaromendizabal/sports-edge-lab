"""Public source-separated snapshot checks; no fitting or metric rescoring."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import unittest


ROOT=Path(os.environ.get('NBA_SNAPSHOT_TEST_DIR',Path(__file__).parent))
SPEC=importlib.util.spec_from_file_location('nba_public_snapshot_validator',ROOT/'validate_research_snapshot.py')
VALIDATOR=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(VALIDATOR)


class SourceSeparatedSnapshotTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved=json.loads((ROOT/'latest_research_outputs.json').read_bytes())

    def test_complete_observed_schedule_and_saved_output_contract(self):
        checks=VALIDATOR.validate_public_report(self.saved)
        self.assertEqual(checks['official_schedule_games'],self.saved['coverage']['official_schedule_games'])
        self.assertEqual(checks['all_game_target_horizon_cells'],6*len(self.saved['games']))

    def test_schedule_and_result_clocks_remain_distinct(self):
        rows=[game for game in self.saved['games'].values() if game.get('result_observation')]
        self.assertEqual(len(rows),self.saved['result_observation_recovery'].get('result_rows_attached',0))
        for game in rows:
            result=game['result_observation']
            self.assertEqual(game['last_confirmed_status'],'FINAL')
            self.assertEqual(game['last_confirmed_status_asof_utc'],result['observed_at_utc'])
            self.assertEqual(game['official_status_at_source'],game['source_status'])
            self.assertFalse(result['original_historical_possession_claim'])
            self.assertFalse(result['new_score_calculation'])

    def test_count_only_live_status_cannot_be_assigned_to_an_unidentified_game(self):
        changed=copy.deepcopy(self.saved)
        game=next(row for row in changed['games'].values()
                  if row['source_status']=='SCHEDULED' and not row.get('result_observation'))
        game['last_confirmed_status']='LIVE'
        with self.assertRaisesRegex(ValueError,'not supported'):
            VALIDATOR.validate_public_report(changed)

    def test_aggregate_row_disagreement_cannot_be_hidden(self):
        changed=copy.deepcopy(self.saved)
        if not changed['coverage']['latest_row_and_source_aggregate_difference']:
            # Invent an aggregate-only discrepancy while preserving its total.
            # No identified game row supplies this LIVE state.
            counts=changed['result_observation_recovery']['source_reported_status_counts']
            counts['FINAL']-=1;counts['LIVE']=counts.get('LIVE',0)+1
        changed['coverage']['latest_row_and_source_aggregate_difference']={}
        with self.assertRaisesRegex(ValueError,'discrepancy hidden'):
            VALIDATOR.validate_public_report(changed)

    def test_results_cannot_be_redated_to_future_publication(self):
        changed=copy.deepcopy(self.saved)
        result=next(row['result_observation'] for row in changed['games'].values() if row.get('result_observation'))
        result['observed_at_utc']='2099-01-01T00:00:00Z'
        with self.assertRaisesRegex(ValueError,'information clock'):
            VALIDATOR.validate_public_report(changed)

    def test_private_model_fields_are_rejected(self):
        changed=copy.deepcopy(self.saved);changed['recipe_id']='PRIVATE_NOT_AUTHORIZED'
        with self.assertRaisesRegex(ValueError,'Private field'):
            VALIDATOR.validate_public_report(changed)


class B076OwnerContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'latest_research_outputs.json').read_bytes())
        cls.previous=json.loads((ROOT/'history/b076_selected_outputs.json').read_bytes())
        cls.audit=json.loads((ROOT/'b077_owner_evidence.json').read_bytes())

    def test_substantive_work_and_failed_packaging_are_separate(self):
        owner=self.data['newest_owner_execution'];work=self.audit['work']
        self.assertEqual(owner['release'],'B076')
        self.assertEqual(owner['observed_exit_code'],3)
        self.assertEqual(owner['new_estimator_fits'],822)
        self.assertEqual(owner['new_forecasts'],196)
        self.assertEqual(work['estimator_fit_reconciliation']['total'],791+3+28)
        self.assertEqual(work['frozen_completed']+work['frozen_deferred'],2328)
        self.assertEqual(work['failed_frozen_tasks'],0)
        self.assertEqual(self.audit['outcome'],owner)
        self.assertFalse(self.audit['V8_continuation']['owner_execution_validated'])

    def test_original_issue_bodies_stay_immutable_when_role_selections_advance(self):
        old,new=self.previous['issues'],self.data['issues']
        shared=set(old)&set(new)
        self.assertEqual(len(shared),1557)
        self.assertEqual(len(set(new)-set(old)),196)
        for key in shared:
            self.assertEqual(old[key],new[key],key)
        self.assertEqual(self.previous['champions'],self.data['champions'])
        self.assertEqual(self.previous['forecast_inventory_game_ids'],self.data['forecast_inventory_game_ids'])
        self.assertEqual(self.data['latest_original_issue_owner_release'],'B076')
        self.assertEqual(self.data['latest_forecast_issue_at_utc'],'2026-11-11T20:00:36.717077+00:00')
        self.assertEqual(self.data['coverage']['original_issued_records_recovered'],2882)
        self.assertEqual(self.data['coverage']['original_issue_horizon_classes']['EARLY_OUTLOOK'],2870)
        pin=hashlib.sha256((ROOT/'history/b076_selected_outputs.json').read_bytes()).hexdigest()
        self.assertEqual(pin,self.audit['public_snapshot']['historical_B076_snapshot_sha256'])

    def test_results_preserve_original_source_clocks_and_all_game_missingness(self):
        for key,game in self.previous['games'].items():
            self.assertEqual(game['schedule_source_asof_utc'],self.data['games'][key]['schedule_source_asof_utc'])
            if game.get('result_observation'):
                prior=game['result_observation'];now=self.data['games'][key]['result_observation']
                for field in ('home_points','away_points','observed_at_utc','available_at_utc','ended_at_utc'):
                    self.assertEqual(prior[field],now[field])
        c=self.data['coverage']
        self.assertEqual(c['official_schedule_games'],1274)
        self.assertEqual(c['official_games_without_original_issues'],1117)
        self.assertEqual(c['all_game_current_role_forecasts_available']+c['all_game_current_role_forecasts_missing'],26532)
        self.assertEqual(c['official_games_by_latest_row_backed_status'],{'FINAL':227,'SCHEDULED':1040,'TBD':7})
        self.assertEqual(c['latest_row_and_source_aggregate_difference'],{})
        recovery=self.data['result_observation_recovery']
        self.assertFalse(recovery['remaining_live_game_identity_recovered'])
        self.assertTrue(recovery['latest_saved_aggregate_matches_identified_rows'])
        self.assertFalse(recovery['full_new_owner_schedule_projection_reconstructed'])

    def test_small_provider_cohorts_do_not_become_promotion_evidence(self):
        market=self.audit['current_matched_provider_comparisons']
        self.assertEqual(market['distinct_reference_matched_games'],6)
        self.assertEqual(market['DraftKings_matched_games'],0)
        self.assertEqual(market['Polymarket_international_matched_games'],0)
        for row in market['saved_same_game_comparisons']:
            self.assertFalse(row['selection_or_promotion_allowed'])
            self.assertEqual(row['fair_probability_games'],0)
            self.assertLessEqual(row['market_qualified_probability_reference_games'],6)
        s=self.audit['science_change']
        self.assertEqual(s['new_candidate_metric_views'],668)
        self.assertEqual(s['new_candidate_paired_comparisons'],2264)
        self.assertEqual(s['new_candidate_positive_adjusted_lower_bound'],0)
        self.assertEqual(s['changed_champion_recipe_roles'],[])
        self.assertFalse(self.audit['low_loss_lead']['verified_full_season_0_40_result'])
        self.assertEqual(self.audit['low_loss_lead']['games'],2)

    def test_public_evidence_does_not_expose_private_recipes_or_source_arrays(self):
        body=(ROOT/'b077_owner_evidence.json').read_text()
        for forbidden in ('recipe_id','/home/','s3://','560403859723','api_key','apiKey','PRIVATE KEY'):
            self.assertNotIn(forbidden,body)
        self.assertEqual(len(self.audit['historical_champions']),44)
        self.assertFalse(self.audit['public_snapshot']['new_fitting_inference_acquisition_or_metric_rescoring_in_publication'])


if __name__=='__main__':unittest.main()
