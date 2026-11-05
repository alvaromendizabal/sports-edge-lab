import copy,json,unittest
from pathlib import Path
from current_issues_n042 import validate_current_issues
HERE=Path(__file__).parent
class CurrentIssues(unittest.TestCase):
 def setUp(self):
  self.d=json.loads((HERE/'current_issues_n042.json').read_text());self.coverage=json.loads((HERE/'current_coverage.json').read_text())
 def test_actual_streams(self):self.assertEqual(validate_current_issues(self.d,self.coverage)['n042_actual_target_rows'],261)
 def test_forbidden_changes(self):
  for key,value in [('owner_pipeline_accepted',True),('protected_original_refits',7),('historical_metrics_changed',True),('final_hour_qualified_cards',29),('actual_target_rows',29)]:
   with self.subTest(key=key):
    d=copy.deepcopy(self.d);d[key]=value
    with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_card_failures(self):
  for key,value in [('game_id','2026_08_CHI_SEA'),('base_feature_asof_at','2026-11-04T01:52:35.279297+00:00'),('calibration_applied',True),('actual_issue_at','2026-11-07T00:00:00Z'),('home_win_probability',float('nan')),('home_score_center',900),('announced_starter_verified',True),('maximum_label_available_at','2026-11-08T00:00:00Z')]:
   with self.subTest(key=key):
    d=copy.deepcopy(self.d);d['streams'][2]['cards'][0][key]=value
    with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_private_fields_rejected(self):
  for field in ['model_weights','component_bindings_json','source_path']:
   d=copy.deepcopy(self.d);d['streams'][2]['cards'][0][field]='private'
   with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_duplicate_event(self):
  self.d['streams'][2]['cards'][1]=self.d['streams'][2]['cards'][0]
  with self.assertRaises(ValueError):validate_current_issues(self.d,self.coverage)
 def test_exploratory_promotion_rejected(self):
  self.d['research']['cross_version_promotion_eligible']=True
  with self.assertRaises(ValueError):validate_current_issues(self.d,self.coverage)
if __name__=='__main__':unittest.main()
