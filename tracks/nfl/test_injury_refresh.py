"""A later source update cannot rewrite an earlier prediction or fit history."""
from copy import deepcopy
import hashlib,json,unittest
from pathlib import Path
from injury_refresh import validate_injury_refresh
HERE=Path(__file__).resolve().parent
class InjuryRefreshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((HERE/'injury_refresh_n039.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text());cls.old=json.loads((HERE/'injury_issue_n037.json').read_text())
 def check(self,d):return validate_injury_refresh(d,self.coverage)
 def test_exact_new_issue_population_from_reused_fits(self):
  before=deepcopy(self.coverage);r=self.check(self.data)
  self.assertEqual(r['injury_refresh_games'],29);self.assertEqual(r['injury_refresh_owner_new_issue_rows'],87);self.assertEqual(r['injury_refresh_current_publication_new_fits'],0);self.assertEqual(self.coverage,before)
 def test_prior_issue_and_historical_metrics_preserved(self):
  self.assertEqual(hashlib.sha256((HERE/'injury_issue_n037.json').read_bytes()).hexdigest(),'400684a1e683583c1d3fe7c521f8633bee4517079708b541bc4b84cf130e1855')
  old={r['game_id']:r for r in self.old['cards']}
  for r in self.data['cards']:
   self.assertEqual(r['home_win_probability'],old[r['game_id']]['home_win_probability'])
   self.assertEqual(r['fit_completed'],old[r['game_id']]['fit_completed'])
   self.assertNotEqual(r['actual_issue_at'],old[r['game_id']]['actual_issue_at'])
 def test_current_injury_coverage_is_partial(self):
  with_reports=[r for r in self.data['cards'] if any(r['injury_source_report_team_count'].values())]
  self.assertEqual(len(with_reports),11)
  jax=next(r for r in with_reports if r['game_id']=='2026_09_JAX_BAL')
  self.assertEqual(jax['injury_source_report_team_count'],{'BAL':18,'JAX':10})
  self.assertEqual((jax['home_margin'],jax['total']),(-5.2,46.6))
 def test_source_time_is_not_silently_refreshed(self):
  for r in self.data['cards']:
   self.assertEqual(r['base_feature_asof_at'],'2026-11-04T01:52:35.279297+00:00')
   self.assertEqual(r['injury_cutoff_at'],'2026-11-05T00:10:00.073931+00:00')
 def test_reused_fits_cannot_be_claimed_new(self):
  for field,value in [('new_selected_forward_fits',3),('restored_selected_forward_fits',0),('new_issue_target_rows',29),('historical_metrics_changed',True),('owner_pipeline_accepted',True)]:
   d=deepcopy(self.data);d[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_wrong_evidence_or_schema_rejected(self):
  for field,value in [('owner_return_sha256','0'*64),('source_member_sha256','0'*64),('schema','other')]:
   d=deepcopy(self.data);d[field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_qualification_cannot_be_promoted(self):
  for field,value in [('full_pipeline_selection_qualified',True),('final_hour_qualified_card',True),('announced_starter_verified',True),('reserve_status_verified',True),('injury_inputs_verified',True),('model_id','original_frozen'),('horizon','T1')]:
   d=deepcopy(self.data);d['cards'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_invalid_clock_and_target_changes_rejected(self):
  for field,value in [('fit_completed','2026-11-05T00:05:00Z'),('injury_cutoff_at','2026-11-06T23:00:00Z'),('actual_issue_at','2026-11-07T00:00:00Z'),('target_feature_views',{'winner':'injury_augmented','margin':'injury','total':'injury'}),('home_win_probability',float('nan'))]:
   d=deepcopy(self.data);d['cards'][0][field]=value
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_duplicate_or_missing_games_rejected(self):
  for mutate in [lambda d:d['cards'].pop(),lambda d:d['cards'].__setitem__(0,d['cards'][1])]:
   d=deepcopy(self.data);mutate(d)
   with self.assertRaises(ValueError):self.check(d)
 def test_missing_reports_cannot_be_called_healthy(self):
  d=deepcopy(self.data);d['cards'][0]['injury_report_status']='HEALTHY'
  with self.assertRaises(ValueError):self.check(d)
 def test_private_payload_rejected(self):
  d=deepcopy(self.data);d['cards'][0]['model_body']='private'
  with self.assertRaises(ValueError):self.check(d)
if __name__=='__main__':unittest.main()
