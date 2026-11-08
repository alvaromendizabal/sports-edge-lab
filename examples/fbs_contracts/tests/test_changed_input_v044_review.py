"""Recovered forecast scope stays distinct from issued or scored forecasts."""
from pathlib import Path
import json
import unittest
ROOT=Path(__file__).resolve().parents[3]

class ChangedInputV044Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.report=json.loads((ROOT/'docs/fbs/changed-input-study-v044.json').read_text())
  cls.fixtures={r['id']:r for r in json.loads((ROOT/'docs/fbs/three-season.json').read_text())['rows']}
  cls.capture={r['id']:r for r in json.loads((ROOT/'docs/fbs/current-capture-v044.json').read_text())['rows']}
 def test_registered_scope_does_not_replace_full_current_week(self):
  r=self.report;ids={g['id'] for g in r['rows']};self.assertEqual(len(ids),119)
  self.assertEqual(sum(self.fixtures[x]['period']=='current' for x in ids),14)
  self.assertEqual(sum(self.fixtures[x]['period']=='previous' for x in ids),0)
  self.assertTrue(all(self.fixtures[x]['season']==2026 and self.fixtures[x]['kickoff_exact'] for x in ids))
  self.assertTrue(all(not self.capture[x]['completed'] for x in ids))
  self.assertFalse(ids & {x for x,g in self.capture.items() if g['newly_observed']})
 def test_all_saved_targets_preserve_family_scope_and_actual_intervals(self):
  outputs=before=after=0
  for row in self.report['rows']:
   game=self.fixtures[row['id']]
   self.assertEqual((row['kickoff'],row['cutoff']),(game['kickoff'],game['cutoff']))
   self.assertEqual(len(row['models']),12)
   for family,model in row['models'].items():
    expected={'winner'} if family.endswith('_logistic') else {'margin','total'} if family.endswith(('_linear','_ridge')) else {'winner','margin','total'}
    self.assertEqual(set(model),expected)
    for target,value in model.items():
     outputs+=1;before+=value['computed_before_cutoff'];after+=not value['computed_before_cutoff']
     if target=='winner':self.assertTrue(0<=value['prediction']<=1)
     if 'fixed_equal_blend' in family:self.assertNotIn('interval80',value);self.assertNotIn('interval95',value)
     elif target!='winner':
      for key in ('interval80','interval95'):self.assertLessEqual(*value[key])
     if target=='margin':self.assertIsNone(value['cover_probability'])
  self.assertEqual((outputs,before,after),(3808,3360,448))
 def test_no_outcomes_means_pending_metrics_without_zero_substitutions(self):
  r=self.report;self.assertEqual(r['counts']['scored_games'],0)
  self.assertEqual((r['counts']['original_base_fits'],r['counts']['original_calibration_fits']),(46,14))
  self.assertTrue(all(rows==[] for rows in r['metrics'].values()))
  self.assertEqual(r['coverage']['current_week']['registered_target_games'],14)
  self.assertEqual(r['coverage']['previous_week']['coverage_status'],'OUTSIDE_REGISTERED_REFRESH_COHORT')
  self.assertFalse(r['forecast_issued']);self.assertFalse(r['promotion_allowed']);self.assertFalse(r['historical_availability_proved'])
  self.assertEqual(r['default_selection_unchanged'],'V038 fixed_equal_blend')
  self.assertEqual((r['current_reporting_new_fits'],r['current_reporting_new_predictions'],r['current_reporting_provider_requests']),(0,0,0))
 def test_public_projection_excludes_private_fit_records_and_matches_companion(self):
  text=json.dumps(self.report)
  for forbidden in ('s3://','fit_identity_sha256','model_state_sha256','/workspace/','api_key','raw_probability','feature_names','model_parameters'):self.assertNotIn(forbidden,text)
  js=(ROOT/'docs/fbs/changed-input-study-v044-data.js').read_text()
  self.assertEqual(json.loads(js.split('=',1)[1].removesuffix(';\n')),self.report)

if __name__=='__main__':unittest.main()
