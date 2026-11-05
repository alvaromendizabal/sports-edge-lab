import copy,json,unittest
from pathlib import Path
from owner_study_n043 import validate_owner_study
from current_issues_n043 import validate_current_issues
from current_source_n043 import validate_current_source
HERE=Path(__file__).parent
class OwnerStudyN043(unittest.TestCase):
 def setUp(self):
  self.study=json.loads((HERE/'owner_study_n043.json').read_text());self.issues=json.loads((HERE/'current_issues_n043.json').read_text());self.source=json.loads((HERE/'current_source_n043.json').read_text());self.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def test_complete_arm_partial_run(self):
  self.assertEqual(validate_owner_study(self.study)['n043_new_native_fits'],1605)
  self.assertEqual(validate_current_issues(self.issues,self.coverage)['n043_actual_target_rows'],174)
  self.assertEqual(validate_current_source(self.source,self.coverage)['source_n043_winner_rows'],58)
 def test_cannot_count_reused_jobs_as_new(self):
  d=copy.deepcopy(self.study);d['additional_unique_rolling_native_fits']=462
  with self.assertRaises(ValueError):validate_owner_study(d)
 def test_completed_grid_does_not_accept_pipeline(self):
  d=copy.deepcopy(self.study);d['owner_research_acceptance']=True
  with self.assertRaises(ValueError):validate_owner_study(d)
 def test_reconstructed_models_cannot_become_issued_picks(self):
  d=copy.deepcopy(self.study);d['new_designation_forecasts']=29
  with self.assertRaises(ValueError):validate_owner_study(d)
 def test_failed_fresh_lane_cannot_be_filled_by_previous_issue(self):
  d=copy.deepcopy(self.study);d['new_fresh_current_rolling_rows']=87
  with self.assertRaises(ValueError):validate_owner_study(d)
 def test_missing_reports_cannot_be_healthy_teams(self):
  d=copy.deepcopy(self.study);d['injury_report_teams']=30
  with self.assertRaises(ValueError):validate_owner_study(d)
 def test_current_reference_cannot_rewrite_metric(self):
  d=copy.deepcopy(self.source);d['historical_metrics_changed']=True
  with self.assertRaises(ValueError):validate_current_source(d,self.coverage)
 def test_postgame_or_future_quote_rejected(self):
  for field in ('acquired_at','quote_at'):
   d=copy.deepcopy(self.source);d['winner_rows'][0][field]='2026-12-01T12:00:00Z'
   with self.assertRaises(ValueError):validate_current_source(d,self.coverage)
 def test_fresh_injury_clock_cannot_refresh_base_features(self):
  d=copy.deepcopy(self.issues);d['streams'][1]['cards'][0]['base_feature_asof_at']=d['streams'][1]['cards'][0]['injury_cutoff_at']
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_private_forecast_fields_rejected(self):
  d=copy.deepcopy(self.issues);d['streams'][0]['cards'][0]['model_weights']='private'
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_no_hindsight_promotion(self):
  d=copy.deepcopy(self.study);d['automatic_promotion']=True
  with self.assertRaises(ValueError):validate_owner_study(d)
if __name__=='__main__':unittest.main()
