import json,unittest
from copy import deepcopy
from pathlib import Path
from injury_contribution import validate_contribution,render_contribution
HERE=Path(__file__).resolve().parent
class ContributionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'injury_contribution_n041.json').read_text())
 def fail(self,change):
  d=deepcopy(self.data);change(d)
  with self.assertRaises(ValueError):validate_contribution(d)
 def test_actual_derived_study_has_no_native_fit_or_issue_credit(self):
  r=validate_contribution(self.data);self.assertEqual(r['injury_contribution_recipes'],960);self.assertEqual(r['injury_contribution_new_native_fits'],0);self.assertFalse(r['injury_contribution_promoted'])
 def test_native_fit_and_issue_credit_rejected(self):
  for k in ('new_native_fits','new_derived_issue_rows'):self.fail(lambda d,k=k:d.__setitem__(k,3))
 def test_no_automatic_promotion(self):
  for k in ('automatic_promotion','owner_pipeline_accepted'):self.fail(lambda d,k=k:d.__setitem__(k,True))
 def test_private_recipe_fields_rejected(self):self.fail(lambda d:d.__setitem__('selected_weights',['private']))
 def test_source_identity_is_bound(self):self.fail(lambda d:d.__setitem__('owner_return_sha256','0'*64))
 def test_unknown_injury_reports_remain_unknown(self):self.fail(lambda d:d['historical_injury_coverage'][1].__setitem__('qualified_both_team_games',285))
 def test_empty_qualified_cohort_has_no_metric(self):self.fail(lambda d:d['season_metrics'][3].__setitem__('model_log_loss',0))
 def test_exact_common_cohort_required(self):self.fail(lambda d:d['season_metrics'][0].__setitem__('control_games',284))
 def test_current_evaluation_cannot_select_recipe(self):self.fail(lambda d:d.__setitem__('selection_period','2026_MONITORING'))
 def test_current_results_cannot_be_independent_validation(self):self.fail(lambda d:d['season_metrics'][4].__setitem__('evaluation','UNTOUCHED_TEST'))
 def test_duplicate_rows_fail(self):self.fail(lambda d:d['season_metrics'].__setitem__(1,d['season_metrics'][0]))
 def test_delta_and_accuracy_reconcile(self):
  self.fail(lambda d:d['season_metrics'][0].__setitem__('paired_primary_delta',-.1))
  self.fail(lambda d:d['season_metrics'][0].__setitem__('model_correct',285))
 def test_render_preserves_uncertainty_and_gaps(self):
  s=render_contribution(self.data);self.assertIn('paired interval',s);self.assertIn('Unknown-report treatment',s);self.assertIn('76 / 119',s);self.assertNotIn('secret',s)
if __name__=='__main__':unittest.main()
