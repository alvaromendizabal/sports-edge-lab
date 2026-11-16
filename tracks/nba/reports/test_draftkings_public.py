import copy
import hashlib
import json
import unittest

from draftkings_public import project_normalized, download_projection, RIGHTS


class DraftKingsAnalyticalTests(unittest.TestCase):
    def setUp(self):
        self.games = [{'game_id': '0022600001', 'home_team': 'DET', 'away_team': 'BOS',
                       'scheduled_start_utc': '2026-10-20T19:00:00Z'},
                      {'game_id': '0022600002', 'home_team': 'LAL', 'away_team': 'CHI',
                       'scheduled_start_utc': '2026-10-20T21:00:00Z'}]
        self.required = [g['game_id'] for g in self.games]
        self.row = {'official_game_id': '0022600001', 'home': 'DET', 'away': 'BOS',
                    'start_utc': '2026-10-20T19:00:00Z', 'target': 'winner', 'horizon_minutes': 120,
                    'source': 'DraftKings', 'source_provider': 'THE_ODDS_API',
                    'raw_download_authorized': False, 'original_issued_evidence': False,
                    'source_rights_status': RIGHTS, 'public_analytical_display_eligible': True,
                    'comparison_eligible': True, 'status': 'QUALIFIED_HISTORICAL_REFERENCE',
                    'source_quote_time': '2026-10-20T16:58:00Z', 'archive_snapshot_time': '2026-10-20T17:00:00Z',
                    'forecast_cutoff': '2026-10-20T17:00:00Z', 'retrieved_at': '2026-11-16T01:00:00Z',
                    'home_decimal_price': 1.8, 'away_decimal_price': 2.1,
                    'home_win_probability': (1/1.8)/(1/1.8+1/2.1), 'reasons': [],
                    'raw_payload': {'private': 'must not escape'}, 'provider_event_id': 'private-provider-binding'}

    def project(self, rows=None, expected=None):
        source = {'schema': 'sel.nba.b089.market_analytical_projection.v1',
                  'raw_provider_export_authorized': False, 'rows': rows if rows is not None else [self.row],
                  'captures_normalized': 1, 'capture_failures': []}
        raw = json.dumps(source).encode()
        return project_normalized(raw, expected_sha256=expected or hashlib.sha256(raw).hexdigest(),
                                  games=self.games, required_game_ids=self.required)

    def test_missing_capture_keeps_required_population(self):
        result = self.project()
        group = next(g for g in result['coverage'] if g['target']=='winner' and g['horizon_minutes']==120)
        self.assertEqual((group['qualified_games'], group['required_games'], group['missing_or_unqualified_games']), (1,2,1))
        self.assertFalse(group['full_population_market_coverage'])
        self.assertEqual(len(result['coverage']), 6)

    def test_quotes_ui_only_and_no_private_provider_payload(self):
        result = self.project()
        self.assertEqual(result['rows'][0]['home_decimal_price'], 1.8)
        self.assertNotIn('raw_payload', json.dumps(result))
        self.assertNotIn('private-provider-binding', json.dumps(result))
        downloadable = download_projection({'draftkings_analytical': result, 'model_scores': {'log_loss': .5}})
        self.assertNotIn('rows', downloadable['draftkings_analytical'])
        self.assertNotIn('home_decimal_price', json.dumps(downloadable))
        self.assertEqual(downloadable['model_scores']['log_loss'], .5)
        self.assertIn('rows', result)

    def test_wrong_identity_or_population_fails_closed(self):
        self.row['home'] = 'BOS'
        with self.assertRaisesRegex(ValueError, 'identity'): self.project()
        self.row['home'] = 'DET'
        self.required = ['0022600999']
        with self.assertRaisesRegex(ValueError, 'population'): self.project()

    def test_source_fingerprint_and_future_quote_rejected(self):
        with self.assertRaisesRegex(ValueError, 'fingerprint'): self.project(expected='0'*64)
        self.row['source_quote_time'] = '2026-10-20T17:01:00Z'
        with self.assertRaisesRegex(ValueError, 'clock'): self.project()

    def test_duplicate_and_inconsistent_probability_rejected(self):
        with self.assertRaisesRegex(ValueError, 'duplicate'): self.project([self.row, copy.deepcopy(self.row)])
        self.row['home_win_probability'] = .9
        with self.assertRaisesRegex(ValueError, 'normalization'): self.project()

    def test_unqualified_values_never_display(self):
        self.row.update(public_analytical_display_eligible=False, comparison_eligible=False,
                        status='MISSING', reasons=['DRAFTKINGS_ABSENT'])
        result = self.project()
        self.assertIsNone(result['rows'][0]['home_win_probability'])
        self.assertIsNone(result['rows'][0]['home_decimal_price'])

    def test_current_capture_not_registered_horizon_or_original_issue(self):
        self.row.update(horizon_minutes=None, retrieved_at='2026-10-20T17:10:00Z',
                        forecast_cutoff=None, archive_snapshot_time=None,
                        comparison_eligible=False, status='QUALIFIED_CURRENT_REFERENCE')
        result = self.project()
        self.assertEqual(result['qualified_current_reference_slots'], 1)
        self.assertEqual(result['qualified_historical_target_slots'], 0)
        self.row['comparison_eligible'] = True
        with self.assertRaisesRegex(ValueError, 'backtest'): self.project()

    def test_new_current_capture_retains_older_observation_without_refreshing_it(self):
        self.games[0].update(phase='regular',status='SCHEDULED')
        self.row.update(horizon_minutes=None, retrieved_at='2026-10-20T17:10:00Z',
                        forecast_cutoff=None, archive_snapshot_time=None,
                        comparison_eligible=False, status='QUALIFIED_CURRENT_REFERENCE')
        newer=copy.deepcopy(self.row)
        newer.update(retrieved_at='2026-10-20T17:20:00Z',source_quote_time='2026-10-20T17:19:00Z')
        result=self.project([self.row,newer])
        self.assertEqual(len(result['rows']),2)
        self.assertEqual(result['rows'][0]['retrieved_at'],'2026-10-20T17:10:00Z')
        self.assertEqual(result['latest_current_capture_utc'],'2026-10-20T17:20:00Z')
        self.assertEqual(result['latest_current_capture_scheduled_games'],1)
        self.assertEqual(result['qualified_current_scheduled_reference_games'],1)
        with self.assertRaisesRegex(ValueError,'duplicate'):self.project([newer,copy.deepcopy(newer)])
        self.games[0]['status']='FINAL'
        result=self.project([self.row,newer])
        self.assertEqual(result['qualified_current_reference_games'],1)
        self.assertEqual(result['qualified_current_scheduled_reference_games'],0)
        self.assertEqual(result['latest_current_capture_scheduled_games'],0)

    def test_spread_is_threshold_and_push_remains_unknown(self):
        self.row.update(target='margin', home_spread_line=-3.5, away_spread_line=3.5, market_home_minus_away=3.5)
        result = self.project()
        self.assertEqual(result['rows'][0]['line_interpretation'], 'SPREAD_THRESHOLD_NOT_DISTRIBUTION_MEAN')
        self.assertIsNone(result['rows'][0]['market_push_probability'])
        self.assertFalse(result['rows'][0]['settlement_qualified'])
        self.row['market_home_minus_away'] = -3.5
        with self.assertRaisesRegex(ValueError, 'orientation'): self.project()

if __name__ == '__main__':
    unittest.main()
