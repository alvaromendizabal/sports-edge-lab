from copy import deepcopy
import json,unittest
from pathlib import Path
from current_source_n042 import validate_current_source
HERE=Path(__file__).resolve().parent
class CurrentSourceRefreshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'current_source_n042.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def check(self,d):return validate_current_source(d,self.coverage)
 def test_current_all_provider_targets_and_extra_week10(self):
  before=deepcopy(self.coverage);result=self.check(self.data)
  self.assertEqual(result['source_n042_winner_rows'],58);self.assertEqual(result['source_n042_point_rows'],116);self.assertEqual(self.coverage,before)
  self.assertEqual(sum(r['game_id'].startswith('2026_10_') for r in self.data['winner_rows']),13)
 def test_recovered_current_quote_preserves_actual_capture(self):
  r=next(r for r in self.data['winner_rows'] if r['game_id']=='2026_09_LV_SF' and r['provider']=='DraftKings')
  self.assertEqual(r['quote_at'],'2026-11-05T04:33:35+00:00');self.assertEqual(r['acquired_at'],'2026-11-05T04:34:39Z')
 def test_current_capture_cannot_be_backdated(self):
  d=deepcopy(self.data);r=next(r for r in d['winner_rows'] if r['game_id']=='2026_09_LV_SF' and r['provider']=='DraftKings');r['acquired_at']='2026-11-05T01:08:58+00:00'
  with self.assertRaises(ValueError):self.check(d)
 def test_provider_observation_cannot_become_quote_clock(self):
  d=deepcopy(self.data);r=next(r for r in d['winner_rows'] if r['provider']=='Kalshi');r['quote_at']=r['acquired_at']
  with self.assertRaises(ValueError):self.check(d)
 def test_no_metric_or_model_promotion(self):
  for field in ['owner_pipeline_accepted','historical_metrics_changed','model_forecasts_changed']:
   d=deepcopy(self.data);d[field]=True
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_unknown_fields_and_wrong_owner_fail(self):
  for change in [lambda d:d.update(owner_return_sha256='0'*64),lambda d:d['point_rows'][0].update(private_payload='body')]:
   d=deepcopy(self.data);change(d)
   with self.assertRaises(ValueError):self.check(d)
 def test_missing_duplicate_and_postkickoff_future_rejected(self):
  for change in [lambda d:d['winner_rows'].pop(),lambda d:d['point_rows'].append(deepcopy(d['point_rows'][0])),lambda d:d['point_rows'][-1].update(acquired_at='2027-01-01T00:00:00Z')]:
   d=deepcopy(self.data);change(d)
   with self.assertRaises(ValueError):self.check(d)
 def test_future_line_cannot_become_mean_prediction(self):
  d=deepcopy(self.data);d['point_rows'][-1]['point_estimate']=3.5
  with self.assertRaises(ValueError):self.check(d)
 def test_recovery_does_not_change_original_owner_counter(self):
  self.assertEqual(self.data['original_normalized_week9_games'],14)
  self.assertEqual(self.data['owner_schedule_recovered_week9_games'],1)
  self.assertTrue(self.data['owner_schedule_recovery_available'])
  d=deepcopy(self.data);d['original_normalized_week9_games']=15
  with self.assertRaises(ValueError):self.check(d)
 def test_recovery_evidence_is_exact_and_no_new_request(self):
  proof=json.loads((HERE/'current_schedule_recovery_n042.json').read_text())
  self.assertEqual(proof['original_full_proof_sha256'],self.data['recovery_evidence_sha256'])
  self.assertEqual(proof['new_provider_requests'],0);self.assertEqual(proof['new_acquisition_credit'],0)
  self.assertFalse(proof['model_feature_input']);self.assertFalse(proof['global_time_tolerance_changed'])
  self.assertEqual(proof['provider_kickoff_utc'],'2026-11-08T21:05:00+00:00')
  self.assertEqual(proof['canonical_kickoff_utc'],'2026-11-08T21:25:00+00:00')
if __name__=='__main__':unittest.main()
