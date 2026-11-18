"""Real aggregate boundary, counting and selection-regression checks."""
import copy
import json
from pathlib import Path
import unittest
from build_b095_review import build, validate

ROOT=Path(__file__).resolve().parent

class B095ReviewContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.value=json.loads((ROOT/'b095_review.json').read_text())
 def bad(self,change,pattern):
  value=copy.deepcopy(self.value);change(value)
  with self.assertRaisesRegex(ValueError,pattern):validate(value)
 def test_deterministic_report_from_public_evidence(self):
  data=build();self.assertEqual(data,(ROOT/'b095_review.html').read_bytes())
  self.assertNotIn(b'fetch(',data);self.assertNotIn(b'<script src',data)
  self.assertIn(b'B095 prepared',data);self.assertIn(b'RMSE aggregation requires correction',data)
 def test_all_objectives_have_identical_annual_populations(self):
  validate(self.value)
  self.assertEqual(len(self.value['objective_leaders']),14)
  for r in self.value['objective_leaders']:
   self.assertEqual([a['games'] for a in r['annual_metrics']],[1314,1315,205])
  self.bad(lambda d:d['objective_leaders'][0]['annual_metrics'][2].update(games=204),'population')
  self.bad(lambda d:d['objective_leaders'][0]['annual_metrics'][2].update(population_sha256='0'*64),'population')
 def test_unknown_missing_census_cannot_be_zero_or_complete(self):
  self.bad(lambda d:d['populations'][0].update(unknown_missing_count=0),'Unknown full-season')
  self.bad(lambda d:d['populations'][0].update(full_season_census_verified=True),'Unknown full-season')
 def test_test_reporting_labels_cannot_change_validation_evidence(self):
  changed=copy.deepcopy(self.value)
  prior_roles=[(r['public_model_alias'],r['selection_score']) for r in changed['objective_leaders']]
  for r in changed['objective_leaders']:r['annual_metrics'][2]['value']=.123456
  validate(changed)
  self.assertEqual(prior_roles,[(r['public_model_alias'],r['selection_score']) for r in changed['objective_leaders']])
  self.assertEqual(changed['weight_sensitivity'],self.value['weight_sensitivity'])
  self.bad(lambda d:d['selection'].update(test_outcomes_used_for_selection=True),'Test selection')
 def test_rmse_legacy_formula_cannot_be_called_v13_annual_mean(self):
  roles=[r for r in self.value['objective_leaders'] if r['objective'].endswith('_rmse')]
  self.assertEqual(len(roles),4)
  for r in roles:self.assertFalse(r['v13_rmse_policy_satisfied'])
  self.bad(lambda d:next(r for r in d['objective_leaders'] if r['objective']=='margin_rmse').update(saved_score_aggregation='Weighted annual metric'),'RMSE aggregation')
  self.bad(lambda d:next(r for r in d['objective_leaders'] if r['objective']=='margin_rmse').update(v13_rmse_policy_satisfied=True),'RMSE policy')
 def test_validation_score_cannot_silently_change(self):
  self.bad(lambda d:d['objective_leaders'][0].update(selection_score=.99),'Selection score')
  self.bad(lambda d:d['weight_sensitivity'][0].update(leader_score=.01),'Sensitivity score')
 def test_weight_sensitivity_is_complete_and_zero_refit(self):
  self.assertEqual(len(self.value['weight_sensitivity']),70)
  self.bad(lambda d:d['weight_sensitivity'].pop(),'Incomplete sensitivity')
  self.bad(lambda d:d['weight_sensitivity'][0].update(estimator_refits=1),'refitted')
  self.bad(lambda d:d['weight_sensitivity'][0].update(predictions_changed=True),'refitted')
  self.bad(lambda d:d['selection'].update(season_training_row_reweighting=True),'reweighting')
 def test_recovery_and_preserved_work_are_not_new_fits(self):
  b=self.value['latest_verified_execution'];self.assertEqual((b['uncertainty_new'],b['uncertainty_reused']),(1199,2101))
  self.bad(lambda d:d['latest_verified_execution'].update(new_estimator_fits=774),'new fitting')
  self.bad(lambda d:d['latest_verified_execution'].update(uncertainty_new=1200),'Uncertainty accounting')
  self.bad(lambda d:d['latest_verified_execution'].update(research_program_complete=True),'complete program')
 def test_no_unmeasured_capacity_or_invoiced_cost_claim(self):
  self.bad(lambda d:d['latest_verified_execution'].update(measured_full_capacity_passes=1),'capacity pass')
  self.bad(lambda d:d['latest_verified_execution'].update(actual_invoiced_cost_usd=3.01),'invoice')
 def test_failed_return_and_multipart_representation_remain_honest(self):
  self.bad(lambda d:d['prior_execution'].update(physical_return_sealed=True),'failed sealing')
  self.bad(lambda d:d['latest_verified_execution'].update(physical_parts=1),'return representation')
  self.bad(lambda d:d['latest_verified_execution'].update(maximum_part_bytes=536870913),'return representation')
 def test_named_source_gaps_and_product_identities_are_preserved(self):
  rows=self.value['sources']['named_provider_coverage']
  self.assertEqual(len(rows),84)
  self.assertEqual({r['source'] for r in rows},{'draftkings','kalshi','polymarket_us','polymarket_international'})
  self.assertEqual(sum(r['qualified_n'] for r in rows if r['season']=='2026-27' and r['population_status']=='COMPLETED'),36)
  self.assertTrue(all(r['qualified_n']==0 for r in rows if r['population_status']=='UPCOMING'))
  self.bad(lambda d:d['sources']['named_provider_coverage'][0].update(missing_n=0),'missingness denominator')
  self.bad(lambda d:d['sources'].update(all_relevant_data_acquired=True),'complete/live')
 def test_private_payload_fields_paths_and_model_ids_are_rejected(self):
  for key in ('recipe_id','feature_names','model_weights','raw_payload','private_alias_map'):
   self.bad(lambda d:d.update({key:'private'}),'Private payload')
  for text in ('s3://private/location','/home/private/file','arn:aws:example','circa'):
   self.bad(lambda d:d['sources'].update(policy=text),'Private or wrong-sport')
  self.bad(lambda d:d['objective_leaders'][0].update(public_model_alias='a'*64),'Private model identity')
 def test_preparation_cannot_be_an_owner_run_or_promotion(self):
  self.bad(lambda d:d['prepared_successor'].update(owner_execution_started=True),'Preparation')
  self.bad(lambda d:d['selection'].update(full_season_champions_certified=1),'champion promotion')
  self.bad(lambda d:d['publication'].update(model_fits_during_preparation=1),'Publication')
 def test_headline_numbers_match_authenticated_saved_evidence(self):
  r=next(r for r in self.value['objective_leaders'] if r['objective']=='winner_accuracy' and r['horizon_minutes']==60)
  self.assertAlmostEqual(r['annual_metrics'][0]['value'],.6689497716894978)
  self.assertAlmostEqual(r['annual_metrics'][1]['value'],.6783269961977187)
  self.assertAlmostEqual(r['annual_metrics'][2]['value'],.6487804878048781)
  self.assertEqual(self.value['sources']['bookmakers_catalogued'],122)
  self.assertEqual(self.value['sources']['bookmakers_with_any_qualified_cell'],28)

if __name__=='__main__':unittest.main()
