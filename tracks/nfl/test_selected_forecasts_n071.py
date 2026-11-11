"""Public selected outputs, denominator and page consistency; no real fitting."""
import copy
import json
from pathlib import Path
import unittest
from selected_review_n071 import render

HERE=Path(__file__).resolve().parent

class SelectedForecastPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.data=json.loads((HERE/'selected_forecasts_n071.json').read_bytes())
    def test_page_exactly_matches_saved_projection(self):
        self.assertEqual((HERE/'season_review_n071.html').read_text(),render(self.data))
    def test_complete_schedule_and_target_denominators(self):
        d=self.data;games=d['games'];counts=d['counts']
        self.assertEqual(len(games),counts['schedule_games'])
        self.assertEqual(len({g['game_id']for g in games}),len(games))
        self.assertEqual(sum(g['completed_in_saved_census']for g in games),counts['completed_games'])
        self.assertEqual(sum(g['official_time_tbd']for g in games),counts['official_time_tbd_games'])
        self.assertTrue(all(set(g['targets'])=={'win','margin','total'}for g in games))
    def test_all_evidence_union_is_explicit_and_not_forward_score(self):
        groups=('current_forecasts','earlier_saved_forward','prior_selected_reconstruction')
        count=sum(any(panel[group]for panel in g['targets'].values()for group in groups)for g in self.data['games'])
        self.assertEqual(count,self.data['counts']['games_with_any_preserved_evidence'])
        self.assertEqual(len(self.data['games'])-count,self.data['counts']['games_without_prediction_evidence_in_this_projection'])
        self.assertFalse(self.data['automatic_promotion'])
        self.assertEqual(self.data['new_model_fits'],0)
        self.assertEqual(self.data['new_model_inference'],0)
        self.assertEqual(self.data['new_forecast_issues'],0)
    def test_tbd_placeholder_is_not_a_clock(self):
        for game in self.data['games']:
            if game['official_time_tbd']:
                self.assertIsNone(game['kickoff_utc'])
                self.assertTrue(all(not panel['current_forecasts']for panel in game['targets'].values()))
    def test_current_issue_role_availability_is_exact(self):
        for game in self.data['games']:
            for panel in game['targets'].values():
                aliases={r['model_alias']for r in panel['current_forecasts']}
                for role in panel['roles']:
                    self.assertEqual(role['current_forecast_available'],role['model_alias']in aliases)
                    if not role['current_forecast_available']:self.assertTrue(role['missing_reason'])
    def test_reconstructed_rows_do_not_acquire_original_issue(self):
        for game in self.data['games']:
            for panel in game['targets'].values():
                for row in panel['prior_selected_reconstruction']:
                    self.assertIsNone(row['original_issue_at_utc'])
                    self.assertEqual(row['evidence_kind'],'historical_reconstruction')
                    self.assertIn('never originally issued',row['evidence_class'])
    def test_no_private_material_or_full_precision_candidate_grid(self):
        text=json.dumps(self.data)
        for token in ('recipe_id','private_source_index','s3://','/home/sagemaker-user','/workspace/','model_pointer','raw_provider_url'):
            self.assertNotIn(token,text)
        self.assertFalse(self.data['evidence_checks']['full_candidate_grid_published'])
        self.assertFalse(self.data['rounding']['metrics_from_rounded_values'])
    def test_season_scorecards_preserve_exposed_role(self):
        roles=self.data['selected_historical_roles']
        self.assertEqual(len({r['role_id']for r in roles}),len(roles))
        for role in roles:
            self.assertEqual(role['selection_seasons'],[2024,2025])
            for card in role['season_metrics']:
                self.assertEqual(card['selection_exposure'],'DEVELOPMENT_EXPOSED')
                self.assertIn(card['season'],(2024,2025))
    def test_html_data_cannot_escape_script_container(self):
        value=copy.deepcopy(self.data);value['qualifications'].append('</script><script>unsafe()</script>')
        self.assertNotIn('</script><script>unsafe()</script>',render(value))

    def test_failed_owner_run_does_not_replace_selected_issues(self):
        previous=json.loads((HERE/'selected_forecasts_n070.json').read_bytes())
        self.assertEqual(self.data['selected_historical_roles'],previous['selected_historical_roles'])
        for old,new in zip(previous['games'],self.data['games']):
            self.assertEqual(old['targets'],new['targets'])
            self.assertEqual(old['source_observed_at_utc'],new['source_observed_at_utc'])
            self.assertEqual(old['kickoff_utc'],new['kickoff_utc'])
            self.assertGreater(new['latest_schedule_observed_at_utc'],old['source_observed_at_utc'])
    def test_new_source_observations_do_not_claim_model_progress(self):
        run=self.data['latest_owner_execution'];src=self.data['latest_source_refresh']
        self.assertIsNone(run['new_native_fits']);self.assertIsNone(run['new_meta_fits'])
        self.assertIsNone(run['new_forecast_issues']);self.assertTrue(run['current_invocation_closure'])
        self.assertEqual(run['verified_new_fit_minimum'],0);self.assertEqual(run['verified_new_issue_minimum'],0)
        self.assertTrue(run['unknown_totals_preserved']);self.assertEqual(run['selected_model_phase_failures'],2)
        self.assertEqual(run['project_cpu_cap'],12);self.assertEqual(run['observed_native_fit_concurrency'],0)
        self.assertTrue(run['failure_pressure_snapshot_available'])
        self.assertFalse(run['external_final_return_completion_checked']);self.assertFalse(run['full_historical_source_closure'])
        self.assertEqual(src['new_normalized_market_rows'],464)
        self.assertEqual(sum(r['normalized_rows']for r in src['provider_coverage']),464)
        self.assertEqual(src['qualified_current_market_winner_baseline_rows'],0)
        self.assertFalse(src['all_sources_complete']);self.assertFalse(src['model_predictions_refreshed'])
    def test_source_missingness_denominators_are_explicit(self):
        for provider in ('kalshi','polymarket'):
            rows=[g['current_source_coverage'][provider]for g in self.data['games']]
            self.assertEqual(sum(r['observation_status']=='CAPTURED_WITH_TARGET_GAPS'for r in rows),27)
            self.assertEqual(sum(r['observation_status']=='NOT_REFRESHED_FOR_THIS_GAME_IN_N070'for r in rows),245)
            self.assertTrue(all(not r['metric_eligible']for r in rows))
        self.assertTrue(all(not g['current_source_coverage']['draftkings']['metric_eligible']for g in self.data['games']))

    def test_actual_source_refresh_is_separate_from_original_issue_clocks(self):
        self.assertEqual(self.data['latest_owner_execution']['release'],'N070')
        self.assertTrue(all(g['latest_schedule_observation_release']=='N070' for g in self.data['games']))
        src=self.data['latest_source_refresh']
        self.assertTrue(src['observed_schedule_from_utc'].startswith('2026-11-11T04:05:'))
        self.assertEqual(src['outcome_or_confirmed_schedule_changes_from_previous_display'],0)
    def test_resource_refusal_does_not_hide_prior_model_failures(self):
        run=self.data['latest_owner_execution']
        self.assertEqual(run['selected_model_phase_failures'],2)
        self.assertEqual(run['reported_resource_refusal'],'EXTERNAL_IO_PRESSURE')
        self.assertEqual(run['selected_model_failure'],'BUNDLED_SELECTION_METADATA_CONTRACT_MISMATCH')
        self.assertEqual(run['public_export_failure'],'RETAINED_SOURCE_VERSION_PREFIX_MISMATCH')
        self.assertIn('unproved',run['failure_pressure_interpretation'])

if __name__=='__main__':unittest.main()
