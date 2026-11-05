import copy,json,unittest
from pathlib import Path
from owner_study_n045 import validate_owner_study
from current_issues_n045 import validate_current_issues
from current_source_n045 import validate_current_source
HERE=Path(__file__).parent
class OwnerCompletionN045(unittest.TestCase):
 def setUp(self):
  self.study=json.loads((HERE/'owner_study_n045.json').read_text());self.issues=json.loads((HERE/'current_issues_n045.json').read_text());self.source=json.loads((HERE/'current_source_n045.json').read_text());self.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def test_completed_study_and_separate_issues(self):
  self.assertEqual(validate_owner_study(self.study)['n045_new_native_fits'],1029)
  self.assertEqual(validate_current_issues(self.issues,self.coverage)['n045_actual_target_rows'],261)
  self.assertEqual(validate_current_source(self.source,self.coverage)['source_n045_draftkings_fresh_games'],15)
 def test_restored_identity_not_new_fit(self):
  self.study['new_native_fits']+=576
  with self.assertRaises(ValueError):validate_owner_study(self.study)
 def test_completion_not_promotion(self):
  for field in ['automatic_promotion','owner_research_acceptance','old_metrics_rewritten','current_sources_all_latest_claimed']:
   d=copy.deepcopy(self.study);d[field]=True
   with self.assertRaises(ValueError):validate_owner_study(d)
 def test_reconstructed_model_not_issued_pick(self):
  self.study['new_designation_forecasts']=29
  with self.assertRaises(ValueError):validate_owner_study(self.study)
 def test_missing_teams_not_healthy(self):
  self.study['injury_report_teams']=30
  with self.assertRaises(ValueError):validate_owner_study(self.study)
 def test_cannot_substitute_prior_better_metric(self):
  self.study['selected_metrics'][1]['log_loss']=.6541795642
  with self.assertRaises(ValueError):validate_owner_study(self.study)
 def test_source_refresh_not_fit_or_promotion(self):
  self.issues['new_native_fits']=1038
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
 def test_current_quote_cannot_revise_historical_cutoff(self):
  self.source['winner_rows'][0]['horizon']='T2'
  with self.assertRaises(ValueError):validate_current_source(self.source,self.coverage)
 def test_future_quote_rejected(self):
  self.source['winner_rows'][0]['quote_at']='2026-12-01T00:00:00Z'
  with self.assertRaises(ValueError):validate_current_source(self.source,self.coverage)
 def test_private_field_rejected(self):
  self.issues['streams'][0]['cards'][0]['weights']='private'
  with self.assertRaises(ValueError):validate_current_issues(self.issues,self.coverage)
if __name__=='__main__':unittest.main()
