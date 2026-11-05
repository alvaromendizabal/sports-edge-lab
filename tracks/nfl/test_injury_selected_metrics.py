from copy import deepcopy
import json,unittest
from pathlib import Path
from injury_selected_metrics import validate_selected_metrics,render_selected_metrics
HERE=Path(__file__).resolve().parent
class RetainedInjuryMetricsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.d=json.loads((HERE/'injury_selected_metrics_n037.json').read_text())
 def test_exact_seasons_targets_and_denominators(self):
  r=validate_selected_metrics(self.d);self.assertEqual(r['retained_injury_metric_rows'],9)
  self.assertFalse(r['retained_injury_metric_promoted']);self.assertEqual(r['retained_injury_metric_new_fits'],0)
 def test_source_and_scope_cannot_be_relabelled(self):
  for k,v in [('source_member_sha256','0'*64),('new_fits',1),('promotion_accepted',True)]:
   d=deepcopy(self.d);d[k]=v
   with self.subTest(k=k),self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_winner_cannot_claim_direct_injury_fields(self):
  d=deepcopy(self.d);next(r for r in d['rows'] if r['target']=='win')['direct_injury_features']=True
  with self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_missing_new_final_cannot_expand_historical_cohort(self):
  d=deepcopy(self.d);next(r for r in d['rows'] if r['target']=='margin' and r['season']==2026)['games']=121
  with self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_target_metric_mix_and_nonfinite_fail(self):
  for field,value in [('log_loss',.5),('mae',float('nan'))]:
   d=deepcopy(self.d);d['rows'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_current_outcomes_do_not_promote_calibration(self):
  r=next(r for r in self.d['rows'] if r['target']=='win' and r['season']==2026)
  self.assertGreater(r['log_loss'],r['uncalibrated_log_loss'])
  self.assertEqual((r['correct'],r['uncalibrated_correct']),(74,76))
 def test_duplicate_and_private_fields_rejected(self):
  for change in (lambda d:d['rows'].__setitem__(0,d['rows'][1]),lambda d:d['rows'][0].update(model_body='secret')):
   d=deepcopy(self.d);change(d)
   with self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_historical_missing_reports_cannot_be_called_complete(self):
  d=deepcopy(self.d);d['historical_report_coverage'][1]['qualified_injury_report_games']=285
  with self.assertRaises(ValueError):validate_selected_metrics(d)
 def test_tables_render_counts_and_target_context(self):
  html=render_selected_metrics(self.d);self.assertIn('74 / 119',html);self.assertIn('matched base',html);self.assertIn('11.477',html)
if __name__=='__main__':unittest.main()
