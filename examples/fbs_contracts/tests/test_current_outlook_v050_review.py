import datetime as dt
import hashlib
import json
from pathlib import Path
import unittest

PUBLIC = Path(__file__).resolve().parents[3] / 'docs' / 'fbs'


class CurrentOutlookV050ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outlooks = json.loads((PUBLIC / 'forward-outlooks-v050.json').read_text())
        cls.source = json.loads((PUBLIC / 'source-status-v050.json').read_text())
        cls.market = json.loads((PUBLIC / 'market-status-v050.json').read_text())
        cls.games = json.loads((PUBLIC / 'observation-status-v046.json').read_text())['rows']

    def test_every_remaining_exact_fixture_has_one_original_outlook(self):
        # The immutable official metadata supplies the independently existing population.
        remaining = [row for row in self.games if row['season'] == 2026 and not row['completed']]
        exact = {str(row['id']):row for row in remaining if row['kickoff_exact']}
        self.assertEqual((len(remaining), len(exact)), (203, 108))
        rows = self.outlooks['rows']
        self.assertEqual(len(rows), len({row['id'] for row in rows}))
        self.assertEqual(set(exact), {row['id'] for row in rows})
        for row in rows:
            game = exact[row['id']]
            for key in ('season', 'home_id', 'away_id', 'kickoff'):
                self.assertEqual(str(row[key]), str(game[key]), (row['id'],key))
        self.assertEqual(self.outlooks['counts']['unresolved_current_season_kickoffs'],95)

    def test_original_clock_order_and_role_aliases_do_not_inflate_issuance(self):
        parse = lambda value:dt.datetime.fromisoformat(value.replace('Z','+00:00'))
        for row in self.outlooks['rows']:
            self.assertTrue(row['original_issue_verified'])
            clocks = [parse(row[k]) for k in ('information_cutoff_utc','computed_at_utc','issued_at_utc','kickoff')]
            self.assertLessEqual(clocks[0],clocks[1]);self.assertLessEqual(clocks[1],clocks[2]);self.assertLess(clocks[2],clocks[3])
            self.assertEqual(row['horizon'],'CURRENT_ORIGIN_OUTLOOK')
            self.assertTrue(row['role_views_share_one_forecast_identity'])
            self.assertEqual(len(row['role_views']),2)
            self.assertFalse(row['production_promotion'])
        self.assertEqual(self.outlooks['counts']['family_views'],216)
        self.assertEqual(self.outlooks['counts']['original_shadow_outlook_games'],108)
        self.assertEqual(self.outlooks['counts']['original_shadow_scalar_targets'],324)

    def test_missing_close_horizon_cover_calibration_and_outcomes_stay_missing(self):
        for row in self.outlooks['rows']:
            self.assertEqual(set(row['targets']),{'winner','margin','total'})
            for target in row['targets'].values():
                self.assertEqual(target,{'available':True,'values_public':False})
            self.assertEqual(row['qualified_close_horizon_issues'],0)
            self.assertFalse(row['qualified_exact_line_cover'])
            self.assertEqual(row['interval_status'],'SAVED_MODEL_INTERVALS_CALIBRATION_UNPROVED')
        for key in ('qualified_close_horizon_games','qualified_exact_line_cover_games','observed_forward_outcomes'):
            self.assertEqual(self.outlooks['counts'][key],0)

    def test_new_owner_counts_are_separate_from_reused_work_and_source_cells(self):
        work = self.outlooks['owner_work']
        self.assertEqual((work['new_base_fits'],work['adaptive_base_fits'],work['retained_policy_base_fits']), (44,17,27))
        self.assertEqual(work['new_calibration_fits'],0)
        self.assertEqual((work['adaptive_scalar_outputs'],work['retained_policy_scalar_outputs'],work['retrospective_development_scalar_outputs_separate']), (324,1098,4932))
        self.assertEqual((work['retained_output_records_unchanged'],work['old_metric_cohorts_reused'],work['old_selector_records_reused']), (91270,245,36))
        rank = self.outlooks['ranking_research']
        self.assertEqual((rank['materialized_snapshots'],rank['observed_feature_values'],rank['registered_case_count']), (4452,19120,16836))
        self.assertEqual(rank['new_model_fits'],0)
        self.assertEqual(rank['new_evaluated_ranking_gains'],0)
        self.assertEqual(rank['reason_counts'],{'RANKING_TRAINING_SUPPORT_NOT_YET_OBSERVED':16836})

    def test_source_recheck_and_market_metadata_do_not_refresh_scores(self):
        self.assertEqual(self.source['capture']['official_current_season_observed_at'],'2026-11-09T03:22:14Z')
        self.assertEqual(self.source['fixture_result_equivalence']['changed_game_count'],0)
        self.assertEqual(self.source['counts']['current_season_completed'],685)
        self.assertEqual(self.source['original_evidence']['all_official_selectors_replayed'],2742)
        self.assertEqual(self.source['source_raw_receipt_closure'],'PASS_15_ORIGINAL_BODIES_15_STANDALONE_RECEIPTS_15_REQUEST_INDICES')
        self.assertEqual((self.market['event_count'],self.market['target_rows']), (67,201))
        self.assertEqual((self.market['exact_display_bound_events'],self.market['exact_display_bound_target_rows']), (33,99))
        self.assertEqual((self.market['source_available_t120_exact_identity_rows'],self.market['source_available_t60_exact_identity_rows']), (99,99))
        self.assertEqual(self.market['raw_source_available_t120_rows'],201)
        self.assertEqual(self.market['qualified_model_cover_rows'],0)
        old = json.loads((PUBLIC/'evaluation-v049.json').read_text())
        self.assertEqual(old['capture']['source_observed_at'],'2026-11-09T01:35:19Z')
        self.assertEqual({k:len(v['rows']) for k,v in old['scopes'].items()},{'baseline':175,'two_epoch':70,'four_epoch':0})

    def test_public_projection_is_metadata_only_and_script_matches_json(self):
        for stem,name in [('source-status-v050','FBS_SOURCE_STATUS_V050'),('market-status-v050','FBS_MARKET_STATUS_V050'),('forward-outlooks-v050','FBS_FORWARD_OUTLOOKS_V050')]:
            script = (PUBLIC/(stem+'-data.js')).read_text()
            self.assertTrue(script.startswith('window.'+name+'='))
            self.assertEqual(json.loads(script.split('=',1)[1].rstrip().rstrip(';').replace('<\\/','</')),json.loads((PUBLIC/(stem+'.json')).read_text()))
            for blocked in ('s3://','arn:','access_token','signed_url','state_key','private_recipe','feature_columns','original_forecast_record_identity_sha256'):
                self.assertNotIn(blocked,script)
        for row in self.outlooks['rows']:
            for blocked in ('summary','home_win_probability','home_margin','total_points','forecast_identity_sha256','distribution','weights','params','recipe'):
                self.assertNotIn(blocked,row)
        self.assertEqual(self.outlooks['local_scientific_calculations'],0)
        self.assertFalse(self.outlooks['new_numeric_candidate_grid_public'])

    def test_all_sixty_two_prior_assets_and_full_readme_history_are_unchanged(self):
        pins = json.loads(Path(__file__).with_name('v050_legacy_asset_pins.json').read_text())
        self.assertEqual(len(pins['files']),62)
        for item in pins['files']:
            body = (PUBLIC.parents[1]/item['path']).read_bytes()
            self.assertEqual(len(body),item['bytes'],item['path'])
            self.assertEqual(hashlib.sha256(body).hexdigest(),item['sha256'],item['path'])
        history = (PUBLIC/'README-history-v049.md').read_bytes()
        self.assertEqual(hashlib.sha256(history).hexdigest(),'ce8fc3ea30376fdf76cf2654157fb220b9df4a8b798f78f5370fbf6ec7e2f179')
        current = (PUBLIC/'README.md').read_text()
        self.assertIn('## Retained V049 scientific work · reported in the V050 review',current)
        self.assertIn('## Current state · V050',(PUBLIC/'README-history-v051.md').read_text())
        self.assertIn('216 role views are not 216 independent forecasts',current)


if __name__ == '__main__':
    unittest.main()
