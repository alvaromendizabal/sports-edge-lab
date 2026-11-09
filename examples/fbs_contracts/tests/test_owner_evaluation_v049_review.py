import hashlib
import json
from pathlib import Path
import unittest

PUBLIC = Path(__file__).resolve().parents[3] / 'docs' / 'fbs'


class OwnerEvaluationV049ReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads((PUBLIC / 'evaluation-v049.json').read_text())
        cls.source = json.loads((PUBLIC / 'source-status-v049.json').read_text())
        cls.market = json.loads((PUBLIC / 'market-status-v049.json').read_text())

    def test_original_aggregate_projection_and_scope_totals(self):
        raw = (PUBLIC / 'evaluation-v049.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '5af3e6323f7e9843a6f8e844d1b268f6aa0e801d7db34f14dcd57e0407103ab7')
        self.assertEqual({k:len(v['rows']) for k,v in self.report['scopes'].items()}, {'baseline':175,'two_epoch':70,'four_epoch':0})
        self.assertFalse(self.report['forecast_issued'])
        self.assertFalse(self.report['promotion_allowed'])
        self.assertEqual(self.report['local_scientific_calculations'], 0)
        self.assertEqual(self.report['scopes']['four_epoch']['scope_coverage_by_period']['cumulative']['scored_target_outputs'], 0)
        self.assertEqual(self.report['scopes']['two_epoch']['scope_coverage_by_period']['current_week']['scored_target_outputs'], 448)

    def test_all_fifty_four_retained_assets_keep_original_bytes(self):
        pins=json.loads(Path(__file__).with_name('v049_legacy_asset_pins.json').read_text())
        self.assertEqual(len(pins['files']),54)
        root=PUBLIC.parents[1]
        for item in pins['files']:
            body=(root/item['path']).read_bytes()
            self.assertEqual(len(body),item['bytes'],item['path'])
            self.assertEqual(hashlib.sha256(body).hexdigest(),item['sha256'],item['path'])

    def test_exact_matched_cohorts_and_original_missingness(self):
        for scope in self.report['scopes'].values():
            for row in scope['rows']:
                self.assertEqual(row['games'], row['metrics']['games'])
                self.assertEqual(row['exact_game_ids_sha256'],row['metrics']['exact_game_ids_sha256'])
                pair = row.get('paired_control')
                if pair:
                    self.assertTrue(pair['exact_match'])
                    for name in ('model_metrics','reference_metrics'):
                        self.assertEqual(pair[name]['games'],pair['games'])
                        self.assertEqual(pair[name]['exact_game_ids_sha256'],pair['exact_game_ids_sha256'])
                    self.assertNotIn('seed',pair['uncertainty'])
                if row['target']!='winner':
                    for name in ('interval80_games','interval95_games','saved_same_outcome_crps_games'):
                        self.assertLessEqual(row['metrics'][name],row['games'])
        current = [r for r in self.report['scopes']['baseline']['rows'] if r['period']=='2026' and r['target']=='winner']
        self.assertEqual({r['games'] for r in current}, {682,685})
        cat = next(r for r in current if r['family']=='v040/catboost')
        self.assertEqual(cat['paired_control']['reference_metrics']['games'],682)

    def test_source_and_evaluation_clocks_are_distinct_from_last_result_change(self):
        self.assertEqual(self.source['capture']['official_current_season_observed_at'],'2026-11-09T01:35:19Z')
        self.assertEqual(self.source['counts']['current_season_completed'],685)
        self.assertEqual(self.source['fixture_result_equivalence']['changed_game_count'],0)
        self.assertEqual(self.source['owner_evidence']['new_fits'],0)
        self.assertEqual(self.source['owner_evidence']['completed_baseline_metric_cohorts'],175)
        self.assertEqual(self.report['capture']['source_observed_at'],self.source['capture']['official_current_season_observed_at'])
        original = json.loads((PUBLIC / 'observation-status-v046.json').read_text())
        self.assertEqual(original['original2026_source_observed_at'],'2026-11-08T19:34:42Z')

    def test_raw_and_exact_source_denominators_remain_separate(self):
        self.assertEqual(self.market['target_rows'],201)
        self.assertEqual(self.market['event_count'],67)
        self.assertEqual(self.market['exact_display_bound_target_rows'],99)
        self.assertEqual(self.market['raw_source_available_t120_rows'],201)
        self.assertEqual(self.market['source_available_t120_exact_identity_rows'],99)
        self.assertEqual(self.market['source_available_t60_exact_identity_rows'],99)
        self.assertEqual(self.market['qualified_model_cover_rows'],0)
        self.assertEqual(self.market['new_scientific_evaluations'],0)

    def test_standalone_assets_match_data_scripts_and_exclude_private_fields(self):
        for stem,name in [('source-status-v049','FBS_SOURCE_STATUS_V049'),('market-status-v049','FBS_MARKET_STATUS_V049'),('evaluation-v049','FBS_EVALUATION_V049')]:
            data=json.loads((PUBLIC/(stem+'.json')).read_text())
            script=(PUBLIC/(stem+'-data.js')).read_text()
            self.assertTrue(script.startswith('window.'+name+'='))
            self.assertEqual(json.loads(script.split('=',1)[1].rstrip().rstrip(';').replace('<\\/','</')),data)
            for blocked in ('s3://','arn:','access_token','signed_url','feature_columns','state_key','private_recipe'):
                self.assertNotIn(blocked,script)

    def test_preserved_readme_history_is_not_rewritten_as_current(self):
        history=(PUBLIC/'README-history-v048.md').read_text()
        current=(PUBLIC/'README-history-v049.md').read_text()  # Exact historical V049 README retained by the successor.
        self.assertIn('## Current state · V048',history)
        self.assertIn('## Current state · V049',current)
        self.assertIn('evaluation of the two',history.lower())
        self.assertNotIn('awaits owner evaluation',current)


if __name__=='__main__':
    unittest.main()
