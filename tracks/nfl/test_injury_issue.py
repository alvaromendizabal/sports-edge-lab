from copy import deepcopy
import hashlib,json,unittest
from pathlib import Path
from injury_issue import validate_injury_issue
HERE=Path(__file__).resolve().parent
class InjuryIssueTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.data=json.loads((HERE/'injury_issue_n037.json').read_text());cls.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def check(self,d):return validate_injury_issue(d,self.coverage)
 def change(self,key,value,game=None):
  d=deepcopy(self.data);r=next(c for c in d['cards']if c['game_id']==game)if game else d['cards'][0];r[key]=value;return d
 def test_exact_separate_issue_population(self):
  before=deepcopy(self.coverage);r=self.check(self.data);self.assertEqual(r['experimental_issue_games'],29);self.assertEqual(r['experimental_issue_target_rows'],87);self.assertEqual(r['experimental_issue_partial_report_games'],1);self.assertEqual(self.coverage,before)
 def test_n037_card_payload_preserved(self):self.assertEqual(hashlib.sha256((HERE/'injury_issue_n037.json').read_bytes()).hexdigest(),'400684a1e683583c1d3fe7c521f8633bee4517079708b541bc4b84cf130e1855')
 def test_frozen_role_cannot_be_replaced(self):
  with self.assertRaises(ValueError):self.check(self.change('model_id','original_frozen'))
 def test_wrong_owner_or_source_identity(self):
  for k in ('owner_return_sha256','source_member_sha256'):
   d=deepcopy(self.data);d[k]='0'*64
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(d)
 def test_no_final_hour_or_production_promotion(self):
  for k,v in [('final_hour_qualified_card',True),('full_pipeline_selection_qualified',True),('horizon','T1'),('announced_starter_verified',True),('reserve_status_verified',True)]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(self.change(k,v))
 def test_source_and_fit_cannot_follow_issue(self):
  for k in ('injury_cutoff_at','source_asof','fit_completed'):
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(self.change(k,'2026-11-04T07:00:00Z'))
 def test_missing_reports_cannot_be_healthy(self):
  for k,v in [('injury_inputs_verified',True),('injury_report_status','HEALTHY'),('injury_observed_at','2026-11-04T05:35:54Z')]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(self.change(k,v))
 def test_partial_qb_exclusions_and_exact_counts_required(self):
  for k,v in [('injury_source_excluded_rows',0),('injury_source_report_team_count',{'BAL':18,'JAX':9}),('injury_report_status','COMPLETE')]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(self.change(k,v,'2026_09_JAX_BAL'))
 def test_winner_injury_view_cannot_be_invented(self):
  d=deepcopy(self.data);d['cards'][0]['target_feature_views']['winner']='injury_augmented'
  with self.assertRaises(ValueError):self.check(d)
 def test_unknown_private_nested_payload_rejected(self):
  d=deepcopy(self.data);d['cards'][0]['raw_source']={'private':'body'}
  with self.assertRaises(ValueError):self.check(d)
 def test_duplicate_completed_and_missing_events_rejected(self):
  d=deepcopy(self.data);d['cards'][0]=d['cards'][1]
  with self.assertRaises(ValueError):self.check(d)
  with self.assertRaises(ValueError):self.check(self.change('game_id','2026_08_CHI_SEA'))
  d=deepcopy(self.data);d['cards'].pop()
  with self.assertRaises(ValueError):self.check(d)
 def test_score_intervals_and_probabilities_guarded(self):
  for k,v in [('home_win_probability',float('nan')),('home_score_center',99),('margin_interval',{'lower':10,'upper':-10,'nominal_coverage':.8}),('correct',True)]:
   with self.subTest(k=k),self.assertRaises(ValueError):self.check(self.change(k,v))
if __name__=='__main__':unittest.main()
