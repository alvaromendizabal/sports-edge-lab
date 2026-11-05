"""A later source update cannot rewrite an earlier prediction or fit history."""
from copy import deepcopy
import hashlib,json,unittest
from pathlib import Path
from injury_refresh_n040 import validate_injury_refresh
HERE=Path(__file__).resolve().parent
class InjuryN040RefreshTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((HERE/'injury_refresh_n040.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text());cls.old=json.loads((HERE/'injury_issue_n037.json').read_text())
 def check(self,d):return validate_injury_refresh(d,self.coverage)
 def test_exact_new_issue_population_from_reused_fits(self):
  before=deepcopy(self.coverage);r=self.check(self.data)
  self.assertEqual(r['injury_n040_games'],29);self.assertEqual(r['injury_n040_owner_new_issue_rows'],87);self.assertEqual(r['injury_n040_current_publication_new_fits'],0);self.assertEqual(self.coverage,before)
 def test_prior_issue_and_historical_metrics_preserved(self):
  self.assertEqual(hashlib.sha256((HERE/'injury_issue_n037.json').read_bytes()).hexdigest(),'400684a1e683583c1d3fe7c521f8633bee4517079708b541bc4b84cf130e1855')
  old={r['game_id']:r for r in self.old['cards']}
  for r in self.data['cards']:
   self.assertEqual(r['home_win_probability'],old[r['game_id']]['home_win_probability'])
   self.assertEqual(r['fit_completed'],old[r['game_id']]['fit_completed'])
   self.assertNotEqual(r['actual_issue_at'],old[r['game_id']]['actual_issue_at'])
 def test_current_injury_coverage_is_partial(self):
  with_reports=[r for r in self.data['cards'] if any(r['injury_source_report_team_count'].values())]
  self.assertEqual(len(with_reports),13)
  jax=next(r for r in with_reports if r['game_id']=='2026_09_JAX_BAL')
  self.assertEqual(jax['injury_source_report_team_count'],{'BAL':18,'JAX':10})
  self.assertEqual((jax['home_margin'],jax['total']),(-5.2,46.6))
 def test_source_time_is_not_silently_refreshed(self):
  for r in self.data['cards']:
   self.assertEqual(r['base_feature_asof_at'],'2026-11-04T01:52:35.279297+00:00')
   self.assertEqual(r['injury_cutoff_at'],'2026-11-05T01:20:43.177580+00:00')
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
 def test_complete_listed_rows_do_not_mean_full_roster_health(self):
  census=self.data['source_census'];self.assertEqual(census['listed_rows'],258)
  self.assertEqual(census['admitted_rows'],258);self.assertFalse(census['full_roster_coverage'])
  self.assertEqual(census['missing_teams'],['BUF','CHI','MIN','SEA','TB'])
  self.assertEqual(sum(sum(c['injury_source_report_team_count'].values()) for c in self.data['cards']),258)
  for field in ('full_roster_coverage','announced_starter_verified','reserve_status_verified'):
   d=deepcopy(self.data);d['source_census'][field]=True
   with self.subTest(field=field),self.assertRaises(ValueError):self.check(d)
 def test_zero_exclusions_cannot_become_guessed_identity_rows(self):
  d=deepcopy(self.data);d['cards'][0]['injury_source_excluded_rows']=1
  with self.assertRaises(ValueError):self.check(d)
 def test_current_capture_cannot_turn_into_historical_gain(self):
  d=deepcopy(self.data);d['changes_since_n039']['new_fits']=3
  with self.assertRaises(ValueError):self.check(d)
 def test_missing_team_is_not_filled_with_another_team(self):
  d=deepcopy(self.data);d['cards'][0]['injury_source_report_team_count']['SEA']=1
  with self.assertRaises(ValueError):self.check(d)
 def test_private_payload_rejected(self):
  d=deepcopy(self.data);d['cards'][0]['model_body']='private'
  with self.assertRaises(ValueError):self.check(d)
if __name__=='__main__':unittest.main()
