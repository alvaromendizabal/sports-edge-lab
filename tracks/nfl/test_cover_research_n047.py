import copy,json,unittest
from pathlib import Path
from cover_research_n047 import load_cover,validate_cover
from current_issues_n047 import load_current_issues,validate_current_issues
HERE=Path(__file__).parent
class ActualDistributionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.coverage=json.loads((HERE/'current_coverage.json').read_text());cls.issues=load_current_issues(cls.coverage)[0];cls.cover=load_cover(cls.coverage,cls.issues)[0]
 def reject(self,mutate):
  d=copy.deepcopy(self.cover);mutate(d)
  with self.assertRaises(ValueError):validate_cover(d,self.coverage,self.issues)
 def test_original_issue_cannot_be_backdated(self):self.reject(lambda d:d['cards'][0].update(actual_issue_at_utc='2026-11-05T00:00:00Z'))
 def test_current_transfer_cannot_be_promoted(self):self.reject(lambda d:d.update(calibration_validated=True))
 def test_unknown_sportsbook_settlement_cannot_be_scored(self):self.reject(lambda d:next(r for r in d['threshold_rows']if r['settlement_policy']=='UNKNOWN').update(scoring_probability=.6))
 def test_nested_interval_order(self):self.reject(lambda d:d['cards'][0]['intervals'].update({'95':[0,1]}))
 def test_current_output_keeps_actual_parent(self):self.reject(lambda d:d['cards'][0].update(home_margin=999))
 def test_negative_provider_evidence_preserved(self):self.reject(lambda d:d['paired_intervals'][0].update(model_minus_provider_log_loss_paired_week_bootstrap_95=[-.1,.1]))
 def test_28_new_native_games_never_include_expired_jacksonville(self):
  self.assertTrue(all(c['game_id']!='2026_09_JAX_BAL'for s in self.issues['streams']for c in s['cards']))
 def test_unknown_designation_block_cannot_become_present(self):
  d=copy.deepcopy(self.issues);d['streams'][-1]['cards'][0]['designation_report_teams_known']={k:True for k in d['streams'][-1]['cards'][0]['designation_report_teams_known']}
  with self.assertRaises(ValueError):validate_current_issues(d,self.coverage)
 def test_three_provider_readiness_keeps_explicit_gap(self):
  self.assertEqual({r['provider']for r in self.cover['threshold_rows']},{'kalshi','polymarket','draftkings'});self.assertEqual(sum(r['settlement_policy']=='UNKNOWN'for r in self.cover['threshold_rows']),54)
 def test_pooled_losses_and_disagreements_reconcile(self):
  for r in self.cover['provider_metrics']:self.assertEqual(r['correct']-r['provider_correct'],r['model_right_provider_wrong']-r['provider_right_model_wrong'])
if __name__=='__main__':unittest.main()
