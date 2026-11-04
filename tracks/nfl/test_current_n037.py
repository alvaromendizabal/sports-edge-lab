"""Source-only current references retain clocks, payoff direction and forecasts."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import current_n037 as current

HERE=Path(__file__).resolve().parent
class CurrentN037Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((HERE/'current_n037.json').read_text())
  cls.inputs=[json.loads((HERE/name).read_text())for name in ('current_coverage.json','current_source_overlay.json','reschedule_reference.json','source_recovery_n036.json')]
 def load(self,data=None):
  if data is None:return current.load_current_n037(*self.inputs)
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);(root/'current_n037.json').write_text(json.dumps(data))
   with patch.object(current,'HERE',root):return current.load_current_n037(*self.inputs)
 def test_all_three_providers_have_all_15_current_game_target_references(self):
  result,receipt=self.load()
  self.assertEqual(receipt['n037_current_source_references'],6)
  self.assertEqual(len(result['combined_week9_coverage']),9)
  self.assertTrue(all(r['available_games']==r['total_games']==15 for r in result['combined_week9_coverage']))
 def test_inputs_and_forecasts_remain_unchanged(self):
  before=deepcopy(self.inputs);result,receipt=self.load()
  self.assertEqual(before,self.inputs);self.assertEqual(receipt['n037_current_source_model_changes'],0)
  self.assertFalse(self.data['historical_metrics_changed']);self.assertFalse(self.data['model_forecasts_changed'])
 def test_exact_rounded_winner_references(self):
  values={r['game_id']:(r['derived_pick'],r['p_home'])for r in self.data['winner_rows']}
  self.assertEqual(values,{'2026_09_TB_CHI':('CHI',.715),'2026_09_BUF_MIN':('BUF',.375)})
 def test_away_win_by_two_means_home_margin_below_negative_one_point_five(self):
  for r in self.data['point_rows']:
   if r['target']!='margin':continue
   self.assertEqual((r['predicate_variable'],r['operator'],r['line']),('home_margin','<',-1.5))
   self.assertEqual(r['predicate'],'Home margin < -1.5')
   self.assertTrue(-2<r['line']);self.assertFalse(-1<r['line'])
 def test_total_24_point_five_is_alternate_threshold_not_mean_or_main_line(self):
  for r in self.data['point_rows']:
   self.assertIsNone(r['point_estimate']);self.assertFalse(r['metric_eligible'])
   self.assertIn('not a main market line',r['reason'])
   if r['target']=='total':
    self.assertEqual((r['predicate_variable'],r['operator'],r['line']),('total','>',24.5))
    self.assertTrue(25>r['line']);self.assertFalse(24>r['line'])
 def test_reference_cannot_be_promoted_to_historical_metric_or_earlier_horizon(self):
  for key,value in [('metric_eligible',True),('horizon','T1'),('horizon','T2'),('horizon','LATEST_PREGAME')]:
   d=deepcopy(self.data);d['winner_rows'][0][key]=value
   with self.subTest(key=key,value=value),self.assertRaises(ValueError):self.load(d)
 def test_threshold_cannot_become_projected_score(self):
  d=deepcopy(self.data);d['point_rows'][0]['point_estimate']=-1.5
  with self.assertRaises(ValueError):self.load(d)
 def test_quote_after_acquisition_is_rejected(self):
  d=deepcopy(self.data);d['winner_rows'][0]['quote_at']='2026-11-05T00:00:00Z'
  with self.assertRaises(ValueError):self.load(d)
 def test_capture_after_kickoff_is_rejected(self):
  d=deepcopy(self.data);d['winner_rows'][0]['acquired_at']='2026-11-09T01:20:00Z';d['as_of']='2026-11-09T02:00:00Z'
  with self.assertRaises(ValueError):self.load(d)
 def test_duplicate_missing_or_wrong_provider_rejected(self):
  for change in [lambda d:d['winner_rows'].pop(),lambda d:d['point_rows'].__setitem__(0,deepcopy(d['point_rows'][1])),lambda d:d['winner_rows'][0].update(provider='Kalshi')]:
   d=deepcopy(self.data);change(d)
   with self.assertRaises(ValueError):self.load(d)
 def test_private_row_payload_is_rejected(self):
  d=deepcopy(self.data);d['winner_rows'][0]['raw_source']={'key':'private'}
  with self.assertRaises(ValueError):self.load(d)
 def test_wrong_owner_return_or_research_credit_is_rejected(self):
  for key,value in [('owner_return_sha256','0'*64),('historical_metrics_changed',True),('model_forecasts_changed',True)]:
   d=deepcopy(self.data);d[key]=value
   with self.subTest(key=key),self.assertRaises(ValueError):self.load(d)
if __name__=='__main__':unittest.main()
