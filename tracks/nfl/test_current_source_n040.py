from copy import deepcopy
import json,unittest
from pathlib import Path
from current_source_n040 import validate_current_source
HERE=Path(__file__).resolve().parent
class CurrentSourceRefreshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'current_source_n040.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def check(self,d):return validate_current_source(d,self.coverage)
 def test_current_all_provider_targets_and_extra_week10(self):
  before=deepcopy(self.coverage);result=self.check(self.data)
  self.assertEqual(result['source_n040_winner_rows'],58);self.assertEqual(result['source_n040_point_rows'],116);self.assertEqual(self.coverage,before)
  self.assertEqual(sum(r['game_id'].startswith('2026_10_') for r in self.data['winner_rows']),13)
 def test_dated_fallback_remains_dated(self):
  r=next(r for r in self.data['winner_rows'] if r['game_id']=='2026_09_LV_SF' and r['provider']=='DraftKings')
  self.assertEqual(r['quote_at'],'2026-11-04T17:31:26+00:00');self.assertEqual(r['acquired_at'],'2026-11-04T17:32:23+00:00')
 def test_fallback_cannot_be_claimed_fresh(self):
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
if __name__=='__main__':unittest.main()
