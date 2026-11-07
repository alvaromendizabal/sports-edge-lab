"""Reject inflated fits, invented timing and promotion in the N054 recovery overlay."""
import copy,gzip,hashlib,json,pathlib,unittest
from actual_recovery_n055 import load_recovery,validate_recovery,enrich
from build_season_review_n054 import load,RETIRED
from publication_audit_n055 import audit
HERE=pathlib.Path(__file__).resolve().parent
class ActualRecoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.base=load();cls.recovery=validate_recovery(load_recovery());cls.data=enrich(cls.base)
 def test_actual_state_jobs_and_negative_comparisons(self):
  r=self.recovery;ledger=r['market_cutoff_ledger'];created=[x for x in ledger if not x['exact_state_reused']]
  self.assertEqual(len(created),102);self.assertTrue(all(x['optimizer_started_this_attempt'] for x in created));self.assertEqual(sum(x['exact_state_reused'] for x in ledger),114)
  self.assertEqual(r['summary']['new_optimizer_returns'],102);self.assertEqual(r['summary']['new_durable_state_commits'],102)
  self.assertTrue(all(x['holm_full_family_p']==1 and not x['confirmatory_significance_claim'] for x in r['market_comparisons']))
 def test_timing_and_selection_errors_fail(self):
  r=copy.deepcopy(self.recovery);r['market_cutoff_ledger'][0]['maximum_training_label_available_at']=r['market_cutoff_ledger'][0]['cutoff']
  with self.assertRaisesRegex(ValueError,'earlier-label'):validate_recovery(r)
  r=copy.deepcopy(self.recovery);r['summary']['automatic_promotion']=True
  with self.assertRaisesRegex(ValueError,'selection boundary'):validate_recovery(r)
  r=copy.deepcopy(self.recovery);r['owner_raw_issues'][0]['actual_issue_at_utc']=r['owner_raw_issues'][0]['kickoff_utc']
  with self.assertRaisesRegex(ValueError,'issue precedes game'):validate_recovery(r)
 def test_complete_augmented_grid_and_unchanged_source_carrier(self):
  d=self.data;a=audit(d);self.assertEqual(len(d['lanes']),73);self.assertEqual(len(d['model_rows']),59568);self.assertEqual(sum(x['available'] for x in d['model_rows']),10041);self.assertEqual(len(d['all_model_metrics']),647)
  self.assertEqual(len(self.base['lanes']),63);self.assertEqual(len(self.base['model_rows']),51408)
  self.assertEqual(hashlib.sha256((HERE/'current_season_n054.json.gz').read_bytes()).hexdigest(),'282896922e4ce3f393fcccde564f8096d131514981514931dca7f95f0ec056f4')
  for key in ['next','raw_per_game','scale_per_game','provider_rows','conditional_rows','owner_execution']:
   self.assertEqual(d[key],self.base[key],key)
  self.assertEqual(a['owner_attempt']['new_scientific_result_credit'],102);self.assertFalse(a['owner_attempt']['full_durable_evidence_closure'])
 def test_actual_issues_are_separate_from_original_review(self):
  d=self.data;near=[x for x in d['model_rows'] if x['lane_id'].startswith('n054_issued_') and x['available']];far=[x for x in d['model_rows'] if x['lane_id'].startswith('n054_outlook_') and x['available']]
  self.assertEqual((len(near),len(far)),(336,1464));self.assertEqual(len({x['game_id'] for x in near+far}),150)
  self.assertTrue(all(x['issue_origin']=='N054_OWNER' and x['new_owner_issue_credit']==1 and x['new_native_fit_credit']==0 and not x['near_term_T1_equivalence_claimed'] for x in near+far))
  old=[x for x in self.base['model_rows'] if x['lane_id'].startswith('n054_outlook_') and x['available']]
  self.assertTrue(all(x['new_owner_issue_credit']==0 and x['new_review_issue_credit']==1 for x in old));self.assertNotEqual(old[0]['issued_at'],far[0]['issued_at'])
 def test_public_payload_has_no_private_or_retired_fields(self):
  import re
  text=json.dumps(self.recovery);self.assertIsNone(RETIRED.search(text));self.assertIsNone(re.search(r's3://|arn:aws:|X-Amz-|state_identity|state_sha256|component_bindings|direct201_',text))
  self.assertIs(enrich(self.data),self.data)
if __name__=='__main__':unittest.main()
