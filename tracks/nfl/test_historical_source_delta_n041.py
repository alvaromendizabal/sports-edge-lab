from copy import deepcopy
import json,unittest
from pathlib import Path
from historical_source_delta_n041 import validate_historical_delta
HERE=Path(__file__).resolve().parent
class HistoricalDeltaTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads((HERE/'historical_source_delta_n041.json').read_text())
 def test_exact_three_target_additions(self):self.assertEqual(validate_historical_delta(self.d)['historical_n041_new_cells'],30)
 def test_no_promotion_or_rewriting(self):
  for k,v in [('historical_metrics_changed',True),('accepted_prior_references_changed',True),('new_native_fits',1),('new_issue_rows',1),('owner_pipeline_accepted',True)]:
   d=deepcopy(self.d);d[k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):validate_historical_delta(d)
 def test_postgame_quote_rejected(self):
  d=deepcopy(self.d);d['winner_rows'][0]['quote_at']=d['winner_rows'][0]['acquired_at']
  with self.assertRaises(ValueError):validate_historical_delta(d)
 def test_duplicate_missing_and_private_rows_rejected(self):
  for change in [lambda d:d['point_rows'].pop(),lambda d:d['winner_rows'].__setitem__(0,d['winner_rows'][1]),lambda d:d['point_rows'][0].update(private_pointer='object')]:
   d=deepcopy(self.d);change(d)
   with self.assertRaises(ValueError):validate_historical_delta(d)
 def test_condition_cannot_become_point_projection(self):
  d=deepcopy(self.d);d['point_rows'][0]['point_estimate']=3.5
  with self.assertRaises(ValueError):validate_historical_delta(d)
 def test_source_reference_cannot_become_fill_or_evaluation(self):
  for k in ('metric_eligible','execution_qualified'):
   d=deepcopy(self.d);d['winner_rows'][0][k]=True
   with self.subTest(k=k),self.assertRaises(ValueError):validate_historical_delta(d)
if __name__=='__main__':unittest.main()
