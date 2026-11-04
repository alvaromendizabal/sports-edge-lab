from copy import deepcopy
import json,unittest
from pathlib import Path
from latest_pregame_n037 import validate_latest_n037
HERE=Path(__file__).resolve().parent
class LatestN037Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'latest_pregame_n037.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def check(self,x):return validate_latest_n037(x,self.coverage)
 def test_all_completed_games_and_targets(self):
  self.assertEqual(self.check(self.data)['latest_n037_games'],121);self.assertEqual(len(self.data['point_rows']),242)
 def test_quote_cannot_cross_kickoff_or_backdate_acquisition(self):
  g=next(g for g in self.coverage['all_games']if g['game_id']==self.data['winner_rows'][0]['game_id'])
  for key,value in [('quote_at',g['kickoff_utc']),('acquired_at',self.data['winner_rows'][0]['quote_at'])]:
   d=deepcopy(self.data);d['winner_rows'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)
 def test_earlier_horizon_and_private_nested_payload_rejected(self):
  for key,value in [('horizon','T1'),('raw_source',{'private':'body'}),('p_home',.54321)]:
   d=deepcopy(self.data);d['winner_rows'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)
 def test_point_probability_never_becomes_mean_or_metrics(self):
  for key,value in [('point_estimate',3.5),('metric_eligible',True),('predicate_variable','away_margin'),('contract_count',0)]:
   d=deepcopy(self.data);d['point_rows'][0][key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)
 def test_duplicate_missing_and_wrong_result_fail(self):
  d=deepcopy(self.data);d['winner_rows'][0]=d['winner_rows'][1]
  with self.assertRaises(ValueError):self.check(d)
  d=deepcopy(self.data);d['point_rows'].pop()
  with self.assertRaises(ValueError):self.check(d)
  d=deepcopy(self.data);d['winner_rows'][0]['correct']=not d['winner_rows'][0]['correct']
  with self.assertRaises(ValueError):self.check(d)
 def test_wrong_counts_and_research_credit_fail(self):
  for key,value in [('private_full_body_proofs',908),('new_fits',1),('owner_pipeline_accepted',True),('historical_metrics_changed',True)]:
   d=deepcopy(self.data);d[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.check(d)
if __name__=='__main__':unittest.main()
