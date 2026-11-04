"""Historical market snapshots cannot become original forecasts or earlier cutoffs."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from latest_pregame import validate_latest_pregame
HERE=Path(__file__).resolve().parent

class LatestPregameTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((HERE/'latest_pregame_n035.json').read_text())
  cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def check(self,x):return validate_latest_pregame(x,self.coverage)
 def test_real_pregame_with_postgame_acquisition_is_allowed(self):
  d=deepcopy(self.coverage);r=self.check(self.data)
  self.assertEqual(r['latest_pregame_rows'],3);self.assertEqual(d,self.coverage)
  self.assertFalse(self.data['winner_rows'][0]['correct'])
 def test_postgame_quote_rejected(self):
  x=deepcopy(self.data);x['winner_rows'][0]['quote_at']='2026-11-04T01:14:00Z'
  with self.assertRaises(ValueError):self.check(x)
 def test_relabel_to_earlier_horizon_rejected(self):
  for h in ('T1','T2','LATEST_OBSERVED'):
   x=deepcopy(self.data);x['winner_rows'][0]['horizon']=h
   with self.subTest(horizon=h),self.assertRaises(ValueError):self.check(x)
 def test_acquisition_cannot_be_backdated_into_original_possession(self):
  x=deepcopy(self.data);x['winner_rows'][0]['acquired_at']=x['winner_rows'][0]['quote_at']
  with self.assertRaises(ValueError):self.check(x)
 def test_other_completed_game_cannot_reuse_this_source(self):
  x=deepcopy(self.data);x['winner_rows'][0]['game_id']='2026_08_KC_DEN'
  with self.assertRaises(ValueError):self.check(x)
 def test_source_presence_is_not_all_season_coverage(self):
  x=deepcopy(self.data);x['coverage'][3]['available_games']=121
  with self.assertRaises(ValueError):self.check(x)
 def test_wrong_winner_is_preserved(self):
  x=deepcopy(self.data);x['winner_rows'][0]['correct']=True
  with self.assertRaises(ValueError):self.check(x)
 def test_point_threshold_cannot_become_mean_score(self):
  x=deepcopy(self.data);x['point_rows'][0]['point_estimate']=3.5
  with self.assertRaises(ValueError):self.check(x)
 def test_point_home_orientation_and_age_checked(self):
  for key,val in [('predicate_variable','away_margin'),('quote_age_seconds',0)]:
   x=deepcopy(self.data);x['point_rows'][0][key]=val
   with self.subTest(field=key),self.assertRaises(ValueError):self.check(x)
 def test_private_nested_payload_rejected(self):
  x=deepcopy(self.data);x['winner_rows'][0]['raw_source']={'body':'private'}
  with self.assertRaises(ValueError):self.check(x)
 def test_new_fit_or_metric_credit_rejected(self):
  for k,v in [('new_fits',1),('new_forecasts',1),('historical_metrics_changed',True),('owner_pipeline_accepted',True)]:
   x=deepcopy(self.data);x[k]=v
   with self.subTest(field=k),self.assertRaises(ValueError):self.check(x)
if __name__=='__main__':unittest.main()
