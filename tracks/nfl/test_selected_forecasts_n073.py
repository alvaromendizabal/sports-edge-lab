"""Actual N072 selected output: horizon roles, partial counts and clock integrity."""
import copy,json,unittest
from datetime import datetime
from pathlib import Path
from selected_review_n073 import render
HERE=Path(__file__).resolve().parent
class ActualN072Publication(unittest.TestCase):
 @classmethod
 def setUpClass(cls): cls.data=json.loads((HERE/'selected_forecasts_n073.json').read_bytes())
 def test_page_reopens_as_exact_saved_data(self): self.assertEqual((HERE/'season_review_n073.html').read_text(),render(self.data))
 def test_both_horizons_retained_without_promotion(self):
  roles=self.data['selected_historical_roles'];self.assertEqual(len(roles),27);self.assertEqual(len({r['role_id']for r in roles}),27)
  for h in (3600,7200):self.assertEqual(sum(r['role_id'].startswith('primary_')and r['comparison_horizon_seconds']==h for r in roles),9)
  self.assertEqual(sum(r['role_id'].startswith('fallback_')for r in roles),9)
  for r in roles:self.assertFalse(r['cross_horizon_global_winner_claimed'])
  self.assertFalse(self.data['automatic_promotion']);self.assertFalse(self.data['latest_owner_execution']['new_champion_promotion'])
  for key in ('new_forecast_issues','new_model_fits','new_model_inference'):self.assertEqual(self.data[key],0)
 def test_partial_totals_not_false_zero(self):
  r=self.data['latest_owner_execution']
  for key in ('new_fits','new_native_fits','new_meta_fits','new_forecasts'):self.assertIsNone(r[key])
  self.assertEqual((r['verified_new_native_fit_minimum'],r['verified_new_meta_fit_minimum'],r['verified_new_fit_minimum']),(21,48,69))
  self.assertEqual(r['verified_distinct_new_forecast_issue_minimum'],1517)
  self.assertEqual(r['verified_issue_row_references']-r['duplicate_issue_references'],1517)
  self.assertEqual(r['frozen_native_cases_reused'],1251);self.assertFalse(r['owner_research_acceptance'])
  self.assertIn('not independent',r['forecast_count_qualification']);self.assertFalse(r['compute_estimate_is_actual_bill'])
 def test_latest_issues_keep_real_pregame_clocks(self):
  count=0
  for game in self.data['games']:
   for target in game['targets'].values():
    for row in target['current_forecasts']:
     issue=datetime.fromisoformat(row['original_issue_at_utc']);kickoff=datetime.fromisoformat(game['kickoff_utc']);fit=datetime.fromisoformat(row['model_completed_at_utc'])
     self.assertLess(issue,kickoff);self.assertLessEqual(fit,issue);self.assertLessEqual(issue,datetime.fromisoformat(self.data['display_cutoff_utc']))
     self.assertAlmostEqual(row['actual_issue_horizon_seconds'],(kickoff-issue).total_seconds(),places=5)
     self.assertIn('not relabeled',row['horizon']);self.assertEqual(row['evidence_kind'],'original_issued');count+=1
  self.assertEqual(count,772)
 def test_complete_denominator_and_explicit_missing_primary_roles(self):
  games=self.data['games'];self.assertEqual(len(games),272);self.assertEqual(len({g['game_id']for g in games}),272)
  self.assertEqual(sum(g['completed_in_saved_census']for g in games),136);self.assertEqual(sum(g['official_time_tbd']for g in games),24)
  self.assertTrue(all(g['kickoff_utc']is None for g in games if g['official_time_tbd']))
  for target,count in [('win',220),('margin',220),('total',332)]:self.assertEqual(sum(len(g['targets'][target]['current_forecasts'])for g in games),count)
  for role in self.data['selected_historical_roles']:
   count=sum(r['current_forecast_available'] for g in games for r in g['targets'][role['target']]['roles'] if r['role_id']==role['role_id'])
   self.assertEqual(count,112 if role['role_id'].startswith('fallback_')or role['role_id']=='primary_total_crps_h3600s'else 27)
  for g in games:
   for t in g['targets'].values():
    for r in t['roles']:
     if not r['current_forecast_available']:self.assertTrue(r['missing_reason'])
 def test_source_counts_do_not_imply_admission(self):
  src=self.data['latest_source_refresh'];self.assertEqual(src['new_normalized_market_rows'],468);self.assertEqual(src['qualified_current_market_winner_baseline_rows'],0)
  self.assertFalse(src['all_sources_complete'])
  for provider in ('kalshi','polymarket'):
   rows=[g['current_source_coverage'][provider]for g in self.data['games']]
   self.assertEqual(sum(r['observation_status']=='CAPTURED_WITH_TARGET_GAPS'for r in rows),27)
   self.assertTrue(all(not r['metric_eligible']and not r['quote_values_published']for r in rows))
 def test_neutral_work_is_not_model_speedup(self):
  run=self.data['latest_owner_execution'];self.assertTrue(run['owner_12_worker_benchmark_completed']);self.assertFalse(run['neutral_benchmark_is_model_fit_speedup'])
  self.assertEqual(run['project_cpu_cap'],12);self.assertEqual([r['requested_workers']for r in run['neutral_benchmark']],[1,2,4,8,12])
  self.assertTrue(all(r['identical_neutral_results_vs_one']for r in run['neutral_benchmark']))
 def test_public_fields_and_no_rounded_rescoring(self):
  text=json.dumps(self.data)
  for token in ('recipe_id','private_source_index','s3://','api_key','FITTED_MODEL.bin','/home/sagemaker-user','sagemaker-sports-edge-lab'):self.assertNotIn(token,text)
  self.assertFalse(self.data['rounding']['metrics_from_rounded_values'])
  for role in self.data['selected_historical_roles']:
   self.assertEqual([r['season']for r in role['season_metrics']],[2024,2025])
   for card in role['season_metrics']:self.assertEqual(card['selection_exposure'],'DEVELOPMENT_EXPOSED')
 def test_embedded_data_escaped(self):
  d=copy.deepcopy(self.data);d['qualifications'].append('</script><script>unsafe()</script>');self.assertNotIn('</script><script>unsafe()</script>',render(d))
if __name__=='__main__':unittest.main()
