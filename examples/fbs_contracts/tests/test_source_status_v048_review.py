"""Public source checks retain immutable prior assets and never expose new grids."""
from pathlib import Path
import hashlib,json,unittest
ROOT=Path(__file__).resolve().parents[3]
class V048SourceReviewTests(unittest.TestCase):
    def test_all_fifty_prior_data_and_history_files_keep_exact_bytes(self):
        pins=json.loads(Path(__file__).with_name('v048_legacy_asset_pins.json').read_text())
        self.assertEqual(len(pins['files']),50)
        for item in pins['files']:
            raw=(ROOT/item['path']).read_bytes()
            self.assertEqual(len(raw),item['bytes'],item['path'])
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['sha256'],item['path'])
    def test_source_check_is_metadata_only_and_metrics_stay_dated(self):
        status=json.loads((ROOT/'docs/fbs/source-status-v048.json').read_text())
        self.assertEqual(status['counts']['identified_fixtures'],2742)
        self.assertEqual(status['counts']['current_season_completed'],685)
        self.assertEqual(status['research']['new_fits'],0)
        self.assertEqual(status['research']['new_predictions'],0)
        self.assertEqual(status['local_scientific_metric_calculations'],0)
        self.assertEqual(status['capture']['official_current_season_observed_at'],'2026-11-08T23:57:41Z')
        self.assertEqual(status['fixture_result_equivalence']['changed_game_count'],0)
        self.assertNotIn('rows',status)
    def test_newest_metadata_census_has_no_prices_predictions_or_private_locators(self):
        raw=(ROOT/'docs/fbs/market-status-v048.json').read_text();data=json.loads(raw)
        self.assertEqual((data['event_count'],data['target_rows'],data['exact_display_bound_events'],data['exact_display_bound_target_rows']),(67,201,33,99))
        self.assertEqual(data['raw_source_available_t120_rows'],201)
        self.assertEqual(data['source_available_t120_exact_identity_rows'],99)
        self.assertEqual(data['source_available_t60_exact_identity_rows'],99)
        self.assertEqual(data['qualified_model_cover_rows'],0)
        self.assertFalse(data['raw_source_values_public'])
        self.assertEqual(data['new_scientific_evaluations'],0)
        forbidden={'prediction','price','outcomes','source_event_id','source_reference','recipe','model_state','weights','s3_uri','bucket','key','access_token','authorization'}
        def walk(value):
            if isinstance(value,dict):
                self.assertFalse(set(value)&forbidden,set(value)&forbidden)
                for item in value.values():walk(item)
            elif isinstance(value,list):
                for item in value:walk(item)
        walk(data)
        self.assertNotIn('s3://',raw)
        for event in data['events']:
            self.assertFalse(event['qualified_exact_line_cover'])
            self.assertFalse(event['strict_model_input_eligible'])
    def test_data_wrappers_equal_the_exact_json_asset(self):
        for stem,name in [('source-status-v048','FBS_SOURCE_STATUS_V048'),('market-status-v048','FBS_MARKET_STATUS_V048')]:
            raw=(ROOT/f'docs/fbs/{stem}-data.js').read_text()
            prefix='window.'+name+' = '
            self.assertTrue(raw.startswith(prefix));self.assertTrue(raw.endswith(';\n'))
            self.assertEqual(json.loads(raw[len(prefix):-2]),json.loads((ROOT/f'docs/fbs/{stem}.json').read_text()))
if __name__=='__main__':unittest.main()
