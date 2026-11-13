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
            counts=dict(changed['result_observation_recovery']['source_reported_status_counts'] or changed['coverage']['official_games_by_latest_row_backed_status'])
            changed['result_observation_recovery']['source_reported_status_counts']=counts
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
        cls.data=json.loads((ROOT/'history/b077_selected_outputs.json').read_bytes())
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


class B077RecoveredContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'history/b077_recovered_selected_outputs.json').read_bytes())
        cls.previous=json.loads((ROOT/'history/b077_selected_outputs.json').read_bytes())
        cls.evidence=json.loads((ROOT/'b078_recovered_b077_evidence.json').read_bytes())

    def test_recovered_issues_do_not_claim_live_refresh_or_new_computation(self):
        self.assertEqual(self.data['newest_owner_execution']['release'],'B077')
        self.assertEqual(self.data['newest_owner_execution']['status'],'FINALIZER_FAILED_CHECKPOINTS_PRESERVED')
        self.assertEqual(self.data['latest_forecast_issue_at_utc'],'2026-11-12T02:02:29.830904+00:00')
        p=self.data['publication_recovery']
        for key in ('new_fits','new_inference','new_metric_calculations','new_forecast_issues'):self.assertEqual(p[key],0)
        self.assertFalse(p['saved_original_B077_export_bytes_recovered'])
        self.assertFalse(p['source_refresh_or_new_forecast_at_publication'])
        self.assertEqual(p['prior_selected_snapshot_sha256'],hashlib.sha256((ROOT/'history/b077_selected_outputs.json').read_bytes()).hexdigest())
        self.assertEqual(self.data['coverage']['distinct_public_selected_issues'],2705)
        self.assertEqual(self.data['coverage']['games_in_original_issued_inventory'],199)
        self.assertEqual(self.data['coverage']['original_issued_records_recovered'],5519)

    def test_unchanged_issues_and_schedule_clocks_are_preserved(self):
        old,new=self.previous['issues'],self.data['issues']
        self.assertEqual(len(set(old)&set(new)),138)
        for key in old.keys()&new.keys():self.assertEqual(old[key],new[key])
        self.assertEqual(set(self.previous['games']),set(self.data['games']))
        for gid,game in self.previous['games'].items():
            for key in ('scheduled_start_utc','schedule_source_asof_utc','source_status','home_team','away_team'):
                self.assertEqual(game[key],self.data['games'][gid][key])

    def test_newer_aggregate_does_not_invent_three_live_game_identities(self):
        self.assertEqual(self.data['coverage']['official_games_by_latest_row_backed_status'],{'FINAL':227,'SCHEDULED':1040,'TBD':7})
        self.assertEqual(self.data['coverage']['latest_row_and_source_aggregate_difference'],{
            'LIVE':{'row_backed':0,'source_aggregate':3},'SCHEDULED':{'row_backed':1040,'source_aggregate':1037}})
        self.assertFalse(self.data['result_observation_recovery']['full_new_owner_schedule_projection_reconstructed'])

    def test_replay_array_and_original_evidence_are_separate(self):
        from collections import Counter
        counts=Counter(row['evidence_track'] for row in self.evidence['metric_rows'])
        self.assertEqual(counts['FROZEN_HISTORICAL'],88)
        self.assertEqual(counts['CURRENT_FIXED_STATE_REPLAY'],90)
        self.assertEqual(counts['SAVED_SEASON_FROZEN_ARRAY']+counts['SAVED_WEEKLY_CURRENT_ARRAY'],38)
        self.assertEqual(counts['ORIGINAL_ISSUED_ROLLING'],32)
        self.assertEqual(self.evidence['completed_current_regular_games'],160)
        self.assertEqual(self.evidence['distinct_original_issue_monitor_games'],6)
        for row in self.evidence['metric_rows']:
            self.assertFalse(row['promotion_allowed'])
            self.assertLessEqual(row['scored_games'],row['completed_game_denominator'])
            if row['evidence_track']=='CURRENT_FIXED_STATE_REPLAY':self.assertFalse(row['original_issue_claim'])

    def test_provider_coverage_and_publication_boundary_remain_explicit(self):
        self.assertEqual(len(self.evidence['provider_comparisons']),24)
        for row in self.evidence['provider_comparisons']:
            self.assertFalse(row['selection_or_promotion_allowed'])
            self.assertEqual(row['fair_probability_games'],0)
            self.assertLessEqual(row['cluster_weeks'],1)
            self.assertLessEqual(row['model_on_same_reference_games']['games'],6)
        for row in self.evidence['provider_coverage']:
            if row['provider']=='DRAFTKINGS' or row['season']!='2026-27':
                self.assertEqual(row['maximum_matched_games_in_one_selected_view'],0)
            self.assertFalse(row['whole_season_provider_performance_available'])
        body=json.dumps(self.evidence)
        for token in ('recipe_id','/home/','s3://','560403859723','apiKey','api_key','feature_names','PRIVATE KEY'):
            self.assertNotIn(token,body)

    def test_display_is_deterministic_from_saved_public_evidence(self):
        spec=importlib.util.spec_from_file_location('nba_b077_display',ROOT/'build_b077_review.py')
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        self.assertEqual(builder.build(check=True)['status'],'PASS')

class B077HistoricalPeakTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.peaks=json.loads((ROOT/'b077_historical_peaks_and_gates.json').read_bytes())

    def test_existing_metrics_original_issues_and_schedule_bytes_are_unchanged(self):
        for name,pin in {'b078_recovered_b077_evidence.json':'74dd8d0632e9efeb1885b410b7c2f5a82129ba5b41f3e2e70114a4aa0e824c1b',
                'history/b077_recovered_selected_outputs.json':'9e6795387c1e64bc6265da04bdd9d4e9fd0fb9860007da7b465549752542149b'}.items():
            self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),pin)

    def test_descriptive_peaks_keep_all_equal_strata_and_coalesce_ties(self):
        rows=self.peaks['historical_peaks']
        expected={(season,horizon,target,metric) for season in ('2024-25','2025-26') for horizon in (60,120)
            for target,metrics in {'winner':('accuracy','log_loss','brier'),'margin':('mae','rmse'),'total':('mae','rmse')}.items() for metric in metrics}
        self.assertEqual({(r['season'],r['horizon_minutes'],r['target'],r['metric']) for r in rows},expected)
        self.assertEqual(len(rows),28);self.assertEqual(sum(r['tied_saved_rows'] for r in rows),31)
        for row in rows:
            self.assertEqual(row['games'],1230);self.assertEqual(row['phase'],'regular')
            self.assertFalse(row['selection_or_promotion_allowed']);self.assertTrue(row['source_row_indexes'])
            self.assertEqual(row['families'],sorted(set(row['families'])))
        self.assertFalse(self.peaks['new_metric_scoring']);self.assertFalse(self.peaks['selection_or_promotion_allowed'])
        text=json.dumps(self.peaks)
        for forbidden in ('recipe_id','s3://','/home/','feature_names','560403859723'):self.assertNotIn(forbidden,text)

    def test_nomination_and_production_requirements_are_not_conflated(self):
        gates=self.peaks['promotion_gates'];history=gates['historical_nomination'];production=gates['registered_production']
        self.assertEqual(history['regular'],{'minimum_games_each_season':250,'minimum_total_games':500,'minimum_week_clusters':30})
        self.assertEqual(history['postseason'],{'minimum_games_each_season':40,'minimum_total_games':80,'minimum_week_clusters':8})
        self.assertFalse(history['positive_paired_interval_is_nomination_requirement'])
        self.assertEqual(production['minimum_matched_games'],500);self.assertEqual(production['minimum_cluster_weeks'],30)
        self.assertFalse(production['automatic_production_promotion'])
        self.assertIn('post-registration',production['prospective_gate']);self.assertIn('independent review',production['prospective_gate'])
        self.assertIsNone(gates['universal_absolute_score_threshold'])

    def test_entry_point_links_current_report_and_preserves_archived_monitor(self):
        repository=ROOT.parents[2]
        page=(repository/'docs/nba/index.html').read_text()
        self.assertIn('id="nba-current-report"',page)
        self.assertIn('href="../../tracks/nba/reports/latest_research_outputs.html"',page)
        self.assertIn('November 3 monitor archive',page)
        self.assertNotIn('latest failed-publication boundary',page)
        archive=(repository/'docs/nba/monitor.html').read_bytes()
        self.assertEqual(hashlib.sha1(f'blob {len(archive)}\0'.encode()+archive).hexdigest(),'e56159f92a39c0bf73385914aa824025b3bb6436')


from test_v9_publication import V9PublicationTests

class V9SavedEvidenceTests(unittest.TestCase):
    def test_v9_cached_display_is_deterministic(self):
        import build_v9_review
        result=build_v9_review.build(check=True)
        self.assertEqual(result['status'],'PASS')
        self.assertEqual(result['observed_games'],1274)
        self.assertFalse(result['new_owner_execution_claim'])

if __name__=='__main__':unittest.main()

